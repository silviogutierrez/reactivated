import subprocess
import os
from pathlib import Path
from typing import Optional
from django.conf import settings


client_path = Path(settings.BASE_DIR).joinpath("client/")
client_config_src_path = client_path.joinpath("reactivated.conf.tsx")


def build_client_config(watch=False, **kwargs) -> Optional[subprocess.Popen]:
    if not client_config_src_path.exists():
        return
    config = {
        "module": "commonjs",
        "moduleResolution": "node",
        "jsx": "react",
        "target": "es2021",
        "esModuleInterop": True,
        "outDir": client_path,
    }
    if watch:
        config["watch"] = True
        config["preserveWatchOutput"] = True

    args = []
    for flag, value in config.items():
        args.append(f"--{flag}")
        if value and value is not True:
            args.append(value)

    tsc_process = subprocess.Popen(
        [
            "npm",
            "exec",
            "tsc",
            "--",
            *args,
            client_config_src_path,
        ],
        env={**os.environ.copy()},
        cwd=settings.BASE_DIR,
        **kwargs,
    )
    return tsc_process
