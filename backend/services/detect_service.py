# backend/services/detect_service.py
from backend.feature_extractor.url_features import extract_url_features
from backend.feature_extractor.text_features import extract_text_features
from backend.feature_extractor.image_features import extract_image_features

from backend.fusion.prompt_builder import build_multimodal_prompt
from backend.fusion.model_inference import call_multimodal_model
from backend.fusion.result_parser import parse_model_output
from backend.fusion.fusion_engine import weighted_fusion

from backend.risk.risk_classifier import classify_risk

def detect_website(url):
    """
    对网站进行多模态检测
    """
    try:
        # 1️⃣ 特征提取
        url_features = extract_url_features(url)
        text_data = extract_text_features(url)
        image_data = extract_image_features(url)

        # 2️⃣ 构造 prompt
        prompt = build_multimodal_prompt(url_features, text_data["text_content"])

        # 3️⃣ 调用模型（函数已修改为接受两个参数）
        response = call_multimodal_model(prompt, image_data.get("image_base64"))

        model_text = response["choices"][0]["message"]["content"]

        # 4️⃣ 三分支评分
        url_score, text_score, image_score,reason = parse_model_output(model_text)

        # 5️⃣ 融合
        final_score = weighted_fusion(url_score, text_score, image_score)

        # 6️⃣ 风险等级判定
        risk_level = classify_risk(final_score)

        print(f"[DEBUG] final_score: {final_score}")

        return {
            "url_analysis": {"score": url_score},
            "text_analysis": {"score": text_score},
            "image_analysis": {"score": image_score},
            "final_score": final_score,
            "risk_level": risk_level,
            "reason": reason
        }

    except Exception as e:
        print(f"[ERROR] 网站检测失败: {e}")
        # 返回默认结果，保证后端稳定
        return {
            "url_analysis": {"score": 0.0},
            "text_analysis": {"score": 0.0},
            "image_analysis": {"score": 0.0},
            "final_score": 0.0,
            "risk_level": "unknown",
            "error": str(e)
        }