# backend/fusion/model_inference.py
import requests
import random
import time

# ==========================
# 🔥 模式切换
# mock  → 本地模拟模型
# api   → 调用 DeepSeek
# ==========================
MODEL_MODE = "mock"   # 改成 "api" 即可调用真实模型

# DeepSeek API 配置（仅 api 模式使用）
API_KEY = "sk-你的真实key"
API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL_NAME = "deepseek-chat"


def call_multimodal_model(prompt, image_base64=None):
    """
    多模态模型统一入口
    """

    # ==========================
    # 🟢 MOCK 模式（开发阶段）
    # ==========================
    if MODEL_MODE == "mock":
        print("[INFO] 当前为 MOCK 模式，不调用真实模型")

        # 模拟延迟
        time.sleep(1)

        # 生成随机分数（更真实一点）
        url_score = round(random.uniform(0.2, 0.9), 2)
        text_score = round(random.uniform(0.2, 0.9), 2)
        image_score = round(random.uniform(0.2, 0.9), 2)

        fake_content = f"url:{url_score},text:{text_score},image:{image_score}"

        return {
            "choices": [
                {
                    "message": {
                        "content": fake_content
                    }
                }
            ]
        }

    # ==========================
    # 🔵 API 模式（真实调用）
    # ==========================
    elif MODEL_MODE == "api":
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            }

            if image_base64:
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ]
            else:
                messages = [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]

            data = {
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.2
            }

            response = requests.post(
                API_URL,
                headers=headers,
                json=data,
                timeout=60
            )

            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"[ERROR] 模型调用失败: {e}")

            return {
                "choices": [
                    {"message": {"content": "url:0.0,text:0.0,image:0.0"}}
                ]
            }

    else:
        raise ValueError("MODEL_MODE 必须为 'mock' 或 'api'")