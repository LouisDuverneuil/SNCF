from django.contrib import admin

from .models import CustomUser, Train, Trajet, Voiture, Place, Ville, Gare, Reduction, Reservation

admin.site.register(CustomUser)
admin.site.register(Train)
admin.site.register(Trajet)
admin.site.register(Voiture)
admin.site.register(Place)
admin.site.register(Ville)
admin.site.register(Gare)
admin.site.register(Reduction)
admin.site.register(Reservation)

