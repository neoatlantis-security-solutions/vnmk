const functions = require('firebase-functions');
const admin = require('firebase-admin');
admin.initializeApp(functions.config().firebase);

function databaseRef(what){
    return functions.database.ref(what);
}





exports.access = functions.https.onCall(function(data, context){
    const uid = context.auth.uid;
    if(!uid){
        return {"error": "unauthorized"};
    }

    return {
        data: data,
        context: context,
    }
});
