import datetime
import io
import os
import random

from PyPDF2 import PdfFileReader, PdfFileWriter
from bootstrap_modal_forms.generic import BSModalCreateView
from dal import autocomplete
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage
from django import forms
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404, FileResponse
from django.shortcuts import render, redirect
from django.templatetags.static import static
from django.urls import reverse_lazy, reverse
from django.utils.http import urlencode
from django.views.generic import CreateView, ListView, DetailView
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from website.forms import SignupForm, TrajetForm, ReservationForm
from website.models import CustomUser, Trajet, Gare, Reservation, Place, Voiture, Reduction


def index(request):
    context = {"date": datetime.date.today()}
    try:
        context["user"] = request.user.nom
    except AttributeError:
        context["user"] = ""
    return render(request, "index.html", context)


class SignupView(CreateView):
    model = CustomUser
    template_name = "account/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("account/login")


class ReservationDetailView(DetailView):
    model = Reservation
    template_name = "detail-reservation.html"
    # context_object_name = ""


class ListReservations(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "list-reservations.html"
    # paginate_by = 2

    def get_queryset(self):
        return Reservation.objects.filter(user=self.request.user).order_by("-trajet__date_depart")

    def get_context_data(self, ** kwargs):
        context = super().get_context_data(**kwargs)
        queries = self.get_queryset()
        context["old_reservations"] = queries.exclude(trajet__date_depart__gt =datetime.date.today())
        context["new_reservations"] = queries.filter(trajet__date_depart__gt =datetime.date.today())
        return context

def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Mot de passe changé avec succès!')
            return redirect('change_password')
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

    # form = CreateReservation


@login_required
def trajet(request):
    context = {}
    trajet_list = []
    if request.method == "POST" and 'recherche' in request.POST:
        form = TrajetForm(request.POST)
        print(request.POST)
        context['form'] = form
        if form.is_valid():
            base_url = reverse('trajet')
            query_string = urlencode(form.cleaned_data)
            url = f"{base_url}?{query_string}"
            context["gare_arrivee_value_initial"] = request.GET.get("gare_depart", "")
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
        print("gare_arrivee_form")

        if gare_depart_form != '':
            gare_depart = Gare.objects.get(nom=gare_depart_form)
            gare_arrivee = Gare.objects.get(nom=gare_arrivee_form)
            reduction = Reduction.objects.get(type=reduction_form)
            date_depart = datetime.datetime.strptime(date_depart_form, '%Y-%m-%d')
            context["gare_arrivee_value_initial"] = gare_arrivee_form
            context["gare_arrivee_value_initial_id"] = gare_arrivee.id
            context["gare_depart_value_initial"] = gare_depart_form
            context["gare_depart_value_initial_id"] = gare_depart.id
            trajet_list = Trajet.objects.filter(
                gare_depart=gare_depart,
                gare_arrivee=gare_arrivee,
                heure_depart__range=(heure_depart_form, datetime.time(23, 59)),
                date_depart=date_depart_form,
            ).order_by("heure_depart")
            # trajet_list = Trajet.objects.raw("""SELECT "website_trajet"."id", "website_trajet"."date_depart",
            # "website_trajet"."heure_depart", "website_trajet"."date_arrivee", "website_trajet"."heure_arrivee",
            # "website_trajet"."prix", "website_trajet"."train_id", "website_trajet"."gare_depart_id",
            # "website_trajet"."gare_arrivee_id"
            # FROM "website_trajet"
            # WHERE ("website_trajet"."date_depart" =
            # %s AND "website_trajet"."gare_arrivee_id" = %s AND "website_trajet"."gare_depart_id" = %s AND
            # "website_trajet"."heure_depart" BETWEEN %s AND 23:59:00) ORDER BY "website_trajet"."heure_depart"
            # ASC""", [date_depart_form, int(gare_arrivee.id), int(gare_depart.id), heure_depart_form]) # date_depart_form , heure_depart_form
            print(f"107 : trajet_list.query : {trajet_list.query}")

            form.fields['gare_depart'].initial = gare_depart.nom
            form.fields['gare_arrivee'].initial = gare_arrivee.nom
            form.fields['date_depart'].initial = datetime.datetime.strptime(
                date_depart_form, '%Y-%m-%d').strftime('%d/%m/%Y')
            form.fields['heure_depart'].initial = heure_depart_form
            form.fields['reduction'].initial = reduction

            trajet_list = list(trajet_list)
            for trajet in trajet_list:
                # TODO : prendre la valeur de trajet correspondant au nombre de places restantes
                reservations = Reservation.objects.filter(trajet=trajet)
                voitures = trajet.train.voiture_set.all() # Voiture.objects.filter(train=trajet.train)
                nb_places = len(Place.objects.filter(voiture__in=voitures))
                if len(reservations) == nb_places:
                    trajet.prix = "Complet"
                    trajet.disabled = "disabled"
                else:
                    # TODO : changer le prix en fonction du client.
                    trajet.prix = round(
                        trajet.prix * (1-reduction.pourcentage/100), 2)  # * (1-request)
                    trajet.disabled = ""
    # context['today'] = datetime.date.today()
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
    print("Essaye de réserver")
    trajet_id = int(request.POST.get("trajet_id"))
    nom = request.POST.get("nom")
    prenom = request.POST.get("prenom")
    print(request.POST.get("reduction"))
    reduction = Reduction.objects.get(id=request.POST.get("reduction"))
    situation = request.POST.get("situation")
    print(situation)
    print(trajet_id)
    # Réserve un trajet.
    request_trajet = Trajet.objects.get(id=trajet_id)

    # Trouve une place
    # Cherche les voitures du trajet pour trouver les places
    voitures = Voiture.objects.filter(train=request_trajet.train)
    # Places du trajet
    places_trajet = Place.objects.filter(voiture__in=voitures)
    # Reservations associées au trajet
    reservations = Reservation.objects.filter(trajet=request_trajet)
    # Places déjà réservées
    places_reservees = list(map(lambda x: x.place, list(reservations)))
    # Places du trajet disponibles
    places_dispo = places_trajet.exclude(id__in=[p.id for p in places_reservees]).filter(situation=situation)
    print(places_dispo)
    # Si aucune place dispo à cette situation, donner une place à une autre situation
    if len(places_dispo) == 0:
        places_dispo = places_trajet.exclude(id__in=[p.id for p in places_reservees])
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
        place=place,
        reduction=reduction,
        date=datetime.date.today(),
    )
    new_reservation.save()
    print(new_reservation)
    print(new_reservation.trajet)
    return JsonResponse({"redirect": True, "new_reservation":new_reservation.id})


