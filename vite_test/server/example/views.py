from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.version import get_docs_version

from . import forms, models, templates


def django_default(request: HttpRequest) -> HttpResponse:
    return templates.DjangoDefault(version=get_docs_version()).render(request)


def polls_index(request: HttpRequest) -> HttpResponse:
    return templates.PollsIndex(
        latest_question_list=list(models.Question.objects.all())
    ).render(request)


def create_poll(request: HttpRequest) -> HttpResponse:
    form = forms.Poll(request.POST or None)
    choice_form_set = forms.ChoiceFormSet(
        request.POST or None, queryset=models.Choice.objects.none()
    )

    if form.is_valid() and choice_form_set.is_valid():
        question = form.save(commit=False)
        question.pub_date = timezone.now()
        question.save()
        for instance in choice_form_set.save(commit=False):
            instance.question = question
            instance.save()

        return redirect("poll_detail", question.pk)

    return templates.EditPoll(form=form, choice_form_set=choice_form_set).render(
        request
    )


def update_poll(request: HttpRequest, question_id: int) -> HttpResponse:
    question = get_object_or_404(models.Question, id=question_id)
    form = forms.Poll(request.POST or None, instance=question)
    choice_form_set = forms.ChoiceFormSet(
        request.POST or None, queryset=models.Choice.objects.filter(question=question)
    )

    if form.is_valid() and choice_form_set.is_valid():
        form.save()
        for instance in choice_form_set.save(commit=False):
            instance.question = question
            instance.save()

        return redirect("poll_detail", question.pk)

    return templates.EditPoll(
        existing_poll=question, form=form, choice_form_set=choice_form_set
    ).render(request)


def poll_detail(request: HttpRequest, question_id: int) -> HttpResponse:
    question = get_object_or_404(models.Question, id=question_id)

    return templates.PollDetail(error_message=None, question=question).render(request)


def poll_comments(request: HttpRequest, question_id: int) -> HttpResponse:
    question = get_object_or_404(models.Question, id=question_id)
    form = forms.Comment(
        request.POST or None, instance=models.Comment(question=question)
    )

    if form.is_valid():
        form.save()

        if request.accepts("application/json") is False:
            return redirect("poll_comments", question.pk)

    return templates.PollComments(question=question, form=form).render(request)


def vote(request: HttpRequest, question_id: int) -> HttpResponse:
    question = get_object_or_404(models.Question, id=question_id)

    try:
        selected_choice = question.choices.get(pk=request.POST["choice"])
    except (KeyError, models.Choice.DoesNotExist):
        return templates.PollDetail(
            error_message="You didn't select a choice.", question=question
        ).render(request)
    else:
        selected_choice.votes += 1
        selected_choice.save()
        return redirect("results", question.pk)


def form_playground(request: HttpRequest) -> HttpResponse:
    form = forms.ExampleForm(request.POST or None)
    form_as_p = forms.ExampleForm(request.POST or None, prefix="as_p")
    form_set = forms.ChoiceFormSet(request.POST or None, prefix="form_set")

    if form.is_valid():
        assert False, "Valid form"

    return templates.FormPlayground(
        form=form, form_as_p=form_as_p, form_set=form_set
    ).render(request)


def results(request: HttpRequest, question_id: int) -> HttpResponse:
    question = get_object_or_404(models.Question, pk=question_id)
    return templates.Results(question=question).render(request)
