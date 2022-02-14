let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz") { };
  download = fetchTarball
    "https://registry.npmjs.org/create-django-app/-/create-django-app-0.20.1-a720.tgz";
in with pkgs;

mkShell {
  buildInputs = [ ];
  inherit download;
  shellHook = ''
    echo "Enter a project name"
    read project_name
    $download/scripts/create-django-app.sh $project_name;
    exit;
  '';
}
