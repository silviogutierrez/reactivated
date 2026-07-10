from reactivated.pick import InlinePick, PickArgs
from reactivated.templates import Template

from . import forms, models


class DjangoDefault(Template):
    version: str


class PollsIndex(Template):
    latest_question_list: list[
        InlinePick[models.Question, PickArgs(fields=["id", "question_text"])]
    ]


class EditPoll(Template):
    form: forms.Poll
    choice_form_set: forms.ChoiceFormSet
    existing_poll: InlinePick[models.Question, PickArgs(fields=["id"])] | None = None


class PollDetail(Template):
    question: InlinePick[
        models.Question,
        PickArgs(fields=["id", "question_text", "choices.id", "choices.choice_text"]),
    ]
    error_message: str | None = None


class PollComments(Template):
    question: InlinePick[
        models.Question,
        PickArgs(fields=["id", "question_text", "comments.comment_text"]),
    ]
    form: forms.Comment


class Results(Template):
    question: InlinePick[
        models.Question,
        PickArgs(
            fields=[
                "id",
                "question_text",
                "choices.id",
                "choices.choice_text",
                "choices.votes",
            ]
        ),
    ]


class FormPlayground(Template):
    form: forms.ExampleForm
    form_as_p: forms.ExampleForm
    form_set: forms.ChoiceFormSet
