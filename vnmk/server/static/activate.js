function fillQRCode(token){
    new QRCode(
        $("#qrcode").empty()[0],
        ("https://t.me/neoatlantis_terminaldogma_bot?start=" + token)
    );
    $("#qrcode").removeAttr("title");
    $("#startcommand").val("/start " + token);
    $("#botlink").attr(
        "href", "https://t.me/neoatlantis_terminaldogma_bot?start=" + token);
}


function refreshQRCode(){
    if($("#qrcode").attr("data-start")){
        fillQRCode($("#qrcode").attr("data-start"));
        $("#qrcode").removeAttr("data-start");
        return refreshQRCode();
    }

    $.ajax({
        url: "./activated",
        dataType: "json",
    }).done(function(data){
        if(data.error && data.relogin){
            fillQRCode(data.error);
        } else if(data.result == true) {
            window.location.reload();
        }
    }).always(function(){
        setTimeout(refreshQRCode, 1000);
    });
}

$(function(){

    refreshQRCode();

});
