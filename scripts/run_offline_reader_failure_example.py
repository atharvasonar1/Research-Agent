"""Save a simulated oversized-reader failure and cached repeat without network."""

import argparse
import json

from gtm_research.agent import run_research
from gtm_research.model import Action
from gtm_research.reader import Response, WebsiteReader


ROOT = "https://oversized.example/"


class RepeatingOfflineModel:
    model = "offline-reader-failure-fixture"
    provider = "offline"

    def decide(self, state, timeout):
        return Action("fetch_page", {"url": ROOT})


class SimulatedOversizedTransport:
    def __init__(self):
        self.calls = 0

    def __call__(self, url, address, timeout, max_bytes):
        self.calls += 1
        return Response(200, {"content-type": "text/plain"}, b"x" * (max_bytes + 1))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="runs/offline-reader-failure-example")
    args = parser.parse_args(argv)
    transport = SimulatedOversizedTransport()
    reader = WebsiteReader(
        ROOT,
        resolver=lambda *unused: "93.184.216.34",
        transport=transport,
        max_bytes=250_000,
        diagnostic_label="SIMULATED 250001-byte cutoff; not a live website measurement",
    )
    result = run_research(
        RepeatingOfflineModel(), reader, output_dir=args.output_dir, max_steps=8,
    )
    print("SIMULATED fixture: observed 250,001 bytes against a 250,000-byte cap.")
    print(f"Network transport calls: {transport.calls} (the repeated fetch used the failure cache)")
    print(json.dumps(result, indent=2))
    print(f"Trace: {result['run_dir']}/trace.json")
    print(f"Result: {result['run_dir']}/result.json")
    return 0 if result["reason"] == "no_researchable_sources" and transport.calls == 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
