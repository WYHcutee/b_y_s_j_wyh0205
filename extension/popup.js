document.getElementById('popup-detect-btn').addEventListener('click', () => {
  const url = document.getElementById('popup-url-input').value.trim();
  if (!url) { alert('请输入网址'); return; }
  const resultDiv = document.getElementById('popup-result');
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
});