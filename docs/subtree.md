# Vendoring Reactivated as a Subtree

Instead of installing reactivated from PyPI and npm, you can vendor the framework
source directly into your project. This enables live editing of the framework during
development: fix a bug or add a feature in the vendored copy, use it immediately in
your app, and push the change upstream as a PR when it's ready.

## Directory layout

Vendor the repo at `upstream/reactivated/` in your project root:

```
upstream/reactivated/           # vendored copy of github.com/silviogutierrez/reactivated
├── reactivated/                # Python package (Django app)
├── packages/reactivated/       # TypeScript package (npm)
├── scripts/generate_types.py   # Generates TS types from Python
├── pyproject.toml              # Python package metadata
└── ...                         # tests, sample, website, etc.
```

### Why `upstream/reactivated` and not `reactivated`

The directory cannot be named `reactivated/` at the project root because Python's
import system would find it as a namespace package (it has no `__init__.py` at the top
level) before the editable install's finder can intercept. Nesting it under `upstream/`
eliminates the collision between the directory name and the Python package name.

## Wiring it up

### Python — `pyproject.toml`

Point uv at the local source with an editable install:

```toml
[project]
dependencies = [
    "reactivated",
]

[tool.uv.sources]
reactivated = { path = "./upstream/reactivated", editable = true }
```

### Node — `package.json`

```jsonc
"dependencies": {
    "reactivated": "file:upstream/reactivated/packages/reactivated"
}
```

## Build steps

After cloning or pulling changes to the subtree, install dependencies, run the
subtree's own build script from your project root, then regenerate your app's
schemas:

```bash
uv sync                          # Install Python deps (editable reactivated)
npm install                      # Install Node deps (symlinks to subtree)

./upstream/reactivated/packages/reactivated/scripts/build_subtree.sh
python manage.py generate_client_assets
```

The script does, in order:

1. Generate types (writes `packages/reactivated/src/generated.tsx`).
2. Compile the TypeScript package to `dist/` (required once before the dev server
   works).
3. Re-run `npm install` against the subtree package — its `bin` entries point into
   `dist/`, which only exists after the compile.

It builds the framework only; it never executes your application. Regenerating the
client schema and server `pick_schema` (`manage.py generate_client_assets`) runs
with your app's settings and models, so that call stays in your hands — make it
after the script, from your project's `setup` helper, CI setup action, and release
script, so every environment builds the same way.

## Live editing

Both Python and Node changes are picked up without reinstalling:

- **Python**: The editable install means changes to
  `upstream/reactivated/reactivated/*.py` are immediately visible — no `uv sync`
  needed.
- **Node**: npm creates a symlink (`node_modules/reactivated` ->
  `upstream/reactivated/packages/reactivated`). Rebuild the TypeScript after editing
  and changes are visible through the symlink:

```bash
# One-off build:
npx tsc -p upstream/reactivated/packages/reactivated/tsconfig.json

# Watch mode (auto-rebuilds on save):
npx tsc -p upstream/reactivated/packages/reactivated/tsconfig.json --watch
```

## CI and Docker

CI and Docker images must build reactivated from source. The sequence:

1. Install Python deps (`uv sync` — installs reactivated from local source)
2. Install Node deps (`npm ci` — gets peer deps like `json-schema-to-typescript`,
   `tsc`)
3. Generate TypeScript types (`python scripts/generate_types.py`)
4. Compile TypeScript (`tsc` in `packages/reactivated/`)
5. Re-install reactivated (`npm install ./upstream/reactivated/packages/reactivated`)
   — required because `npm ci` copies instead of symlinking, so the copy must be
   updated with the freshly built `dist/`

In Docker, use `uv sync --no-editable` since live editing isn't needed in production.
Exclude subtree dev artifacts from the build context in `.dockerignore` (`.venv/`,
`node_modules/`, `sample/`, `development/`, `website/`, `tests/`).

## Why not `git subtree` or `git submodule`?

- **`git subtree`** is fundamentally incompatible with squash merges. `git subtree pull`
  creates two-parent merge commits that link upstream history to the parent repo.
  `git subtree split/push` walks the commit graph looking for those merge commits to
  know what's already been synced. Squash merging (GitHub's default for PRs) flattens
  those into single-parent commits, severing the link. The next `split` either
  reprocesses the entire history (producing duplicate commits upstream) or fails
  outright with "Can't squash-merge: '<dir>' was never added". On top of that, GitHub's
  squash merge rewrites commit messages with CRLF line endings, which breaks the
  `git-subtree-dir:` / `git-subtree-split:` markers that `git subtree` (a bash script)
  greps for. If either repo uses squash merges, `git subtree` is broken by design.
