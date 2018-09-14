var config = JSON.parse($("#config").text());

var sessionTimeout=config.session_timeout;
firebase.initializeApp(config.firebase);


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

firebase.auth().onAuthStateChanged(function(user){
    if(user){
        $("#firebase-result").show().text(user.email);
        $("#firebaseui-auth-container").hide();
        $("#login").attr("disabled", false);
    } else {
        $("#firebase-result").hide();
        $("#firebaseui-auth-container").show();
        $("#login").attr("disabled", true);
    }
});

function onFirebaseAuth(authResult){
    return false;
}

/*function onTelegramAuth(user) {
    console.log(user);
    var username = user.username;
    $("#telegram").text(username);
    $("#login").attr("disabled", false);
    AUTH = {
        type: "telegram", 
        data: user
    };
}*/



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


function onReloginRequired(){
    firebase.auth().signOut()
}


function onLogin(){
    var accesscode = $("#accesscode").val().trim();
    if(undefined == accesscode || accesscode.length < 3){
        alert("No valid access code provided.");
        return;
    }

    $("#login").attr("disabled", true);

    firebase.auth().currentUser.getIdToken(true)
    .then(function(idToken){
        return {
            type: "firebase", 
            data: idToken,
        };
    })
    .then(function(authdata){
        return $.ajax({
            url: "./validate",
            method: "POST",
            data: JSON.stringify({
                auth: authdata,
                code: accesscode,
            }),
            dataType: "json",
            contentType: "application/json",
        });
    })
    .then(function(answer){
        console.log(answer);
        if(answer.error){
            $("#error").text(answer.error);
            if(true == answer.relogin){
                onReloginRequired();
            }
            return;
        }
        $("body")
            .removeClass("status-not-authenticated")
            .addClass("status-authenticated")
        ;
        initResult(answer.result);
    })
    .then(function(){
        $("#login").attr("disabled", false);
    })
    .catch(function(){
        $("#login").attr("disabled", false);
    });
}
$("button#login").click(onLogin);


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
$("button#decrypt").click(tryDecrypt);


