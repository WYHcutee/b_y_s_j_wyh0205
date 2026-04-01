// background.js - 服务 worker，负责调用后端 API
console.log('[Background] 扩展已加载');

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('[Background] 收到消息:', message.action);
  
  if (message.action === 'ping') {
    sendResponse({ success: true, message: 'pong' });
    return true;
  }
  
  if (message.action === 'detect') {
    const url = message.url;
    const model = 'glm-4v-flash';
    
    console.log('[Background] 检测URL:', url);
    
    fetch('http://127.0.0.1:5555/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input_type: 'url',
        url: url,
        model: model
      })
    })
    .then(res => {
      console.log('[Background] 服务器响应状态:', res.status);
      return res.json();
    })
    .then(data => {
      console.log('[Background] URL检测成功:', data);
      sendResponse({ success: true, data: data });
    })
    .catch(err => {
      console.error('[Background] URL检测错误:', err);
      sendResponse({ success: false, error: err.message });
    });
    return true;
  }
  
  if (message.action === 'detectCurrentPage') {
    const pageText = message.text;
    const imageBase64 = message.image;
    const currentUrl = message.url || '';
    const currentTitle = message.title || '';
    const model = 'glm-4v-flash';
    
    console.log('[Background] 检测当前页面');
    console.log('[Background] URL:', currentUrl);
    console.log('[Background] 标题:', currentTitle);
    console.log('[Background] 文本长度:', pageText ? pageText.length : 0);
    console.log('[Background] 图片:', imageBase64 ? '有数据' : '无');
    
    fetch('http://127.0.0.1:5555/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        input_type: 'text',
        text_content: pageText,
        image_base64: imageBase64,
        url: currentUrl,
        title: currentTitle,
        model: model
      })
    })
    .then(res => {
      console.log('[Background] 服务器响应状态:', res.status);
      return res.json();
    })
    .then(data => {
      console.log('[Background] 页面检测成功:', data);
      sendResponse({ success: true, data: data });
    })
    .catch(err => {
      console.error('[Background] 页面检测错误:', err);
      sendResponse({ success: false, error: err.message });
    });
    return true;
  }
  
  if (message.action === 'captureScreen') {
    console.log('[Background] 截取当前标签页');
    
    chrome.tabs.captureVisibleTab(null, { format: 'jpeg', quality: 50 }, (dataUrl) => {
      if (chrome.runtime.lastError) {
        console.error('[Background] 截图失败:', chrome.runtime.lastError);
        sendResponse({ success: false, error: chrome.runtime.lastError.message });
      } else {
        console.log('[Background] 截图成功');
        const base64 = dataUrl.split(',')[1];
        sendResponse({ success: true, image: base64 });
      }
    });
    return true;
  }
  
  return true;
});