from typing import NamedTuple, List


from reactivated import template, Pick

from . import models, forms


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
