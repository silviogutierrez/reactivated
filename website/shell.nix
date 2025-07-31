let requirements = import ../requirements.nix;

in with requirements.pkgs;

mkShell {
  dependencies = requirements.production_dependencies;
  buildInputs = requirements.production_dependencies
    ++ requirements.development_dependencies
    ++ requirements.contributing_dependencies;
  shellHook = ''
    setup_script="$(npm root)/.bin/setup_environment.sh"

    if [ ! -f $setup_script ]; then
       npm install
    fi

    source $setup_script
    pip install -e .. --config-settings editable_mode=compat
  '';
}
