from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.version import get_docs_version

from . import forms, models, templates


def django_default(request: HttpRequest) -> HttpResponse:
    form = forms.StoryboardForm()
    return templates.DjangoDefault(form=form, version=get_docs_version()).render(
        request
    )


def polls_index(request: HttpRequest) -> HttpResponse:
    return templates.PollsIndex(
        latest_question_list=list(models.Question.objects.all())
    ).render(request)


def create_question(request: HttpRequest) -> HttpResponse:
    form = forms.CreateQuestion(request.POST or None)

    if form.is_valid():
        question = form.save(commit=False)
        question.pub_date = timezone.now()
        question.save()
        return redirect("polls_index")

    return templates.CreateQuestion(form=form).render(request)


def poll_detail(request: HttpRequest, poll_id: int) -> HttpResponse:
    question = get_object_or_404(models.Question, id=poll_id)

    return templates.PollDetail(question=question).render(request)
