let
  stableTarball =
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
  unstableTarball =
    fetchTarball "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz";
  pkgs = import stableTarball { };
  unstable = import unstableTarball { };

  download = fetchTarball (if pkgs.stdenv.isDarwin then {
    url = "https://github.com/superfly/flyctl/releases/download/v0.0.286/flyctl_0.0.286_macOS_arm64.tar.gz";
    sha256 = "sha256:0q1nkaj9jia1kwiphps5hd7jfn9516sqrsjd5ydamq5zpavyg41x";
  } else {
    url = "https://github.com/superfly/flyctl/releases/download/v0.0.286/flyctl_0.0.286_Linux_x86_64.tar.gz";
    sha256 = "sha256:1z3jxvvaya8j6261p9i1hb0cnkxlkk3qs9348p2r5lxax9wsaq1b";
  });

  flyctlLatest = derivation {
    name = "flyctl";
    inherit download;
    coreutils = pkgs.coreutils;
    builder = "${pkgs.bash}/bin/bash";
    args = [
      "-c"
      ''
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
  dependencies = dependencies;
  buildInputs = [
    dependencies
    (yarn.override { nodejs = nodejs-16_x; })
    # Needed for psycopg2 to build on Mac Silicon.
    openssl

    # Needed for psycopg2 to build in general (pg_config)
    postgresql_13

    flyctlLatest
  ];
  shellHook = ''
    # Needed to use pip wheels
    SOURCE_DATE_EPOCH=$(date +%s);
    VIRTUAL_ENV=$PWD/.venv
    PATH=$VIRTUAL_ENV/bin:$PATH
    POSTGRESQL_DATA="$VIRTUAL_ENV/postgresql"
    POSTGRESQL_LOGS="$VIRTUAL_ENV/postgresql/logs.txt"
    TMP_ENV="$TMPDIR/reactivated/$(echo $VIRTUAL_ENV | md5sum | awk '{print $1}')";

    export PGPORT=1
    export PGDATABASE="database"
    export PGHOST=$TMP_ENV


    if [ ! -d "$VIRTUAL_ENV" ]; then
        NEED_DATABASE=true
        rm -rf $TMP_ENV
        mkdir -p $TMP_ENV
        virtualenv "$VIRTUAL_ENV"
        initdb "$POSTGRESQL_DATA"
        pip install -r requirements.txt
    fi

    pg_ctl -o "-p 1 -k \"$PGHOST\" -c listen_addresses=\"\"" -D $POSTGRESQL_DATA -l $POSTGRESQL_LOGS start &> /dev/null

    if [ "$NEED_DATABASE" == true ]; then
        createdb $PGDATABASE &> /dev/null
    fi
  '';
}