- **`git submodule`** adds deployment complexity (submodule init/update in CI, Docker,
  every clone) and makes the subtree feel second-class. Vendoring keeps everything in
  one repo with one `git clone`.

Instead, use **patch-based sync**: generate diffs between known commits and apply them
with `git apply --3way`, which preserves local additions on both sides and uses git's
merge machinery to handle conflicts.

## Sync version tracking

The subtree's `pyproject.toml` contains the `version` field (e.g. `0.50.1`). This is
the **upstream version the subtree is synced to**. Your project may have local
additions on top, but this version tells you the upstream baseline.

To find what's new upstream since the last sync:

```bash
REACTIVATED=/path/to/reactivated/checkout
SYNCED_VERSION=$(grep '^version' upstream/reactivated/pyproject.toml | sed 's/.*"\(.*\)"/\1/')

cd $REACTIVATED && git checkout main && git pull
git log --oneline v$SYNCED_VERSION..HEAD
```

## Pushing changes upstream (creating a PR)

When you've accumulated changes in `upstream/reactivated/` and want to contribute them
back:

1. **Find the baseline commit** — the last commit in your project that synced with
   upstream:

    ```bash
    git log --oneline -- upstream/reactivated/ | head -20
    ```

2. **Generate a patch** from your subtree changes, stripping the
   `upstream/reactivated/` prefix so paths match this repo's layout:

    ```bash
    git diff <baseline>..HEAD -- upstream/reactivated/ \
      | sed -E \
        -e 's|^diff --git a/upstream/reactivated/(.+) b/upstream/reactivated/(.+)|diff --git a/\1 b/\2|' \
        -e 's|^--- a/upstream/reactivated/|--- a/|' \
        -e 's|^\+\+\+ b/upstream/reactivated/|+++ b/|' \
        -e 's|^rename from upstream/reactivated/|rename from |' \
        -e 's|^rename to upstream/reactivated/|rename to |' \
      > /tmp/reactivated-changes.patch
    ```

3. **Create a branch on a reactivated checkout** from `main`, apply the patch:

    ```bash
    cd /path/to/reactivated/checkout
    git checkout main && git pull
    git checkout -b downstream/my-changes main
    git apply --3way /tmp/reactivated-changes.patch
    ```

    `--3way` uses git's merge machinery, so conflicts are resolvable with standard
    tools instead of failing outright.

4. **Rebuild lock files** if `pyproject.toml` or
   `packages/reactivated/package.json` changed:

    ```bash
    uv lock
    npm install --package-lock-only
    ```

5. **Commit, push, create a PR** against `silviogutierrez/reactivated`.

6. After the PR merges, pull the squashed result back down using the patch flow below.
   This picks up any fixes made during review.

### Common pitfalls

