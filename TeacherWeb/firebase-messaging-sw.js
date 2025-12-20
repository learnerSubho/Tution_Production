importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');


firebase.initializeApp({
  apiKey: "AIzaSyCLrqb9JU3AsNj5-IbQRPfMVisLU9Cw6b0",
  authDomain: "test-noti-26fe8.firebaseapp.com",
  projectId: "test-noti-26fe8",
  storageBucket: "test-noti-26fe8.appspot.com",
  messagingSenderId: "324451601078",
  appId: "1:324451601078:web:2a89bfdf05279a313cb417",
});

const messaging = firebase.messaging();

messaging.onBackgroundMessage(function(payload) {
  console.log('BG message:', payload);

  const title = payload.data.title;
  const options = {
    body: payload.data.body,
    icon: payload.data.icon,
    image: payload.data.image
  };

  self.registration.showNotification(title, options);
});


// firebase.initializeApp({
//   apiKey: "AIzaSyCLrqb9JU3AsNj5-IbQRPfMVisLU9Cw6b0",
//   authDomain: "test-noti-26fe8.firebaseapp.com",
//   projectId: "test-noti-26fe8",
//   storageBucket: "test-noti-26fe8.appspot.com",
//   messagingSenderId: "324451601078",
//   appId: "1:324451601078:web:2a89bfdf05279a313cb417",
// });

// const messaging = firebase.messaging();

// messaging.onBackgroundMessage(function (payload) {
//   console.log('[firebase-messaging-sw.js] Received background message', payload);

//   const title =
//     payload.data?.title || payload.notification?.title || "New Notification";

//   const options = {
//     body: payload.data?.body || payload.notification?.body,
//     icon: payload.data?.icon || '/static/icons/icon-192.png',
//     image: payload.data?.image,
//   };

//   self.registration.showNotification(title, options);
// });

// // Optional but recommended
// self.addEventListener('notificationclick', function (event) {
//   event.notification.close();
//   event.waitUntil(
//     clients.openWindow('/')
//   );
// });
