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

Assuming you have `docker` installed and running, create your project first. We'll
name it `my_app`.

```bash
docker run -itv $PWD:/app silviogutierrez/reactivated install my_app
```

The container will take some time to boot the first time, as it will create a
`virtualenv`, run `yarn` and create an isolated database.

Once done, `cd` into your project, start the container, and start the development server.

```bash
cd my_app
docker run -itp 8000:8000 -v $PWD:/app --name my_app silviogutierrez/reactivated nix-shell
python manage.py runserver 0.0.0.0:8000
```

On your host machine, you should be able to visit `localhost:8000` and see Reactivated in action.

### Limitations

On MacOS, the filesystem operations will be slow. This
[may improve](https://www.docker.com/blog/speed-boost-achievement-unlocked-on-docker-desktop-4-6-for-mac/)
in the future.

To visit the site on the host machine, you *must* bind to `0.0.0.0` manually.
 By default, `runserver` without a port will bind to `localhost` and will not let
 outside hosts, including the host machine, reach the site.

And you'll need to run `manage.py` shell commands in the _same_ container instance, like
so:

```bash
docker exec -it my_app nix-shell

# Once inside nix-shell
python manage.py migrate
python manage.py check
```

### Cleaning up

When you're done using Docker, you can stop the container like so:

```bash
docker remove -f my_app
```

Your files and project will stay behind for future use.
