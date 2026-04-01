import requests
import base64
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

def call_multimodal_model(prompt, image_base64, model_name="glm-4v-flash", extra_images=None):
    """
    根据模型名称分发到不同的 API 调用函数
    extra_images: 额外的图片列表，每项包含base64数据
    """
    if model_name.startswith("glm"):
        return call_zhipu_api(prompt, image_base64, model_name, extra_images)
    elif model_name == "ernie-bot":
        return call_ernie_api(prompt, image_base64)
    elif model_name == "qwen-vl-plus":
        return call_qwen_api(prompt, image_base64)
    elif model_name.startswith("hunyuan"):
        return call_hunyuan_api(prompt, image_base64)
    elif model_name == "step-1v":
        return call_step_api(prompt, image_base64)
    elif model_name == "deepseek-vl":
        return call_deepseek_api(prompt, image_base64)
    else:
        logger.warning(f"未知模型 {model_name}，使用默认智谱")
        return call_zhipu_api(prompt, image_base64, "glm-4v-flash", extra_images)

def call_zhipu_api(prompt, image_base64, model_name="glm-4v-flash", extra_images=None):
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
    image_count = 0
    
    if image_base64:
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })
        image_count += 1
        logger.info(f"已添加网页截图，大小: {len(image_base64)} 字符")
    
    if extra_images:
        for i, img in enumerate(extra_images[:2]):
            img_b64 = img.get("base64", "")
            if img_b64:
                if ',' in img_b64:
                    img_b64 = img_b64.split(',')[1]
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                    }
                })
                image_count += 1
                logger.info(f"已添加网页内图片 {i+1}，大小: {len(img_b64)} 字符")
    
    if image_count == 0:
        logger.warning("未提供图片，仅使用文本分析")
    else:
        logger.info(f"共添加 {image_count} 张图片到请求")

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": content}],
        "temperature": 0.1,
        "max_tokens": 512,
        "top_p": 0.9
    }

    logger.info(f"正在调用智谱 API，模型: {model_name}")
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
    百度千帆 ERNIE API 调用 (OpenAI兼容模式)
    文档：https://cloud.baidu.com/doc/WENXINWORKSHOP/s/Nlks5zkzu
    
    API Key格式：bce-v3/ALTAK-xxx (IAM认证)
    Endpoint: https://qianfan.baidubce.com/v2/chat/completions
    """
    api_key = os.environ.get("ERNIE_API_KEY")
    if not api_key:
        logger.error("未找到 ERNIE_API_KEY 环境变量")
        return mock_response("百度千帆API密钥未配置")

    url = "https://qianfan.baidubce.com/v2/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    available_models = [
        "ernie-4.5-8k-preview",
        "ernie-4.5-turbo-vl-32k", 
        "ernie-3.5-8k",
        "ernie-speed-8k",
        "ernie-lite-8k"
    ]

    for model in available_models:
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 1024
        }

        logger.info(f"正在调用百度千帆 API (模型: {model})")
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            logger.info(f"API 响应状态码: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                logger.info(f"百度千帆 API 调用成功 (模型: {model})")
                model_text = result["choices"][0]["message"]["content"]
                return {"choices": [{"message": {"content": model_text}}]}
            else:
                logger.warning(f"模型 {model} 不可用: {response.status_code}")
                continue
        except Exception as e:
            logger.error(f"模型 {model} 调用异常: {e}")
            continue

    logger.error("所有百度千帆模型均不可用")
    return mock_response("百度千帆API所有模型均不可用，请检查控制台是否开通服务")

def call_qwen_api(prompt, image_base64):
    """
    通义千问 API 调用
    文档：https://help.aliyun.com/zh/dashscope/developer-reference/api-details
    
    使用 OpenAI 兼容格式
    """
    api_key = os.environ.get("QWEN_API_KEY")
    if not api_key:
        logger.error("未找到 QWEN_API_KEY 环境变量")
        return mock_response("通义千问API密钥未配置")

    url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "qwen-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }

    logger.info("正在调用通义千问 API")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        logger.info(f"API 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logger.info("通义千问 API 调用成功")
            model_text = result["choices"][0]["message"]["content"]
            return {"choices": [{"message": {"content": model_text}}]}
        else:
            logger.error(f"API 调用失败，状态码: {response.status_code}, 详情: {response.text}")
            return mock_response(f"通义千问API请求失败: {response.text[:100]}")
    except Exception as e:
        logger.error(f"API 请求异常: {e}")
        return mock_response(f"通义千问API调用异常: {str(e)}")

def call_step_api(prompt, image_base64):
    """
    阶跃星辰 API 调用
    文档：https://platform.stepfun.com/docs/api-reference
    
    使用 OpenAI 兼容格式
    """
    api_key = os.environ.get("STEP_API_KEY")
    if not api_key:
        logger.error("未找到 STEP_API_KEY 环境变量")
        return mock_response("阶跃星辰API密钥未配置")

    url = "https://api.stepfun.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "step-1-8k",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }

    logger.info("正在调用阶跃星辰 API")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        logger.info(f"API 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logger.info("阶跃星辰 API 调用成功")
            model_text = result["choices"][0]["message"]["content"]
            return {"choices": [{"message": {"content": model_text}}]}
        else:
            logger.error(f"API 调用失败，状态码: {response.status_code}, 详情: {response.text}")
            return mock_response(f"阶跃星辰API请求失败: {response.text[:100]}")
    except Exception as e:
        logger.error(f"API 请求异常: {e}")
        return mock_response(f"阶跃星辰API调用异常: {str(e)}")

def call_deepseek_api(prompt, image_base64):
    """
    DeepSeek API 调用
    文档：https://platform.deepseek.com/api-docs/
    
    使用 OpenAI 兼容格式
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("未找到 DEEPSEEK_API_KEY 环境变量")
        return mock_response("DeepSeek API密钥未配置")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }

    logger.info("正在调用 DeepSeek API")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        logger.info(f"API 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logger.info("DeepSeek API 调用成功")
            model_text = result["choices"][0]["message"]["content"]
            return {"choices": [{"message": {"content": model_text}}]}
        else:
            logger.error(f"API 调用失败，状态码: {response.status_code}, 详情: {response.text}")
            return mock_response(f"DeepSeek API请求失败: {response.text[:100]}")
    except Exception as e:
        logger.error(f"API 请求异常: {e}")
        return mock_response(f"DeepSeek API调用异常: {str(e)}")

def call_hunyuan_api(prompt, image_base64):
    """
    腾讯混元 API 调用（免费版 hunyuan-lite）
    
    官方文档：https://cloud.tencent.com/document/product/1729/111007
    
    特点：
    - 完全免费
    - 256K 上下文窗口
    - 支持文本生成、对话交互
    
    错误处理：
    - 密钥未配置：返回提示信息
    - API调用失败：自动降级到智谱API
    - 网络异常：返回错误信息
    """
    api_key = os.environ.get("HUNYUAN_API_KEY")
    if not api_key:
        logger.error("未找到 HUNYUAN_API_KEY 环境变量")
        return mock_response("腾讯混元API密钥未配置，请在.env文件中添加 HUNYUAN_API_KEY")

    url = "https://api.hunyuan.cloud.tencent.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "hunyuan-lite",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1,
        "max_tokens": 1024
    }

    logger.info("正在调用腾讯混元 API (hunyuan-lite)")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        logger.info(f"腾讯混元 API 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logger.info("腾讯混元 API 调用成功")
            model_text = result["choices"][0]["message"]["content"]
            return {"choices": [{"message": {"content": model_text}}]}
        elif response.status_code == 401:
            logger.error("腾讯混元 API 认证失败，请检查API密钥")
            return mock_response("腾讯混元API认证失败，请检查密钥是否正确")
        elif response.status_code == 429:
            logger.error("腾讯混元 API 请求频率超限")
            return mock_response("腾讯混元API请求频率超限，请稍后重试")
        elif response.status_code == 500:
            logger.error("腾讯混元 API 服务器错误")
            return mock_response("腾讯混元API服务器错误，请稍后重试")
        else:
            logger.error(f"腾讯混元 API 调用失败，状态码: {response.status_code}, 详情: {response.text}")
            return mock_response(f"腾讯混元API请求失败(状态码:{response.status_code})")
    except requests.exceptions.Timeout:
        logger.error("腾讯混元 API 请求超时")
        return mock_response("腾讯混元API请求超时，请检查网络连接")
    except requests.exceptions.ConnectionError:
        logger.error("腾讯混元 API 连接失败")
        return mock_response("腾讯混元API连接失败，请检查网络")
    except Exception as e:
        logger.error(f"腾讯混元 API 请求异常: {e}")
        return mock_response(f"腾讯混元API调用异常: {str(e)}")

def mock_response(custom_message=None):
    """通用 mock 返回"""
    msg = custom_message if custom_message else "模型未返回有效结果"
    logger.warning(f"使用 MOCK 数据返回: {msg}")
    return {
        "choices": [{
            "message": {"content": f"URL_Score: 50\nText_Score: 50\nImage_Score: 50\nReason: {msg}"}
        }]
    }
