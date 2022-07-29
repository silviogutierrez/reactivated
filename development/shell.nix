let requirements = import ../requirements.nix;

in with requirements.pkgs;

mkShell {
  dependencies = requirements.production_dependencies;
  buildInputs = requirements.production_dependencies
    ++ requirements.development_dependencies;
  shellHook = ''
    setup_script="$(npm bin)/setup_environment.sh"

    if [ ! -f $setup_script ]; then
       npm install
    fi

    source $setup_script
  '';
}
