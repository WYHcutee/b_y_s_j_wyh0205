import requests
import base64
import os
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def call_multimodal_model(prompt, image_base64):
    """
    调用智谱 AI (BigModel) 的多模态大模型 API
    官方文档: https://open.bigmodel.cn/dev/api#glm-4v
    """
    # 1. 从环境变量获取 API Key (强烈推荐！)
    #    在运行 Flask 的终端中先执行: set ZHIPU_API_KEY=你的密钥
    api_key = os.environ.get("ZHIPU_API_KEY")

    # 临时测试：如果没设置环境变量，可以暂时直接写在这里（但千万别提交到 GitHub！）
    if not api_key:
         api_key = "31610ff110fd48ac96d6dd4f2e149270.sAeQ4Hi98p58SLMH"  # 替换成你的真实密钥

    if not api_key:
        logger.error("未找到 ZHIPU_API_KEY 环境变量")
        return mock_response()

    # 2. 智谱 AI 多模态模型的 API 地址 (固定不变)
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

    # 3. 构造请求头 (关键！必须是 Bearer Token)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # 4. 构造消息内容 (多模态：文本 + 图像)
    #    注意：智谱的消息格式中，图像需要是 base64 编码的字符串，并标明格式
    content = [
        {
            "type": "text",
            "text": prompt
        }
    ]

    # 如果传入了图片，则添加图片内容
    if image_base64:
        # 确保 base64 字符串没有 data:image 前缀，如果有则提取后半部分
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]

        content.append({
            "type": "image_url",
            "image_url": {
                # 智谱支持直接传递 base64 格式的图片
                "url": f"data:image/jpeg;base64,{image_base64}"
            }
        })

    # 5. 构造完整的请求 payload
    payload = {
        "model": "glm-4v-flash",  # 使用支持图像理解的模型，也可以用 glm-4v
        "messages": [
            {
                "role": "user",
                "content": content
            }
        ],
        "temperature": 0.1,  # 降低随机性，让输出更稳定
        "max_tokens": 1024,
        "top_p": 0.9
    }

    logger.info(f"正在调用智谱 API，图片大小: {len(image_base64 or '')} 字符")

    try:
        # 6. 发送 POST 请求
        response = requests.post(url, headers=headers, json=payload, timeout=30)

        # 7. 打印响应状态码和原始内容（用于调试）
        logger.info(f"API 响应状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            logger.info(f"API 调用成功，响应: {result}")

            # 8. 从智谱的响应格式中提取模型生成的文本
            # 智谱返回格式: { "choices": [ { "message": { "content": "..." } } ] }
            if result.get("choices") and len(result["choices"]) > 0:
                model_text = result["choices"][0]["message"]["content"]

                # 返回与之前 parse_model_output 兼容的格式
                return {
                    "choices": [{
                        "message": {"content": model_text}
                    }]
                }
            else:
                logger.error(f"API 返回格式异常: {result}")
                return mock_response()
        else:
            # 9. 处理错误响应（智谱的错误信息通常在 response.text 中）
            error_detail = response.text
            logger.error(f"API 调用失败，状态码: {response.status_code}, 详情: {error_detail}")

            # 尝试解析错误 JSON
            try:
                error_json = response.json()
                logger.error(f"错误详情: {error_json}")
            except:
                pass

            return mock_response()

    except Exception as e:
        logger.error(f"API 请求发生异常: {str(e)}")
        return mock_response()


def mock_response():
    """API调用失败或超时时的备用返回"""
    logger.warning("使用 MOCK 数据返回")
    return {
        "choices": [{
            "message": {"content": "URL风险: 50, 文本风险: 50, 图像风险: 50"}
        }]
    }


# 可选：如果你还需要一个函数来测试 API Key 是否有效
def test_api_key(api_key):
    """用最简单的文本请求测试 API Key 有效性"""
    test_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "glm-4-flash",  # 使用免费的快速模型测试
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    try:
        r = requests.post(test_url, headers=headers, json=payload, timeout=10)
        return r.status_code == 200
    except:
        return False