let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/1ac507ba981970c8e864624542e31eb1f4049751.tar.gz")
    { };

  unstable = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/4a2481f0c7085c5fc4eab5e0a6e09dad54d4caaa.tar.gz")
    { };
in with pkgs;
let
  dependencies =
    [ python38 python38Packages.virtualenv python38Packages.pip nodejs-14_x ];
  devDependencies = [
    gitAndTools.gh
    jq

    python38
    python38Packages.virtualenv
    nodejs-14_x
    (yarn.override { nodejs = nodejs-14_x; })

    # Otherwise AWS gets some weird conflicts with python 2.7
    (tmuxp.override { python = python38; })

    ripgrep
    shellcheck
    shfmt
    nixfmt

    heroku

    postgresql

    # For psycopg2 to build
    openssl

    # Purely for formatting right now.
    terraform
  ];
in mkShell {
  dependencies = dependencies;
  buildInputs = dependencies ++ devDependencies;
  src = ./scripts/helpers.sh;
  shellHook = ''
    # Needed to use pip wheels
    SOURCE_DATE_EPOCH=$(date +%s);

    source $src;

    setup_environment;
  '';
}
