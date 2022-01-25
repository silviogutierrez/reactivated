let
  stableTarball = fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
  unstableTarball = fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
  pkgs = import stableTarball { };
  unstable = import unstableTarball { };

  dependencies = [
    pkgs.python39
    pkgs.python39Packages.virtualenv
    pkgs.python39Packages.pip
    pkgs.nodejs-16_x
  ];
in with pkgs;

mkShell {
  dependencies = dependencies;
  buildInputs = [
    dependencies
    (yarn.override { nodejs = nodejs-16_x; })
    # Needed for psycopg2 to build on Mac Silicon.
    openssl

    # Needed for psycopg2 to build in general (pg_config)
    postgresql_13

    flyctl
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
