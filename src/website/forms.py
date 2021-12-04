from dal import autocomplete
from django import forms
import datetime

from bootstrap_datepicker_plus import TimePickerInput
from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, Trajet, Reduction, Gare


class SignupForm(UserCreationForm):
    reduction = forms.ModelChoiceField(queryset=Reduction.objects.filter(user_allowed=True).order_by("type"), required=False,
                                       label="Reduction", empty_label=None, initial="Aucune")

    class Meta:
        model = CustomUser
        fields = ("email", "nom", "prenom", "date_naissance", "reduction")
        # help_texts = {'reduction': "Carte avantage SNCF ?"}
        widgets = {
            "email": forms.TextInput({"placeholder": "zinedine@zidane.fr"}),
            "nom": forms.TextInput({"placeholder": "Zidane"}),
            "prenom": forms.TextInput({"placeholder": "Zinedine"}),
            "date_naissance": forms.SelectDateWidget()
        }
        labels = {
            'reduction': "Carte avantage SNCF",
            'prenom': 'Prénom',
            'date_naissance': "Date de naissance"
        }
        # query_settings = {
        #     "reduction": Reduction.objects.filter(user_allowed=True),
        # }


class UpdateUserForm(forms.ModelForm):
    reduction = forms.ModelChoiceField(queryset=Reduction.objects.filter(user_allowed=True).order_by("type"),
                                       required=False,
                                       label="Reduction", empty_label=None, initial="Aucune")

    class Meta:
        model = CustomUser
        fields = ("email", "nom", "prenom", "reduction")
        # help_texts = {'reduction': "Carte avantage SNCF ?"}

        labels = {
            'reduction': "Carte avantage SNCF",
            'prenom': 'Prénom'
        }


now = datetime.datetime.now()
YEAR_CHOICE = [now.year, now.year + 1]


class TrajetForm(forms.ModelForm):
    reduction = forms.ModelChoiceField(queryset=Reduction.objects.filter(user_allowed=True).order_by("type"), required=False,
                                       label="Reduction", empty_label=None)

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
        }


class ReservationForm(forms.Form):
    FENETRE = "F"
    COULOIR = "C"

    SITUATIONS = [
        (FENETRE, "Fenêtre"),
        (COULOIR, "Couloir")
    ]

    if_user = forms.BooleanField(initial=False, required=False, label="Je ne suis pas le voyageur")
    reduction = forms.ModelChoiceField(queryset=Reduction.objects.filter(user_allowed=True), required=False,
                                       widget=forms.Select(attrs={'id': 'id_reduction_form'}), empty_label=None,
                                       help_text="Attention, votre carte de réduction sera contrôlée à bord du train")
    nom = forms.CharField(max_length=100, disabled=True)
    prenom = forms.CharField(max_length=100, disabled=True)
    date_naissance = forms.DateField(disabled=True)
    situation = forms.ChoiceField(required=False, choices=SITUATIONS)

    def __init__(self, user, *args, **kwargs):
        super(ReservationForm, self).__init__(*args, **kwargs)
        self.fields['nom'].initial = user.nom
        self.fields['prenom'].initial = user.prenom
        self.fields['date_naissance'].initial = user.date_naissance
