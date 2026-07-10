from typing import Annotated, Literal

from reactivated.forms import DjangoForm, DjangoFormSet
from reactivated.pick import InlinePick
from reactivated.templates import Template

from . import forms, models


class DjangoDefault(Template):
    version: str


class PollsIndex(Template):
    latest_question_list: list[
        InlinePick[models.Question, Literal["id", "question_text"]]
    ]


class EditPoll(Template):
    form: Annotated[forms.Poll, DjangoForm]
    choice_form_set: Annotated[forms.ChoiceFormSet, DjangoFormSet]
    existing_poll: InlinePick[models.Question, Literal["id"]] | None = None


class PollDetail(Template):
    question: InlinePick[
        models.Question,
        Literal["id", "question_text", "choices.id", "choices.choice_text"],
    ]
    error_message: str | None = None


class PollComments(Template):
    question: InlinePick[
        models.Question,
        Literal["id", "question_text", "comments.comment_text"],
    ]
    form: Annotated[forms.Comment, DjangoForm]


class Results(Template):
    question: InlinePick[
        models.Question,
        Literal[
            "id",
            "question_text",
            "choices.id",
            "choices.choice_text",
            "choices.votes",
        ],
    ]


class FormPlayground(Template):
    form: Annotated[forms.ExampleForm, DjangoForm]
    form_as_p: Annotated[forms.ExampleForm, DjangoForm]
    form_set: Annotated[forms.ChoiceFormSet, DjangoFormSet]
