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
    gitAndTools.gh
    jq

    python39
    python39Packages.virtualenv
    nodejs-16_x
    (yarn.override { nodejs = nodejs-16_x; })

    tmuxp

    ripgrep
    shellcheck
    shfmt
    nixfmt

    postgresql

    # Purely for formatting right now.
    terraform
  ];
  src = ./scripts/helpers.sh;
  shellHook = ''
    # Needed to use pip wheels
    SOURCE_DATE_EPOCH=$(date +%s);

    source $src;

    setup_environment;
  '';
}
