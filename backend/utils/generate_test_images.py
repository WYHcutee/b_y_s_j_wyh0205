"""
生成测试图片样本
使用PIL生成简单的测试图片
"""
import os
import base64
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("警告: PIL未安装，将使用纯色图片")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "test_data", "screenshots")

def create_sample_image(text, color, width=800, height=600):
    """创建示例图片"""
    if PIL_AVAILABLE:
        img = Image.new('RGB', (width, height), color=color)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        lines = text.split('\n')
        y_offset = height // 3
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw.text((x, y_offset), line, fill='white', font=font)
            y_offset += 50
        
        return img
    else:
        img = Image.new('RGB', (width, height), color=color)
        return img

def image_to_base64(img):
    """将图片转换为base64"""
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

def main():
    os.makedirs(os.path.join(SCREENSHOTS_DIR, "normal"), exist_ok=True)
    os.makedirs(os.path.join(SCREENSHOTS_DIR, "malicious"), exist_ok=True)
    
    print("=" * 50)
    print("生成测试图片样本")
    print("=" * 50)
    
    normal_samples = [
        {
            "id": "img_normal_baidu",
            "name": "百度搜索",
            "text": "百度搜索\nwww.baidu.com\n\n[ 搜索框 ]\n\n正常搜索引擎网站",
            "color": "#2932E1"
        },
        {
            "id": "img_normal_taobao",
            "name": "淘宝电商",
            "text": "淘宝网\nwww.taobao.com\n\n[ 商品展示 ]\n\n正常电商平台",
            "color": "#FF5000"
        },
        {
            "id": "img_normal_github",
            "name": "GitHub",
            "text": "GitHub\nwww.github.com\n\n[ 代码仓库 ]\n\n正常开发者平台",
            "color": "#24292E"
        },
        {
            "id": "img_normal_bilibili",
            "name": "B站",
            "text": "哔哩哔哩\nwww.bilibili.com\n\n[ 视频内容 ]\n\n正常视频网站",
            "color": "#00A1D6"
        },
    ]
    
    malicious_samples = [
        {
            "id": "img_malicious_phishing_bank",
            "name": "钓鱼银行网站",
            "text": "⚠️ 安全警告 ⚠️\n\n【XX银行】紧急通知\n您的账户存在异常！\n\n[ 账号: ______ ]\n[ 密码: ______ ]\n\n[ 立即验证 ]\n\n可疑特征: 模仿银行登录",
            "color": "#8B0000"
        },
        {
            "id": "img_malicious_prize",
            "name": "中奖诈骗网站",
            "text": "⚠️ 诈骗警告 ⚠️\n\n恭喜您中奖了！\niPhone 15 Pro Max\n\n[ 输入身份证 ]\n[ 输入银行卡 ]\n\n[ 立即领取 ]\n\n可疑特征: 虚假中奖",
            "color": "#FF4500"
        },
        {
            "id": "img_malicious_fake_login",
            "name": "仿冒登录页面",
            "text": "⚠️ 钓鱼警告 ⚠️\n\n支付宝安全中心\npaypa1-secure.com\n\n[ 账号: ______ ]\n[ 密码: ______ ]\n\n[ 登录 ]\n\n可疑特征: 域名仿冒",
            "color": "#4A0080"
        },
        {
            "id": "img_malicious_virus_warning",
            "name": "恐吓式诈骗",
            "text": "⚠️ 恐吓警告 ⚠️\n\n您的电脑已感染病毒！\n所有数据将被删除！\n\n[ 拨打客服电话 ]\n[ 下载安全软件 ]\n\n可疑特征: 恐吓诱导",
            "color": "#DC143C"
        },
    ]
    
    results = {"normal": [], "malicious": []}
    
    print("\n[1/2] 生成正常网站样本...")
    for sample in normal_samples:
        img = create_sample_image(sample["text"], sample["color"])
        save_path = os.path.join(SCREENSHOTS_DIR, "normal", f"{sample['id']}.png")
        img.save(save_path)
        
        base64_data = image_to_base64(img)
        
        results["normal"].append({
            "id": sample["id"],
            "name": sample["name"],
            "description": f"正常网站: {sample['name']}",
            "expected": "safe",
            "screenshot_path": save_path,
            "base64": base64_data
        })
        print(f"  ✓ {sample['name']}")
    
    print("\n[2/2] 生成恶意网站样本...")
    for sample in malicious_samples:
        img = create_sample_image(sample["text"], sample["color"])
        save_path = os.path.join(SCREENSHOTS_DIR, "malicious", f"{sample['id']}.png")
        img.save(save_path)
        
        base64_data = image_to_base64(img)
        
        results["malicious"].append({
            "id": sample["id"],
            "name": sample["name"],
            "description": f"恶意网站: {sample['name']}",
            "expected": "malicious",
            "screenshot_path": save_path,
            "base64": base64_data
        })
        print(f"  ✓ {sample['name']}")
    
    import json
    results_file = os.path.join(SCREENSHOTS_DIR, "image_test_data.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 50)
    print("生成完成！")
    print(f"正常网站样本: {len(results['normal'])} 个")
    print(f"恶意网站样本: {len(results['malicious'])} 个")
    print(f"保存位置: {SCREENSHOTS_DIR}")
    print(f"测试数据: {results_file}")
    print("=" * 50)

if __name__ == "__main__":
    main()
