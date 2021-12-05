import datetime
import io
import os
import random
from abc import ABC

import pandas as pd
import plotly
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django import forms
from django.db.models import Q
from django.http import HttpResponse, JsonResponse, Http404, FileResponse
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.templatetags.static import static
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.http import urlencode
from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from reportlab.pdfgen import canvas
import plotly.express as px


from website.forms import SignupForm, TrajetForm, ReservationForm, UpdateUserForm
from website.models import CustomUser, Trajet, Gare, Reservation, Place, Voiture, Reduction, calculate_prix


def index(request):
    context = {"date": datetime.date.today()}
    try:
        context["user_nom"] = request.user.nom
    except AttributeError:
        context["user_nom"] = ""
    return render(request, "index.html", context)


class SignupView(CreateView):
    model = CustomUser
    template_name = "account/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("account/login")

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['update'] = False
        context['date'] = datetime.date(year=1972, month=6, day=23).strftime('%d/%m/%Y')
        return context


class DetailUser(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = CustomUser
    template_name = "account/detail-user.html"

    def test_func(self):
        return self.request.user.id == self.kwargs["pk"]


class UpdateUser(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    template_name = "account/signup.html"
    form_class = UpdateUserForm
    # success_url = reverse_lazy("detail-profile", kwargs={'pk': request.user.id})

    def get_success_url(self):
        return reverse_lazy("detail-profile", kwargs={'pk': self.request.user.id})

    def test_func(self):
        return self.request.user.id == self.kwargs["pk"]

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super().get_context_data(**kwargs)
        # Add in a QuerySet of all the books
        context['update'] = True
        context['date'] = self.request.user.date_naissance
        return context


class ReservationDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Reservation
    template_name = "detail-reservation.html"
    # context_object_name = ""
    permission_denied_message = "Hop Hop Hop, où vas-tu. Connectes toi pour en voir plus"

    def test_func(self):
        reservation = Reservation.objects.get(pk=self.kwargs["pk"])
        return self.request.user.id == reservation.user.id


class ReservationDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Reservation
    template_name = "delete-reservation.html"
    success_url = reverse_lazy("reservations")
    # context_object_name = "reservation"

    def test_func(self):
        reservation = Reservation.objects.get(pk=self.kwargs["pk"])
        return self.request.user.id == reservation.user.id


class ListReservations(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "list-reservations.html"
    # paginate_by = 2
    permission_denied_message = "Hop Hop Hop, où vas-tu. Connectes toi pour en voir plus"

    def get_queryset(self):
        # qs = Reservation.objects.filter(user=self.request.user).order_by("-trajet__date_depart")
        qs = Reservation.objects.raw("""SELECT * FROM "website_reservation" INNER JOIN 
        "website_trajet" ON ("website_reservation"."trajet_id" = "website_trajet"."id") WHERE 
        "website_reservation"."user_id" = %s ORDER BY "website_trajet"."date_depart" DESC """, [self.request.user.id])
        return list(qs)

    def get_context_data(self, ** kwargs):
        context = super().get_context_data(**kwargs)
        queries = self.get_queryset()
        # on limite à 5 trajets anciens
        print("context :")
        # context["old_reservations"] = queries.exclude(trajet__date_depart__gt=datetime.date.today())[:5]
        context["old_reservations"] = Reservation.objects.raw("""SELECT * FROM "website_reservation" INNER JOIN 
        "website_trajet" ON ("website_reservation"."trajet_id" = "website_trajet"."id") WHERE (
        "website_reservation"."user_id" = %s AND NOT ("website_trajet"."date_depart" > %s)) ORDER BY 
        "website_trajet"."date_depart" DESC LIMIT 5 """, [self.request.user.id, str(datetime.date.today())])
        # context["new_reservations"] = queries.filter(trajet__date_depart__gt =datetime.date.today())
        context["new_reservations"] = Reservation.objects.raw("""SELECT * FROM "website_reservation" INNER JOIN 
        "website_trajet" ON ("website_reservation"."trajet_id" = "website_trajet"."id") WHERE (
        "website_reservation"."user_id" = %s AND "website_trajet"."date_depart" > %s) ORDER BY 
        "website_trajet"."date_depart" DESC """, [self.request.user.id, str(datetime.date.today())])
        return context


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mot de passe changé avec succès!')
            return redirect('detail-profile', pk=request.user.id)
        else:
            messages.error(request, "Veuillez corriger l'erreur ci-dessus")
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'account/change_password.html', {
        'form': form
    })


class CreateReservation(LoginRequiredMixin, CreateView):
    model = Reservation
    template_name = "create-reservation.html"
    personne = forms.SelectMultiple()
    fields = (
        'trajet',
        'place',
    )
    widgets = {
        'trajet': forms.Textarea(attrs={'readonly': 'readonly'})
    }
    permission_denied_message = "Hop Hop Hop, où vas-tu. Connectes toi pour en voir plus"



@login_required
def trajet(request):
    user_profile = CustomUser.objects.get(id=request.user.id)
    context = {'user_profile_nom':user_profile.nom,
               'user_profile_prenom':user_profile.prenom,
               'user_profile_date_naissance':user_profile.date_naissance.strftime('%d/%m/%Y')
    }
    trajet_list = []
    if request.method == "POST" and 'recherche' in request.POST:
        form = TrajetForm(request.POST)
        context['form'] = form
        if form.is_valid():
            base_url = reverse('trajet')
            query_string = urlencode(form.cleaned_data)
            url = f"{base_url}?{query_string}"
            context["gare_arrivee_value_initial"] = request.GET.get("gare_depart", "")
            context["made_request"] = True
            return redirect(url, context)
    else:
        reduction_form = request.GET.get("reduction", "")
        initial = {'reduction': request.user.reduction} if reduction_form == "" else {}
        form = TrajetForm(initial=initial)
        second_form = ReservationForm(user=request.user)
        context['form'] = form
        context['second_form'] = second_form
        date_depart_form = request.GET.get("date_depart", "")
        gare_depart_form = request.GET.get("gare_depart", "")
        gare_arrivee_form = request.GET.get("gare_arrivee", "")
        heure_depart_form = request.GET.get("heure_depart", "")

        if gare_depart_form != '':
            gare_depart = Gare.objects.get(nom=gare_depart_form)
            gare_arrivee = Gare.objects.get(nom=gare_arrivee_form)
            reduction = Reduction.objects.get(type=reduction_form)
            date_depart = datetime.datetime.strptime(date_depart_form, '%Y-%m-%d')
            context["gare_arrivee_value_initial"] = gare_arrivee_form
            context["gare_arrivee_value_initial_id"] = gare_arrivee.id
            context["gare_depart_value_initial"] = gare_depart_form
            context["gare_depart_value_initial_id"] = gare_depart.id
            # trajet_list = Trajet.objects.filter(
            #     gare_depart=gare_depart,
            #     gare_arrivee=gare_arrivee,
            #     heure_depart__range=(heure_depart_form, datetime.time(23, 59)),
            #     date_depart=date_depart_form,
            # ).order_by("heure_depart")
            l = [date_depart_form, int(gare_arrivee.id), int(gare_depart.id), str(heure_depart_form)]
            trajet_list = Trajet.objects.raw("""SELECT * FROM "website_trajet" WHERE ("website_trajet"."date_depart" = %s AND
            "website_trajet"."gare_arrivee_id" = %s AND "website_trajet"."gare_depart_id" = %s AND
            "website_trajet"."heure_depart" BETWEEN %s AND "23:59:00") ORDER BY "website_trajet"."heure_depart"
            ASC""", l)
            form.fields['gare_depart'].initial = gare_depart.nom
            form.fields['gare_arrivee'].initial = gare_arrivee.nom
            form.fields['date_depart'].initial = datetime.datetime.strptime(
                date_depart_form, '%Y-%m-%d').strftime('%d/%m/%Y')
            form.fields['heure_depart'].initial = heure_depart_form
            form.fields['reduction'].initial = reduction

            trajet_list = list(trajet_list)
            for trajet in trajet_list:
                places_restantes = trajet.places_libres
                if places_restantes == 0:
                    trajet.prix = "Complet"
                    trajet.disabled = "disabled"
                else:
                    date_naissance = request.user.date_naissance
                    trajet.prix = calculate_prix(trajet, reduction, date_naissance)
                    trajet.disabled = ""
    context["made_request"] = True
    paginator = Paginator(trajet_list, 5)
    try:
        current_page = request.GET.get('page')
        if not current_page:
            current_page = 1
        trajet_list = paginator.page(current_page)
        context['page_obj'] = paginator.get_page(current_page)
    except EmptyPage:
        trajet_list = paginator.page(paginator.num_pages)
        context['page_obj'] = paginator.get_page(paginator.num_pages)
    context['trajet_list'] = trajet_list

    context['today'] = datetime.date.today().strftime('%d/%m/%Y')
    return render(request, "trajet_form.html", context)


def reserver(request):
    trajet_id = int(request.POST.get("trajet_id"))
    nom = request.POST.get("nom")
    prenom = request.POST.get("prenom")
    if not prenom or not nom:
        return JsonResponse({"redirect": False,
                             "message_erreur": "Veuillez entrer un nom et prénom valides"})
    date_naissance_form = request.POST.get("date_naissance")
    try:
        date_naissance = datetime.datetime.strptime(date_naissance_form, '%d/%m/%Y')
    except ValueError:
        return JsonResponse({"redirect": False,
                             "message_erreur": "Veuillez entrer une date valide (format : jj/mm/aaaa)"})
    reduction = Reduction.objects.get(id=request.POST.get("reduction"))
    situation = request.POST.get("situation")
    # Réserve un trajet.
    request_trajet = Trajet.objects.get(id=trajet_id)

    # Trouve une place
    # Cherche les voitures du trajet pour trouver les places
    # voitures = Voiture.objects.filter(train=request_trajet.train)
    # Places du trajet
    # places_trajet = Place.objects.filter(voiture__in=voitures)
    # Reservations associées au trajet
    # reservations = Reservation.objects.filter(trajet=request_trajet)
    # Places déjà réservées
    # places_reservees = list(map(lambda x: x.place, list(reservations)))
    # Places du trajet disponibles
    # places_dispo = places_trajet.exclude(id__in=[p.id for p in places_reservees]).filter(situation=situation)
    places_dispo = Place.objects.raw("""SELECT * FROM "website_place" WHERE ("website_place"."voiture_id" IN 
    (SELECT U0."id" FROM "website_voiture" U0 WHERE U0."train_id" = %s) AND NOT 
    ("website_place"."id" IN  (SELECT U1."place_id" FROM "website_reservation" U1 WHERE U1."trajet_id" = %s)) 
    AND "website_place"."situation" = %s) """, [request_trajet.train.id, trajet_id, situation])
    # Si aucune place dispo à cette situation, donner une place à une autre situation
    if len(places_dispo) == 0:
        # places_dispo = places_trajet.exclude(id__in=[p.id for p in places_reservees])
        places_dispo = Place.objects.raw("""SELECT * FROM "website_place" WHERE ("website_place"."voiture_id" IN 
        (SELECT U0."id" FROM "website_voiture" U0 WHERE U0."train_id" = %s) AND NOT 
        ("website_place"."id" IN  (SELECT U1."place_id" FROM "website_reservation" U1 WHERE U1."trajet_id" = %s)))
        """, [request_trajet.train.id, trajet_id])
    if len(places_dispo) == 0:
        # ne doit pas arriver si le formulaire n'est pas (mal) intentionnellement modifié
        raise Http404("<h1>Aucune place disponible</h1>")
    # choix de la place en fonction de la demande de situation:
    place = random.choice(places_dispo)
    print(place)
    new_reservation = Reservation(
        user=request.user,
        trajet=request_trajet,
        nom=nom,
        prenom=prenom,
        date_naissance=date_naissance,
        place=place,
        reduction=reduction,
        date=timezone.now(),
    )
    new_reservation.save()
    print(new_reservation)
    print(new_reservation.trajet)
    return JsonResponse({"redirect": True, "new_reservation":new_reservation.id})


def trajet_prix(request):
    trajet_id = int(request.POST.get("trajet_id"))
    # reduction = Reduction.objects.get(id=request.POST.get("reduction"))
    reduction = Reduction.objects.raw(""" SELECT * FROM "website_reduction" WHERE 
    "website_reduction"."id" = %s """, [request.POST.get("reduction")])[0]
    date_naissance = request.POST.get("date_naissance")
    # trajet = Trajet.objects.get(pk=trajet_id)
    trajet = Trajet.objects.raw(""" SELECT * FROM "website_trajet" WHERE 
    "website_trajet"."id" = %s """, [str(trajet_id)])[0]
    prix = calculate_prix(trajet=trajet, reduction=reduction, born=date_naissance)
    return JsonResponse({"prix": prix})


@login_required
def billet_generator(request, reservation_id):
    # vérifie que le user est le propiétaire de la réservation
    reservation = Reservation.objects.get(pk=reservation_id)
    if request.user != reservation.user:
        return HttpResponse("<h1> Billet introuvable </h1>")

    # créer le pdf du billet :
    # Create a file-like buffer to receive PDF data.

    # buffer = open('SNCF/'+static('SNCF/img/e-billet.pdf'), 'r+')
    buffer = io.BytesIO()
    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer)
    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    # TODO : changer le pdf et mettre toutes les infos
    p.drawString(100, 100, "C'est mon pdffffffff.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename='hello.pdf')


@login_required
def GareAutoComplete(request):
    gare_text = request.POST.get("gare_text")
    # gares = Gare.objects.filter(Q(nom__icontains=gare_text) | Q(ville__nom__icontains=gare_text)).order_by("nom")
    gares = list(Gare.objects.raw("""SELECT * FROM 
    "website_gare" INNER JOIN "website_ville" ON ("website_gare"."ville_id" = "website_ville"."id") WHERE (
    "website_gare"."nom" LIKE %s ESCAPE '\\' OR "website_ville"."nom" LIKE %s ESCAPE '\\') ORDER BY 
    "website_gare"."nom" ASC """, [f"%{str(gare_text)}%", f"%{str(gare_text)}%"]))
    context = {gare.nom: gare.id for gare in gares}
    return JsonResponse(context)


@login_required
def statistics(request):
    context = {}
    # my_resa = Reservation.objects.filter(user=request.user)
    my_resa = Reservation.objects.raw("""SELECT * FROM "website_reservation" WHERE 
    "website_reservation"."user_id" = %s """, [request.user.id])

    if not my_resa:
        return render(request, 'statistics.html', context)
    prices = list(map(lambda x: x.prix, my_resa))
    dates = list(map(lambda x: x.trajet.date_depart, my_resa))
    df_prix = pd.DataFrame({'prix': prices, 'date':dates})
    # print(df_prix)

    fig_prix = px.histogram(df_prix, x='date', y='prix')
    fig_prix.update_layout(
        title="Prix des réservations de billet de train au cours du temps",
        xaxis_title='Date de départ du train',
        yaxis_title='Prix du billet (en €)')

    plt_div_prix = plotly.offline.plot(fig_prix, output_type='div')

    context["graph_prix"] = plt_div_prix
    return render(request, 'statistics.html', context)


def handler404(request, exception):
    return render(request, '404.html', status=404)
