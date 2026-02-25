let historyData = JSON.parse(localStorage.getItem("history")) || [];
let radarChart = null;

/* 页面切换 */
function showPage(pageId) {
    document.querySelectorAll(".page").forEach(p => p.style.display = "none");
    document.getElementById(pageId).style.display = "block";

    if (pageId === "history") renderHistory();
    if (pageId === "experiment") renderExperimentChart();
}

/* 保存历史 */
function saveHistory(record) {
    historyData.push(record);
    localStorage.setItem("history", JSON.stringify(historyData));
}

/* 渲染历史 */
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

/* 数字动画（保留以备将来使用，但当前未调用） */
function animateNumber(element, value) {
    if (!element) return;
    let start = 0;
    let duration = 1000;
    let startTime = null;

    function update(time) {
        if (!startTime) startTime = time;
        let progress = time - startTime;
        let current = Math.min(Math.floor(progress / duration * value), value);
        element.innerText = current;
        if (progress < duration) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

/* 雷达图 */
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
            labels: ['URL风险', '文本风险', '图像风险', '综合评分'],
            datasets: [{
                label: '风险评估',
                data: [
                    data.url_analysis ? data.url_analysis.score : 0,
                    data.text_analysis ? data.text_analysis.score : 0,
                    data.image_analysis ? data.image_analysis.score : 0,
                    data.final_score || 0
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
            plugins: {
                legend: { display: false },
                tooltip: { enabled: true }
            },
            scales: {
                r: {
                    min: 0,
                    max: 100,
                    beginAtZero: true,
                    ticks: {
                        stepSize: 10,
                        callback: function(value) {
                            return value + '';
                        },
                        color: '#9ca3af',
                        backdropColor: 'transparent',
                    },
                    grid: {
                        color: 'rgba(255,255,255,0.1)',
                        circular: true,
                    },
                    pointLabels: {
                        color: '#e5e7eb',
                        font: { size: 12, weight: '500' }
                    }
                }
            },
            layout: {
                padding: { top: 20, bottom: 20, left: 20, right: 20 }
            }
        }
    });
}

/* 实验图 */
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

/* 展开解释 */
function toggleExplain() {
    let box = document.getElementById("explainBox");
    if (box) box.style.display = box.style.display === "none" ? "block" : "none";
}

/* 检测逻辑（核心） */
function detect() {
    let url = document.getElementById("urlInput").value;
    if (!url) {
        alert("请输入URL");
        return;
    }

    document.getElementById("loading").style.display = "block";
    document.getElementById("resultSection").style.display = "none";

    callDetectAPI(url).then(data => {
        document.getElementById("loading").style.display = "none";
        document.getElementById("resultSection").style.display = "block";

        console.log("后端返回数据:", data);

        // ----- 更新仪表盘进度圆环 -----
        const gauge = document.getElementById("gaugeProgress");
        if (gauge) {
            const circumference = 339.292; // 2 * π * 54
            const finalScore = data.final_score || 0;
            const offset = circumference - (finalScore / 100) * circumference;
            gauge.style.strokeDashoffset = offset;

            let strokeColor = "#22c55e";
            if (data.risk_level === "Medium Risk" || data.risk_level === "中风险") strokeColor = "#f59e0b";
            if (data.risk_level === "High Risk" || data.risk_level === "高风险") strokeColor = "#ef4444";
            gauge.style.stroke = strokeColor;
        }

        // ----- 显示风险等级 -----
        const riskElem = document.getElementById("riskLevel");
        if (riskElem) riskElem.innerText = data.risk_level || "未知";

        // ----- 显示分数（核心修改：使用 scoreDisplay） -----
        const scoreDisplay = document.getElementById("scoreDisplay");
        if (scoreDisplay) {
            scoreDisplay.textContent = Math.round(data.final_score || 0);
            console.log("分数已设置为:", Math.round(data.final_score || 0));
        } else {
            console.error("scoreDisplay 元素不存在！");
        }

        // ----- 三个分析卡片 -----
        const urlResult = document.getElementById("urlResult");
        if (urlResult) {
            urlResult.innerText = "得分: " + (data.url_analysis ? data.url_analysis.score : 'N/A');
        }
        const textResult = document.getElementById("textResult");
        if (textResult) {
            textResult.innerText = "得分: " + (data.text_analysis ? data.text_analysis.score : 'N/A');
        }
        const imageResult = document.getElementById("imageResult");
        if (imageResult) {
            imageResult.innerText = "得分: " + (data.image_analysis ? data.image_analysis.score : 'N/A');
        }

        // ----- 解释文本 -----
        let explain = document.getElementById("explainText");
        if (explain) {
            explain.innerText = "该网站在URL结构、文本语义及视觉特征中存在风险信号，经多模态加权融合得出综合评分。";
        }

        // 在设置三个卡片分数之后，添加：
       const reasonElem = document.getElementById("reasonText");
       if (reasonElem) {
        reasonElem.innerText = data.reason || "暂无详细分析。";
       }


       // ----- 显示风险报告 -----
const reportContent = document.getElementById("reportContent");
if (reportContent && data.reason) {
    reportContent.innerText = data.reason;
    console.log("风险报告已填充");
} else if (reportContent) {
    reportContent.innerText = "模型未返回详细分析。";
}

        // ----- 保存历史 -----
        saveHistory({
            url: url,
            score: data.final_score,
            level: data.risk_level,
            time: new Date().toLocaleString()
        });

        // ----- 绘制雷达图 -----
        if (document.getElementById("radarChart")) {
            renderRadar(data);
        }
    }).catch(error => {
        console.error("检测失败：", error);
        document.getElementById("loading").style.display = "none";
        alert("检测出错，请查看控制台");
    });
}