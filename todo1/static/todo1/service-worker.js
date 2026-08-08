self.addEventListener("push", function(event) {

    const data = event.data.json();

    console.log("PUSH DATA:", data);

    self.registration.showNotification(
        data.head,
        {
            body: data.body,
            icon: data.icon,
            image: data.image,
        }
    );

});