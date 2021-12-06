"""SNCF URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import django.contrib.auth.urls
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path

# CreateReservation
from django.views.static import serve

from .views import index, trajet, SignupView, ListReservations, \
    ReservationDetailView, reserver, trajet_prix,\
    billet_generator, GareAutoComplete, change_password, \
    UpdateCustomUser, DetailUser, statistics, ReservationDeleteView

handler404 = 'SNCF.views.handler404'

urlpatterns = [
    path("", index, name="homepage"),
    path('admin/', admin.site.urls),
    path("account/", include('django.contrib.auth.urls')),
    path('account/signup/', SignupView.as_view(), name="signup"),
    path('account/password/', change_password, name='change-password'),
    path('account/update/<int:pk>', UpdateCustomUser.as_view(), name='update-profile'),
    path('account/detail/<int:pk>', DetailUser.as_view(), name='detail-profile'),
    path('trajet/', trajet, name="trajet"),
    path('reservations/', ListReservations.as_view(), name="reservations"),
    path('reservations/<slug:pk>/detail/', ReservationDetailView.as_view(),name='detail_reservation'),
    path('reservations/<slug:pk>/delete/', ReservationDeleteView.as_view(), name='delete-reservation'),
    path('trajet/reserver/', reserver, name="reserver"),
    path('trajet/prix', trajet_prix, name='trajet_prix'),
    path('billet/<slug:reservation_id>/', billet_generator, name='billet'),
    path('trajet/gare-autocomplete/', GareAutoComplete, name='gare-autocomplete'),
    path('statistics/', statistics, name='statistics' ),
    # re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),

]