def trajet_prix(request):
    trajet_id = int(request.POST.get("trajet_id"))
    reduction = Reduction.objects.get(id=request.POST.get("reduction"))
    trajet = Trajet.objects.get(pk=trajet_id)
    prix = trajet.prix * (1 - reduction.pourcentage/100)
    return JsonResponse({"prix": prix})


@login_required
def billet_generator(request, reservation_id):
    # vérifie que le user est le propiétaire de la réservation
    reservation = Reservation.objects.get(pk=reservation_id)
    if request.user != reservation.user:
        return HttpResponse("<h1> Billet introuvable </h1>")

    # créer le pdf du billet :
    # Create a file-like buffer to receive PDF data.

    buffer = open('SNCF/'+static('SNCF/img/e-billet.pdf'), 'r+')
    # Create the PDF object, using the buffer as its "file."
    p = canvas.Canvas(buffer)
    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    # TODO : changer le pdf et mettre toutes les infos
    p.drawString(10, 10, "C'est mon pdffffffff.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    # p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename='hello.pdf')


@login_required
def GareAutoComplete(request):
    gare_text = request.POST.get("gare_text")
    gares = Gare.objects.filter(nom__icontains=gare_text).order_by("nom")
    context = {gare.nom: gare.id for gare in gares}
    return JsonResponse(context)


class GareAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            print('not authentificated')
            return Gare.objects.none()
        qs = Gare.objects.all()
        if self.q:
            qs = qs.filter(nom__icontains=self.q)
        return qs