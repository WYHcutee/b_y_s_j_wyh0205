from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import re
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route("/detect", methods=["POST"])
def detect():
    try:
        data = request.json
        input_type = data.get("input_type", "url")
        url = data.get("url", "")
        
        print(f"[检测] input_type={input_type}, url={url}")
        
        if input_type == "url":
            url_features = {
                "raw_url": url,
                "domain": url.split("//")[-1].split("/")[0] if "//" in url else url,
                "path": "/" + "/".join(url.split("//")[-1].split("/")[1:]) if "//" in url and len(url.split("//")[-1].split("/")) > 1 else "/",
                "params": ""
            }
            
            text_content = ""
            try:
                resp = requests.get(url, timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                resp.encoding = resp.apparent_encoding
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style"]):
                    tag.extract()
                text_content = soup.get_text(separator=' ', strip=True)[:2000]
                print(f"[检测] 提取文本长度: {len(text_content)}")
            except Exception as e:
                print(f"[检测] 文本提取失败: {e}")
                text_content = "无法获取网页内容"
            
            prompt = f"""
你是一个网络安全专家，请分析以下网站并给出风险评分。

【URL结构分析】
{url_features}

【网页文本内容】
{text_content}

请按以下格式输出：
URL_Score: [分数]
Text_Score: [分数]
Image_Score: [分数]
Reason:
- URL风险分析：[详细说明]
- 文本风险分析：[详细说明]
- 图像风险分析：[详细说明]
- 综合判断：[简短总结]
"""
            
            api_key = os.environ.get("ZHIPU_API_KEY")
            if not api_key:
                return jsonify({"error": "API Key 未配置"}), 500
            
            print(f"[检测] 调用智谱 API...")
            api_response = requests.post(
                "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "glm-4v-flash",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 1024
                },
                timeout=60
            )
            
            print(f"[检测] API 响应状态码: {api_response.status_code}")
            
            if api_response.status_code == 200:
                result = api_response.json()
                content = result["choices"][0]["message"]["content"]
                print(f"[检测] 模型返回内容:\n{content}")
                
                url_score_match = re.search(r"URL_Score:\s*(\d+)", content)
                text_score_match = re.search(r"Text_Score:\s*(\d+)", content)
                image_score_match = re.search(r"Image_Score:\s*(\d+)", content)
                reason_match = re.search(r"Reason:\s*([\s\S]*)", content)
                
                url_score = int(url_score_match.group(1)) if url_score_match else 50
                text_score = int(text_score_match.group(1)) if text_score_match else 50
                image_score = int(image_score_match.group(1)) if image_score_match else 50
                reason = reason_match.group(1).strip() if reason_match else "模型未提供详细分析理由。"
                
                final_score = (url_score + text_score + image_score) / 3
                
                risk_level = "Safe"
                if final_score >= 70:
                    risk_level = "High Risk"
                elif final_score >= 40:
                    risk_level = "Medium Risk"
                
                return jsonify({
                    "checked_urls": [url],
                    "final_score": round(final_score, 1),
                    "image_analysis": {"score": image_score},
                    "rag_knowledge": "",
                    "reason": reason,
                    "risk_level": risk_level,
                    "text_analysis": {"score": text_score},
                    "url_analysis": {"score": url_score}
                })
            else:
                return jsonify({"error": f"API 调用失败: {api_response.status_code}"}), 500
                
        return jsonify({"error": "不支持的输入类型"}), 400
        
    except Exception as e:
        print(f"[检测] 错误: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 50)
    print("简化版服务器启动")
    print("=" * 50)
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)