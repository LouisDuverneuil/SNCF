import datetime

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import UniqueConstraint, Q
from django.db.models.signals import post_delete, pre_save, post_save
from django.dispatch import receiver


class Reduction(models.Model):
    type = models.CharField(max_length=45, unique=True)
    pourcentage = models.FloatField(default=0)
    user_allowed = models.BooleanField(default=False)

    def __str__(self):
        return self.type


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, nom=None, prenom=None, date_naissance=None):
        if not email:
            raise ValueError("Vous devez rentrer un email")

        user = self.model(
            email=self.normalize_email(email),
            nom=nom,
            prenom=prenom,
            date_naissance = date_naissance,
        )
        user.set_password(password)
        user.save()
        return user

    def create_super_user(self, email, password=None, nom=None, prenom=None, date_naissance=None):
        user = self.create_user(
            email=email,
            password=password,
            nom=nom,
            prenom=prenom,
            date_naissance=date_naissance,
        )
        user.is_admin = True
        user.is_staff = True
        user.save()
        return user


class CustomUser(AbstractBaseUser):
    email = models.EmailField(
        unique=True,
        max_length=255,
        blank=False
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    reduction = models.ForeignKey(Reduction, blank=True, null=True, on_delete=models.SET_NULL)

    USERNAME_FIELD = "email"
    objects = MyUserManager()
    REQUIRED_FIELDS = ["nom", "prenom", "date_naissance"]

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def __str__(self):
        return f"{self.nom} {self.prenom}"


class Train(models.Model):
    # date = models.DateTimeField(blank=True, null=True) # Pour date de création ?
    def __str__(self):
        return f"Train n°{self.id}"


class Voiture(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    numero = models.IntegerField()

    class Meta:
        unique_together = ("train", "numero")

    def __str__(self):
        return f"Train n°{self.train.id} - voiture {self.numero}"


class Place(models.Model):
    FENETRE = "F"
    COULOIR = "C"

    SITUATIONS = [
        (FENETRE, "Fenêtre"),
        (COULOIR, "Couloir")
    ]
    voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE)
    numero = models.IntegerField()
    situation = models.CharField(max_length=1, blank=True, choices=SITUATIONS)

    class Meta:
        unique_together = ("voiture", "numero")

    def __str__(self):
        return f"{self.voiture} - place {self.numero}"


class Ville(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom


class Gare(models.Model):
    # TODO : changer en PROTECT ?
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE)
    nom = models.CharField(max_length=100)

    # TODO : ajouter une relation many to many pour les gares reliées ?

    def __str__(self):
        return self.nom


class Trajet(models.Model):
    date_depart = models.DateField()
    heure_depart = models.TimeField()
    date_arrivee = models.DateField()
    heure_arrivee = models.TimeField()
    prix = models.FloatField()
    train = models.ForeignKey(Train, on_delete=models.PROTECT)
    # Un train ne peut pas être supprimé s'il a des trajets
    gare_depart = models.ForeignKey(
        Gare, on_delete=models.CASCADE, related_name="gare_depart")
    gare_arrivee = models.ForeignKey(
        Gare, on_delete=models.CASCADE, related_name="gare_arrivee")
    places_libres = models.IntegerField(blank=True, null=True, verbose_name="Nombre de places libres")
    # TODO : ajouter variable nombre de places dispo dans le trajet.

    def save(self, *args, **kwargs):
        reservations = Reservation.objects.filter(trajet=self.id)
        voitures = self.train.voiture_set.all()
        nb_places = len(Place.objects.filter(voiture__in=voitures))
        self.places_libres = nb_places - len(reservations)
        super().save(*args, **kwargs)


def calculate_reduction_age(age):
    print(f"Age : {age}, type : {type(age)}")
    if age <= 8:
        my_type = "-8ans"
    elif 8 < age < 19:
        my_type = "-18ans"
    elif age >= 65:
        my_type = "Senior"
    else:
        my_type = "Aucune"
    print(my_type)
    my_reduction_age = Reduction.objects.get(type=my_type)
    return my_reduction_age


def calculate_reduction_date(wait_time):
    if wait_time >= 30:
        my_type = "J-30"
    elif 30 > wait_time > 8:
        my_type = "J-8"
    else:
        my_type = "Aucune"
    my_reduction_date = Reduction.objects.get(type=my_type)
    return my_reduction_date


def calculate_prix(trajet, reduction, born):
    today = datetime.date.today()
    if type(born) == str:
        born = datetime.datetime.strptime(born, '%d/%m/%Y')
    age_voyageur = int(today.year - born.year - ((today.month, today.day) < (born.month, born.day)))
    reduction_age = calculate_reduction_age(age_voyageur)
    waiting_time = (today - trajet.date_depart).days
    reduction_date = calculate_reduction_date(waiting_time)
    # Application de la réduction liée à une carte de réduction
    cumulated_pourcentage = min(reduction.pourcentage + reduction_date.pourcentage + reduction_age.pourcentage, 100)
    prix = round(trajet.prix * (1 - cumulated_pourcentage / 100), 2)
    return prix


class Reservation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE)
    prix = models.FloatField(blank=True, null=True)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    reduction = models.ForeignKey(
        Reduction, null=True, on_delete=models.SET_NULL)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date_naissance = models.DateField()
    date = models.DateTimeField()

    class Meta:
        unique_together = ("trajet", "place")
        # constraints = [
        #     UniqueConstraint(fields=["trajet", "place"], condition=Q(confirmation=True), name="billet")
        # ]
        # unique_together = ("trajet", "place", "confirmation")

    def save(self, *args, **kwargs):
        print(self.reduction.pourcentage)
        self.prix = calculate_prix(
            trajet=self.trajet,
            reduction=self.reduction,
            born=self.date_naissance,
        )
        super().save(*args, **kwargs)


@receiver(post_delete, sender=Reservation)
def del_reservation(sender, instance, **kwargs):
    trajet = instance.trajet
    # Dans tous les cas, le nombre de place est recalculé lors de la méthode save :
    trajet.save()


@receiver(post_save, sender=Reservation)
def add_reservation(sender, instance, **kwargs):
    trajet = instance.trajet
    # Dans tous les cas, le nombre de place est recalculé lors de la méthode save :
    trajet.save()