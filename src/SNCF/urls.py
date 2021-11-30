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
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# CreateReservation
from .views import index, trajet, SignupView, ListReservations, ReservationDetailView, reserver

urlpatterns = [
    path("", index, name="homepage"),
    path('admin/', admin.site.urls),
    path("account/", include('django.contrib.auth.urls')),
    path('account/signup/', SignupView.as_view(), name="signup"),
    path('trajet/', trajet, name="trajet"),
    path('reservations/', ListReservations.as_view(), name="reservations"),
    # path('reservations/(?P<pk>\d+)', ReservationDetailView.as_view(),
    #      name='detail_reservation'),
    path('reservations/<slug:pk>', ReservationDetailView.as_view(),
         name='detail_reservation'),
    # path('trajet/reservation/', ReservationCreateView.as_view(), name='create_reservation'),
    path('trajet/reserver/', reserver, name="reserver"),
    # path('trajet/reservation/', CreateReservation.as_view(), name='new-reservation')
]
