let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/1ac507ba981970c8e864624542e31eb1f4049751.tar.gz")
    { };

  unstable = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/4a2481f0c7085c5fc4eab5e0a6e09dad54d4caaa.tar.gz")
    { };

  dependencies = [
    pkgs.python38
    pkgs.python38Packages.virtualenv
    pkgs.python38Packages.pip
    pkgs.nodejs-14_x
  ];

in with pkgs;

mkShell {
  dependencies = dependencies;
  buildInputs = import ./nix/requirements.nix {
    inherit pkgs;
    inherit unstable;
    inherit dependencies;
  };
  src = ./scripts/helpers.sh;
  shellHook = ''
    set -e
    # Needed to use pip wheels
    SOURCE_DATE_EPOCH=$(date +%s);
    source $src;

    set -a
    setup_environment
    set +a
    set +e
  '';
}
