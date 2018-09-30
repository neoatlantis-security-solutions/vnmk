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
        // prepare for login with our server 
        return {
            type: "firebase", 
            data: idToken,
        };
    })
    .then(function(authdata){
        // send login data
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
        if(answer.error){
            $("#error").text(answer.error);
            if(true == answer.relogin){
                onReloginRequired();
            }
            throw answer.error;
        }
        return answer.result;
    })
    .then(function(credentials){
        var newToken = credentials.token,
            credential = credentials.credential;
        $("body")
            .removeClass("status-not-authenticated")
            .addClass("status-authenticated")
        ;
        prepareResult(credential);
        return firebase.auth().signOut().then(function(){
            return firebase.auth().signInWithCustomToken(newToken);
        });
    })
    .then(function(){ // get remote decrypt key
        var r = firebase.database().ref("/credential/" + config.userid + "/");
        return r.once("value");
    })
    .then(function(result){ // on remote decrypt key retrieved
        unlockResult(result.val());
    })
    .then(function(){
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
    $("#credential").text(result);
}

function unlockResult(remoteEncryptKey){
    var key = nacl.util.decodeBase64(remoteEncryptKey),
        ciphertext = nacl.util.decodeBase64($("#credential").text());
    var nonce = ciphertext.slice(0, nacl.secretbox.nonceLength),
        ciphertext = ciphertext.slice(nacl.secretbox.nonceLength);
    var result = nacl.secretbox.open(ciphertext, nonce, key);
    result = nacl.util.encodeUTF8(result);
    $("#credential").text(result);
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


