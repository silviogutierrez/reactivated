let requirements = import ../requirements.nix;

in with requirements.pkgs;

mkShell {
  dependencies = requirements.production_dependencies;
  buildInputs = requirements.production_dependencies
    ++ requirements.development_dependencies
    ++ requirements.contributing_dependencies;
  shellHook = ''
    source $(npm bin)/setup_environment.sh
  '';
}
