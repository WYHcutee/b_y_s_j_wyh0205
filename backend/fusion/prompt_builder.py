import logging

logger = logging.getLogger(__name__)

def get_relevant_knowledge(query):
    try:
        from backend.fusion.rag_engine import get_relevant_knowledge as rag_get_knowledge
        knowledge = rag_get_knowledge(query)
        if knowledge:
            logger.info(f"RAG检索到相关知识: {len(knowledge)} 字符")
            return knowledge
    except Exception as e:
        logger.warning(f"RAG检索失败: {e}")
    return ""

def build_multimodal_prompt(url_features, text_content, mode='url', page_images=None):
    query = f"{url_features} {text_content[:500]}" if url_features else text_content[:500]
    relevant_knowledge = get_relevant_knowledge(query)
    
    if relevant_knowledge:
        relevant_knowledge = f"\n【相关知识库信息】\n{relevant_knowledge}\n"
    
    page_images_info = ""
    image_count = 1
    if page_images and len(page_images) > 0:
        image_count = 1 + len(page_images[:2])
        img_urls = [img.get("url", "") for img in page_images[:2]]
        if img_urls:
            page_images_info = f"\n【网页内图片】（共{len(img_urls)}张，已作为额外图像输入）\n图片URL：\n" + "\n".join([f"- {url}" for url in img_urls])
    
    if mode == 'url':
        prompt = f"""
你是一个中文网络安全专家，请用中文分析以下网站信息，判断其是否为恶意网站（如钓鱼、诈骗、包含恶意软件等）。

【重要提示】你的所有回复必须使用中文！不要使用英文！

{relevant_knowledge}

【URL结构分析】
{url_features}

【网页文本内容】
{text_content}

【图像输入】（共{image_count}张图片）
- 第1张：网页整体截图
{page_images_info}

请按以下步骤分析：
1. URL风险：分析域名、路径、参数等是否存在可疑特征（如随机字符串、仿冒知名域名、异常端口等），列出具体风险点，并给出分数（0-100，越高越危险）。
2. 文本风险：分析页面文字是否存在诱导、诈骗、敏感信息（如紧急通知、账号密码输入框、虚假中奖等），列出可疑文本片段或关键词，并给出分数。
3. 图像风险：分析网页截图和网页内图片，检查是否模仿知名网站、是否存在异常元素（如伪造的登录框、隐藏的iframe、虚假按钮、可疑logo等），描述可疑区域，并给出分数。

请按以下格式输出，不要有其他解释：
URL_Score: [分数]
Text_Score: [分数]
Image_Score: [分数]
Reason:
- URL风险分析：[用中文详细说明，包括具体特征]
- 文本风险分析：[用中文详细说明，包括可疑内容]
- 图像风险分析：[用中文详细说明，包括网页截图和网页内图片的视觉特征]
- 综合判断：[用中文简短总结]

再次提醒：所有分析内容必须使用中文！
"""
    elif mode == 'text':
        prompt = f"""
你是一个中文网络安全专家，用户只提供了网页文本内容，没有URL和截图。请用中文分析其风险（是否包含钓鱼、诈骗、诱导等）。

【重要提示】你的所有回复必须使用中文！不要使用英文！

{relevant_knowledge}

文本内容：
{text_content}

请按以下格式输出：
URL_Score: 0
Text_Score: [文本风险分数]
Image_Score: 0
Reason:
- 文本风险分析：[用中文详细说明，包括可疑关键词、句子、意图等]
- 综合判断：[用中文简短总结]

再次提醒：所有分析内容必须使用中文！
"""
    elif mode == 'text_with_image':
        prompt = f"""
你是一个中文网络安全专家，用户提供了网页文本内容和网页截图。请用中文综合分析其风险（是否包含钓鱼、诈骗、诱导等）。

【重要提示】你的所有回复必须使用中文！不要使用英文！

{relevant_knowledge}

文本内容：
{text_content}

【网页截图】（已作为图像输入）

请按以下格式输出：
URL_Score: 0
Text_Score: [文本风险分数]
Image_Score: [图像风险分数]
Reason:
- 文本风险分析：[用中文详细说明，包括可疑关键词、句子、意图等]
- 图像风险分析：[用中文详细说明，包括页面布局、元素仿冒、异常区域等]
- 综合判断：[用中文简短总结]

再次提醒：所有分析内容必须使用中文！
"""
    elif mode == 'image':
        prompt = f"""
你是一个中文网络安全专家，用户只提供了网页截图，没有URL和文本。请用中文分析其视觉风险（是否模仿知名网站、是否存在异常元素等）。

【重要提示】你的所有回复必须使用中文！不要使用英文！

{relevant_knowledge}

请按以下格式输出：
URL_Score: 0
Text_Score: 0
Image_Score: [图像风险分数]
Reason:
- 图像风险分析：[用中文详细说明，包括页面布局、元素仿冒、异常区域等]
- 综合判断：[用中文简短总结]

再次提醒：所有分析内容必须使用中文！
"""
    else:
        prompt = ""
    return prompt