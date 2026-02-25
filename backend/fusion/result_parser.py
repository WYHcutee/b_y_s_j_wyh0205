import re


def parse_model_output(text):
    url_score_match = re.search(r"URL_Score:\s*(\d+)", text)
    text_score_match = re.search(r"Text_Score:\s*(\d+)", text)
    image_score_match = re.search(r"Image_Score:\s*(\d+)", text)

    # 提取 Reason。注意：Reason 可能跨行，用 [\s\S]* 匹配所有字符直到字符串结束
    reason_match = re.search(r"Reason:\s*([\s\S]*)", text)

    url_score = int(url_score_match.group(1)) if url_score_match else 50
    text_score = int(text_score_match.group(1)) if text_score_match else 50
    image_score = int(image_score_match.group(1)) if image_score_match else 50
    # 如果找不到 Reason，返回一个默认提示
    reason = reason_match.group(1).strip() if reason_match else "模型未提供详细分析理由。"

    return url_score, text_score, image_score, reason