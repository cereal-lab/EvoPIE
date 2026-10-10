import os
import subprocess
import sys
from pathlib import Path


def test_app_refuses_to_start_without_secret_key():
    env = os.environ.copy()
    env.pop("EVOPIE_SECRET_KEY", None)
    repository = Path(__file__).resolve().parents[1]

    result = subprocess.run(
        [sys.executable, "-c", "import evopie"],
        cwd=repository,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "EVOPIE_SECRET_KEY must be set" in result.stderr
