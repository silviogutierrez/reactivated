from typing import Optional, cast

import requests
from django.conf import settings
from django.core.cache import cache
from django.http import Http404, HttpRequest, HttpResponse

from . import templates


def get_stars() -> str:
    stars = None

    try:
        response = requests.get(
            "https://api.github.com/repos/silviogutierrez/reactivated"
        )
        raw_stars = response.json()["stargazers_count"]
        # raw_stars = 1200
        stars = f"{round(raw_stars / 1000, 1)}k" if raw_stars > 999 else str(raw_stars)
    except Exception:
        return ""

    return stars


def get_latest_tag() -> str:
    tag = ""

    try:
        response = requests.get(
            "https://registry.npmjs.org/create-django-app/",
        )
        tag = response.json()["dist-tags"]["latest"]
    except Exception:
        pass

    return tag


def home_page(request: HttpRequest) -> HttpResponse:
    stars = cache.get_or_set("stars", get_stars)

    return templates.HomePage(stars=cast(str, stars)).render(request)


def install(request: HttpRequest, *, tag: Optional[str] = None) -> HttpResponse:
    tag = tag or cache.get_or_set("tag", get_latest_tag)

    return HttpResponse(
        """
let
  pkgs = import (fetchTarball
    "https://github.com/NixOS/nixpkgs/archive/8ca77a63599e.tar.gz") { };
  download = fetchTarball
    "https://registry.npmjs.org/create-django-app/-/create-django-app-%s.tgz";
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
    """
        % tag
    )


toc = (
    ("getting-started", "Getting Started"),
    ("concepts", "Concepts"),
    ("philosophy-goals", "Philosophy & Goals"),
    # Maybe call concepts basics?
    # ("basics", "Basics"),
    ("api", "API"),
    ("existing-projects", "Existing Projects"),
    ("deploying", "Deploying a Reactivated Project"),
    ("styles", "Styles and CSS"),
    ("troubleshooting", "Troubleshooting"),
    # Load discussions from GitHub here.
    ("rfc", "Request for Comments"),
    ("why-nix", "Why Nix?"),
)


def documentation(request: HttpRequest, *, page_name: str) -> HttpResponse:
    try:
        content = (settings.BASE_DIR / f"server/docs/{page_name}.md").read_text()
    except FileNotFoundError:
        raise Http404

    return templates.Documentation(toc=toc, content=content, path=request.path).render(
        request
    )
