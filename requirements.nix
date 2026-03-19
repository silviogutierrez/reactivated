let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/3cb4ae6689d2.tar.gz") { };
  unstable = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/69ba8f9b9132.tar.gz") { };

in with pkgs; {
  inherit pkgs;
  inherit unstable;

  production_dependencies = [ pkgs.python312 unstable.nodejs_22 ];
  development_dependencies = [
    unstable.flyctl

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
