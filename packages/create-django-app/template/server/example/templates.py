from typing import List, NamedTuple, Optional

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
class CreatePoll(NamedTuple):
    form: forms.Poll
    choice_form_set: forms.ChoiceFormSet


@template
class UpdatePoll(NamedTuple):
    form: forms.Poll
    choice_form_set: forms.ChoiceFormSet


@template
class PollDetail(NamedTuple):
    question: Pick[
        models.Question, "id", "question_text", "choices.id", "choices.choice_text"
    ]
    error_message: Optional[str] = None


@template
class Results(NamedTuple):
    question: Pick[
        models.Question,
        "id",
        "question_text",
        "choices.id",
        "choices.choice_text",
        "choices.votes",
    ]
