// Firebase client config — thyroid-laboratory
// This file is safe to commit (apiKey is not a secret, it’s an identifier)
// Security is enforced via Firebase Security Rules, not the apiKey
import { initializeApp, getApps, getApp, type FirebaseApp } from "firebase/app";
import { getAnalytics, isSupported, type Analytics } from "firebase/analytics";

const firebaseConfig = {
  apiKey: "AIzaSyA0Z7pTHbOMlKh8PmGo6HA5iEdGWg-0vDE",
  authDomain: "thyroid-laboratory.firebaseapp.com",
  projectId: "thyroid-laboratory",
  storageBucket: "thyroid-laboratory.firebasestorage.app",
  messagingSenderId: "51555214466",
  appId: "1:51555214466:web:20688db12034b382ca009b",
  measurementId: "G-308RQXCL1K"
};

export const app: FirebaseApp = getApps().length ? getApp() : initializeApp(firebaseConfig);

// Analytics only in browser and when supported (not during SSR / export)
export let analytics: Analytics | null = null;
if (typeof window !== "undefined") {
  isSupported().then((ok) => {
    if (ok) analytics = getAnalytics(app);
  }).catch(() => {
    // analytics not available (e.g. ad-blocker, file://)
  });
}
