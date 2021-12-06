from dal import autocomplete
from django import forms
import datetime

from bootstrap_datepicker_plus import TimePickerInput
from django import forms
from django.contrib.auth.forms import UserCreationForm, ReadOnlyPasswordHashField

from .models import CustomUser, Trajet, Reduction, Gare


class SignupForm(UserCreationForm):
    """
    Formulaire d'inscription. Le champs réduction est modifié pour que l'utilisateur n'ait
    accès qu'aux cartes de réductions.
    """
    reduction = forms.ModelChoiceField(queryset=Reduction.objects.filter(user_allowed=True).order_by("type"), required=False,
                                       label="Reduction", empty_label=None, initial="Aucune")

    class Meta:
        """ Lier le formulaire au modèle d'utilisateur et définir les champs à entrer par l'utilisateur """

        model = CustomUser
        fields = ("email", "nom", "prenom", "date_naissance", "reduction")
        # définition de valeurs en fond pour aider l'utilisateur
        widgets = {
            "email": forms.TextInput({"placeholder": "zinedine@zidane.fr"}),
            "nom": forms.TextInput({"placeholder": "Zidane"}),
            "prenom": forms.TextInput({"placeholder": "Zinedine"}),
            "date_naissance": forms.SelectDateWidget()
        }
        # définition
        labels = {
            'reduction': "Carte avantage SNCF",
            'prenom': 'Prénom',
            'date_naissance': "Date de naissance"
        }


class UpdateUserForm(forms.ModelForm):
    """
    Formulaire de modification des champs d'un utilisateur, autre que le mot de passe. Le champs réduction est
    modifié pour que l'utilisateur n'ait accès qu'aux cartes de réductions.
    """

    reduction = forms.ModelChoiceField(queryset=Reduction.objects.filter(user_allowed=True).order_by("type"),
                                       required=False,
                                       label="Reduction", empty_label=None, initial="Aucune")

    class Meta:
        """ Lier le formulaire au modèle d'utilisateur et définir les champs à entrer par l'utilisateur """

        model = CustomUser
        fields = ("email", "nom", "prenom", "reduction", "date_naissance")
        # help_texts = {'reduction': "Carte avantage SNCF ?"}

        labels = {
            'reduction': "Carte avantage SNCF",
            'prenom': 'Prénom',
            'date_naissance': 'Date de naissance'
        }


class TrajetForm(forms.ModelForm):
    """
    Formulaire pour la recherche de trajet
    """
    reduction = forms.ModelChoiceField(queryset=Reduction.objects.filter(user_allowed=True).order_by("type"), required=False,
                                       label="Reduction", empty_label=None)

    class Meta:
        """ Lier le formulaire au modèle de Trajet et définir les champs de filtres """

        model = Trajet
        fields = (
            "gare_depart",
            "gare_arrivee",
            "date_depart",
            "heure_depart",
        )
        widgets = {
            "heure_depart": TimePickerInput(),
        }


class ReservationForm(forms.Form):
    """
    Formulaire pour la création de réservation
    Args:
        if_user: Vrai si l'utilisateur est le voyageur, faux sinon.
        reduction: Carte de reduction du voyageur
        nom: Nom du voyageur (utile lorsque if_user=False)
        prenom: Prenom du voyageur (utile lorsque if_user=False)
        date_naissance: Date de naissance du voyageur (utile lorsque if_user=False)
        situation: Fenetre ou Couloir, situation souhaitée
    """
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
        """ Surcharge de la méthode init pour définir les champs initiaux du formulaire """
        super(ReservationForm, self).__init__(*args, **kwargs)
        self.fields['nom'].initial = user.nom
        self.fields['prenom'].initial = user.prenom
        self.fields['date_naissance'].initial = user.date_naissance
