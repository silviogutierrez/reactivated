let
  stableTarball =
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
  unstableTarball =
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
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
    (import ./development/shell.nix).flyctlLatest
  ];
  src = ./scripts/helpers.sh;
  shellHook = ''
    # Needed to use pip wheels
    SOURCE_DATE_EPOCH=$(date +%s);

    source $src;

    setup_environment;
  '';
}
