const CONFIG = require("./config.js");

//////////////////////////////////////////////////////////////////////////////

const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp(functions.config().firebase);

function dbServiceRef(uid, what){
    return admin.database().ref("/" + uid + "/service/" + what);
}

function dbUserRef(uid, what){
    return admin.database().ref("/" + uid + "/user/" + what);
}

function nowtime(){ return Date.now(); }


// Database Operations

async function deleteAccount(uid){
    var ref = admin.database().ref("/" + uid);
    return ref.remove();
}

// Record user access time

exports.recordUserAccess = functions.database.ref(
    "/{uid}/user/"
).onWrite(async (changeObj, context)=>{
    if(!context.auth.uid || context.auth.uid != context.params.uid) return;
    dbServiceRef(
        context.params.uid,
        "last-access"
    ).set(admin.database.ServerValue.TIMESTAMP);
});

// Query for countdown

exports.countdown = functions.https.onCall(async (data, context) => {
    const uid = context.auth.uid;
    if(!uid) return null;

    const lastAccessQuery = await dbServiceRef(uid, "last-access").once("value");
    var lastAccess = lastAccessQuery.val();
    if(null === lastAccess){
        return {"error": "nonexistent"};
    }
    return CONFIG.LOGIN_INTERVAL_MAX - (nowtime() - lastAccess);
});

// Access function

exports.access = functions.https.onCall(async (data, context) => {
    const uid = context.auth.uid;
    if(!uid){
        return {"error": "unauthorized"};
    }

    const existenceQuery = await dbUserRef(uid, "").once("value");
    const userdata = existenceQuery.val();
    if(!(userdata && userdata.authcode && userdata.secret)){
        return {"error": "nonexistent"};
    }

    // Check last access, and see if that's too old -- if yes, delete account.

    const lastAccessQuery = await dbServiceRef(uid, "last-access").once("value");
    var lastAccess = lastAccessQuery.val();
    if(null === lastAccess){
        lastAccess = nowtime();
    }
    if(nowtime() - lastAccess > CONFIG.LOGIN_INTERVAL_MAX){
        await deleteAccount(uid);
        return {"error": "nonexistent"};
    }

    // Validate authcode, return user secret if correct, otherwise, delete
    // account.

    if(!(data.authcode && data.authcode.length >= 4)){
        return {"error": "invalid-authcode"};
    }
    if(userdata.authcode !== data.authcode){
        await deleteAccount(uid);
        return {"error": "nonexistent"};
    }

    // Record this access.
    await dbServiceRef(uid, "last-access").set(
        admin.database.ServerValue.TIMESTAMP);

    return {"secret": userdata.secret};
});

//////////////////////////////////////////////////////////////////////////////

exports[CONFIG.TELEGRAM_SECRET_INTERFACE] = functions.https.onRequest(
    require("./telegram.js"));