- **Generate the patch from the full subtree diff — don't cherry-pick files.** A
  hand-picked patch is how a utility lands upstream without its tests (it happened:
  #451 shipped `flatten_schema` bare; #453 had to port the test after the fact).
- **npm peer dep conflicts**: This repo's integration test creates a fresh project
  with no lock file, so it resolves peer deps from the registry. If upstream packages
  bumped (e.g. `tsx` pulling a newer `esbuild`), bump pinned peer deps in
  `packages/reactivated/package.json` and regenerate `package-lock.json`.
- **Prettier on generated files**: Auto-generated files like `client/schema.tsx` must
  be in `.gitignore` (prettier reads `.gitignore` to skip files). Check both `sample/`
  and `website/` directories.
- **Lock files**: rebuild them inside this repo's nix-shell
  (`npm install --package-lock-only`).

## Pulling upstream changes

When this repo has new changes you want in your project (whether from your own merged
PRs or independent upstream work):

```bash
REACTIVATED=/path/to/reactivated/checkout
SYNCED_VERSION=$(grep '^version' upstream/reactivated/pyproject.toml | sed 's/.*"\(.*\)"/\1/')

# Update the reactivated checkout
cd $REACTIVATED && git checkout main && git pull

# Check what's new
git log --oneline v$SYNCED_VERSION..HEAD

# Generate a patch of upstream changes since the last sync
git diff v$SYNCED_VERSION..HEAD > /tmp/reactivated-upstream.patch

# Add the upstream/reactivated/ prefix so paths match your project's layout
sed -E \
  -e 's|^diff --git a/(.+) b/(.+)|diff --git a/upstream/reactivated/\1 b/upstream/reactivated/\2|' \
  -e 's|^--- a/|--- a/upstream/reactivated/|' \
  -e 's|^\+\+\+ b/|+++ b/upstream/reactivated/|' \
  -e 's|^rename from (.+)|rename from upstream/reactivated/\1|' \
  -e 's|^rename to (.+)|rename to upstream/reactivated/\1|' \
  /tmp/reactivated-upstream.patch > /tmp/reactivated-prefixed.patch

# Apply with 3-way merge (preserves your local additions, conflicts are resolvable)
cd /path/to/your/project
git apply --3way /tmp/reactivated-prefixed.patch

# Regen lock files
uv sync
npm install --package-lock-only
```

If there are conflicts, `--3way` leaves standard conflict markers that you resolve
normally. The common cause is a file that both sides modified (e.g. both added code to
the end of the same test file). Resolve by keeping both sides.

### Reconcile peer pins in the lock file

`npm install --package-lock-only` records the vendored package's new version but does
**not** re-resolve packages the lock already pins. This package pins its peers exactly
(e.g. `"vite": "8.0.13"`), so if a sync bumps a peer pin, the lock keeps the old
resolution and npm prints an `ERESOLVE overriding peer dependency` warning on every
install — forever, without failing.

If the sync diff touches `peerDependencies` in `packages/reactivated/package.json`,
update each changed pin and verify the invariant — a strict install succeeds:

```bash
npm update vite   # once per changed peer pin

rm -rf node_modules
npm install --strict-peer-deps   # fails on any peer conflict
```

Consumer CI should run `npm install --strict-peer-deps` in its setup action so pin
drift fails PRs instead of warning forever.

While you're in the lock file: if the subtree ever moved (e.g. from a differently
named directory), the lock may retain an entry for the old path — npm never prunes
entries for directories that no longer exist, and their stale metadata feeds the
resolver. Delete any `packages` key that doesn't correspond to a real directory.

### Why not rsync?

`rsync --delete` overwrites the entire subtree, destroying any local additions
(utilities, tests, etc.) that haven't been pushed upstream yet. It also picks up
untracked files from the upstream checkout (build artifacts, editor config) that
shouldn't be vendored. The patch approach only applies what upstream actually changed
in git.

## Lint exclusions

The vendored source has its own lint configs. To avoid conflicts with your project's
linters, exclude `upstream/reactivated/` from them:

- **ruff**: `exclude = ["upstream/reactivated/"]` in `pyproject.toml`
- **mypy**: add `upstream/reactivated/` to `exclude` in `mypy.ini`, add
  `./upstream/reactivated` to `mypy_path`, plus `follow_imports = silent` for
  `reactivated` and `reactivated.*` modules (suppresses errors within reactivated
  source while still type-checking your usage of it)
- **eslint**: add `"upstream/reactivated/"` to your ignores
- **prettier**: add `upstream/reactivated/packages/reactivated/src/generated.tsx` to
  `.gitignore` (prettier reads `.gitignore` patterns by default)
- **shellcheck/shfmt/nixfmt and fix scripts**: if your lint scripts enumerate files
  with `git ls-files`, filter the subtree out
  (`grep -v '^upstream/reactivated/'`) — the vendored shell/nix files follow this
  repo's conventions, not yours

## Running reactivated's test suite

The subtree carries reactivated's own tests and Nix environment. To run them, enter
the subtree and use its own tooling — completely independent from your project's
checks:

```bash
cd upstream/reactivated
nix-shell --command "scripts/test.sh"
```

Consider wiring this up as a dedicated CI job so subtree changes are validated against
reactivated's own suite before you push them upstream.

## Ejecting back to published packages

To switch back to PyPI and npm, no source changes are needed — imports work
identically with the published packages:

1. In `pyproject.toml`: pin `"reactivated>=LATEST_VERSION"` and delete the
   `[tool.uv.sources]` override, then `uv sync`.
2. In `package.json`: change `"file:upstream/reactivated/packages/reactivated"` to
   `"^LATEST_VERSION"`, then `npm install`.
3. Remove any subtree-specific build steps from CI and Docker (the source COPY lines,
   type generation, tsc, re-install of the built package — `uv sync` and `npm ci`
   stay and pull the published packages instead). The runtime layout is unchanged:
   the published npm package puts built files in the same `node_modules` locations.
4. Remove the lint exclusions and any `.dockerignore` entries for the subtree.
5. `rm -rf upstream/reactivated/`

Then verify: `uv sync && npm install`, regenerate client assets
(`python manage.py generate_client_assets`), and run your project's checks.
