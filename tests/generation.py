from pathlib import Path

from reactivated.generation import (
    GeneratedModule,
    emit,
    expect,
    expected_outputs,
    prune_orphans,
)


def test_prune_removes_stale_toplevel_output(tmp_path: Path) -> None:
    root = tmp_path / "client" / "generated"
    root.mkdir(parents=True)
    stale = root / "constants.tsx"
    stale.write_text("export const GHOST = 1;")
    fresh = root / "schema.tsx"
    fresh.write_text("// Digest: abc")
    stranger = root / "README.md"
    stranger.write_text("hands off")

    expected_outputs.clear()
    expect(fresh)
    prune_orphans(str(tmp_path))

    assert not stale.exists()
    assert fresh.exists()
    assert stranger.exists()


def test_prune_never_recurses_into_satellites(tmp_path: Path) -> None:
    # Hooks may skip a run without registering their directories.
    root = tmp_path / "client" / "generated"
    (root / "icons").mkdir(parents=True)
    icon = root / "icons" / "Icon0001.tsx"
    icon.write_text("export const Icon0001 = null;")

    expected_outputs.clear()
    prune_orphans(str(tmp_path))

    assert icon.exists()


def test_skip_cache_run_still_registers_expectations(tmp_path: Path) -> None:
    root = tmp_path / "client" / "generated"
    root.mkdir(parents=True)
    module = GeneratedModule("things", "export const A = 1;")

    expected_outputs.clear()
    emit(root, module, skip_cache=True)
    written = root / "things.tsx"
    assert written.exists()

    expected_outputs.clear()
    emit(root, module, skip_cache=False)
    prune_orphans(str(tmp_path))
    assert written.exists()
