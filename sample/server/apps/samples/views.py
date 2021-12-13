from django.http import HttpRequest, HttpResponse

from . import forms, models, templates


def hello_world(request: HttpRequest) -> HttpResponse:
    composer = models.Composer(name="Arrigo Boito")
    opera = models.Opera(
        name="Mefistofele", composer=composer, style=models.Opera.Style.GRAND
    )
    return templates.HelloWorld(opera=opera).render(request)


def storyboard(request: HttpRequest) -> HttpResponse:
    form = forms.StoryboardForm()
    return templates.Storyboard(form=form,).render(request)
