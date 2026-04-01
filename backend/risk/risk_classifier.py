def classify_risk(score):
    """
    风险等级分类（5档）
    
    分数范围说明：
    - 0-20: 安全 - 无明显风险特征
    - 21-40: 低风险 - 存在轻微可疑特征
    - 41-60: 中风险 - 存在一定风险特征，需谨慎
    - 61-80: 高风险 - 存在明显恶意特征，建议远离
    - 81-100: 危险 - 确认为恶意网站，请勿访问
    """
    if score <= 20:
        return "安全"
    elif score <= 40:
        return "低风险"
    elif score <= 60:
        return "中风险"
    elif score <= 80:
        return "高风险"
    else:
        return "危险"