// ==================== 全局变量 ====================
let historyData = JSON.parse(localStorage.getItem("history")) || [];
let radarChart = null;
let currentMode = 'url';      // 当前输入模式: url / text / image
let imageBase64 = '';         // 存储上传图片的 base64

// ==================== 页面切换 ====================
function showPage(pageId) {
    document.querySelectorAll(".page").forEach(p => p.style.display = "none");
    document.getElementById(pageId).style.display = "block";

    document.querySelectorAll(".sidebar ul li").forEach(li => li.classList.remove("active"));
    const menuMap = { 'home': 0, 'history': 1, 'experiment': 2, 'about': 3 };
    const index = menuMap[pageId];
    if (index !== undefined) {
        document.querySelectorAll(".sidebar ul li")[index].classList.add("active");
    }

    if (pageId === "history") renderHistory();
    if (pageId === "experiment") renderExperimentChart();
}

// ==================== 历史记录 ====================
function saveHistory(record) {
    historyData.push(record);
    localStorage.setItem("history", JSON.stringify(historyData));
}

function renderHistory() {
    let table = document.getElementById("historyTable");
    if (!table) return;
    let tbody = table.querySelector("tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    historyData.forEach(item => {
        tbody.innerHTML += `
            <tr>
                <td>${item.url}</td>
                <td>${item.score}</td>
                <td>${item.level}</td>
                <td>${item.time}</td>
            </tr>
        `;
    });
}

// ==================== 数字动画 ====================
function animateNumber(element, value) {
    if (!element) return;
    let startTime = null;
    function update(time) {
        if (!startTime) startTime = time;
        let progress = time - startTime;
        let current = Math.min(Math.floor(progress / 1000 * value), value);
        element.innerText = current;
        if (progress < 1000) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ==================== 雷达图（只显示三个维度）====================
function renderRadar(data) {
    const canvas = document.getElementById("radarChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (radarChart) radarChart.destroy();

    canvas.parentElement.style.width = '400px';
    canvas.parentElement.style.height = '400px';
    canvas.style.width = '100%';
    canvas.style.height = '100%';

    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['URL风险', '文本风险', '图像风险'],
            datasets: [{
                label: '风险评估',
                data: [
                    data.url_analysis ? data.url_analysis.score : 0,
                    data.text_analysis ? data.text_analysis.score : 0,
                    data.image_analysis ? data.image_analysis.score : 0
                ],
                backgroundColor: 'rgba(56,189,248,0.2)',
                borderColor: '#38bdf8',
                pointBackgroundColor: '#38bdf8',
                pointBorderColor: '#fff',
                pointRadius: 4,
                pointHoverRadius: 6,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false }, tooltip: { enabled: true } },
            scales: {
                r: {
                    min: 0, max: 100, beginAtZero: true,
                    ticks: { stepSize: 10, callback: v => v + '', color: '#9ca3af', backdropColor: 'transparent' },
                    grid: { color: 'rgba(255,255,255,0.1)', circular: true },
                    pointLabels: { color: '#e5e7eb', font: { size: 12, weight: '500' } }
                }
            },
            layout: { padding: { top: 20, bottom: 20, left: 20, right: 20 } }
        }
    });
}

// ==================== 实验图表 ====================
function renderExperimentChart() {
    const canvas = document.getElementById("experimentChart");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['传统规则', '单模态模型', '多模态模型'],
            datasets: [{
                label: '准确率(%)',
                data: [78, 85, 92],
                backgroundColor: ['#64748b', '#3b82f6', '#22c55e']
            }]
        }
    });
}

// ==================== 展开解释（备用） ====================
function toggleExplain() {
    let box = document.getElementById("explainBox");
    if (box) box.style.display = box.style.display === "none" ? "block" : "none";
}

// ==================== 模式切换 ====================
function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelector(`.mode-btn[data-mode="${mode}"]`).classList.add('active');
    document.getElementById('url-input-area').style.display = mode === 'url' ? 'flex' : 'none';
    document.getElementById('text-input-area').style.display = mode === 'text' ? 'block' : 'none';
    document.getElementById('image-input-area').style.display = mode === 'image' ? 'block' : 'none';

    // 切换模式时清空图片预览并隐藏清除图片按钮
    if (mode !== 'image') {
        const preview = document.getElementById('imagePreview');
        if (preview) preview.style.display = 'none';
        const p = document.querySelector('.image-upload-area p');
        if (p) p.style.display = 'block';
        imageBase64 = '';
        const clearBtn = document.querySelector('.clear-image-btn');
        if (clearBtn) clearBtn.style.display = 'none';
    } else {
        // 切换到图片模式时隐藏清除按钮（因为初始没有图片）
        const clearBtn = document.querySelector('.clear-image-btn');
        if (clearBtn) clearBtn.style.display = 'none';
    }
}

