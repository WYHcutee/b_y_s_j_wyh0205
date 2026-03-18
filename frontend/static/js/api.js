/*function callDetectAPI(url, text, imageBase64) {
    const model = document.getElementById('modelSelector').value;
    const mode = document.querySelector('.mode-btn.active').dataset.mode;
    let payload = { model: model };

    if (mode === 'url') {
        payload.input_type = 'url';
        payload.url = url;
    } else if (mode === 'text') {
        payload.input_type = 'text';
        payload.text_content = text;
    } else if (mode === 'image') {
        payload.input_type = 'image';
        payload.image_base64 = imageBase64;
    }

    return fetch("/detect", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
    }).then(res => res.json());
}*/
function callDetectAPI(url, text, imageBase64) {
    const model = window.selectedModel || 'glm-4v-flash';
    const mode = document.querySelector('.mode-btn.active').dataset.mode;
    let payload = { model: model };

    if (mode === 'url') {
        payload.input_type = 'url';
        payload.url = url;
    } else if (mode === 'text') {
        payload.input_type = 'text';
        payload.text_content = text;
    } else if (mode === 'image') {
        payload.input_type = 'image';
        payload.image_base64 = imageBase64;
    }

    return fetch("/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    }).then(res => res.json());
}