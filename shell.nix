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
    export DATABASE_NAME="reactivated"
    npm install
    setup_script="$(npm bin)/setup_environment.sh"

    if [ -f $setup_script ]; then
       source $setup_script
    fi
  '';
}
