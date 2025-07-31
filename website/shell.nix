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
       DID_INSTALL=1
       npm install
    fi

    source $setup_script

    if [ "$DID_INSTALL" = "1" ]; then
        # I don't know why this suddenly stopped working, including SETUPTOOLS_ENABLE_FEATURES
        # https://github.com/pypa/setuptools/issues/3499
        # Broken here maybe: https://github.com/pypa/pip/issues/12094
        pip install -e .. --config-settings editable_mode=compat
    fi
  '';
}
