function refreshQRCode(){
    $.ajax({
        url: "./activated",
        dataType: "json",
    }).done(function(data){
        console.log(data);
        if(data.error && data.relogin){
            new QRCode(
                $("#qrcode").empty()[0],
                ("https://t.me/neoatlantis_terminaldogma_bot?start="
                + data.error)
            )
        } else if(data.result == true) {
            window.location.reload();
        }
    }).always(function(){
        setTimeout(refreshQRCode, 3000);
    });
}

$(function(){

    refreshQRCode();

});
