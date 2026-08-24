import os
import pathlib
import subprocess
import sys


def test_refuses_to_write_empty_output_when_json2ts_fails(
    tmp_path: pathlib.Path,
) -> None:
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    fake_npm = fake_bin / "npm"
    fake_npm.write_text("#!/bin/sh\nexit 1\n")
    fake_npm.chmod(0o755)

    generated = pathlib.Path("packages/reactivated/src/generated.tsx")
    before = generated.read_bytes() if generated.exists() else None

    result = subprocess.run(
        [sys.executable, "scripts/generate_types.py"],
        env={**os.environ, "PATH": f"{fake_bin}:{os.environ['PATH']}"},
        capture_output=True,
    )

    assert result.returncode != 0
    assert b"refusing to write an empty generated.tsx" in result.stderr

    after = generated.read_bytes() if generated.exists() else None
    assert after == before
