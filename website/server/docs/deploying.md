# Deploying

Local development is great. But eventually you'll want to publish your site.

There's a million different ways to deploy a Django project, but if you use our
[all-in-one setup script](/documentation/getting-started/), deployment to production is
trivial.

## Production runtime

The core challenge for a server deployment is that you need both, Python and Node.js in
the same instance. Even with Docker, this can be tricky.

Fortunately, just like in local development, we [use Nix](/documentation/why-nix/)
inside a Docker image. It's optimized to be as light as can be, with only the runtime
requirements. Review the `Dockerfile` provided after setup for details.

## Hosting provider

Theoretically, you can run this Docker image anywhere. But we've scripted the entire
deployment to [fly.io](https://fly.io/) for you.

> **Note**: Fly is under heavy development and deployments can be spotty. Particularly
> for new applications and new accounts. Be patient, once it's working, it works quite
> well.

## Initial deployment

Once you're ready to deploy your app, **make sure you've committed your changes.**

Then run `scripts/launch.sh` from `BASE_DIR`.

You'll almost certainly be asked to authenticate. And if you've never used
Fly before, you'll have to sign up. Go ahead and do so.

> **Note**: You'll probably be asked for a credit card to sign up. If you deploy a
> single app using our scripts, you'll remain in the free tier. The card requirement
> prevents abuse.

This script will:

-   Create a _free_ PostgreSQL instance on Fly.
-   Create an application instance.
-   Attach the instance to the database.
-   Build the `Dockerfile` remotely and deploy it to the instance.
-   Run database migrations.

> **Warning**: Initial deploys to Fly are still spotty. If anything goes wrong, delete
> the `fly.toml` file that is created and re-rerun `scripts/launch.sh`. **Make sure** to
> delete any apps using the [Fly dashboard](https://fly.io/apps) to avoid being billed.

## Follow up deployments

Deploying after this is as easy as running `scripts/deploy.sh` and waiting a few
minutes. Migrations are auto-run for you after deployment.

## SSH access

You may want to SSH into your app. Just run `flyctl ssh console` and you'll gain access
to the running instance.

> **Note**: There are a few quirks with the SSH session. You'll likely need to manually
> activate the virtualenv and `cd` into the `WORKDIR` of your Docker image.

## Custom domain

Adding a custom domain with **TLS** is easy. However, we don't automate the process
because DNS steps vary depending on your registrar.

Just follow the steps in
[their documentation](https://fly.io/docs/app-guides/custom-domains-with-fly/).

## Next steps

Live deployments is still in heavy development, but both this site and a few others are
hosted reliably on Fly.

Read the full [Fly documentation](https://fly.io/docs/) and be sure to visit the
[community](https://community.fly.io/) for support.
