import re

def parse_model_output(text):
    print(f"[解析器] 收到文本长度: {len(text)}")
    print(f"[解析器] 文本内容前500字符: {text[:500]}")
    
    if text.startswith("SECURITY_BLOCK:"):
        reason = text.replace("SECURITY_BLOCK:", "").strip()
        return 0, 0, 0, reason

    url_score_match = re.search(r"URL_Score:\s*(\d+)", text)
    text_score_match = re.search(r"Text_Score:\s*(\d+)", text)
    image_score_match = re.search(r"Image_Score:\s*(\d+)", text)
    
    print(f"[解析器] URL匹配: {url_score_match}")
    print(f"[解析器] Text匹配: {text_score_match}")
    print(f"[解析器] Image匹配: {image_score_match}")

    url_score = int(url_score_match.group(1)) if url_score_match else 0
    text_score = int(text_score_match.group(1)) if text_score_match else 0
    image_score = int(image_score_match.group(1)) if image_score_match else 0
    
    if url_score == 0 and text_score == 0 and image_score == 0:
        if "无风险" in text or "正常" in text or "安全" in text or "未发现" in text:
            url_score = 0
            text_score = 0
            image_score = 0
            print("[解析器] 检测到安全关键词，分数设为0")
        elif "高风险" in text or "危险" in text or "恶意" in text:
            url_score = 70
            text_score = 70
            image_score = 70
            print("[解析器] 检测到高风险关键词，分数设为70")
    
    reason_match = re.search(r"Reason:\s*([\s\S]*)", text)
    if not reason_match:
        reason_match = re.search(r"综合判断[：:]\s*([\s\S]*)", text)
    
    print(f"[解析器] Reason匹配: {reason_match}")
    
    if reason_match:
        reason = reason_match.group(1).strip()
        print(f"[解析器] 提取的Reason: {reason[:200]}...")
    else:
        print("[解析器] 未找到Reason，使用默认值")
        reason = "模型未提供详细分析理由。"

    return url_score, text_score, image_score, reason