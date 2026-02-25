from backend.utils.screenshot import capture_screenshot

def extract_image_features(url):
    """
    提取网页截图特征（容错版本）
    即使截图失败，也不会影响整体系统
    """
    try:
        image_base64 = capture_screenshot(url)

        if image_base64 is None:
            print("[WARN] 截图返回 None，使用空图像")
            return {"image_base64": None}

        return {"image_base64": image_base64}

    except Exception as e:
        print(f"[ERROR] 图像特征提取失败: {e}")
        return {"image_base64": None}