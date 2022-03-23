# Getting Started

## With Nix

The easiest way to get started with Reactivated is to use our setup script.

Think of `create-react-app` but for Django+React.

### Requirements

-   Nix 2.4 or later. [Why Nix?](/documentation/why-nix/)
-   MacOS Monterey, MacOS Big Sur, or any modern Linux distribution.
-   Windows may work but it's untested.

### Installation

Once you've [installed Nix](https://nixos.org/download.html), run this command on your
shell:

```bash
nix-shell -E "$(curl -L https://reactivated.io/install/)"
```

You'll be asked to enter a project name. That's it. Press enter and let Reactivated do
its thing.

### Post Installation

Just run `cd <project_name>`, then `nix-shell` and finally `python manage.py runserver`

With the server running, you can visit `http://localhost:8000` to see Reactivated in
action.

### Next Steps

The project will have an `example` application that demonstrates some of the features in
Reactivated. The home page of your local site will guide you through an enhanced version
of the polls app from the
[Django tutorial](https://docs.djangoproject.com/en/dev/intro/tutorial01/).

If you're done checking out the example, terminate the server and run
`scripts/remove_example.sh`.

This will remove all example code, remove the migrations, and leave you with an empty
project.

## With Docker

Really, you should be using [Nix](/documentation/why-nix/).

But fine, you don't want to commit. And the Nix installer requires `sudo`. Maybe it
looks scary.

Assuming you `git` and `docker` installed and running, you can just clone the repository
and run our image on the code.

```bash
git clone git@github.com:silviogutierrez/reactivated.git
cd reactivated/development
docker run -it --rm -t -v $PWD:/app -p 8000:8000 silviogutierrez/reactivated
```

The container will take some time to boot the first time, as it will create a
`virtualenv`, run `yarn` and create an isolated database.

### Next steps

In another shell, you can modify the code inside `reactivated/development` to get an
idea how things work.

You can also use this project as a template to develop locally with Docker.

### Limitations

On MacOS, the filesystem operations will be slow. This
[may improve](https://www.docker.com/blog/speed-boost-achievement-unlocked-on-docker-desktop-4-6-for-mac/)
in the future.

And you'll need to run `manage.py` shell commands in another container instance. Like
so:

```bash
docker run -it --rm -t -v $PWD:/app silviogutierrez/reactivated python manage.py makemigrations
```
