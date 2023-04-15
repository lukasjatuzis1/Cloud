'use strict';
window.addEventListener('load', function(){
  document.getElementById('sign-out').onclick = function() {
    // ask firebase to sign out the user
    firebase.auth().signOut();
  };

  var uiConfig = {
   signInSuccessUrl: '/', //If firebase sign in was successful, we will be redirected to the URL
   signInOptions: [
   firebase.auth.EmailAuthProvider.PROVIDER_ID
   ]
  };

  firebase.auth().onAuthStateChanged(function(user) { //only be called if the onAuthStateChanged() function is called by firebase (called if user has logged in or out)
    if(user) { //If user has logged in
      document.getElementById('sign-out').hidden = false;
      document.getElementById('login-info').hidden = false;
      console.log('Signed in as ${user.displayName} (${user.email})');
      user.getIdToken().then(function(token) {   //get the token that represents the user and attach it to a cookie for this document(used to 1.Identify the currently logged in user. 2. Maintain session information for this user.)
        document.cookie = "token=" + token;
      });
    } else { //If user has logged out
      var ui = new firebaseui.auth.AuthUI(firebase.auth());  //start new firebase authenticationn widget and set it to parameters defined in html code 100
      ui.start('#firebase-auth-container', uiConfig);      //start UI widget anbd display it to the user.
      document.getElementById('sign-out').hidden = true;
      document.getElementById('login-info').hidden = true;
      document.cookie = "token=";  //Clear token
    }
  }, function(error) {   //If an error occurs
      console.log(error);
      alert('Unable to log in: ' + error);
    });
});
