#!/usr/bin/env bash
# Builds the vendored reactivated subtree in a project that consumes it at
# upstream/reactivated/ (see docs/subtree.md). Run from the project root,
# after `npm install` and `uv sync`.
set -euo pipefail

ROOT="$PWD"
SUBTREE="$ROOT/upstream/reactivated"

if [ ! -d "$SUBTREE" ]; then
    echo "No upstream/reactivated/ found. Run from the root of a project that vendors reactivated." >&2
    exit 1
fi

# Generate packages/reactivated/src/generated.tsx from the Python types.
(cd "$SUBTREE" && PATH="$ROOT/node_modules/.bin:$PATH" python scripts/generate_types.py)

# Compile the TypeScript package to dist/.
"$ROOT/node_modules/.bin/tsc" --project "$SUBTREE/packages/reactivated/tsconfig.json"

# Re-link the file: dependency: its bin entries point into dist/, which only
# now exists.
npm install ./upstream/reactivated/packages/reactivated

# The framework is now built. Regenerate your app's schemas against it:
#     python manage.py generate_client_assets
# That call belongs to the consumer (it runs with your app's settings), so it
# is intentionally not made here.
