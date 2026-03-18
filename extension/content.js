// content.js - 注入到每个网页的悬浮球

let floatingCard = null;
let floatingBall = null;
let isDragging = false;
let startX, startY, startLeft, startTop;
const DRAG_THRESHOLD = 5;

// 创建悬浮球和卡片
function createFloatingUI() {
  // 悬浮球（一个盾牌图标）
  floatingBall = document.createElement('div');
  floatingBall.id = 'floating-ball';
  floatingBall.innerHTML = '🛡️';
  floatingBall.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
    background: #2563eb;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    cursor: pointer;
    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    z-index: 10000;
    transition: transform 0.2s;
  `;
  document.body.appendChild(floatingBall);

  // 卡片
  floatingCard = document.createElement('div');
  floatingCard.id = 'floating-card';
  floatingCard.className = 'floating-card';
  floatingCard.innerHTML = `
    <button class="close-btn" id="close-card">✕</button>
    <input type="text" id="floating-url-input" placeholder="输入网址检测" value="">
    <button id="floating-detect-btn">快速检测</button>
    <div class="floating-result" id="floating-result">
      <div>等待检测...</div>
    </div>
  `;
  document.body.appendChild(floatingCard);

  // 默认隐藏卡片
  floatingCard.style.display = 'none';

  // 绑定事件
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
}

// 拖拽相关
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
  if (!isDragging) {
    // 视为点击，由 click 事件处理
  }
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
  const cardWidth = floatingCard.offsetWidth;
  const cardHeight = floatingCard.offsetHeight;
  let left = ballRect.right + 10;
  let top = ballRect.top + (ballRect.height/2) - (cardHeight/2);
  if (left + cardWidth > window.innerWidth) {
    left = ballRect.left - cardWidth - 10;
  }
  top = Math.max(10, Math.min(top, window.innerHeight - cardHeight - 10));
  floatingCard.style.left = left + 'px';
  floatingCard.style.top = top + 'px';
}

// 检测函数：通过消息发送给 background
function detectUrl(url) {
  const resultDiv = document.getElementById('floating-result');
  resultDiv.innerHTML = '<div>检测中...</div>';
  chrome.runtime.sendMessage(
    { action: 'detect', url: url },
    (response) => {
      if (response && response.success) {
        const data = response.data;
        const score = Math.round(data.final_score || 0);
        let levelClass = '';
        if (data.risk_level === 'High Risk' || data.risk_level === '高风险') levelClass = 'high';
        else if (data.risk_level === 'Medium Risk' || data.risk_level === '中风险') levelClass = 'medium';
        else levelClass = 'low';
        resultDiv.innerHTML = `
          <div class="score ${levelClass}">${score}</div>
          <div class="risk-level ${levelClass}">${data.risk_level || '未知'}</div>
          <div class="reason">${data.reason || '无详细分析'}</div>
        `;
      } else {
        resultDiv.innerHTML = `<div style="color: #ef4444;">检测失败</div>`;
      }
    }
  );
}

// 初始化
createFloatingUI();