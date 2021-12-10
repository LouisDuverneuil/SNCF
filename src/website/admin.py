from django.contrib import admin

from .models import CustomUser, Train, Trajet, Voiture, Place, Ville, Gare, Reduction, Reservation


# class CustomUserAdmin(admin.ModelAdmin):
#     list_display = ('id', 'employee_id', 'license_number')
#     fields = ['employee_id','license_number']


class CustomAdmin(admin.ModelAdmin):

    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name != 'id']
        super(CustomAdmin, self).__init__(model, admin_site)


class TrajetAdmin(admin.ModelAdmin):
    list_filter = ('date_depart',)

    def __init__(self, model, admin_site):
        self.list_display = [field.name for field in model._meta.fields if field.name != 'id']
        super(TrajetAdmin, self).__init__(model, admin_site)


admin.site.register(CustomUser, CustomAdmin)
admin.site.register(Train, CustomAdmin)
admin.site.register(Trajet, TrajetAdmin)
admin.site.register(Voiture, CustomAdmin)
admin.site.register(Place, CustomAdmin)
admin.site.register(Ville, CustomAdmin)
admin.site.register(Gare, CustomAdmin)
admin.site.register(Reduction, CustomAdmin)
admin.site.register(Reservation, CustomAdmin)

