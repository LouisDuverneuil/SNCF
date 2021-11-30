import datetime
import random

from bootstrap_modal_forms.generic import BSModalCreateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator, EmptyPage
from django import forms
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.http import urlencode
from django.views.generic import CreateView, ListView, DetailView

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
        context["to_confirm_reservations"] = queries.filter(confirmation=False)
        context["old_reservations"] = queries.exclude(
            trajet__date_depart__gt=datetime.date.today()).filter(confirmation=True)
        context["new_reservations"] = queries.filter(
            trajet__date_depart__gt=datetime.date.today(), confirmation=True)
        return context


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
        context['form'] = form
        if form.is_valid():
            base_url = reverse('trajet')
            query_string = urlencode(form.cleaned_data)
            url = f"{base_url}?{query_string}"
            return redirect(url)
    elif request.method == "POST" and 'reservation' in request.POST:
        print('you tried to save some resa')
    else:
        reduction_form = request.GET.get("reduction", "")
        initial = {
            'reduction': request.user.reduction} if reduction_form == "" else {}
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
            # date_depart = datetime.datetime.strptime(date_depart_form, '%Y-%m-%d')
            trajet_list = Trajet.objects.filter(
                gare_depart=gare_depart,
                gare_arrivee=gare_arrivee,
                heure_depart__range=(heure_depart_form, datetime.time(23, 59)),
                date_depart=date_depart_form,
            ).order_by("heure_depart")
            form.fields['gare_depart'].initial = gare_depart
            form.fields['gare_arrivee'].initial = gare_arrivee
            form.fields['date_depart'].initial = datetime.datetime.strptime(
                date_depart_form, '%Y-%m-%d').strftime('%d/%m/%Y')
            form.fields['heure_depart'].initial = heure_depart_form
            form.fields['reduction'].initial = reduction

            trajet_list = list(trajet_list)
            for trajet in trajet_list:
                # TODO : prendre la valeur de trajet correspondant au nombre de places restantes
                reservations = Reservation.objects.filter(
                    trajet=trajet, confirmation=True)
                # Voiture.objects.filter(train=trajet.train)
                voitures = trajet.train.voiture_set.all()
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
    paginator = Paginator(trajet_list, 1)
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

    voitures = Voiture.objects.filter(train=request_trajet.train)
    places_trajet = Place.objects.filter(voiture__in=voitures)
    reservations = Reservation.objects.filter(trajet=request_trajet)
    places_reservees = list(map(lambda x: x.place, list(reservations)))
    places_dispo = places_trajet.exclude(
        id__in=[p.id for p in places_reservees]).filter(situation=situation)
    print(places_dispo)
    # TODO: filtre sur la situation
    if len(places_dispo) == 0:
        # Regarder parmis les places reservées non confirmees
        reservations = reservations.filter(confirmation=True)
        places_reservees = list(map(lambda x: x.place, list(reservations)))
        places_dispo = places_trajet.exclude(
            id__in=[p.id for p in places_reservees]).filter(situation=situation)
    if len(places_dispo) == 0:
        # regarder parmis les places ayant une autre situation
        places_dispo = places_trajet.exclude(
            id__in=[p.id for p in places_reservees])
    if len(places_dispo) == 0:
        # ne doit pas arriver si le formulaire n'est pas intentionnelement modifié
        raise Http404("<h1>Aucune place disponible</h1>")
    # choix de la place en fonction de la demande de situation:
    place = random.choice(places_dispo)
    print(place)
    # TODO : supprimer les trajets précédents non confirmés
    old_reservations_not_confirmed = Reservation.objects.filter(
        user=request.user, confirmation=False).order_by("date")

    # éviter de stocker trop de réservations non confirmées:
    if len(old_reservations_not_confirmed) > 5:
        pass

    new_reservation = Reservation(
        user=request.user,
        confirmation=False,
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
    return JsonResponse({"redirect": True})


# # @login_required(login_required, name='dispatch')
# class TrajetListView(ListView):
#     model = Trajet
#     template_name = "trajet-form.html"
#     form_class = TrajetForm
#
#     def get_queryset(self):
#         # sourcery skip: inline-immediately-returned-variable
#         form = self.form_class(self.request.POST)
#         trajet_list = Trajet.objects.filter(
#             date_depart=form.fields["date_depart"],
#             heure_depart__range=(form.fields["heure_depart"],  datetime.time(23, 59)),
#             gare_depart=form.fields["gare_depart"],
#             gare_arrivee = form.fields["gare_arrivee"],
#         ).order_by("heure_depart")
#
#         # TODO : si aucun train, faire la recherche par ville.
#         return trajet_list

# @login_required
# def trajet(request):
#     filter = TrajetFilter(request.GET, queryset=Trajet.objects.all())
#     print(filter.qs)
#     return render(request, 'trajet_form.html', {'filter': filter})

# @login_required
# def trajet(request):
#     context = {}
#     if request.method == "POST":
#         form = TrajetForm(request.POST)
#     else:
#         form = TrajetForm(request.POST)
#         # trajet_list = []
#     context['form'] = form
#
#     if form.is_valid():
#         gare_depart_nom = form.cleaned_data["gare_depart"]
#         gare_depart = Gare.objects.get(nom=gare_depart_nom)
#
#         gare_arrivee_nom = form.cleaned_data["gare_arrivee"]
#         gare_arrivee = Gare.objects.get(nom=gare_arrivee_nom)
#
#         heure_depart_form = form.cleaned_data["heure_depart"]
#         date_depart_form = form.cleaned_data["date_depart"]
#
#         trajet_list = Trajet.objects.filter(
#             gare_depart=gare_depart,
#             gare_arrivee=gare_arrivee,
#             heure_depart__range=(heure_depart_form, datetime.time(23, 59)),
#             date_depart=date_depart_form,
#         ).order_by("heure_depart")
#         # check if each trajet has places remaining, else don't show it
#         trajet_list = list(trajet_list)
#         for trajet in trajet_list:
#             # TODO : prendre la valeur de trajet correspondant au nombre de places restantes
#             reservations = Reservation.objects.filter(trajet=trajet, confirmation=True)
#             voitures = Voiture.objects.filter(train=trajet.train)
#             nb_places = len(Place.objects.filter(voiture__in=voitures))
#             if len(reservations) == nb_places:
#                 # enlever trajet de la liste, il est complet.
#                 # trajet_list.remove(trajet)
#                 trajet.prix = "Complet"
#                 trajet.disabled = "disabled"
#             else:
#                 # TODO : changer le prix en fonction du client.
#                 trajet.prix = trajet.prix - 0.01  # * (1-request)
#                 trajet.disabled = ""
#     else:
#         print("Is not valid")
#         trajet_list = []
#
#     context["trajet_list"] = trajet_list
#
#     return render(request, "trajet_form.html", context)
