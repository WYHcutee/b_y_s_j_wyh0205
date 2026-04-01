// content.js - 注入到每个网页的悬浮球

let floatingCard = null;
let floatingBall = null;
let isDragging = false;
let startX, startY, startLeft, startTop;
const DRAG_THRESHOLD = 5;

function createFloatingUI() {
  floatingBall = document.createElement('div');
  floatingBall.id = 'floating-ball';
  floatingBall.innerHTML = '🛡️';
  floatingBall.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    cursor: pointer;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    z-index: 2147483647;
    transition: transform 0.2s, box-shadow 0.2s;
  `;
  document.body.appendChild(floatingBall);

  floatingBall.addEventListener('mouseenter', () => {
    floatingBall.style.transform = 'scale(1.1)';
  });
  floatingBall.addEventListener('mouseleave', () => {
    floatingBall.style.transform = 'scale(1)';
  });

  floatingCard = document.createElement('div');
  floatingCard.id = 'floating-card';
  floatingCard.className = 'floating-card';
  floatingCard.innerHTML = `
    <button class="close-btn" id="close-card">✕</button>
    <div style="font-weight: bold; margin-bottom: 12px; font-size: 15px; color: #1f2937; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px;">
      🔍 恶意网站检测
    </div>
    <input type="text" id="floating-url-input" placeholder="输入网址检测" style="width: 100%; padding: 10px 12px; border: 1px solid #e5e7eb; border-radius: 8px; margin-bottom: 10px; box-sizing: border-box; font-size: 13px;">
    <button id="floating-detect-btn" style="width: 100%; padding: 10px; background: #2563eb; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; font-size: 13px; margin-bottom: 8px;">
      📎 检测输入网址
    </button>
    <button id="floating-scan-btn" style="width: 100%; padding: 10px; background: #059669; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 500; font-size: 13px; margin-bottom: 12px;">
      📷 扫描当前页面
    </button>
    <div class="floating-result" id="floating-result">
      <div style="color: #6b7280; text-align: center; padding: 20px;">点击按钮开始检测</div>
    </div>
  `;
  document.body.appendChild(floatingCard);

  floatingCard.style.display = 'none';
  document.getElementById('floating-url-input').value = window.location.href;

  floatingBall.addEventListener('mousedown', onMouseDown);
  floatingBall.addEventListener('click', toggleCard);
  document.getElementById('close-card').addEventListener('click', () => {
    floatingCard.style.display = 'none';
  });
  document.getElementById('floating-detect-btn').addEventListener('click', () => {
    const url = document.getElementById('floating-url-input').value.trim();
    if (!url) { alert('请输入网址'); return; }
    detectUrl(url);
  });
  document.getElementById('floating-scan-btn').addEventListener('click', scanCurrentPage);
}

function onMouseDown(e) {
  e.preventDefault();
  isDragging = false;
  const rect = floatingBall.getBoundingClientRect();
  startLeft = rect.left;
  startTop = rect.top;
  startX = e.clientX;
  startY = e.clientY;
  document.addEventListener('mousemove', onMouseMove);
  document.addEventListener('mouseup', onMouseUp);
}

function onMouseMove(e) {
  const dx = e.clientX - startX;
  const dy = e.clientY - startY;
  if (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD) {
    isDragging = true;
  }
  if (isDragging) {
    floatingBall.style.left = (startLeft + dx) + 'px';
    floatingBall.style.top = (startTop + dy) + 'px';
    floatingBall.style.bottom = 'auto';
    floatingBall.style.right = 'auto';
  }
}

function onMouseUp(e) {
  document.removeEventListener('mousemove', onMouseMove);
  document.removeEventListener('mouseup', onMouseUp);
  isDragging = false;
}

function toggleCard(e) {
  if (isDragging) return;
  if (floatingCard.style.display === 'none' || floatingCard.style.display === '') {
    positionCardNearBall();
    floatingCard.style.display = 'block';
  } else {
    floatingCard.style.display = 'none';
  }
}

function positionCardNearBall() {
  const ballRect = floatingBall.getBoundingClientRect();
  const cardWidth = 320;
  let left = ballRect.right + 10;
  let top = ballRect.top - 50;
  if (left + cardWidth > window.innerWidth) {
    left = ballRect.left - cardWidth - 10;
  }
  top = Math.max(10, Math.min(top, window.innerHeight - 400));
  floatingCard.style.left = left + 'px';
  floatingCard.style.top = top + 'px';
}

const MAX_RETRIES = 3;
const RETRY_DELAY = 2000;

async function retrySendMessage(message, retries = MAX_RETRIES) {
  return new Promise((resolve, reject) => {
    const attempt = (currentRetry) => {
      console.log(`[悬浮球] 发送消息尝试 ${currentRetry + 1}/${retries + 1}`);
      
      chrome.runtime.sendMessage(message, (response) => {
        if (chrome.runtime.lastError) {
          const error = chrome.runtime.lastError.message || '扩展通信错误';
          console.error(`[悬浮球] 尝试 ${currentRetry + 1} 失败:`, error);
          
          if (currentRetry < retries) {
            console.log(`[悬浮球] ${RETRY_DELAY/1000}秒后重试...`);
            setTimeout(() => attempt(currentRetry + 1), RETRY_DELAY);
          } else {
            reject(new Error(`重试${retries}次后仍失败: ${error}`));
          }
        } else {
          resolve(response);
        }
      });
    };
    attempt(0);
  });
}

function detectUrl(url) {
  const resultDiv = document.getElementById('floating-result');
  resultDiv.innerHTML = '<div style="text-align: center; padding: 30px;"><div style="font-size: 24px;">⏳</div><div style="margin-top: 10px; color: #6b7280;">正在检测中...</div></div>';
  
  console.log('[悬浮球] 开始检测URL:', url);
  
  retrySendMessage({ action: 'detect', url: url })
    .then(response => {
      console.log('[悬浮球] URL检测响应:', response);
      if (response && response.success) {
        displayResult(response.data);
      } else {
        const errorMsg = response?.error || '未知错误';
        resultDiv.innerHTML = `<div style="color: #ef4444; text-align: center; padding: 20px;">❌ 检测失败: ${errorMsg}<br><button onclick="detectUrl('${url}')" style="margin-top:10px;padding:6px 12px;background:#2563eb;color:white;border:none;border-radius:6px;cursor:pointer;">重新检测</button></div>`;
      }
    })
    .catch(error => {
      console.error('[悬浮球] 检测失败:', error);
      resultDiv.innerHTML = `<div style="color: #ef4444; text-align: center; padding: 20px;">❌ ${error.message}<br><div style="font-size:11px;color:#9ca3af;margin-top:8px;">请检查服务器是否运行，或刷新页面重试</div><br><button onclick="detectUrl('${url}')" style="margin-top:10px;padding:6px 12px;background:#2563eb;color:white;border:none;border-radius:6px;cursor:pointer;">重新检测</button></div>`;
    });
}

function scanCurrentPage() {
  const resultDiv = document.getElementById('floating-result');
  resultDiv.innerHTML = '<div style="text-align: center; padding: 30px;"><div style="font-size: 24px;">📸</div><div style="margin-top: 10px; color: #6b7280;">正在准备扫描...</div></div>';
  
  console.log('[悬浮球] 当前页面URL:', window.location.href);
  console.log('[悬浮球] 当前页面标题:', document.title);
  
  let pageText = extractPageContent();
  
  console.log('[悬浮球] 页面文本长度:', pageText.length);
  console.log('[悬浮球] 页面文本前200字符:', pageText.substring(0, 200));
  
  captureWithChromeAPI(pageText, resultDiv);
}

function extractPageContent() {
  let content = [];
  
  content.push('【页面标题】' + document.title);
  
  const metaDesc = document.querySelector('meta[name="description"]');
  if (metaDesc) {
    content.push('【页面描述】' + metaDesc.content);
  }
  
  const h1s = document.querySelectorAll('h1');
  if (h1s.length > 0) {
    content.push('【一级标题】' + Array.from(h1s).map(h => h.innerText.trim()).filter(t => t).join(' | '));
  }
  
  const h2s = document.querySelectorAll('h2');
  if (h2s.length > 0) {
    content.push('【二级标题】' + Array.from(h2s).map(h => h.innerText.trim()).filter(t => t).slice(0, 5).join(' | '));
  }
  
  const article = document.querySelector('article') || document.querySelector('main') || document.querySelector('[role="main"]');
  if (article) {
    const articleClone = article.cloneNode(true);
    articleClone.querySelectorAll('script, style, noscript, nav, header, footer, aside, .ad, .advertisement, .sidebar').forEach(el => el.remove());
    const articleText = articleClone.innerText.replace(/\s+/g, ' ').trim();
    if (articleText) {
      content.push('【正文内容】' + articleText.substring(0, 2000));
    }
  }
  
  const paragraphs = document.querySelectorAll('p');
  if (paragraphs.length > 0 && !article) {
    const pText = Array.from(paragraphs)
      .map(p => p.innerText.trim())
      .filter(t => t.length > 20)
      .slice(0, 10)
      .join(' ');
    if (pText) {
      content.push('【段落内容】' + pText.substring(0, 1500));
    }
  }
  
  const links = document.querySelectorAll('a[href]');
  const linkTexts = Array.from(links)
    .map(a => a.innerText.trim())
    .filter(t => t.length > 2 && t.length < 50)
    .slice(0, 10);
  if (linkTexts.length > 0) {
    content.push('【链接文本】' + linkTexts.join(' | '));
  }
  
  const clone = document.body.cloneNode(true);
  clone.querySelectorAll('#floating-ball, #floating-card, .floating-card, script, style, noscript, nav, header, footer').forEach(el => el.remove());
  const bodyText = (clone.innerText || clone.textContent || '').replace(/\s+/g, ' ').trim();
  content.push('【页面其他内容】' + bodyText.substring(0, 1000));
  
  return content.join('\n').substring(0, 4000);
}

function captureWithChromeAPI(pageText, resultDiv) {
  resultDiv.innerHTML = '<div style="text-align: center; padding: 30px;"><div style="font-size: 24px;">📷</div><div style="margin-top: 10px; color: #6b7280;">正在截取页面...</div></div>';
  
  console.log('[悬浮球] 使用 Chrome API 截图');
  
  // 隐藏扩展元素
  const ballDisplay = floatingBall.style.display;
  const cardDisplay = floatingCard.style.display;
  floatingBall.style.display = 'none';
  floatingCard.style.display = 'none';
  
  // 延迟一下让 UI 更新
  setTimeout(() => {
    chrome.runtime.sendMessage(
      { action: 'captureScreen' },
      (response) => {
        // 恢复扩展元素
        floatingBall.style.display = ballDisplay;
        floatingCard.style.display = cardDisplay;
        
        if (chrome.runtime.lastError) {
          console.error('[悬浮球] 扩展错误:', chrome.runtime.lastError);
          resultDiv.innerHTML = `<div style="color: #ef4444; text-align: center; padding: 20px;">❌ 扩展已更新，请刷新页面后重试</div>`;
          return;
        }
        
        if (response && response.success) {
          console.log('[悬浮球] 截图成功, 图片大小:', response.image.length);
          sendForDetection(pageText, response.image, resultDiv, null);
        } else {
          console.error('[悬浮球] 截图失败:', response?.error);
          sendForDetection(pageText, null, resultDiv, '截图失败: ' + (response?.error || '未知错误'));
        }
      }
    );
  }, 100);
}

function sendForDetection(pageText, imageBase64, resultDiv, warningMsg) {
  resultDiv.innerHTML = '<div style="text-align: center; padding: 30px;"><div style="font-size: 24px;">🔍</div><div style="margin-top: 10px; color: #6b7280;">正在分析页面...</div></div>';
  
  const currentUrl = window.location.href;
  const currentTitle = document.title;
  
  console.log('[悬浮球] 发送检测请求, URL:', currentUrl);
  console.log('[悬浮球] 发送检测请求, 图片:', imageBase64 ? '有(' + imageBase64.length + '字符)' : '无');
  
  const message = { 
    action: 'detectCurrentPage', 
    text: pageText, 
    image: imageBase64,
    url: currentUrl,
    title: currentTitle
  };
  
  retrySendMessage(message)
    .then(response => {
      if (response && response.success) {
        displayResult(response.data, warningMsg);
      } else {
        const errorMsg = response?.error || '未知错误';
        resultDiv.innerHTML = `<div style="color: #ef4444; text-align: center; padding: 20px;">❌ 检测失败: ${errorMsg}<br><button onclick="document.getElementById('floating-scan-btn').click()" style="margin-top:10px;padding:6px 12px;background:#059669;color:white;border:none;border-radius:6px;cursor:pointer;">重新扫描</button></div>`;
      }
    })
    .catch(error => {
      console.error('[悬浮球] 检测失败:', error);
      resultDiv.innerHTML = `<div style="color: #ef4444; text-align: center; padding: 20px;">❌ ${error.message}<br><div style="font-size:11px;color:#9ca3af;margin-top:8px;">请检查服务器是否运行，或刷新页面重试</div><br><button onclick="document.getElementById('floating-scan-btn').click()" style="margin-top:10px;padding:6px 12px;background:#059669;color:white;border:none;border-radius:6px;cursor:pointer;">重新扫描</button></div>`;
    });
}

function translateRiskLevel(level) {
  if (!level) return '未知';
  level = level.toLowerCase();
  if (level === 'danger' || level === '危险') return '危险';
  if (level === 'high risk' || level === '高风险') return '高风险';
  if (level === 'medium risk' || level === '中风险') return '中风险';
  if (level === 'low risk' || level === '低风险') return '低风险';
  if (level === 'safe' || level === '安全') return '安全';
  if (level === 'unknown' || level === '未知') return '未知';
  return level;
}

function displayResult(data, warningMsg) {
  const resultDiv = document.getElementById('floating-result');
  
  console.log('[悬浮球] 完整响应数据:', JSON.stringify(data, null, 2));
  console.log('[悬浮球] reason字段:', data.reason);
  
  const score = Math.round(data.final_score || 0);
  
  let levelColor = '#22c55e';
  let levelBgColor = '#dcfce7';
  let levelText = translateRiskLevel(data.risk_level);
  
  if (levelText === '危险') {
    levelColor = '#dc2626';
    levelBgColor = '#fecaca';
  } else if (levelText === '高风险') {
    levelColor = '#ef4444';
    levelBgColor = '#fee2e2';
  } else if (levelText === '中风险') {
    levelColor = '#f59e0b';
    levelBgColor = '#fef3c7';
  } else if (levelText === '低风险') {
    levelColor = '#84cc16';
    levelBgColor = '#ecfccb';
  } else if (levelText === '安全') {
    levelColor = '#22c55e';
    levelBgColor = '#dcfce7';
  }
  
  const reason = data.reason || '无详细分析';
  const urlScore = data.url_analysis?.score || 0;
  const textScore = data.text_analysis?.score || 0;
  const imageScore = data.image_analysis?.score || 0;
  
  let warningHtml = '';
  if (warningMsg) {
    warningHtml = `<div style="background: #fef3c7; color: #92400e; padding: 6px 10px; border-radius: 6px; font-size: 11px; margin-bottom: 10px;">⚠️ ${warningMsg}</div>`;
  }
  
  resultDiv.innerHTML = `
    <div style="text-align: center; padding: 10px 0;">
      <div style="font-size: 42px; font-weight: bold; color: ${levelColor};">${score}</div>
      <div style="font-size: 11px; color: #9ca3af; margin-bottom: 6px;">风险分数 (0-100)</div>
      <div style="display: inline-block; padding: 5px 16px; border-radius: 20px; background: ${levelBgColor}; color: ${levelColor}; font-weight: 600; font-size: 13px; margin-bottom: 12px;">
        ${levelText}
      </div>
      
      <div style="display: flex; justify-content: center; gap: 15px; margin-bottom: 12px; padding: 8px; background: #f9fafb; border-radius: 8px;">
        <div style="text-align: center;">
          <div style="font-size: 14px; font-weight: 600; color: #3b82f6;">${Math.round(urlScore)}</div>
          <div style="font-size: 10px; color: #9ca3af;">URL</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 14px; font-weight: 600; color: #8b5cf6;">${Math.round(textScore)}</div>
          <div style="font-size: 10px; color: #9ca3af;">文本</div>
        </div>
        <div style="text-align: center;">
          <div style="font-size: 14px; font-weight: 600; color: #ec4899;">${Math.round(imageScore)}</div>
          <div style="font-size: 10px; color: #9ca3af;">图片</div>
        </div>
      </div>
    </div>
    
    ${warningHtml}
    
    <div style="text-align: left; font-size: 12px; color: #374151; background: #f9fafb; padding: 10px; border-radius: 8px; line-height: 1.6; max-height: 120px; overflow-y: auto; border: 1px solid #e5e7eb;">
      <div style="font-weight: 600; margin-bottom: 6px; color: #1f2937;">📋 分析详情:</div>
      <div style="white-space: pre-wrap; word-break: break-word;">${reason}</div>
    </div>
  `;
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', createFloatingUI);
} else {
  createFloatingUI();
}