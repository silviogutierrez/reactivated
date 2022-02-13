appName:
let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz") { };
  download = pkgs.fetchurl {
    url = "http://localhost:8000/static/script.sh";
    executable = true;
    hash = null;
  };
in with pkgs;

mkShell {
  buildInputs = [ ];
  src = download;
  appName = appName;
  shellHook = ''
    echo $appName;
    exit
    // echo "Enter a project name"
    // read project_name
    // $src $project_name;
  '';
}
