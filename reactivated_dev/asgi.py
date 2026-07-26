from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from django.http import FileResponse, HttpRequest


class CORSStaticFilesHandler(ASGIStaticFilesHandler):
    # Serves /static/* outside the middleware stack, so corsheaders never runs
    # for assets. In build mode a mobile simulator may load the bundle as a
    # cross-origin ES module (capacitor://localhost -> a tunnel), which the
    # webview refuses to execute without CORS, so add the header on static hits.
    def serve(self, request: HttpRequest) -> FileResponse:
        response = super().serve(request)
        response["Access-Control-Allow-Origin"] = "*"
        return response


def create_application() -> ASGIStaticFilesHandler:
    # Reactivated convention: the project's ASGI app lives at server.asgi, which
    # sets DJANGO_SETTINGS_MODULE itself. This module only loads in the uvicorn
    # worker (via the factory string), never in the supervisor — Django stays
    # out of the supervisor process entirely.
    from server.asgi import application  # type: ignore[import-not-found]

    return CORSStaticFilesHandler(application)
