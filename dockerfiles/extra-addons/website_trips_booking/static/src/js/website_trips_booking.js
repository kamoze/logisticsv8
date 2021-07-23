$(document).ready(function () {
    var today = new Date();
    openerp.jsonRpc("/trips/locations", 'call', {})
        .then(function (data) {
            $( ".list_of_city" ).autocomplete({
            source: data
        });
    });
    $("#list_of_available_trips_id").html("");
        $("#list_of_return_trips_id").html("");
        var departing_from = $("input[name=departing_location]").val();
        var arriving_at = $("input[name=arriving_location]").val();
        var departing_on = $("input[name=departing_on]").val();
        var arriving_on = $("input[name=arriving_on]").val();
        var is_return_trip = $("#return_trip").is(":checked");
        var number_of_passengers = $("input[name=number_of_passengers]").val();
        openerp.jsonRpc("/trips/find-available-trips", 'call', {'departing_from':departing_from,'arriving_at':arriving_at,'departing_on':departing_on,'number_of_passengers':number_of_passengers,'arriving_on':arriving_on,'is_return_trip':is_return_trip})
        .then(function (data) {
            if(data['avail_trips_name']!= undefined){
                for(var i=0;i<data['avail_trips_name'].length;i++){
                $("#list_of_available_trips_id").append('<option value='+data['avail_trips_name'][i][0]+'>'+data['avail_trips_name'][i][1]+'</option>');
                }
            }
            if(data['available_return_trip']!= undefined){
                for(var i=0;i<data['available_return_trip'].length;i++){
                    $("#list_of_return_trips_id").append('<option value='+data['available_return_trip'][i][0]+'>'+data['available_return_trip'][i][1]+'</option>');
                }
            }
    });

    $('.ac_all_fields_change').change(function(){
        $("#list_of_available_trips_id").html("");
        $("#list_of_return_trips_id").html("");
        var departing_from = $("input[name=departing_location]").val();
        var arriving_at = $("input[name=arriving_location]").val();
        var departing_on = $("input[name=departing_on]").val();
        var arriving_on = $("input[name=arriving_on]").val();
        var is_return_trip = $("#return_trip").is(":checked");
        var number_of_passengers = $("input[name=number_of_passengers]").val();
        openerp.jsonRpc("/trips/find-available-trips", 'call', {'departing_from':departing_from,'arriving_at':arriving_at,'departing_on':departing_on,'number_of_passengers':number_of_passengers,'arriving_on':arriving_on,'is_return_trip':is_return_trip})
        .then(function (data) {
            if(data['avail_trips_name']!= undefined){
                for(var i=0;i<data['avail_trips_name'].length;i++){
                $("#list_of_available_trips_id").append('<option value='+data['avail_trips_name'][i][0]+'>'+data['avail_trips_name'][i][1]+'</option>');
                }
            }
            if(data['available_return_trip']!= undefined){
                for(var i=0;i<data['available_return_trip'].length;i++){
                    $("#list_of_return_trips_id").append('<option value='+data['available_return_trip'][i][0]+'>'+data['available_return_trip'][i][1]+'</option>');
                }
            }
    });

    });
    $('#datepicker_departing').datepicker({
        dateFormat: 'dd/mm/yy',
        minDate : today,
    });
    $('#datepicker_departing').change(function(){
        $( "#datepicker_arriving" ).datepicker( "option", "minDate",  stringToDate($("input[name=departing_on]").val(),"dd/MM/yyyy","/"));
    });

    $('#datepicker_arriving').datepicker({
        dateFormat: 'dd/mm/yy',
        minDate :today,
    });

    function stringToDate(_date,_format,_delimiter){
        var formatLowerCase=_format.toLowerCase();
        var formatItems=formatLowerCase.split(_delimiter);
        var dateItems=_date.split(_delimiter);
        var monthIndex=formatItems.indexOf("mm");
        var dayIndex=formatItems.indexOf("dd");
        var yearIndex=formatItems.indexOf("yyyy");
        var month=parseInt(dateItems[monthIndex]);
        month-=1;
        var formatedDate = new Date(dateItems[yearIndex],month,dateItems[dayIndex]);
        return formatedDate;
    }


    $(".a-submit-trip-ac").click(function(){
        $('.ac_trip_search_form').attr('action', "/trips/available").submit();

    });

    if ($("#one_way_trip").is(":checked")) {
        $(".ac_arriving_on_group").hide();
    }

    $("input[name='ac_event_type']").click(function(){
         if ($("#one_way_trip").is(":checked")) {
            $(".ac_arriving_on_group").hide();
         }
         else{
             $(".ac_arriving_on_group").show();
         }
    });

    $(".pessanger_type_selection").change(function(){
        $(".calculate_total"+$(this).find('option:selected').attr("passenger")).html($(this).find('option:selected').attr("data"));

    });

     $(".pessanger_type_selection").each(function(){
        $(".calculate_total"+$(this).find('option:selected').attr("passenger")).html($(this).find('option:selected').attr("data"));
     });
    $(".ac-view-trip-fares").click(function(){
         $('.ac_trip_search_form').attr('action', "/trips/get-price#view-fares-position").submit();
    });
});
