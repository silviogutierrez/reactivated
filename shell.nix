let
  stableTarball = fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/f112b512e1710da6c8beb8e541a8ad9fcd81e6e6.tar.gz";
  unstableTarball = fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/f112b512e1710da6c8beb8e541a8ad9fcd81e6e6.tar.gz";
  pkgs = import stableTarball { };
  unstable = import unstableTarball { };
in with pkgs;

mkShell {
  buildInputs = [
    gitAndTools.gh
    jq

    python39
    python39Packages.virtualenv
    nodejs-14_x
    (yarn.override { nodejs = nodejs-14_x; })

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