// ==================== 图片上传处理 ====================
function initImageUpload() {
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const preview = document.getElementById('imagePreview');
    if (!dropArea) return;

    dropArea.addEventListener('click', () => fileInput.click());

    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.style.borderColor = '#3b82f6';
    });

    dropArea.addEventListener('dragleave', () => {
        dropArea.style.borderColor = 'rgba(255,255,255,0.2)';
    });

    dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.style.borderColor = 'rgba(255,255,255,0.2)';
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleImageFile(file);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) handleImageFile(e.target.files[0]);
    });

    document.addEventListener('paste', (e) => {
        if (currentMode !== 'image') return;
        const items = e.clipboardData.items;
        for (let item of items) {
            if (item.type.startsWith('image/')) {
                const file = item.getAsFile();
                handleImageFile(file);
                break;
            }
        }
    });
}

function handleImageFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        imageBase64 = e.target.result.split(',')[1]; // 去掉 data:image 前缀
        const preview = document.getElementById('imagePreview');
        preview.src = e.target.result;
        preview.style.display = 'block';
        document.querySelector('.image-upload-area p').style.display = 'none';
        // 显示清除图片按钮
        const clearBtn = document.querySelector('.clear-image-btn');
        if (clearBtn) clearBtn.style.display = 'inline-block';
    };
    reader.readAsDataURL(file);
}

// ==================== 清空按钮逻辑（新增隐藏结果）====================
// 定义隐藏结果区域的函数
function hideResults() {
    const resultSection = document.getElementById('resultSection');
    if (resultSection) {
        resultSection.style.display = 'none';
    }
}

// 清空 URL 和文本输入框
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('clear-input-btn')) {
        const targetId = e.target.dataset.target;
        if (targetId) {
            const input = document.getElementById(targetId);
            if (input) input.value = '';
        }
        hideResults(); // 隐藏之前的检测结果
    }
});

// 清除图片按钮逻辑
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('clear-image-btn')) {
        // 清除预览
        const preview = document.getElementById('imagePreview');
        if (preview) {
            preview.src = '';
            preview.style.display = 'none';
        }
        // 恢复上传区域文字
        const uploadText = document.querySelector('.image-upload-area p');
        if (uploadText) uploadText.style.display = 'block';
        // 清空图片数据
        imageBase64 = '';
        // 隐藏清除按钮
        e.target.style.display = 'none';
        // 清空文件输入
        const fileInput = document.getElementById('fileInput');
        if (fileInput) fileInput.value = '';

        hideResults(); // 隐藏之前的检测结果
    }
});

