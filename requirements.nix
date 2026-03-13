let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/50ab793786d9.tar.gz") { };
  unstable = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/400de68cd101.tar.gz") { };

in with pkgs; {
  inherit pkgs;
  inherit unstable;

  production_dependencies = [ pkgs.python312 pkgs.nodejs_22 ];
  development_dependencies = [
    unstable.flyctl

    # Needed for pip-installed wheels with native extensions (e.g. greenlet) on Linux.
    pkgs.stdenv.cc.cc.lib

    # Needed for psycopg on MacOS Silicon... maybe? Maybe psycopg 3 doesn't need it.
    pkgs.openssl

    # Needed for psycopg on MacOS... maybe? Maybe psycopg 3 doesn't need it.
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
