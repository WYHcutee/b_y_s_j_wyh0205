import requests
import base64
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def call_multimodal_model(prompt, image_base64, model_name="glm-4v-flash"):
    """
    根据模型名称分发到不同的 API 调用函数
    """
    if model_name.startswith("glm"):
        return call_zhipu_api(prompt, image_base64, model_name)
    elif model_name == "ernie-bot":
        return call_ernie_api(prompt, image_base64)
    elif model_name == "qwen-vl-plus":
        return call_qwen_api(prompt, image_base64)
    elif model_name == "step-1v":
        return call_step_api(prompt, image_base64)
    elif model_name == "deepseek-vl":  # 新增 DeepSeek 分支
        return call_deepseek_api(prompt, image_base64)
    else:
        logger.warning(f"未知模型 {model_name}，使用默认智谱")
        return call_zhipu_api(prompt, image_base64, "glm-4v-flash")

def call_zhipu_api(prompt, image_base64, model_name="glm-4v-flash"):
    """
    调用智谱 API
    """
    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        logger.error("未找到 ZHIPU_API_KEY 环境变量")
        return mock_response("智谱API密钥未配置")

    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    content = [{"type": "text", "text": prompt}]
    if image_base64:
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 1024,
        "top_p": 0.9
    }

    logger.info(f"正在调用智谱 API，图片大小: {len(image_base64 or '')} 字符")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        logger.info(f"API 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logger.info(f"API 调用成功")
            model_text = result["choices"][0]["message"]["content"]
            return {"choices": [{"message": {"content": model_text}}]}
        elif response.status_code == 400:
            error_data = response.json()
            if error_data.get("error", {}).get("code") == "1301":
                logger.error("内容安全策略拦截了本次请求")
                return {
                    "choices": [{
                        "message": {"content": "SECURITY_BLOCK: 系统检测到输入内容可能包含不安全或敏感信息，无法进行分析。"}
                    }]
                }
            else:
                logger.error(f"API 调用失败，状态码: 400, 详情: {response.text}")
                return mock_response("智谱API请求错误")
        else:
            logger.error(f"API 调用失败，状态码: {response.status_code}, 详情: {response.text}")
            return mock_response("智谱API请求失败")
    except Exception as e:
        logger.error(f"API 请求异常: {e}")
        return mock_response("智谱API调用异常")

def call_ernie_api(prompt, image_base64):
    """
    文心一言 API 调用（待实现）
    """
    logger.warning("文心一言 API 尚未实现，返回 mock 数据")
    return mock_response("文心一言模型暂未接入，请使用其他模型")

def call_qwen_api(prompt, image_base64):
    """
    通义千问 API 调用（待实现）
    """
    logger.warning("通义千问 API 尚未实现，返回 mock 数据")
    return mock_response("通义千问模型暂未接入，请使用其他模型")

def call_step_api(prompt, image_base64):
    """
    阶跃星辰 API 调用（待实现）
    """
    logger.warning("阶跃星辰 API 尚未实现，返回 mock 数据")
    return mock_response("阶跃星辰模型暂未接入，请使用其他模型")

def call_deepseek_api(prompt, image_base64):
    """
    DeepSeek 多模态 API 调用（待实现）
    """
    logger.warning("DeepSeek API 尚未实现，返回 mock 数据")
    # 这里应替换为真实的 DeepSeek API 调用代码
    return mock_response("DeepSeek 模型暂未接入，请使用其他模型")

def mock_response(custom_message=None):
    """通用 mock 返回"""
    msg = custom_message if custom_message else "模型未返回有效结果"
    logger.warning(f"使用 MOCK 数据返回: {msg}")
    return {
        "choices": [{
            "message": {"content": f"URL_Score: 50\nText_Score: 50\nImage_Score: 50\nReason: {msg}"}
        }]
    }