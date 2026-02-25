function callDetectAPI(url) {
    return fetch("/detect", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ url: url })
    }).then(res => res.json());
}