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
    table.innerHTML = "";
    historyData.forEach(item => {
        table.innerHTML += `
            <tr>
                <td>${item.url}</td>
                <td>${item.score}</td>
                <td>${item.level}</td>
                <td>${item.time}</td>
            </tr>
        `;
    });
}

/* 数字动画 */
function animateNumber(element, value) {
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
    const ctx = document.getElementById("radarChart").getContext("2d");
    if (radarChart) radarChart.destroy();

    radarChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['URL风险', '文本风险', '图像风险', '综合评分'],
            datasets: [{
                label: '风险评估',
                data: [
                    data.url_analysis.score,
                    data.text_analysis.score,
                    data.image_analysis.score,
                    data.final_score
                ],
                backgroundColor: 'rgba(56,189,248,0.2)',
                borderColor: '#38bdf8'
            }]
        }
    });
}

/* 实验图 */
function renderExperimentChart() {
    const ctx = document.getElementById("experimentChart").getContext("2d");
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
    box.style.display = box.style.display === "none" ? "block" : "none";
}

/* 检测逻辑 */
function detect() {

    let url = document.getElementById("urlInput").value;

    document.getElementById("loading").style.display = "block";
    document.getElementById("resultSection").style.display = "none";

    callDetectAPI(url).then(data => {

        document.getElementById("loading").style.display = "none";
        document.getElementById("resultSection").style.display = "block";

        const circumference = 565;
        const offset = circumference - (data.final_score / 100) * circumference;
        let gauge = document.getElementById("gaugeProgress");
        gauge.style.strokeDashoffset = offset;

        let strokeColor = "#22c55e";
        if (data.risk_level === "Medium Risk") strokeColor = "#f59e0b";
        if (data.risk_level === "High Risk") {
            strokeColor = "#ef4444";
            gauge.classList.add("high-risk-glow");
        } else {
            gauge.classList.remove("high-risk-glow");
        }

        gauge.style.stroke = strokeColor;

        document.getElementById("riskLevel").innerText = data.risk_level;
        animateNumber(document.getElementById("scoreNumber"), data.final_score);

        document.getElementById("urlResult").innerText =
            "得分: " + data.url_analysis.score;

        document.getElementById("textResult").innerText =
            "得分: " + data.text_analysis.score;

        document.getElementById("imageResult").innerText =
            "得分: " + data.image_analysis.score;

        document.getElementById("explainText").innerText =
            "该网站在URL结构、文本语义及视觉特征中存在风险信号，经多模态加权融合得出综合评分。";

        saveHistory({
            url: url,
            score: data.final_score,
            level: data.risk_level,
            time: new Date().toLocaleString()
        });

        renderRadar(data);
    });
}