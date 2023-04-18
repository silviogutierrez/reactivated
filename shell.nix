let requirements = import ./requirements.nix;

in with requirements.pkgs;

mkShell {
  buildInputs = requirements.production_dependencies
    ++ requirements.development_dependencies
    ++ requirements.contributing_dependencies ++ [
      # Needed for recursive nix-shell --pure scripts
      # Like scripts/script-create-django-app.sh calling sync-development.sh
      requirements.pkgs.nix
    ];
  shellHook = ''
    source "./packages/reactivated/scripts/setup_environment.sh"
  '';
}
