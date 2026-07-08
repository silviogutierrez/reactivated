import os

import requests
from django.conf import settings
from django.core.cache import cache
from django.http import Http404, HttpRequest, HttpResponse

from . import templates


def get_stars() -> str:
    # GitHub rate-limits unauthenticated requests to 60/hour per IP. On Fly the
    # egress IP is shared NAT across tenants, so that budget is routinely
    # exhausted by neighbors and every unauthenticated call gets a 403. Sending
    # a token bumps us to 5000/hour on our own budget. Set GITHUB_TOKEN as a Fly
    # secret (a fine-grained token with no scopes / public read is enough).
    headers = {
        "User-Agent": "reactivated.io",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.get(
        "https://api.github.com/repos/silviogutierrez/reactivated",
        headers=headers,
        timeout=5,
    )
    response.raise_for_status()
    raw_stars = response.json()["stargazers_count"]
    return f"{round(raw_stars / 1000, 1)}k" if raw_stars > 999 else str(raw_stars)


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
    # Don't use get_or_set: it caches failures ("") just as durably as
    # successes, so one bad fetch would poison the button until expiry. Instead
    # cache a real count for a day, and only briefly on failure so we recover
    # quickly (e.g. once a token is deployed) without hammering GitHub.
    stars = cache.get("stars")
    if stars is None:
        try:
            stars = get_stars()
            cache.set("stars", stars, 60 * 60 * 24)
        except Exception:
            stars = ""
            cache.set("stars", stars, 60 * 5)

    return templates.HomePage(stars=stars).render(request)


def install(request: HttpRequest, *, tag: str | None = None) -> HttpResponse:
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
