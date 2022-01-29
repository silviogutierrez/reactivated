from typing import List, NamedTuple

from reactivated import Pick, template

from . import forms, models


@template
class DjangoDefault(NamedTuple):
    version: str
    form: forms.StoryboardForm


@template
class PollsIndex(NamedTuple):
    latest_question_list: List[Pick[models.Question, "id", "question_text"]]


@template
class CreateQuestion(NamedTuple):
    form: forms.CreateQuestion


@template
class PollDetail(NamedTuple):
    question: Pick[models.Question, "id", "question_text"]
