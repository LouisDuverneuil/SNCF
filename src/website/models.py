from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import UniqueConstraint, Q


class Reduction(models.Model):
    type = models.CharField(max_length=45, unique=True)
    pourcentage = models.FloatField(default=0)

    def __str__(self):
        return self.type


class MyUserManager(BaseUserManager):
    def create_user(self, email, password=None, nom=None, prenom=None):
        # TODO : ajouter un client lors de l'ajout d'un utilisateur. OU
        if not email:
            raise ValueError("Vous devez rentrer un email")

        user = self.model(
            email=self.normalize_email(email),
            nom=nom,
            prenom=prenom
        )
        user.set_password(password)
        user.save()
        return user

    def create_super_user(self, email, password=None, nom=None, prenom=None):
        user = self.create_user(
            email=email, password=password, nom=nom, prenom=prenom)
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
    reduction = models.ForeignKey(
        Reduction, blank=True, null=True, on_delete=models.SET_NULL)

    USERNAME_FIELD = "email"
    objects = MyUserManager()
    REQUIRED_FIELDS = ["nom", "prenom"]

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

    # places = models.IntegerField() # TODO : à voir si on laisse

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
    # train = models.ForeignKey(Train, on_delete=models.CASCADE)
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
    train = models.ForeignKey(Train, on_delete=models.CASCADE)
    # TODO : PROTECT ? Un train ne peut pas être supprimé s'il a des trajets ?
    gare_depart = models.ForeignKey(
        Gare, on_delete=models.CASCADE, related_name="gare_depart")
    gare_arrivee = models.ForeignKey(
        Gare, on_delete=models.CASCADE, related_name="gare_arrivee")
    # TODO : ajouter variable nombre de places dispo dans le trajet.
    # complet = models.BooleanField(default=False)
    # TODO : vérifier que le train est apte à faire ce trajet
    # TODO : méthode pour modifier un trajet, impliquant de modifier tout les billets ?


class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    reduction = models.ForeignKey(
        Reduction, blank=True, null=True, on_delete=models.SET_NULL)
    mail = models.EmailField()

    def __str__(self):
        return f"{self.nom} {self.prenom}"


class Agence(models.Model):
    nom = models.CharField(max_length=100)


class Reservation(models.Model):
    # TODO : changer le client en user
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    # confirmation = models.BooleanField()
    trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE)
    prix = models.FloatField(blank=True, null=True)
    agence = models.ForeignKey(
        Agence, blank=True, null=True, on_delete=models.SET_NULL)
    place = models.ForeignKey(Place, on_delete=models.CASCADE)
    reduction = models.ForeignKey(
        Reduction, null=True, on_delete=models.SET_NULL)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    date = models.DateTimeField()

    class Meta:
        unique_together = ("trajet", "place")
        # constraints = [
        #     UniqueConstraint(fields=["trajet", "place"], condition=Q(confirmation=True), name="billet")
        # ]
        # unique_together = ("trajet", "place", "confirmation")

    def save(self, *args, **kwargs):
        print(self.reduction.pourcentage)
        if self.reduction.pourcentage:
            self.prix = self.trajet.prix * (1 - self.reduction.pourcentage/100)
        else:
            self.prix = self.trajet.prix
        super().save(*args, **kwargs)

#
# class Billet(models.Model):
#     trajet = models.ForeignKey(Trajet, on_delete=models.CASCADE)
#     reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
#     voiture = models.ForeignKey(Voiture, on_delete=models.CASCADE)
#     place = models.ForeignKey(Place, on_delete=models.CASCADE)
#
#
#     # TODO : méthode vérifiant que la réservation est confirmée avant de créer le billet. Retourne une erreur sinon
