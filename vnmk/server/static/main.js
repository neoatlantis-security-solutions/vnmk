var AUTH;

$(function(){
    var ui = new firebaseui.auth.AuthUI(firebase.auth());
    ui.start('#firebaseui-auth-container', {
        signInOptions: [
            firebase.auth.GoogleAuthProvider.PROVIDER_ID,
            firebase.auth.GithubAuthProvider.PROVIDER_ID
        ],
        signInFlow: 'popup',
        callbacks: {
            signInSuccessWithAuthResult: onFirebaseAuth,
        }
    });

});

function onFirebaseAuth(authResult){
    firebase.auth().currentUser.getIdToken(true).then(function(idToken){
        AUTH = {
            type: "firebase", 
            data: idToken,
        };
        $("#login").attr("disabled", false);
    });
    return false;
}

function onTelegramAuth(user) {
    console.log(user);
    var username = user.username;
    $("#telegram").text(username);
    $("#login").attr("disabled", false);
    AUTH = {
        type: "telegram", 
        data: user
    };
}



//////////////////////////////////////////////////////////////////////////////
// Page related functions and callbacks


setInterval(function(){
    var countdown = sessionTimeout - new Date().getTime() / 1000;
    $("#countdown").text(countdown.toFixed(0));
}, 500);


function onPageUnload(){
    $("body").empty();
}
$(window).on("beforeunload", onPageUnload);


function onLogin(){
    var accesscode = $("#accesscode").val().trim();
    if(undefined == accesscode || accesscode.length < 3){
        alert("No valid access code provided.");
        return;
    }

    $("#login").attr("disabled", true);
    $.ajax({
        url: "./validate",
        method: "POST",
        data: JSON.stringify({
            auth: AUTH,
            code: accesscode,
        }),
        dataType: "json",
        contentType: "application/json",
    })
    .done(function(answer){
        console.log(answer);
        if(answer.error){
            $("#error").text(answer.error);
            return;
        }
        $("body")
            .removeClass("status-not-authenticated")
            .addClass("status-authenticated")
        ;
        initResult(answer.result);
    })
    .always(function(){
        $("#login").attr("disabled", false);
    });
}

// After successful authentication.

function isPGPMessage(text){
    try{
        var attempt = openpgp.message.readArmored(text);
        if(attempt.packets.length > 0){
            for(var i=0; i<attempt.packets.length; i++)
                if(attempt.packets[i].tag == 18) return true;
        }
    } catch {
    }
    return false;
}

function initResult(result){
    $("#credential").text(result);
    if(isPGPMessage(result)){
        $("#decrypt-prompt").show();
    } else {
        $("#decrypt-prompt").hide();
    }
}

function tryDecrypt(){
}



