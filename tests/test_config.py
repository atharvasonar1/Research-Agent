from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gtm_research.config import load_config


class ConfigTests(unittest.TestCase):
    def test_explicit_file_and_environment_precedence_without_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env.local'
            path.write_text('GEMINI_API_KEY="hidden-key"\nGEMINI_MODEL=from-file\nRESEARCH_PROVIDER=gemini\nUNRELATED=ignored\nOPENAI_MODEL=$(touch never-execute)\n')
            with patch.dict('os.environ', {'GEMINI_MODEL': 'from-env'}, clear=True):
                config = load_config(path)
            self.assertEqual(config['GEMINI_API_KEY'], 'hidden-key')
            self.assertEqual(config['GEMINI_MODEL'], 'from-env')
            self.assertEqual(config['OPENAI_MODEL'], '$(touch never-execute)')
            self.assertNotIn('UNRELATED', config)

    def test_no_implicit_env_file_loading(self):
        with patch.dict('os.environ', {}, clear=True):
            self.assertEqual(load_config(), {})

    def test_invalid_file_error_does_not_expose_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / '.env.local'
            for content in ('secret-key-without-assignment', 'GEMINI_API_KEY="secret'):
                path.write_text(content)
                with patch.dict('os.environ', {}, clear=True):
                    with self.assertRaises(ValueError) as error:
                        load_config(path)
                self.assertNotIn('secret', str(error.exception))

    def test_interactive_setup_preserves_other_settings_and_hides_key(self):
        import importlib.util
        import os
        script = Path(__file__).resolve().parents[1] / 'scripts' / 'configure_gemini.py'
        spec = importlib.util.spec_from_file_location('configure_gemini', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / '.env.local'
            target.write_text('OPENAI_MODEL=existing\nGEMINI_API_KEY=old\n')
            with patch.object(module, '__file__', str(root / 'scripts' / 'configure_gemini.py')), \
                 patch.object(module.sys.stdin, 'isatty', return_value=True), \
                 patch.object(module, 'getpass', return_value='new-hidden-key'), \
                 patch('builtins.print') as output:
                module.main()
            text = target.read_text()
            self.assertIn('OPENAI_MODEL=existing', text)
            self.assertIn('GEMINI_API_KEY=new-hidden-key', text)
            self.assertIn('GEMINI_MODEL=gemini-3.8-flash', text)
            self.assertEqual(text.count('GEMINI_API_KEY='), 1)
            self.assertEqual(os.stat(target).st_mode & 0o777, 0o600)
            self.assertNotIn('new-hidden-key', str(output.call_args_list))
