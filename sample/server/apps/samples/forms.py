from typing import Any, Dict

from django import forms

from reactivated.forms import Autocomplete, EnumChoiceField, ModelFormSetFactory
from sample.server.apps.samples import models


class PlaygroundForm(forms.Form):
    choice_field = forms.ChoiceField(
        choices=(("", "- blank -"), ("first", "First"), ("second", "Second")),
        initial="first",
    )

    # TODO: figure out why adding this class makes the plugin work.
    # Something in
    # plugin.py#ctx.api.add_symbol_table_node(ctx.name, SymbolTableNode(GDEF, info))
    # causes a recursion error when using the plugin together with django-stubs
    # plugin.
    class Meta:
        pass


class ComposerForm(forms.ModelForm[models.Composer]):
    class Meta:
        model = models.Composer
        fields = "__all__"


class ComposerFormSet(ModelFormSetFactory[models.Composer, ComposerForm]):
    extra = 0
    min_num = 1
    validate_min = True


class OperaForm(forms.ModelForm[models.Opera]):
    class Meta:
        model = models.Opera
        fields = "__all__"
        widgets = {"composer": Autocomplete()}


class OperaFormSet(ModelFormSetFactory[models.Opera, OperaForm]):
    extra = 0
    min_num = 1


class StoryboardForm(forms.Form):
    hidden_field = forms.CharField(widget=forms.HiddenInput())
    char_field = forms.CharField()
    integer_field = forms.IntegerField()
    date_field = forms.DateField(widget=forms.SelectDateWidget(years=[2000, 2001]))
    date_time_field = forms.SplitDateTimeField(
        widget=forms.SplitDateTimeWidget,
    )
    choice_field = forms.ChoiceField(
        choices=(
            (1, "One"),
            (2, "Two"),
        )
    )
    enum_field = EnumChoiceField(enum=models.Opera.Style)
    boolean_field = forms.BooleanField(help_text="Not blank")

    def clean(self) -> Dict[str, Any]:
        raise forms.ValidationError(
            "Non-field error",
        )
