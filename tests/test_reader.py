import io
import socket
import time
from unittest.mock import Mock, patch
import unittest

from gtm_research.reader import Response, ToolError, WebsiteReader, canonical_url, request, resolve_public
from helpers import ROOT, SELLERS, fixture_reader


class ReaderTests(unittest.TestCase):
    def test_links_and_visible_text(self):
        reader = fixture_reader()
        page = reader.fetch(ROOT)
        self.assertEqual(page["links"], [SELLERS])
        self.assertNotIn("invented script-only fact", page["text"])
        self.assertIn("Our team serves Harbor City.", page["text"])

    def test_cached_page_avoids_duplicate_network_call(self):
        transport = Mock(return_value=Response(200, {"content-type": "text/plain"}, b"Team"))
        reader = fixture_reader(transport)
        self.assertIs(reader.fetch(ROOT), reader.fetch(ROOT))
        self.assertEqual(transport.call_count, 1)

    def test_url_validation(self):
        for url in ("file:///etc/passwd", "https://a:b@team.example/", "https://team.example:8080/",
                    "https://team.example/\n", "https://team.example\\@evil.example/", "https://team.example./"):
            with self.subTest(url=url), self.assertRaises(ToolError):
                canonical_url(url)
        self.assertEqual(canonical_url("https://TEAM.example:443#fragment"), ROOT)

    def test_private_and_mixed_dns_answers_blocked(self):
        for addresses in (["127.0.0.1"], ["10.1.2.3"], ["169.254.169.254"], ["::1"],
                          ["fc00::1"], ["224.0.0.1"], ["ff02::1"], ["64:ff9b::a00:1"], ["fec0::1"], ["0.0.0.0"], ["100.64.0.1"], ["::ffff:127.0.0.1"],
                          ["93.184.216.34", "192.168.1.2"]):
            records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 443)) for ip in addresses]
            with self.subTest(addresses=addresses), patch("socket.getaddrinfo", return_value=records):
                with self.assertRaisesRegex(ToolError, "blocked_address"):
                    resolve_public("team.example", 443, 1)

    def test_public_dns_address_is_pinned_for_transport(self):
        transport = Mock(return_value=Response(200, {"content-type": "text/plain"}, b"Team"))
        records = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
        with patch("socket.getaddrinfo", return_value=records) as dns:
            reader = WebsiteReader(ROOT, transport=transport)
            reader.fetch(ROOT)
        self.assertEqual(dns.call_count, 1)
        self.assertEqual(transport.call_args.args[1], "93.184.216.34")

    def test_private_destination_never_reaches_transport(self):
        transport = Mock()
        with patch("socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))]):
            with self.assertRaisesRegex(ToolError, "blocked_address"):
                WebsiteReader("127.0.0.1", transport=transport).fetch("https://127.0.0.1/")
        transport.assert_not_called()

    def test_dns_timeout_and_failure(self):
        with patch("socket.getaddrinfo", side_effect=socket.gaierror):
            with self.assertRaisesRegex(ToolError, "dns_error"):
                resolve_public("team.example", 443, 1)
        with patch("socket.getaddrinfo", side_effect=lambda *a, **kw: time.sleep(0.1)):
            with self.assertRaisesRegex(ToolError, "timeout"):
                resolve_public("team.example", 443, 0.005)

    def test_external_redirect_rejected_before_second_request(self):
        for target in ("https://evil.example/", "https://www.team.example/", "http://169.254.169.254/", "//evil.example/"):
            transport = Mock(return_value=Response(302, {"location": target}, b""))
            with self.subTest(target=target), self.assertRaisesRegex(ToolError, "blocked_host"):
                fixture_reader(transport).fetch(ROOT)
            self.assertEqual(transport.call_count, 1)

    def test_same_host_redirect_and_source_provenance(self):
        transport = Mock(side_effect=[Response(301, {"location": "/home"}, b""),
                                     Response(200, {"content-type": "text/plain"}, b"Our team")])
        reader = fixture_reader(transport)
        page = reader.fetch(ROOT)
        self.assertEqual(page["url"], ROOT + "home")
        self.assertEqual(page["requested_url"], ROOT)
        self.assertEqual(page["redirects"], [{"from": ROOT, "to": ROOT + "home"}])
        self.assertIs(reader.pages[ROOT], reader.pages[ROOT + "home"])

    def test_redirect_rechecks_dns_and_blocks_rebinding(self):
        transport = Mock(return_value=Response(302, {"location": "/home"}, b""))
        records = [[(2, 1, 6, "", ("93.184.216.34", 443))], [(2, 1, 6, "", ("127.0.0.1", 443))]]
        with patch("socket.getaddrinfo", side_effect=records):
            with self.assertRaisesRegex(ToolError, "blocked_address"):
                WebsiteReader(ROOT, transport=transport).fetch(ROOT)
        self.assertEqual(transport.call_count, 1)

    def test_redirect_limit_and_downgrade(self):
        transport = Mock(return_value=Response(302, {"location": "/loop"}, b""))
        with self.assertRaisesRegex(ToolError, "redirect_limit"):
            fixture_reader(transport, max_redirects=2).fetch(ROOT)
        self.assertEqual(transport.call_count, 3)
        with self.assertRaisesRegex(ToolError, "blocked_downgrade"):
            fixture_reader(lambda *a: Response(302, {"location": "http://team.example/"}, b"")).fetch(ROOT)

    def test_response_errors(self):
        cases = [
            (Response(404, {}, b""), "http_404"),
            (Response(200, {"content-type": "application/pdf"}, b"pdf"), "unsupported_content_type"),
            (Response(200, {"content-type": "text/plain"}, b" " * 11), "response_too_large"),
            (Response(200, {"content-type": "text/plain"}, b" "), "empty_page"),
        ]
        for response, code in cases:
            with self.subTest(code=code), self.assertRaisesRegex(ToolError, code):
                fixture_reader(lambda *a: response, max_bytes=10).fetch(ROOT)

    def test_page_deadline_checked_after_transport(self):
        def slow(*args):
            time.sleep(0.01)
            return Response(200, {"content-type": "text/plain"}, b"Team")
        with self.assertRaisesRegex(ToolError, "timeout"):
            fixture_reader(slow, timeout=0.001).fetch(ROOT)


class TransportTests(unittest.TestCase):
    def call_transport(self, body, headers=(), cap=8, status=200, https=False):
        response = Mock(status=status)
        response.getheaders.return_value = list(headers)
        response.read1.side_effect = io.BytesIO(body).read
        sock = Mock()
        conn = Mock()
        conn.getresponse.return_value = response
        with patch("socket.create_connection", return_value=sock) as connect, \
             patch("http.client.HTTPConnection", return_value=conn), \
             patch("gtm_research.reader.truststore.SSLContext") as context:
            context.return_value.wrap_socket.return_value = sock
            result = request(("https" if https else "http") + "://team.example/", "93.184.216.34", 1, cap)
            self.assertEqual(connect.call_args.args[0], ("93.184.216.34", 443 if https else 80))
            if https:
                import ssl
                context.assert_called_once_with(ssl.PROTOCOL_TLS_CLIENT)
                context.return_value.wrap_socket.assert_called_once_with(sock, server_hostname="team.example")
            conn.close.assert_called_once()
            return result

    def test_actual_transport_reads_at_most_cap_plus_one(self):
        with self.assertRaisesRegex(ToolError, "response_too_large"):
            self.call_transport(b"123456789")
        self.assertEqual(self.call_transport(b"12345678").body, b"12345678")

    def test_content_length_cap_and_incomplete_body(self):
        with self.assertRaisesRegex(ToolError, "response_too_large"):
            self.call_transport(b"", [("Content-Length", "9")])
        with self.assertRaisesRegex(ToolError, "incomplete_response"):
            self.call_transport(b"123", [("Content-Length", "8")])

    def test_compression_is_rejected(self):
        with self.assertRaisesRegex(ToolError, "unsupported_encoding"):
            self.call_transport(b"abc", [("Content-Encoding", "gzip")])

    def test_tls_uses_original_hostname(self):
        self.assertEqual(self.call_transport(b"abc", https=True).body, b"abc")

    def test_redirect_body_not_downloaded(self):
        self.assertEqual(self.call_transport(b"123456789", [("Location", "/home")], status=302).body, b"")

    def test_socket_watchdog_interrupts_stalled_body(self):
        from threading import Event
        interrupted = Event()
        response = Mock(status=200)
        response.getheaders.return_value = []

        def stalled_read(size):
            if not interrupted.wait(1):
                raise AssertionError("socket watchdog did not fire")
            return b""

        response.read1.side_effect = stalled_read
        sock = Mock()
        sock.shutdown.side_effect = lambda *args: interrupted.set()
        conn = Mock()
        conn.getresponse.return_value = response
        with patch("socket.create_connection", return_value=sock), \
             patch("http.client.HTTPConnection", return_value=conn):
            with self.assertRaisesRegex(ToolError, "timeout"):
                request("http://team.example/", "93.184.216.34", 0.02, 8)
        self.assertTrue(interrupted.is_set())
        conn.close.assert_called_once()

    def test_native_trust_context_keeps_certificate_and_hostname_checks(self):
        import ssl
        import truststore
        context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(context.check_hostname)
