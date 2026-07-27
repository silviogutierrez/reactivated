# The Dev Server

Start everything with one command:

```bash
reactivate
```

That's the whole interface. Under the hood you get Django running as ASGI
under uvicorn, Vite serving your frontend with hot module replacement, a
TypeScript compiler in watch mode, and client asset generation. Spawned
together, wired together, and torn down together when you hit Ctrl-C.

Nothing here needs Nix. `reactivate` is a console script installed with the
Python package; it wants `DEBUG_PORT` set and your node modules installed,
and that's it.

## Two modes

**Vite mode** is the default. Vite owns the user-facing port and proxies
everything that isn't an asset to Django. You get HMR, instant saves, the
usual modern niceties. Startup blocks until Vite is actually listening rather
than guessing with a sleep, and fails loudly if Vite dies on boot. No
half-started server that looks alive and serves nothing.

**Build mode** (`reactivate --build`) skips the Vite dev server entirely: a
full production client build, served by Django, rebuilt on every change. No
HMR and slower per save, but a page load is a handful of requests instead of
hundreds of unbundled modules. That's the mode for testing behind proxies and
tunnels, where a module waterfall is unbearable.

## Smart reload

Change server code and the dev server doesn't just restart Django. It
regenerates the client assets too, so a new pick, procedure, or template shows
up in TypeScript on the very next save. Types can't go stale mid-session. In
build mode it rebuilds the client bundle as well.

The file watches are scoped to `server/` (plus `client/` in build mode) on
purpose. An unscoped watcher registers a recursive watch over `node_modules`
and `.git` and melts your filesystem event daemon. Test files are excluded
from the watch, so saving a test doesn't bounce the server you're testing
against.

## Configuration

Everything is environment-driven; there are no flags to memorize beyond
`--build`.

- **`DEBUG_PORT`** (required): the user-facing port. Projects created with the
  [setup script](/documentation/getting-started/) already derive and export
  this in their shell environment, so there's nothing to do. On an existing
  project, export it yourself; any free port works. If it's missing, startup
  is an explicit error telling you so.
- **`REACTIVATED_PROCESSES`**: newline-separated sidecar commands. A database
  tunnel, a worker, whatever your project needs running alongside. They spawn
  with the server and get cleaned up with it. `$VAR` references resolve at
  spawn time, including the runtime ports the server just allocated. A
  sidecar that exits immediately warns instead of killing the server, since
  the usual cause is another checkout already holding the shared resource.
- **`DEV_URL` / `DEV_EXTRA_URLS`**: what the startup banner prints when your
  project fronts the server through richer hostnames or an HTTPS proxy.
  Without them, plain localhost.

## Port safety

If something is already serving on `DEBUG_PORT`, usually another checkout's
dev server, startup is an explicit error naming the port. This matters more
than it sounds: in Vite mode the loser of a port race binds a wildcard socket
that macOS happily lets coexist with the winner's, so it "starts" cleanly and
never receives a single request. We'd rather tell you.

## What about runserver?

`python manage.py runserver` still works, unchanged. Reactivated patches it to
generate client assets and spawn Vite and the TypeScript watcher at boot, same
as it always has. Either way, you get the full stack.

But `reactivate` is better, and here's how. Runserver generates your client
assets once, at boot; `reactivate` regenerates them on every server change, so
your TypeScript never drifts from your Python within a session. Runserver has
no build mode. It can't tell you another worktree already owns your port; it
has no concept of sidecar processes; and Django runs under WSGI's dev server
instead of uvicorn, so async views aren't actually async while you develop.

Use `runserver` if muscle memory insists. It will keep working. But
`reactivate` is the recommended entry point, and once the banner prints your
URL you won't go back.
