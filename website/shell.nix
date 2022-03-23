let
  stableTarball =
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
  unstableTarball =
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/9bc841fec1c0.tar.gz";
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
    ripgrep
    unstable.flyctl
    (yarn.override { nodejs = nodejs-16_x; })
    # Needed for psycopg2 to build on Mac Silicon.
    openssl

    # Needed for psycopg2 to build in general (pg_config)
    postgresql_13

    # Needed for automating flyctl
    jq

    # Used by our deployment scripts.
    curl
    cacert

    shfmt
    shellcheck
    nixfmt
  ];
  shellHook = ''
    source scripts/setup_environment.sh
  '';
}
