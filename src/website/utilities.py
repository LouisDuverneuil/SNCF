from datetime import datetime

from .models import Reduction


def calculate_reduction_age(age):
    if age <= 8:
        my_type = "-8ans"
    if 8 < age < 19:
        my_type = "-18ans"
    if age >= 65:
        my_type = "Senior"
    else:
        my_type = "Aucune"
    print(my_type)
    my_reduction_age = Reduction.objects.get(type=my_type)
    return my_reduction_age


def calculate_reduction_date(wait_time):
    if wait_time >= 30:
        my_type = "J-30"
    if 30 > wait_time > 8:
        my_type = "J-8"
    else:
        my_type = "Aucune"
    my_reduction_date = Reduction.objects.get(type=my_type)
    return my_reduction_date


def calculate_prix(trajet, reduction, born):
    today = datetime.date.today()
    age_voyageur = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    reduction_age = calculate_reduction_age(age_voyageur)
    waiting_time = (today - trajet.date_depart).days
    reduction_date = calculate_reduction_date(waiting_time)
    # Application de la réduction liée à une carte de réduction
    cumulated_pourcentage = min(reduction.pourcentage + reduction_date.pourcentage + reduction_age.pourcentage, 100)
    prix = round(trajet.prix * (1 - cumulated_pourcentage / 100), 2)
    return prix
