let requirements = import ./requirements.nix;

in with requirements.pkgs;

mkShell {
  buildInputs = requirements.production_dependencies
    ++ requirements.development_dependencies
    ++ requirements.contributing_dependencies;
  shellHook = ''
    source "./packages/reactivated/scripts/setup_environment.sh"
  '';
}
