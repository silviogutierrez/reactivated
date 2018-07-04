from django.http import HttpRequest, HttpResponse

def test(request: HttpResponse) -> HttpResponse:
    return HttpResponse('Hello 2!')
