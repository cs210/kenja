// src/firebase.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
    apiKey: "AIzaSyBbExOkIkzL5CcPch2CuXD4mdeez5mb-IE",
    authDomain: "kenja-de166.firebaseapp.com",
    projectId: "kenja-de166",
    storageBucket: "kenja-de166.appspot.com",
    messagingSenderId: "932008787047",
    appId: "1:932008787047:web:387bbf1b21f0502a3aa8c2",
    measurementId: "G-X97JJD9LPJ"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

export { auth };
