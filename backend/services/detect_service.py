from backend.feature_extractor.url_features import extract_url_features
from backend.feature_extractor.text_features import extract_text_features
from backend.feature_extractor.image_features import extract_image_features
from backend.fusion.prompt_builder import build_multimodal_prompt
from backend.fusion.model_inference import call_multimodal_model
from backend.fusion.result_parser import parse_model_output
from backend.fusion.fusion_engine import weighted_fusion
from backend.risk.risk_classifier import classify_risk

def detect_website(input_type='url', url=None, text_content=None, image_base64=None, model_name='glm-4v-flash'):
    """
    统一检测入口，支持URL、文本、图片三种输入
    """
    try:
        # 根据输入类型提取特征
        if input_type == 'url':
            url_features = extract_url_features(url)
            text_data = extract_text_features(url)
            image_data = extract_image_features(url)
            prompt = build_multimodal_prompt(url_features, text_data["text_content"], mode='url')
            img_b64 = image_data.get("image_base64")
        elif input_type == 'text':
            # 文本模式：无URL特征，无图像
            url_features = {"raw_url": "", "domain": "", "path": "", "params": ""}
            prompt = build_multimodal_prompt(url_features, text_content, mode='text')
            img_b64 = None
        elif input_type == 'image':
            # 图片模式：无URL和文本
            url_features = {"raw_url": "", "domain": "", "path": "", "params": ""}
            prompt = build_multimodal_prompt(url_features, "", mode='image')
            img_b64 = image_base64
        else:
            raise ValueError(f"未知输入类型: {input_type}")

        # 调用模型
        response = call_multimodal_model(prompt, img_b64, model_name=model_name)
        model_text = response["choices"][0]["message"]["content"]

        # 解析结果（模型应返回三个分数）
        url_score, text_score, image_score, reason = parse_model_output(model_text)

        # 根据输入类型调整：如果某模态缺失，将其分数设为0（模型可能已返回0，但保险）
        if input_type == 'text':
            url_score = 0
            image_score = 0
            reason = "[文本模式]" + reason
        elif input_type == 'image':
            url_score = 0
            text_score = 0
            reason = "[图片模式]" + reason

        # 融合（可根据输入类型调整权重，此处简单平均或直接使用对应分数）
        if input_type == 'url':
            final_score = weighted_fusion(url_score, text_score, image_score)
        elif input_type == 'text':
            final_score = text_score
        elif input_type == 'image':
            final_score = image_score

        risk_level = classify_risk(final_score)

        return {
            "url_analysis": {"score": url_score},
            "text_analysis": {"score": text_score},
            "image_analysis": {"score": image_score},
            "final_score": final_score,
            "risk_level": risk_level,
            "reason": reason

        }

    except Exception as e:
        print(f"[ERROR] 检测失败: {e}")
        return {
            "url_analysis": {"score": 0.0},
            "text_analysis": {"score": 0.0},
            "image_analysis": {"score": 0.0},
            "final_score": 0.0,
            "risk_level": "unknown",
            "reason": f"检测过程发生错误: {str(e)}"
        }