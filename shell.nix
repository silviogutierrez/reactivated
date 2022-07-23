let requirements = import ./requirements.nix;

in with requirements.pkgs;

mkShell {
  buildInputs = [
    requirements.production_dependencies
    requirements.development_dependencies
    requirements.contributing_dependencies
  ];
  shellHook = ''
    # Needed for our script below to work.
    SOURCE_DATE_EPOCH=$(date +%s);
    npm install
    source $(npm bin)/setup_environment.sh
    export DATABASE_NAME="reactivated"
  '';
}
