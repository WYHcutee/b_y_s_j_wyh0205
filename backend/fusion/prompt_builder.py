def build_multimodal_prompt(url_features, text_content):

    prompt = f"""
你是一名网络安全专家。

请从三个维度分别评估网站风险：

1. URL结构风险（0-100）
2. 网页文本语义风险（0-100）
3. 页面视觉风险（0-100）

网站信息如下：

【URL特征】
{url_features}

【网页文本内容】
{text_content[:1500]}

请严格按照如下格式输出：

URL_Score: xx
Text_Score: xx
Image_Score: xx
Reason: 简要说明判断依据
"""

    return prompt