// ==================== 检测逻辑（支持三种模式） ====================
function detect() {
    let url = document.getElementById("urlInput")?.value || '';
    let text = document.getElementById("textInput")?.value || '';

    if (currentMode === 'url' && !url) {
        alert("请输入URL");
        return;
    }
    if (currentMode === 'text' && !text) {
        alert("请输入文本内容");
        return;
    }
    if (currentMode === 'image' && !imageBase64) {
        alert("请上传或粘贴图片");
        return;
    }

    document.getElementById("loading").style.display = "block";
    document.getElementById("resultSection").style.display = "none";

    callDetectAPI(url, text, imageBase64).then(data => {
        document.getElementById("loading").style.display = "none";
        document.getElementById("resultSection").style.display = "block";

        console.log("后端返回数据:", data);

        // 更新仪表盘
        const gauge = document.getElementById("gaugeProgress");
        if (gauge) {
            const circumference = 339.292;
            const finalScore = data.final_score || 0;
            const offset = circumference - (finalScore / 100) * circumference;
            gauge.style.strokeDashoffset = offset;

            let strokeColor = "#22c55e";
            if (data.risk_level === "Medium Risk" || data.risk_level === "中风险") strokeColor = "#f59e0b";
            if (data.risk_level === "High Risk" || data.risk_level === "高风险") strokeColor = "#ef4444";
            gauge.style.stroke = strokeColor;
        }

        // 显示风险等级
        const riskElem = document.getElementById("riskLevel");
        if (riskElem) riskElem.innerText = data.risk_level || "未知";

        // 显示分数
        const scoreDisplay = document.getElementById("scoreDisplay");
        if (scoreDisplay) {
            scoreDisplay.textContent = Math.round(data.final_score || 0);
        }

        // 三模态卡片
        document.getElementById("urlResult").innerText = "得分: " + (data.url_analysis?.score ?? 'N/A');
        document.getElementById("textResult").innerText = "得分: " + (data.text_analysis?.score ?? 'N/A');
        document.getElementById("imageResult").innerText = "得分: " + (data.image_analysis?.score ?? 'N/A');

        // 风险报告
        const reportContent = document.getElementById("reportContent");
        if (reportContent && data.reason) {
            reportContent.innerText = data.reason;
        } else {
            reportContent.innerText = "模型未返回详细分析。";
        }

        // 保存历史（根据模式记录）
        let recordUrl = url;
        if (currentMode === 'text') recordUrl = '[文本] ' + text.substring(0, 30) + (text.length > 30 ? '...' : '');
        if (currentMode === 'image') recordUrl = '[图片] 截图上传';
        saveHistory({
            url: recordUrl,
            score: data.final_score,
            level: data.risk_level,
            time: new Date().toLocaleString()
        });

        // 绘制雷达图
        if (document.getElementById("radarChart")) {
            renderRadar(data);
        }
    }).catch(error => {
        console.error("检测失败：", error);
        document.getElementById("loading").style.display = "none";
        alert("检测出错，请查看控制台");
    });
}

// ==================== 网络状态监听 ====================
document.addEventListener('DOMContentLoaded', function() {
    function updateConnectionStatus() {
        const statusElem = document.getElementById('connectionStatus');
        if (statusElem) {
            statusElem.className = navigator.onLine ? 'online' : 'offline';
            statusElem.innerText = navigator.onLine ? '● 在线' : '● 离线';
        }
    }
    window.addEventListener('online', updateConnectionStatus);
    window.addEventListener('offline', updateConnectionStatus);
    updateConnectionStatus();

    // 初始化图片上传
    initImageUpload();
});

// ==================== 动态下拉菜单（body 下固定定位）====================
(function() {
    // 创建菜单元素并添加到 body
    const menu = document.createElement('ul');
    menu.className = 'dropdown-menu';
    menu.innerHTML = `
        <li data-value="glm-4v-flash" class="selected">智谱 (GLM-4V-Flash)</li>
        <li data-value="ernie-bot">文心一言 (ERNIE-Bot)</li>
        <li data-value="qwen-vl-plus">通义千问 (Qwen-VL)</li>
        <li data-value="step-1v">阶跃星辰 (Step-1V)</li>
        <li data-value="deepseek-vl">DeepSeek (VL)</li>
    `;
    document.body.appendChild(menu);

    const button = document.querySelector('.dropdown-button');
    if (!button) return;

    // 显示菜单并定位
    function showMenu() {
        const rect = button.getBoundingClientRect();
        menu.style.left = (rect.left + 9.5)+'px';
        menu.style.top = rect.bottom + 'px';
        menu.style.display = 'block';
        button.classList.add('active');
    }

    // 隐藏菜单
    function hideMenu() {
        menu.style.display = 'none';
        button.classList.remove('active');
    }

    // 点击按钮切换
    button.addEventListener('click', function(e) {
        e.stopPropagation();
        if (menu.style.display === 'block') {
            hideMenu();
        } else {
            showMenu();
        }
    });

    // 点击选项
    menu.addEventListener('click', function(e) {
        const li = e.target.closest('li');
        if (li) {
            button.textContent = li.textContent;
            // 移除其他选中样式
            document.querySelectorAll('.dropdown-menu li').forEach(item => item.classList.remove('selected'));
            li.classList.add('selected');
            hideMenu();
            window.selectedModel = li.dataset.value; // 存储选中值供后续使用
            console.log('选中模型:', window.selectedModel);
        }
    });

    // 点击页面其他区域关闭
    document.addEventListener('click', function(e) {
        if (!button.contains(e.target) && !menu.contains(e.target)) {
            hideMenu();
        }
    });

    // 滚动或窗口大小变化时重新定位（如果菜单显示）
    function reposition() {
        if (menu.style.display === 'block') {
            const rect = button.getBoundingClientRect();
            menu.style.left = rect.left + 'px';
            menu.style.top = rect.bottom + 'px';
        }
    }
    window.addEventListener('scroll', reposition);
    window.addEventListener('resize', reposition);
})();

