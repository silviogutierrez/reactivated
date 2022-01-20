let
  stableTarball = fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/391f93a83c3.tar.gz";
  unstableTarball = fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/391f93a83c3.tar.gz";
  pkgs = import stableTarball { };
  unstable = import unstableTarball { };
in with pkgs;

mkShell {
  buildInputs = [
    python39
    python39Packages.virtualenv
    nodejs-14_x
    (yarn.override { nodejs = nodejs-14_x; })
    # Needed for psycopg2 to build on Mac Silicon.
    openssl

    # Needed for psycopg2 to build in general (pg_config)
    postgresql_13
  ];
  shellHook = ''
    # Needed to use pip wheels
    SOURCE_DATE_EPOCH=$(date +%s);
    VIRTUAL_ENV=$PWD/.venv
    PATH=$VIRTUAL_ENV/bin:$PATH

    if [ ! -d "$VIRTUAL_ENV" ]; then
        virtualenv "$VIRTUAL_ENV"
        pip install -r requirements.txt
    fi
  '';
}
