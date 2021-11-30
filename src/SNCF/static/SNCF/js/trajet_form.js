$(document).ready(function(){
        var date_input=$('input[name="date_depart"]'); //our date input has the name "date"
        var container=$('.bootstrap-iso form').length>0 ? $('.bootstrap-iso form').parent() : "body";
        date_input.datepicker({
            format: 'dd/mm/yyyy',
            container: container,
            todayHighlight: true,
            autoclose: true,
        })
    });

//$(document).ready(function() {
//    $("#create-reservation").modalForm({
//        formURL: "{% url 'create_reservation' %}"
//    });
//});

var trajet, trajet_id,
trajet_gare_depart, trajet_gare_arrivee, trajet_prix,
trajet_heure_depart, trajet_heure_arrivee, trajet_gare_arrivee;
$('#exampleModalCenter').on('show.bs.modal', function (event) {
    var button = $(event.relatedTarget); // Button that triggered the modal
    trajet = button.data('whatever').split('|'),
    trajet_id = trajet[0], trajet_gare_depart = trajet[1],
    trajet_gare_arrivee = trajet[2], trajet_prix = trajet[3],
    trajet_heure_depart = trajet[4], trajet_heure_arrivee = trajet[5],
    trajet_date_depart = trajet[6];; // Extract info from data-* attributes
    // const traj_list = "{{ trajet }}";
    // If necessary, you could initiate an AJAX request here (and then do the updating in a callback).
    // Update the modal's content. We'll use jQuery here, but you could use a data binding library or other methods instead.
    var modal = $(this);
    console.log("trajet_date_depart : ")
    console.log(document.getElementById("id_date_depart").value)
    modal.find('.modal-title').text(trajet_gare_depart + " - " + trajet_gare_arrivee);
    modal.find('.modal-title4').text("Le : " + document.getElementById("id_date_depart").value);
    modal.find('.modal-title2').text("Depart : " + trajet_heure_depart + " -    Arrivee : " + trajet_heure_arrivee);
    modal.find('.modal-title3').text("Prix : " + trajet_prix + "€");
    modal.find('.id_submission').name(trajet_id);
    // modal.find('.modal-body input').val(recipient)
    // var reduc = document.getElementById("id_reduction");
});


document.querySelector("#id_if_user").addEventListener('change', event => {
    console.log(document.querySelector("#id_if_user").checked);
    var bool = document.querySelector("#id_if_user").checked;
    if (bool) {
    console.log("Checkbox is checked..");
    var nom = document.getElementById("id_nom");
    nom.removeAttribute("disabled");
    var prenom = document.getElementById("id_prenom");
    prenom.removeAttribute("disabled");
  } else {
    console.log("Checkbox is not checked..");
    var nom = document.getElementById("id_nom");
    nom.setAttribute("disabled", true);
    var prenom = document.getElementById("id_prenom");
    prenom.setAttribute("disabled", true);
  }
});


