// 创建悬浮球
const ball = document.createElement('div');
ball.id = 'floatingBall';
ball.innerText = '🛡';
document.body.appendChild(ball);

// 创建小面板
const panel = document.createElement('div');
panel.id = 'floatingPanel';
panel.innerHTML = `
    <input type="text" id="floatingUrlInput" placeholder="请输入需要检测的网址">
    <button id="floatingDetectBtn">开始检测</button>
`;
document.body.appendChild(panel);

// 点击悬浮球显示/隐藏面板
ball.addEventListener('click', () => {
    panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
});

// 拖拽悬浮球
let isDragging = false, offsetX, offsetY;

ball.addEventListener('mousedown', (e) => {
    isDragging = true;
    offsetX = e.clientX - ball.offsetLeft;
    offsetY = e.clientY - ball.offsetTop;
});

document.addEventListener('mousemove', (e) => {
    if (!isDragging) return;
    ball.style.left = (e.clientX - offsetX) + "px";
    ball.style.top = (e.clientY - offsetY) + "px";

    // 面板跟随悬浮球
    panel.style.left = ball.style.left;
    panel.style.bottom = (window.innerHeight - (e.clientY - offsetY) - 70) + 'px';
});

document.addEventListener('mouseup', () => { isDragging = false; });

// 点击面板按钮触发检测
document.getElementById('floatingDetectBtn').addEventListener('click', () => {
    const url = document.getElementById('floatingUrlInput').value;
    if (!url) return alert("请输入网址！");
    if (typeof detect === 'function') {
        detect(url); // 支持传入 URL
    } else {
        console.log("detect() 函数未定义");
    }
});