let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/3cb4ae6689d2.tar.gz") { };
  unstable = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/3cb4ae6689d2.tar.gz") { };

in with pkgs; {
  inherit pkgs;
  inherit unstable;

  production_dependencies = [ pkgs.python312 pkgs.nodejs-18_x ];
  development_dependencies = [
    unstable.flyctl

    # Needed for psycopg2 to build on Mac Silicon.
    pkgs.openssl

    # Needed for psycopg2 to build in general (pg_config)
    pkgs.postgresql_13

    # Needed for automating flyctl
    pkgs.jq

    # Used by our deployment scripts.
    pkgs.curl
    pkgs.cacert

    pkgs.shfmt
    pkgs.shellcheck
    pkgs.nixfmt
  ];
  contributing_dependencies = [ pkgs.gitAndTools.gh pkgs.ripgrep pkgs.bash ];

}
