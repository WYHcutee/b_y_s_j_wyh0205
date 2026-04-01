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
    const menuMap = { 'home': 0, 'history': 1, 'experiment': 2, 'rag': 3, 'about': 4 };
    const index = menuMap[pageId];
    if (index !== undefined) {
        document.querySelectorAll(".sidebar ul li")[index].classList.add("active");
    }

    if (pageId === "history") renderHistory();
    if (pageId === "experiment") renderExperimentChart();
    if (pageId === "rag") loadRagKnowledgePath();
}

// ==================== 历史记录 ====================
let currentHistoryFilter = 'all';

function saveHistory(record) {
    if (!record.type) record.type = 'url';
    historyData.push(record);
    localStorage.setItem("history", JSON.stringify(historyData));
}

function clearHistory() {
    if (confirm('确定要清除所有检测历史记录吗？')) {
        historyData = [];
        localStorage.removeItem("history");
        renderHistory();
    }
}

function filterHistory(filter) {
    currentHistoryFilter = filter;
    document.querySelectorAll('.history-filter').forEach(f => f.classList.remove('active'));
    document.querySelector(`.history-filter[data-filter="${filter}"]`).classList.add('active');
    renderHistory();
}

function renderHistory() {
    let table = document.getElementById("historyTable");
    if (!table) return;
    let tbody = table.querySelector("tbody");
    if (!tbody) return;
    tbody.innerHTML = "";
    
    let filteredData = historyData;
    if (currentHistoryFilter !== 'all') {
        filteredData = historyData.filter(item => {
            let itemType = getHistoryItemType(item);
            return itemType === currentHistoryFilter;
        });
    }
    
    if (filteredData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #94a3b8; padding: 30px;">暂无检测记录</td></tr>';
        return;
    }
    
    filteredData.forEach(item => {
        let itemType = getHistoryItemType(item);
        let typeIcon = 'fa-link';
        let typeName = 'URL';
        let typeColor = '#3b82f6';
        
        if (itemType === 'text') {
            typeIcon = 'fa-file-alt';
            typeName = '文本';
            typeColor = '#10b981';
        } else if (itemType === 'image') {
            typeIcon = 'fa-image';
            typeName = '图片';
            typeColor = '#f59e0b';
        }
        
        let levelClass = '';
        if (item.level === '危险') levelClass = 'color: #dc2626;';
        else if (item.level === 'High Risk' || item.level === '高风险') levelClass = 'color: #ef4444;';
        else if (item.level === 'Medium Risk' || item.level === '中风险') levelClass = 'color: #f59e0b;';
        else if (item.level === '低风险') levelClass = 'color: #84cc16;';
        else levelClass = 'color: #10b981;';
        
        let content = item.url || item.content || '-';
        if (content.startsWith('[文本]')) {
            content = content.substring(4).trim();
        } else if (content.startsWith('[图片]')) {
            content = content.substring(4).trim();
        } else if (content.startsWith('[当前页面]')) {
            content = content.substring(6).trim();
        }
        if (content.length > 50) {
            content = content.substring(0, 50) + '...';
        }
        
        let levelText = translateRiskLevel(item.level);
        
        tbody.innerHTML += `
            <tr>
                <td><span style="background: ${typeColor}20; color: ${typeColor}; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;"><i class="fas ${typeIcon}" style="margin-right: 3px;"></i>${typeName}</span></td>
                <td title="${item.url || item.content || ''}">${content}</td>
                <td>${item.score}</td>
                <td style="${levelClass}">${levelText}</td>
                <td>${item.time}</td>
            </tr>
        `;
    });
}

function getHistoryItemType(item) {
    if (item.type) return item.type;
    
    let url = item.url || '';
    if (url.startsWith('[文本]') || item.content) {
        return 'text';
    } else if (url.startsWith('[图片]')) {
        return 'image';
    }
    return 'url';
}

