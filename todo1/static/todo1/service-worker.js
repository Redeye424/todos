
self.addEventListener("push", function(event) {

    let data = {};

    try {
        data = event.data ? event.data.json() : {};
    } catch (error) {
        console.error("Could not read push data:", error);
    }

    console.log("PUSH DATA:", data);

    const title = data.head || "Todos";

    const options = {
        body: data.body || "You have a new notification.",
        icon: data.icon || "/static/icons/icon-192.png",
        badge: data.badge || "/static/icons/icon-192.png",
        image: data.image || undefined,

        data: {
            url: data.url || "/"
        }
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});


self.addEventListener("notificationclick", function(event) {

    event.notification.close();

    const url = event.notification.data?.url || "/";

    event.waitUntil(
        clients.matchAll({
            type: "window",
            includeUncontrolled: true
        }).then(function(clientList) {

            // If your Todos app is already open, focus it
            for (const client of clientList) {

                if ("focus" in client) {
                    client.navigate(url);
                    return client.focus();
                }
            }

            // Otherwise open the site
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});
