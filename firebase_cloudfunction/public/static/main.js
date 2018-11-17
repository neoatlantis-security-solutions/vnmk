firebase.auth().setPersistence(firebase.auth.Auth.Persistence.NONE);

function isNonexistent(a){
    return (a.error && a.error == "nonexistent");
}


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
    $(".not-authenticated").removeClass("status-logout status-login status-update");
    if(user){
        $(".not-authenticated").addClass("status-login");
        $("#firebase-result").show().text(user.email);
//        $("#firebaseui-auth-container").hide();
        $("#login").attr("disabled", false);
        refreshCountdown();
    } else {
        $(".not-authenticated").addClass("status-logout");
//        $("#firebase-result").hide();
//        $("#firebaseui-auth-container").show();
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


// ---------------------------------------------------------------------------
// Switch to update page
function switchUpdate(on){
    var x = $(".not-authenticated")
        .removeClass("status-logout status-login status-update");
    if(on){
        x.addClass("status-update");
    } else {
        if(firebase.auth().currentUser){
            x.addClass("status-login");
        } else {
            x.addClass("status-logout");
        }
    }
}


// ---------------------------------------------------------------------------
// Countdowns

var countdown = -1;
function refreshCountdown(){
    firebase.functions().httpsCallable("countdown")().then(function(answer){
        if(isNonexistent(answer.data)){ return switchUpdate(true); }
        if(answer.data && answer.data > 0)
            countdown = answer.data;
        else
            countdown = -1;
    });
}

setInterval(function(){
    if(countdown <= 0){
        $("#countdown").text("(unknown)");
    } else {
        countdown -= 500;
        $("#countdown").text((countdown / 1000).toFixed(0));
    }
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
    $("#accesscode").val("");
    if(undefined == accesscode || accesscode.length < 4){
        alert("No valid access code provided.");
        return;
    }

    $("#login").attr("disabled", true);

    firebase.functions().httpsCallable("access")({
        authcode: accesscode.toString(),
    })
    .then(function(result){
        result = result.data;
        if(isNonexistent(result)){ return switchUpdate(true); }
        if(result.secret){
            prepareResult(result.secret);
            return;
        }
        if(result.error){
            $("#error").text(result.error);
            throw result.error;
        }
    })
    .then(function(){
        firebase.auth().signOut();
        $("#login").attr("disabled", false);
    })
    .catch(function(){
        $("#login").attr("disabled", false);
    });
}
$("button#login").click(onLogin);


//----------------------------------------------------------------------------
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

function prepareResult(result){
    $("body")
        .removeClass("status-not-authenticated")
        .addClass("status-authenticated status-unlocked")
    ;
    $(".authenticated")
        .removeClass("status-locked")
        .addClass("status-unlocked")
    ;

    $("#credential").text(result).attr("data-unlocked", "1").show();
    if(isPGPMessage(result)){
        $("#decrypt-prompt").show();
    } else {
        $("#decrypt-prompt").hide();
    }
}

function tryDecrypt(){
    var ciphertext = $('#credential').text();
    $("button#decrypt").attr("disabled", true);
    openpgp.decrypt({
        message: openpgp.message.readArmored(ciphertext),
        passwords: [$("#password").val()],
    }).then(function(plaintext){
        console.log(plaintext);
    }).catch(function(){
        $("button#decrypt").attr("disabled", false);
        alert("Password error.");
    });

}
$("button#decrypt").click(tryDecrypt);

// ---------------------------------------------------------------------------

function updateCredential(){
    if(!firebase.auth().currentUser){
        return alert("Cannot update credential. Must login.");
    }
    var authcode = $("#newauthcode").val(),
        authcode2 = $("#newauthcode2").val(),
        credential = $("#newcredential").val();
    if(authcode != authcode2 || authcode.length < 4){
        alert("Authcode invalid or does not match.");
        return;
    }
    var uid = firebase.auth().currentUser.uid;
    $("textarea").val("");
    $("input").val("");
    firebase.database().ref("/" + uid + "/user").set({
        authcode: authcode,
        secret: credential,
    }).then(function(){
        window.location.reload();
    }).catch(function(){
        alert("Failed updating credential. Try again or relogin.");
    });
}
$("button#update-credential").click(updateCredential);
