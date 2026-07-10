"""Generated TypeScript modules contributed by app code.

Hooks decorated with ``@generate`` return ``GeneratedModule`` instances —
pure strings. Digests, atomic writes, stale-file pruning, and the output
location (``client/generated/``) all live here, once.
"""

import dataclasses
import hashlib
import logging
import os
import tempfile
from pathlib import Path
from typing import Protocol

logger = logging.getLogger("django.server")


@dataclasses.dataclass
class GeneratedModule:
    """One generated module: ``name="icons"`` lands at
    ``client/generated/icons.tsx`` — or, when ``files`` is given, at
    ``client/generated/icons/index.tsx`` plus one file per entry."""

    name: str
    content: str
    files: dict[str, str] = dataclasses.field(default_factory=dict)


class GenerateFunction(Protocol):
    def __call__(self) -> "list[GeneratedModule]": ...


generate_callbacks: list[GenerateFunction] = []


def generate(function: GenerateFunction) -> GenerateFunction:
    generate_callbacks.append(function)
    return function


def generated_path(name: str) -> Path:
    """Where a GeneratedModule named ``name`` lands (directory form)."""
    from django.conf import settings

    return Path(settings.BASE_DIR) / "client" / "generated" / name / "index.tsx"


# Rebuilt every generation run: everything the pipeline intends to produce,
# registered BEFORE each emitter's digest short-circuit so up-to-date files
# that skip their write still count as expected.
expected_outputs: set[Path] = set()

# generator.mts (a subprocess) writes these directly and cannot register.
NODE_OUTPUTS = ("context.tsx", "forms.tsx", "urls.tsx")


def expect(path: Path) -> None:
    expected_outputs.add(path.resolve())


def prune_orphans(base_dir: str) -> None:
    """Delete top-level generated files no current emitter produces. A
    generator that stops emitting a file otherwise leaves the stale copy
    behind locally, masking the deletion until a fresh checkout diverges.

    Top-level only, deliberately: satellite directories prune their own
    stragglers in emit(), and hooks may skip a run entirely (source-digest
    early exit) without registering their directories — recursing here
    would eat their up-to-date output."""
    root = Path(base_dir) / "client" / "generated"
    if not root.exists():
        return
    for name in NODE_OUTPUTS:
        expect(root / name)
    for path in sorted(root.iterdir()):
        if path.is_dir() or path.resolve() in expected_outputs:
            continue
        if path.suffix in (".tsx", ".ts"):
            path.unlink()
            logger.warning(
                "pruned orphan %s — stale output of an older generator", path
            )
        else:
            logger.warning(
                "unexpected file %s in client/generated (left in place)", path
            )


def write_atomic(path: Path, content: str) -> None:
    expect(path)
    fd, temp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as handle:
        handle.write(content)
    os.replace(temp, path)


def emit(root: Path, module: GeneratedModule, skip_cache: bool) -> None:
    payload = module.content + "".join(
        name + body for name, body in sorted(module.files.items())
    )
    digest = hashlib.sha1(payload.encode()).hexdigest()
    banner = f"// Digest: {digest}\n"

    index = (
        root / module.name / "index.tsx"
        if module.files
        else root / f"{module.name}.tsx"
    )

    expect(index)
    for name in module.files:
        expect(index.parent / name)

    if skip_cache is False and index.exists():
        with open(index) as existing:
            if digest in existing.read(len(banner) + 10):
                return

    index.parent.mkdir(parents=True, exist_ok=True)
    # Satellites first, index last: the index is the only entry point, so a
    # reader that sees the new index sees complete satellites.
    for name, body in module.files.items():
        write_atomic(index.parent / name, body)
    write_atomic(index, banner + module.content)
    if module.files:
        for straggler in index.parent.glob("*.tsx"):
            if straggler.name != "index.tsx" and straggler.name not in module.files:
                straggler.unlink()


def run_generate_callbacks(base_dir: str, skip_cache: bool) -> None:
    root = Path(base_dir) / "client" / "generated"
    for callback in generate_callbacks:
        for module in callback():
            emit(root, module, skip_cache)
