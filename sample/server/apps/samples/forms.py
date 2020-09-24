from django import forms

from reactivated.forms import Autocomplete
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


class ComposerForm(forms.ModelForm):
    class Meta:
        model = models.Composer
        fields = "__all__"


ComposerFormSet = forms.modelformset_factory(
    model=models.Composer, form=ComposerForm, extra=0, min_num=1, validate_min=True
)


class OperaForm(forms.ModelForm):
    class Meta:
        model = models.Opera
        fields = "__all__"
        widgets = {"composer": Autocomplete()}


OperaFormSet = forms.modelformset_factory(
    model=models.Opera, form=OperaForm, extra=0, min_num=1, validate_min=True
)
