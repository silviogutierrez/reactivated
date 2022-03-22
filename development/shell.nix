let
  stableTarball =
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
  unstableTarball =
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
  pkgs = import stableTarball { };
  unstable = import unstableTarball { };

  download = fetchTarball (

    if pkgs.stdenv.isDarwin then
      (if pkgs.stdenv.hostPlatform.darwinArch == "arm64" then
        "https://github.com/superfly/flyctl/releases/download/v0.0.306/flyctl_0.0.306_macOS_arm64.tar.gz"
      else
        "https://github.com/superfly/flyctl/releases/download/v0.0.306/flyctl_0.0.306_macOS_x86_64.tar.gz")
    else
      "https://github.com/superfly/flyctl/releases/download/v0.0.306/flyctl_0.0.306_Linux_x86_64.tar.gz");

  flyctlLatest = derivation {
    name = "flyctl";
    inherit download;
    coreutils = pkgs.coreutils;
    builder = "${pkgs.bash}/bin/bash";
    args = [
      "-c"
      ''
        sleep 0.5;
        unset PATH;
        export PATH=$coreutils/bin;
        mkdir -p $out/bin;
        cp $download $out/bin/fly;
        chmod +x $out/bin/fly;
      ''
    ];

    system = builtins.currentSystem;
  };

  dependencies = [
    pkgs.python39
    pkgs.python39Packages.virtualenv
    pkgs.python39Packages.pip
    pkgs.nodejs-16_x
  ];
in with pkgs;

mkShell {
  flyctlLatest = flyctlLatest;
  dependencies = dependencies;
  buildInputs = [
    dependencies
    (yarn.override { nodejs = nodejs-16_x; })
    # Needed for psycopg2 to build on Mac Silicon.
    openssl

    # Needed for psycopg2 to build in general (pg_config)
    postgresql_13

    flyctlLatest
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
