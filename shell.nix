let
  stableTarball = fetchTarball
    "https://github.com/NixOS/nixpkgs-channels/archive/0a146054bdf6f70f66de4426f84c9358521be31e.tar.gz";
  unstableTarball = fetchTarball
    "https://github.com/NixOS/nixpkgs-channels/archive/0a146054bdf6f70f66de4426f84c9358521be31e.tar.gz";
  pkgs = import stableTarball { };
  unstable = import unstableTarball { };
in with pkgs;

mkShell {
  buildInputs = [
    gitAndTools.gh
    jq

    python38
    python38Packages.virtualenv
    nodejs-13_x
    (yarn.override { nodejs = nodejs-13_x; })

    # Otherwise AWS gets some weird conflicts with python 2.7
    (tmuxp.override { python = python38; })

    ripgrep
    shellcheck
    shfmt
    nixfmt

    postgresql

    # For psycopg2 to build
    openssl

    # Purely for formatting right now.
    terraform
  ];
  src = builtins.path { path = ./scripts/helpers.sh; name = "reactivated"; };
  shellHook = ''
    # Needed to use pip wheels
    SOURCE_DATE_EPOCH=$(date +%s);

    source $src;

    setup_environment;
  '';
}
