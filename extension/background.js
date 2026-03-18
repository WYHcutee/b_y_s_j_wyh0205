// background.js - 服务 worker，负责调用后端 API
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'detect') {
    const url = message.url;
    const model = 'glm-4v-flash'; // 或从存储中获取
    fetch('http://127.0.0.1:5000/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input_type: 'url',
        url: url,
        model: model
      })
    })
    .then(res => res.json())
    .then(data => sendResponse({ success: true, data: data }))
    .catch(err => sendResponse({ success: false, error: err.message }));
    return true; // 保持通道开启以异步响应
  }
});