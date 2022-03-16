# Troubleshooting

## Database issues

If you get an error like so:

```
django.db.utils.OperationalError: could not connect to server: No such file or directory
```

This means the isolated database process Reactivated creates is stuck.

In the future, Reactivated will handle this much more gracefully.

Two options, the latter harsher.

### Manual cleanup

1. Use `ps aux` and find the zombie `postgres` process that is running. You should
   recognize it because the project path will be in the arguments.
2. Kill this process.
3. Exit your shell, start new shell and run `nix-shell` as always. This will start a new
   DB process.

### Full reset

1. Kill the postgres process as in option 1.
2. Exit all shells for this project.
3. Remove and delete `BASE_DIR/.venv`.
4. Start nix-shell again.

> **Warning**: This option will delete your database! Get in the habit of having an easy
> to setup local development database. Use
> [fixtures](https://docs.djangoproject.com/en/4.0/howto/initial-data/) or
> [factory boy](https://factoryboy.readthedocs.io/en/stable/).
