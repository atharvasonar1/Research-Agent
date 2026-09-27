"""Explicit local configuration loading without executing shell expressions."""

import os
from pathlib import Path

KEYS = {"GEMINI_API_KEY", "GEMINI_MODEL", "OPENAI_API_KEY", "OPENAI_MODEL", "RESEARCH_PROVIDER"}


def load_config(env_file=None):
    values = {}
    if env_file is not None:
        for number, line in enumerate(Path(env_file).read_text(encoding="utf-8").splitlines(), 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            key, separator, value = line.partition("=")
            key = key.strip()
            if not separator:
                raise ValueError(f"Invalid env-file assignment on line {number}")
            if key not in KEYS:
                continue
            value = value.strip()
            if value.startswith(('"', "'")):
                if len(value) < 2 or value[-1] != value[0]:
                    raise ValueError(f"Invalid env-file quoting on line {number}")
                value = value[1:-1]
            values[key] = value
    values.update({key: os.environ[key] for key in KEYS if key in os.environ})
    return values
