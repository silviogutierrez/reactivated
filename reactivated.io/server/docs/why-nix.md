# Why Nix

Nix solves a major technical challenge for us: having the _right_ Python and the _right_
Node.js installations coexisting peacefully. This may not sound like much, but this way
we skip the land of [`pyenv`](https://github.com/pyenv/pyenv) and
[`nvm`](https://github.com/nvm-sh/nvm).

For local development, it's convenient. For actual deployments, it's critical.

But Nix is much bigger than that.

## Beyond Reactivated

Your projects should guarantee three things: reproducibility, isolation, and native
performance.

### Reproducibility

Your projects should be reproducible. Table stakes.

Checking out a version, tag or branch should declaratively state every requirement
needed to run the application. For _that_ specific project, in _that_ specific branch,
at _that_ point in time.

Not just language-level dependencies like `requests` or `react`, but actual binaries and
language runtimes themselves. That's right, you should declare `python3.9` and `jdk11`.
Don't just document them, _require_ them.

Check these requirements into your code.

### Isolation

But working on one project should not affect working on another. Your blog may depend on
`python 3.9` and `go 1.17`. And your consulting client has a site that requires
`python 3.8`. You should be able to switch between these seamlessly.

In fact, working on the _same_ project with differing requirements should be possible.
You'll often collaborate on a long-lived branch to update a project to `python 3.10`.
Dare to live in a world where both branches can co-exist on your machine. Without having
to think about it.

This is true isolation. And Nix provides it. But... so does Docker, right?

### Native performance

You spent thousands of dollars on a machine. It runs quiet. It runs cool. It runs
forever on battery. Why throw all that way and run your projects on Docker?

If you develop on a Mac: you're doing just that. Docker on MacOS is virtualized. And if
you use Apple Silicon hardware, images can run even slower depending on the
architecture.

Even keeping the development files in sync can be slow. Volume mounting is notoriously
resource-intensive with Docker on Mac.

Moreover, running commands and scripting with Docker is clunky. A plain old shell
experience is far nicer.

Finally: some will say running on Docker better reflects what is running on production —
which does use containers. A [pillar](https://12factor.net/dev-prod-parity) of the
12-factor app in fact.

Maybe, but probably not. You're on different architectures at this point. Or worse,
emulating them. Many cloud providers internally don't even use Docker at all.

## Nix to the rescue

Enter Nix. Using a single `shell.nix` file, we declare _everything_ our project needs.
In that point in time, on that branch, in that one instance of the project.

We list out `python`, `nodejs`, `postgresql`, `shellcheck` and more.

## Nix standardizes

It's happened before. You know it has. Your colleague is using `sed` on a Mac. Another
is using `sed` on Ubuntu. And you are using `sed` on a Mac but installed `coreutils` to
get the Linux version. An absolute mess.

Nix standardizes **everything**. Once inside `nix-shell`, everyone will have the same
`sed`, the same `grep` and the same `find`. And best of all: the same `bash`.

No surprises.

## Nix for scripting

Remember, this applies to our scripts too. Open up one of those "quick, only for now
then I'll rewrite it later in Python" 1000 line scripts. Yes,
`convert-gcp-mp4s-to-gifs-and-upload-to-aws.sh`, I'm looking at you.

Try to identify all the binaries that need to exist. Probably the regular cast of
characters: `sed`, `git`, and `wget`. You can sort of expect most devs or setups to have
this, [OS-level differences aside](https://stackoverflow.com/a/4247319).

But you need `gcloud` installed, probably a version that supports their latest storage
options. And the `aws` CLI.

Last but not least, you need `ffmpeg`.

Are you going to list all of these with setup instructions? Identifying versions?
Provide a Docker image?

No, you're just going to list them in `requirements.nix`.

And at the top of your script file, refer to it, using the `--pure` flag. This will
ensure _nothing_ unlisted is available to the script.

```bash
#! /usr/bin/env nix-shell
#! nix-shell requirements.nix --pure -i bash

# redacted
ffmpeg -y -i "$filepath" -filter_complex "<filter options>" "$ANIMATED"
aws s3 cp myfolder s3://mybucket/myfolder --recursive
# redacted

```

New dev working on the project? Tell them to install Nix, check out the repository, and
run the script. That's it. Nix will install and cache all the dependencies.

Eudaimonia.