function translateRiskLevel(level) {
    if (!level) return '未知';
    level = level.toLowerCase();
    if (level === 'danger') return '危险';
    if (level === 'high risk') return '高风险';
    if (level === 'medium risk') return '中风险';
    if (level === 'low risk') return '低风险';
    if (level === 'safe') return '安全';
    if (level === 'unknown') return '未知';
    if (level === '危险') return '危险';
    if (level === '高风险') return '高风险';
    if (level === '中风险') return '中风险';
    if (level === '低风险') return '低风险';
    if (level === '安全') return '安全';
    return level;
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
    document.getElementById('batch-input-area').style.display = mode === 'batch' ? 'block' : 'none';

    if (mode !== 'image') {
        const preview = document.getElementById('imagePreview');
        if (preview) preview.style.display = 'none';
        const p = document.querySelector('.image-upload-area p');
        if (p) p.style.display = 'block';
        imageBase64 = '';
        const clearBtn = document.querySelector('.clear-image-btn');
        if (clearBtn) clearBtn.style.display = 'none';
    } else {
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

// ==================== 检测逻辑（支持四种模式） ====================
function detect() {
    if (currentMode === 'batch') {
        batchDetect();
        return;
    }
    
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
    document.getElementById("resultSection").style.display = "block";
    
    const singleSection = document.getElementById("singleResultSection");
    const batchSection = document.getElementById("batchResults");
    if (singleSection) singleSection.style.display = "block";
    if (batchSection) batchSection.style.display = "none";
    
    const urlList = document.getElementById("urlList");
    if (urlList) {
        urlList.innerHTML = '<div style="padding: 10px; text-align: center; color: #94a3b8;">检测中...</div>';
    }

    callDetectAPI(url, text, imageBase64).then(data => {
        document.getElementById("loading").style.display = "none";

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
        if (riskElem) riskElem.innerText = translateRiskLevel(data.risk_level);

        // 显示分数
        const scoreDisplay = document.getElementById("scoreDisplay");
        if (scoreDisplay) {
            scoreDisplay.textContent = Math.round(data.final_score || 0);
        }
        
        // 显示检测耗时
        const timeDisplay = document.getElementById("timeDisplay");
        if (timeDisplay && data.detection_time) {
            timeDisplay.textContent = `检测耗时: ${data.detection_time}`;
            timeDisplay.style.display = 'block';
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

        // 显示检查过的 URL 列表
        const urlList = document.getElementById("urlList");
        if (urlList && data.checked_urls) {
            if (data.checked_urls.length > 0) {
                let html = "";
                data.checked_urls.forEach((checkedUrl, index) => {
                    html += `<div style="margin-bottom: 5px;">${index + 1}. <a href="${checkedUrl}" target="_blank" style="color: #3b82f6;">${checkedUrl}</a></div>`;
                });
                urlList.innerHTML = html;
            } else {
                urlList.innerHTML = "无检查记录";
            }
        }

        // 显示 RAG 知识库引用
        const ragContent = document.getElementById("ragContent");
        const ragStatusBadge = document.getElementById("ragStatusBadge");
        
        if (ragStatusBadge) {
            const status = data.rag_status || 'unknown';
            const mode = data.rag_mode || 'none';
            const sources = data.rag_sources || [];
            
            let statusText = '';
            let statusColor = '';
            let bgColor = '';
            
            if (status === 'available') {
                statusText = `已引用 (${mode === 'vector' ? '向量检索' : '关键词匹配'})`;
                statusColor = '#22c55e';
                bgColor = '#dcfce7';
            } else if (status === 'no_match') {
                statusText = '无匹配内容';
                statusColor = '#f59e0b';
                bgColor = '#fef3c7';
            } else if (status === 'disabled') {
                statusText = '已禁用';
                statusColor = '#6b7280';
                bgColor = '#e5e7eb';
            } else if (status === 'error') {
                statusText = '检索出错';
                statusColor = '#ef4444';
                bgColor = '#fee2e2';
            } else {
                statusText = '未知状态';
                statusColor = '#6b7280';
                bgColor = '#e5e7eb';
            }
            
            ragStatusBadge.textContent = statusText;
            ragStatusBadge.style.color = statusColor;
            ragStatusBadge.style.backgroundColor = bgColor;
        }
        
        if (ragContent) {
            if (data.rag_knowledge && data.rag_knowledge.trim() !== "") {
                ragContent.innerHTML = `<div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; padding: 15px; border-radius: 8px; white-space: pre-wrap;">${data.rag_knowledge}</div>`;
            } else {
                const status = data.rag_status || 'unknown';
                let msg = '';
                if (status === 'disabled') {
                    msg = '知识库已禁用。如需启用，请将 .env 文件中的 RAG_DISABLED 设为 0';
                } else if (status === 'no_match') {
                    msg = '知识库已检索，但未找到与当前检测内容相关的知识';
                } else if (status === 'error') {
                    msg = '知识库检索过程中发生错误';
                } else {
                    msg = '本次检测未引用知识库内容';
                }
                ragContent.innerHTML = `<div style="padding: 10px; text-align: center; color: #94a3b8;"><i class="fas fa-info-circle" style="margin-right: 5px;"></i>${msg}</div>`;
            }
        }

        // 显示网页内容预览
        const pagePreview = document.getElementById("pagePreview");
        const pageTextPreview = document.getElementById("pageTextPreview");
        const pageImagePreview = document.getElementById("pageImagePreview");
        const pageImagesSection = document.getElementById("pageImagesSection");
        const pageImagesPreview = document.getElementById("pageImagesPreview");
        
        if (currentMode === 'url' && pagePreview) {
            pagePreview.style.display = 'block';
            
            if (pageTextPreview && data.page_text) {
                pageTextPreview.textContent = data.page_text;
            } else if (pageTextPreview) {
                pageTextPreview.textContent = '未能获取网页文本';
            }
            
            if (pageImagePreview && data.page_image) {
                pageImagePreview.innerHTML = `<img src="${data.page_image}" style="max-width: 100%; max-height: 300px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);" />`;
            } else if (pageImagePreview) {
                pageImagePreview.innerHTML = '<div style="color: #94a3b8;">暂无截图</div>';
            }
            
            if (pageImagesSection && pageImagesPreview && data.page_images && data.page_images.length > 0) {
                pageImagesSection.style.display = 'block';
                pageImagesPreview.innerHTML = data.page_images.map(img => 
                    `<div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; text-align: center;">
                        <img src="${img.base64}" style="max-width: 200px; max-height: 150px; border-radius: 4px;" />
                        <div style="color: #94a3b8; font-size: 12px; margin-top: 5px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${img.url}</div>
                    </div>`
                ).join('');
            } else if (pageImagesSection) {
                pageImagesSection.style.display = 'none';
            }
        } else if (pagePreview) {
            pagePreview.style.display = 'none';
        }

        // 保存历史（根据模式记录）
        let recordUrl = url;
        let recordContent = '';
        let recordType = currentMode;
        if (currentMode === 'text') {
            recordContent = text.substring(0, 50) + (text.length > 50 ? '...' : '');
            recordUrl = '';
        } else if (currentMode === 'image') {
            recordContent = '图片上传检测';
            recordUrl = '';
        }
        saveHistory({
            url: recordUrl,
            content: recordContent,
            type: recordType,
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

// ==================== 批量检测 ====================
function batchDetect() {
    const batchInput = document.getElementById("batchUrlsInput")?.value || '';
    const urls = batchInput.split('\n').map(u => u.trim()).filter(u => u);
    
    if (urls.length === 0) {
        alert("请输入至少一个URL");
        return;
    }
    
    if (urls.length > 10) {
        alert("最多支持10个URL同时检测");
        return;
    }
    
    document.getElementById("loading").style.display = "block";
    document.getElementById("resultSection").style.display = "block";
    
    const singleSection = document.getElementById("singleResultSection");
    const batchSection = document.getElementById("batchResults");
    if (singleSection) singleSection.style.display = "none";
    if (batchSection) batchSection.style.display = "block";
    
    if (batchSection) {
        batchSection.innerHTML = `<div style="text-align: center; padding: 30px;">
            <div style="font-size: 24px;">⏳</div>
            <div style="margin-top: 10px; color: #94a3af;">正在批量检测 ${urls.length} 个URL...</div>
            <div style="margin-top: 10px; color: #6b7280; font-size: 12px;">预计需要 ${urls.length * 5} 秒左右</div>
        </div>`;
    }
    
    fetch("http://127.0.0.1:5555/batch_detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ urls: urls })
    })
    .then(res => res.json())
    .then(data => {
        document.getElementById("loading").style.display = "none";
        
        if (data.success && data.results) {
            displayBatchResults(data.results);
        } else {
            alert("批量检测失败: " + (data.error || "未知错误"));
        }
    })
    .catch(error => {
        document.getElementById("loading").style.display = "none";
        console.error("批量检测失败:", error);
        alert("批量检测失败，请检查服务器是否运行");
    });
}

function displayBatchResults(results) {
    const resultDiv = document.getElementById("batchResults");
    if (!resultDiv) return;
    
    let html = `<div style="margin-bottom: 15px; padding: 10px; background: rgba(59, 130, 246, 0.1); border-radius: 10px;">
        <span style="color: #3b82f6; font-weight: 600;">批量检测完成</span>
        <span style="color: #94a3af;">共检测 ${results.length} 个URL</span>
    </div>`;
    
    html += '<div style="display: grid; gap: 10px;">';
    
    results.forEach((item, index) => {
        const score = Math.round(item.final_score || 0);
        let levelColor = '#22c55e';
        let levelBg = '#dcfce7';
        let levelText = translateRiskLevel(item.risk_level);
        
        if (item.risk_level === 'High Risk' || item.risk_level === '高风险') {
            levelColor = '#ef4444';
            levelBg = '#fee2e2';
        } else if (item.risk_level === 'Medium Risk' || item.risk_level === '中风险') {
            levelColor = '#f59e0b';
            levelBg = '#fef3c7';
        } else if (item.risk_level === 'Error') {
            levelColor = '#6b7280';
            levelBg = '#f3f4f6';
            levelText = '检测失败';
        }
        
        html += `
        <div style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="flex: 1; overflow: hidden;">
                    <span style="color: #94a3af; font-size: 12px;">#${index + 1}</span>
                    <a href="${item.url}" target="_blank" style="color: #3b82f6; margin-left: 8px; word-break: break-all;">${item.url}</a>
                </div>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 24px; font-weight: bold; color: ${levelColor};">${score}</span>
                    <span style="padding: 4px 12px; border-radius: 20px; background: ${levelBg}; color: ${levelColor}; font-size: 12px; font-weight: 600;">${levelText}</span>
                </div>
            </div>
            <div style="display: flex; gap: 15px; font-size: 12px; color: #94a3af;">
                <span>URL: ${item.url_analysis?.score || 0}</span>
                <span>文本: ${item.text_analysis?.score || 0}</span>
                <span>图片: ${item.image_analysis?.score || 0}</span>
            </div>
            ${item.reason ? `<div style="margin-top: 8px; font-size: 12px; color: #cbd5e1; line-height: 1.5;">${item.reason.substring(0, 150)}${item.reason.length > 150 ? '...' : ''}</div>` : ''}
        </div>`;
        
        saveHistory({
            url: item.url,
            content: '',
            type: 'url',
            score: item.final_score || 0,
            level: item.risk_level || '未知',
            time: new Date().toLocaleString()
        });
    });
    
    html += '</div>';
    resultDiv.innerHTML = html;
}

// ==================== 检测当前页面 ====================
function detectCurrentPage(pageText, imageBase64) {
    document.getElementById("loading").style.display = "block";
    document.getElementById("resultSection").style.display = "none";
    
    // 清空 URL 列表，显示加载提示
    const urlList = document.getElementById("urlList");
    if (urlList) {
        urlList.innerHTML = '<div style="padding: 10px; text-align: center; color: #94a3b8;">检测中...</div>';
    }

    const model = window.selectedModel || 'glm-4v-flash';

    fetch("/detect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            input_type: 'text',
            text: pageText,
            image: imageBase64,
            model: model
        })
    })
    .then(res => res.json())
    .then(data => {
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
        if (riskElem) riskElem.innerText = translateRiskLevel(data.risk_level);

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

        // 显示检查过的 URL 列表
        const urlList = document.getElementById("urlList");
        if (urlList && data.checked_urls) {
            if (data.checked_urls.length > 0) {
                let html = "";
                data.checked_urls.forEach((checkedUrl, index) => {
                    html += `<div style="margin-bottom: 5px;">${index + 1}. <a href="${checkedUrl}" target="_blank" style="color: #3b82f6;">${checkedUrl}</a></div>`;
                });
                urlList.innerHTML = html;
            } else {
                urlList.innerHTML = "无检查记录";
            }
        }

        // 显示 RAG 知识库引用
        const ragContent2 = document.getElementById("ragContent");
        const ragStatusBadge2 = document.getElementById("ragStatusBadge");
        
        if (ragStatusBadge2) {
            const status = data.rag_status || 'unknown';
            const mode = data.rag_mode || 'none';
            
            let statusText = '';
            let statusColor = '';
            let bgColor = '';
            
            if (status === 'available') {
                statusText = `已引用 (${mode === 'vector' ? '向量检索' : '关键词匹配'})`;
                statusColor = '#22c55e';
                bgColor = '#dcfce7';
            } else if (status === 'no_match') {
                statusText = '无匹配内容';
                statusColor = '#f59e0b';
                bgColor = '#fef3c7';
            } else if (status === 'disabled') {
                statusText = '已禁用';
                statusColor = '#6b7280';
                bgColor = '#e5e7eb';
            } else if (status === 'error') {
                statusText = '检索出错';
                statusColor = '#ef4444';
                bgColor = '#fee2e2';
            } else {
                statusText = '未知状态';
                statusColor = '#6b7280';
                bgColor = '#e5e7eb';
            }
            
            ragStatusBadge2.textContent = statusText;
            ragStatusBadge2.style.color = statusColor;
            ragStatusBadge2.style.backgroundColor = bgColor;
        }
        
        if (ragContent2) {
            if (data.rag_knowledge && data.rag_knowledge.trim() !== "") {
                ragContent2.innerHTML = `<div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; padding: 15px; border-radius: 8px; white-space: pre-wrap;">${data.rag_knowledge}</div>`;
            } else {
                const status = data.rag_status || 'unknown';
                let msg = '';
                if (status === 'disabled') {
                    msg = '知识库已禁用。如需启用，请将 .env 文件中的 RAG_DISABLED 设为 0';
                } else if (status === 'no_match') {
                    msg = '知识库已检索，但未找到与当前检测内容相关的知识';
                } else if (status === 'error') {
                    msg = '知识库检索过程中发生错误';
                } else {
                    msg = '本次检测未引用知识库内容';
                }
                ragContent2.innerHTML = `<div style="padding: 10px; text-align: center; color: #94a3b8;"><i class="fas fa-info-circle" style="margin-right: 5px;"></i>${msg}</div>`;
            }
        }

        // 保存历史
        saveHistory({
            url: '[当前页面] ' + window.location.href,
            content: '',
            type: 'url',
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

    initImageUpload();
    
    const batchInput = document.getElementById('batchUrlsInput');
    if (batchInput) {
        batchInput.addEventListener('input', function() {
            const urls = this.value.split('\n').map(u => u.trim()).filter(u => u);
            const countElem = document.getElementById('urlCount');
            if (countElem) {
                countElem.textContent = `已输入: ${urls.length} 个URL`;
                countElem.style.color = urls.length > 10 ? '#ef4444' : '#3b82f6';
            }
        });
    }
});

// ==================== 动态下拉菜单（body 下固定定位）====================
(function() {
    // 创建菜单元素并添加到 body
    const menu = document.createElement('ul');
    menu.className = 'dropdown-menu';
    menu.innerHTML = `
        <li data-value="glm-4v-flash" class="selected">智谱 (GLM-4V-Flash)</li>
        <li data-value="ernie-bot">百度千帆 (ERNIE-Bot)</li>
        <li data-value="qwen-vl-plus">通义千问 (Qwen-VL)</li>
        <li data-value="hunyuan-lite">腾讯混元 (免费)</li>
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
        if (data.risk_level === '危险') levelClass = 'danger';
        else if (data.risk_level === 'High Risk' || data.risk_level === '高风险') levelClass = 'high';
        else if (data.risk_level === 'Medium Risk' || data.risk_level === '中风险') levelClass = 'medium';
        else if (data.risk_level === '低风险') levelClass = 'low';
        else levelClass = 'safe';

        let levelText = translateRiskLevel(data.risk_level);

        resultDiv.innerHTML = `
            <div class="score ${levelClass}">${score}</div>
            <div class="risk-level ${levelClass}">${levelText}</div>
            <div class="reason">${data.reason || '无详细分析'}</div>
        `;
        
        saveHistory({
            url: url,
            content: '',
            type: 'url',
            score: data.final_score || 0,
            level: data.risk_level || '未知',
            time: new Date().toLocaleString()
        });
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

// ==================== 知识库管理 ====================
function switchRagTab(tabName) {
    document.querySelectorAll('.rag-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.rag-tab-content').forEach(t => t.style.display = 'none');
    document.querySelector(`.rag-tab[onclick="switchRagTab('${tabName}')"]`).classList.add('active');
    document.getElementById(`rag-${tabName}-tab`).style.display = 'block';
    
    if (tabName === 'view') loadRagKnowledgeList();
}

async function loadRagKnowledgePath() {
    try {
        const response = await fetch('/rag/list');
        const data = await response.json();
        if (data.knowledge_base_path) {
            document.getElementById('knowledgeBasePath').textContent = data.knowledge_base_path;
        }
    } catch (error) {
        console.error('获取知识库路径失败:', error);
    }
}

async function loadRagKnowledgeList() {
    try {
        const response = await fetch('/rag/list');
        const data = await response.json();
        const list = document.getElementById('ragKnowledgeList');
        
        if (data.items && data.items.length > 0) {
            list.innerHTML = data.items.map(item => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 8px;">
                    <div>
                        <i class="fas fa-file-alt" style="color: #10b981; margin-right: 10px;"></i>
                        <span>${item.name}</span>
                    </div>
                    <span style="color: #94a3b8; font-size: 0.85rem;">${(item.size / 1024).toFixed(2)} KB</span>
                </div>
            `).join('');
        } else {
            list.innerHTML = '<p style="text-align: center; color: #94a3b8;">知识库 documents 目录为空</p>';
        }
    } catch (error) {
        document.getElementById('ragKnowledgeList').innerHTML = '<p style="text-align: center; color: #ef4444;">加载失败</p>';
    }
}

async function addRagKnowledge() {
    const source = document.getElementById('ragSourceInput').value;
    const content = document.getElementById('ragContentInput').value;
    const status = document.getElementById('ragAddStatus');
    
    if (!content.trim()) {
        status.style.display = 'block';
        status.style.background = 'rgba(239, 68, 68, 0.2)';
        status.style.color = '#ef4444';
        status.textContent = '请输入知识内容';
        return;
    }
    
    try {
        const response = await fetch('/rag/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source, content })
        });
        const data = await response.json();
        
        status.style.display = 'block';
        if (data.success) {
            status.style.background = 'rgba(16, 185, 129, 0.2)';
            status.style.color = '#10b981';
            status.textContent = '知识添加成功！';
            document.getElementById('ragContentInput').value = '';
            document.getElementById('ragSourceInput').value = '';
        } else {
            status.style.background = 'rgba(239, 68, 68, 0.2)';
            status.style.color = '#ef4444';
            status.textContent = '添加失败：' + data.error;
        }
        setTimeout(() => { status.style.display = 'none'; }, 5000);
    } catch (error) {
        status.style.display = 'block';
        status.style.background = 'rgba(239, 68, 68, 0.2)';
        status.style.color = '#ef4444';
        status.textContent = '请求失败：' + error.message;
    }
}

async function initRagKnowledgeBase() {
    const status = document.getElementById('ragInitStatus');
    status.style.display = 'block';
    status.style.background = 'rgba(59, 130, 246, 0.2)';
    status.style.color = '#3b82f6';
    status.textContent = '正在初始化知识库...';
    
    try {
        const response = await fetch('/rag/init', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        
        if (data.success) {
            status.style.background = 'rgba(16, 185, 129, 0.2)';
            status.style.color = '#10b981';
            status.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
        } else {
            status.style.background = 'rgba(239, 68, 68, 0.2)';
            status.style.color = '#ef4444';
            status.textContent = '初始化失败：' + data.error;
        }
    } catch (error) {
        status.style.background = 'rgba(239, 68, 68, 0.2)';
        status.style.color = '#ef4444';
        status.textContent = '请求失败：' + error.message;
    }
}

async function testRagRetrieve() {
    const query = document.getElementById('ragQueryInput').value;
    const result = document.getElementById('ragRetrieveResult');
    
    if (!query.trim()) return;
    
    try {
        const response = await fetch('/rag/retrieve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        });
        const data = await response.json();
        
        if (data.knowledge && data.knowledge.trim() !== '') {
            result.innerHTML = `<div style="background: rgba(16, 185, 129, 0.1); border-left: 3px solid #10b981; padding: 15px; border-radius: 8px; white-space: pre-wrap;">${data.knowledge}</div>`;
        } else {
            result.innerHTML = '<p style="text-align: center; color: #94a3b8;">未找到相关知识</p>';
        }
    } catch (error) {
        result.innerHTML = '<p style="text-align: center; color: #ef4444;">检索失败：' + error.message + '</p>';
    }
}