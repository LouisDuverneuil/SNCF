from dal import autocomplete
from django import forms
import datetime

from bootstrap_datepicker_plus import TimePickerInput
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, Trajet, Reduction, Gare


class SignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email", "nom", "prenom", "reduction")
        # help_texts = {'reduction': "Carte avantage SNCF ?"}
        widgets = {
            "email": forms.TextInput({"placeholder": "zinedine@zidane.fr"}),
            "nom": forms.TextInput({"placeholder": "Zidane"}),
            "prenom": forms.TextInput({"placeholder": "Zinedine"}),
        }
        labels = {
            'reduction': "Carte avantage SNCF",
            'prenom': 'Prénom'
        }


now = datetime.datetime.now()
YEAR_CHOICE = [now.year, now.year + 1]


class TrajetForm(forms.ModelForm):
    reduction = forms.ModelChoiceField(queryset=Reduction.objects.all().order_by("type"), required=False,
                                       label="Reduction", empty_label=None)
    # gare_depart = forms.ModelChoiceField(
    #     queryset=Gare.objects.all(),
    #     widget=autocomplete.ModelSelect2(url='gare-autocomplete')
    # )

    class Meta:
        model = Trajet
        fields = (
            "gare_depart",
            "gare_arrivee",
            "date_depart",
            "heure_depart",
        )
        widgets = {
            "date_depart": forms.SelectDateWidget(years=YEAR_CHOICE),
            "heure_depart": TimePickerInput(),
            # "gare_depart": autocomplete.ModelSelect2(url='gare-autocomplete'),
        }


class ReservationForm(forms.Form):
    FENETRE = "F"
    COULOIR = "C"

    SITUATIONS = [
        (FENETRE, "Fenêtre"),
        (COULOIR, "Couloir")
    ]

    if_user = forms.BooleanField(initial=False, required=False, label="Je ne suis pas le voyageur")
    reduction = forms.ModelChoiceField(queryset=Reduction.objects.all(), required=False,
                                       widget=forms.Select(attrs={'id': 'id_reduction_form'}), empty_label=None)
    nom = forms.CharField(max_length=100, disabled=True)
    prenom = forms.CharField(max_length=100, disabled=True)
    situation = forms.ChoiceField(required=False, choices=SITUATIONS)

    def __init__(self, user, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)
        self.fields['nom'].initial = user.nom
        self.fields['prenom'].initial = user.prenom
        # self.fields['reduction'].initial = user.reduction
        # self.fields['nom'].widget.attrs['style'] = 'display:none'
        # self.fields['user'].widget.attrs['id'] = 'user_choice'
        # self.fields['if_user'].widget.attrs['onclick'] = "javascript:toggleDiv('if_user');"