// ==================== 悬浮球卡片 ====================
let floatingCard = null;

function positionFloatingCard() {
    if (!floatingCard) return;
    const ball = document.getElementById('floatingBall');
    const rect = ball.getBoundingClientRect();
    const cardWidth = floatingCard.offsetWidth;
    const cardHeight = floatingCard.offsetHeight;
    let left = rect.right + 10; // 悬浮球右侧10px
    let top = rect.top;          // 顶部对齐

    // 如果右侧空间不足，则放在左侧
    if (left + cardWidth > window.innerWidth) {
        left = rect.left - cardWidth - 10;
    }
    // 如果底部溢出，则向上调整（简单处理）
    if (top + cardHeight > window.innerHeight) {
        top = window.innerHeight - cardHeight - 20;
    }
    floatingCard.style.left = left + 'px';
    floatingCard.style.top = top + 'px';
}


window.toggleFloatingCard = function() {
    if (!window.floatingCard) {
        window.createFloatingCard();
    } else {
        if (window.floatingCard.style.display === 'block') {
            window.floatingCard.style.display = 'none';
        } else {
            window.positionCardNearBall();
            window.floatingCard.style.display = 'block';
        }
    }
};

window.createFloatingCard = function() {
    if (window.floatingCard) return;
    const card = document.createElement('div');
    card.className = 'floating-card';
    card.innerHTML = `
        <button class="close-btn" onclick="window.closeFloatingCard()">✕</button>
        <input type="text" id="floating-url-input" placeholder="输入网址检测">
        <button onclick="window.floatingDetect()">快速检测</button>
        <div class="floating-result" id="floating-result">
            <div>等待检测...</div>
        </div>
    `;
    document.body.appendChild(card);
    window.floatingCard = card;
    window.positionCardNearBall();
    card.style.display = 'block';
};

// 新增函数：根据悬浮球位置定位卡片
window.positionCardNearBall = function() {
    const card = window.floatingCard;
    if (!card) return;
    const ball = document.getElementById('floatingBall');
    if (!ball) return;
    const ballRect = ball.getBoundingClientRect();
    const cardWidth = card.offsetWidth;
    const cardHeight = card.offsetHeight;
    // 默认放在右侧，垂直居中
    let left = ballRect.right + 10;
    let top = ballRect.top + (ballRect.height / 2) - (cardHeight / 2);
    // 防止超出右边界
    if (left + cardWidth > window.innerWidth) {
        left = ballRect.left - cardWidth - 10;
    }
    // 防止超出上下边界
    top = Math.max(10, Math.min(top, window.innerHeight - cardHeight - 10));
    card.style.left = left + 'px';
    card.style.top = top + 'px';
};

window.closeFloatingCard = function() {
    if (window.floatingCard) {
        window.floatingCard.style.display = 'none';
    }
};

window.floatingDetect = function() {
    const urlInput = document.getElementById('floating-url-input');
    const url = urlInput.value.trim();
    if (!url) {
        alert('请输入网址');
        return;
    }

    const resultDiv = document.getElementById('floating-result');
    resultDiv.innerHTML = '<div>检测中...</div>';

    const model = window.selectedModel || 'glm-4v-flash';

    fetch("/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            input_type: 'url',
            url: url,
            model: model
        })
    })
    .then(res => res.json())
    .then(data => {
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
    })
    .catch(error => {
        resultDiv.innerHTML = `<div style="color: #ef4444;">检测失败</div>`;
        console.error('悬浮球检测失败:', error);
    });
};

// 点击外部关闭卡片
document.addEventListener('click', function(e) {
    if (floatingCard && floatingCard.style.display === 'block') {
        if (!floatingCard.contains(e.target) && e.target.id !== 'floatingBall') {
            floatingCard.style.display = 'none';
        }
    }
});