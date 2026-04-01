import json
import os
import base64

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST_DATA_PATH = os.path.join(PROJECT_ROOT, "test_data")
SCREENSHOTS_DIR = os.path.join(TEST_DATA_PATH, "screenshots")

test_datasets = {
    "url": [
        {"id": "url_001", "input": "https://www.taobao.com", "expected": "safe", "description": "正规电商网站"},
        {"id": "url_002", "input": "http://login-verify-account.com/secure/login", "expected": "malicious", "description": "钓鱼网站特征URL"},
        {"id": "url_003", "input": "https://www.baidu.com", "expected": "safe", "description": "正规搜索引擎"},
        {"id": "url_004", "input": "http://192.168.1.100/login.php", "expected": "malicious", "description": "IP地址作为域名"},
        {"id": "url_005", "input": "https://www.zjgsu.edu.cn", "expected": "safe", "description": "正规高校网站"},
        {"id": "url_006", "input": "http://paypa1-secure.com/verify", "expected": "malicious", "description": "仿冒PayPal域名(字母l替换为1)"},
        {"id": "url_007", "input": "https://www.jd.com", "expected": "safe", "description": "正规电商网站"},
        {"id": "url_008", "input": "http://free-iphone-winner.xyz/claim", "expected": "malicious", "description": "可疑中奖网站"},
        {"id": "url_009", "input": "https://www.bilibili.com", "expected": "safe", "description": "正规视频网站"},
        {"id": "url_010", "input": "http://amaz0n-account-suspend.com/verify", "expected": "malicious", "description": "仿冒Amazon域名(字母o替换为0)"},
        {"id": "url_011", "input": "https://www.github.com", "expected": "safe", "description": "正规开发者平台"},
        {"id": "url_012", "input": "http://bankofchina.cc-verify.net/login", "expected": "malicious", "description": "仿冒银行域名+可疑子域名"},
        {"id": "url_013", "input": "https://www.zhihu.com", "expected": "safe", "description": "正规问答社区"},
        {"id": "url_014", "input": "http://www.qq.com@evil.com/login", "expected": "malicious", "description": "URL欺骗(@符号后的域名才是真实域名)"},
        {"id": "url_015", "input": "https://www.douban.com", "expected": "safe", "description": "正规社交网站"},
        {"id": "url_016", "input": "http://login-taobao.com.abc.xyz/", "expected": "malicious", "description": "多级子域名伪装正规网站"},
        {"id": "url_017", "input": "https://www.csdn.net", "expected": "safe", "description": "正规技术社区"},
        {"id": "url_018", "input": "http://weixin-pay-verify.com/secure", "expected": "malicious", "description": "伪装微信支付验证"},
        {"id": "url_019", "input": "https://www.sina.com.cn", "expected": "safe", "description": "正规门户网站"},
        {"id": "url_020", "input": "http://alipay-security-center.net/confirm", "expected": "malicious", "description": "伪装支付宝安全中心"}
    ],
    "text": [
        {"id": "text_001", "input": "欢迎访问浙江工商大学教务处网站。我们提供学生服务、教师服务、教务管理等功能。如有问题请联系教务处。", "expected": "safe", "description": "正常教务网站文本"},
        {"id": "text_002", "input": "紧急通知！您的银行账户存在异常，请立即点击链接验证您的身份信息，否则账户将被冻结。请在24小时内完成验证，输入您的银行卡号和密码。", "expected": "malicious", "description": "钓鱼诈骗文本-银行账户异常"},
        {"id": "text_003", "input": "今日新闻：国内经济持续稳定发展，科技创新成果显著。专家表示，数字化转型将为企业带来更多机遇。", "expected": "safe", "description": "正常新闻文本"},
        {"id": "text_004", "input": "恭喜您！您已被选中为幸运用户，获得iPhone 15大奖！请立即点击领取，输入您的身份证号和银行卡号完成验证。机会仅此一次，错过不再！", "expected": "malicious", "description": "中奖诈骗文本"},
        {"id": "text_005", "input": "产品说明书：本产品采用环保材料制作，符合国家质量标准。使用前请仔细阅读说明书，如有问题请联系客服。", "expected": "safe", "description": "正常产品说明"},
        {"id": "text_006", "input": "系统警告：检测到您的电脑存在病毒感染风险！请立即下载我们的安全软件进行扫描，否则您的所有数据将被删除。点击此处立即下载。", "expected": "malicious", "description": "恐吓式诈骗文本"},
        {"id": "text_007", "input": "尊敬的用户，您的快递已到达，请点击链接确认收货地址：http://kd-verify.com/confirm", "expected": "malicious", "description": "快递诈骗文本"},
        {"id": "text_008", "input": "本店营业时间：周一至周五 9:00-18:00，周六周日休息。地址：杭州市西湖区文三路123号。", "expected": "safe", "description": "正常店铺信息"},
        {"id": "text_009", "input": "您的支付宝账户存在安全风险，请立即登录 http://alipay-secure-verify.com 进行身份验证，否则账户将被永久冻结！", "expected": "malicious", "description": "支付宝诈骗文本"},
        {"id": "text_010", "input": "会议通知：本周五下午2点在会议室召开部门例会，请各位同事准时参加。", "expected": "safe", "description": "正常会议通知"},
        {"id": "text_011", "input": "【税务局通知】您有一笔退税待领取，请点击链接填写银行卡信息：http://tax-refund-gov.com", "expected": "malicious", "description": "退税诈骗文本"},
        {"id": "text_012", "input": "招聘启事：本公司诚聘软件开发工程师，要求本科及以上学历，熟悉Python/Java开发。", "expected": "safe", "description": "正常招聘信息"}
    ],
    "image": [
        {"id": "img_001", "input": "正常网站截图：显示正规电商网站首页，有清晰的导航栏、商品展示、官方logo，页面布局专业", "expected": "safe", "description": "正常电商网站截图"},
        {"id": "img_002", "input": "钓鱼网站截图：模仿银行登录页面，要求输入账号密码，有紧急提示信息，页面设计粗糙", "expected": "malicious", "description": "钓鱼网站截图-银行登录"},
        {"id": "img_003", "input": "正常网站截图：高校官网首页，有学校logo、导航菜单、新闻公告，页面设计规范", "expected": "safe", "description": "正常高校网站截图"},
        {"id": "img_004", "input": "诈骗网站截图：显示中奖弹窗，要求输入个人信息，有倒计时催促，背景模糊", "expected": "malicious", "description": "中奖诈骗网站截图"},
        {"id": "img_005", "input": "正常网站截图：政府门户网站，有国徽标志、政务公开栏目、领导信息，页面庄重", "expected": "safe", "description": "正常政府网站截图"},
        {"id": "img_006", "input": "钓鱼网站截图：模仿支付宝登录页面，URL显示为可疑域名，要求输入账号密码和支付密码", "expected": "malicious", "description": "钓鱼网站截图-仿支付宝"},
        {"id": "img_007", "input": "正常网站截图：知名企业官网，有企业logo、产品介绍、联系方式，页面设计精美", "expected": "safe", "description": "正常企业网站截图"},
        {"id": "img_008", "input": "诈骗网站截图：显示系统警告弹窗，声称电脑中毒，要求拨打客服电话或下载软件", "expected": "malicious", "description": "恐吓式诈骗网站截图"},
        {"id": "img_009", "input": "正常网站截图：新闻媒体网站，有新闻标题、图片新闻、评论功能，页面布局清晰", "expected": "safe", "description": "正常新闻网站截图"},
        {"id": "img_010", "input": "钓鱼网站截图：模仿微信登录页面，要求扫描二维码或输入账号密码，域名可疑", "expected": "malicious", "description": "钓鱼网站截图-仿微信"}
    ]
}

def get_real_image_test_data():
    """获取真实图片测试数据"""
    image_data_file = os.path.join(SCREENSHOTS_DIR, "image_test_data.json")
    
    if not os.path.exists(image_data_file):
        return []
    
    try:
        with open(image_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        real_images = []
        
        for item in data.get("normal", []):
            real_images.append({
                "id": item["id"],
                "input": item.get("base64", ""),
                "expected": "safe",
                "description": item.get("description", ""),
                "is_real_image": True
            })
        
        for item in data.get("malicious", []):
            real_images.append({
                "id": item["id"],
                "input": item.get("base64", ""),
                "expected": "malicious",
                "description": item.get("description", ""),
                "is_real_image": True
            })
        
        return real_images
    except Exception as e:
        print(f"加载真实图片数据失败: {e}")
        return []

def get_test_data(modality=None):
    if modality == "image":
        real_images = get_real_image_test_data()
        if real_images:
            return real_images
        return test_datasets.get("image", [])
    if modality:
        return test_datasets.get(modality, [])
    return test_datasets

def save_test_result(result):
    results_path = os.path.join(TEST_DATA_PATH, "test_results.json")
    os.makedirs(TEST_DATA_PATH, exist_ok=True)
    
    results = []
    if os.path.exists(results_path):
        try:
            with open(results_path, 'r', encoding='utf-8') as f:
                results = json.load(f)
        except:
            results = []
    
    results.append(result)
    
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results_path

def get_test_results():
    results_path = os.path.join(TEST_DATA_PATH, "test_results.json")
    if os.path.exists(results_path):
        try:
            with open(results_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def clear_test_results():
    results_path = os.path.join(TEST_DATA_PATH, "test_results.json")
    if os.path.exists(results_path):
        os.remove(results_path)
    return True

def calculate_metrics(results):
    """
    计算分类评估指标
    
    Args:
        results: 测试结果列表，每个结果包含 expected 和 predicted 字段
    
    Returns:
        dict: 包含 accuracy, precision, recall, f1, tp, tn, fp, fn
    """
    tp = 0  
    tn = 0  
    fp = 0  
    fn = 0  
    
    for r in results:
        expected = r.get("expected", "safe").lower()
        predicted = r.get("predicted", "safe").lower()
        
        if expected == "malicious" and predicted == "malicious":
            tp += 1
        elif expected == "safe" and predicted == "safe":
            tn += 1
        elif expected == "safe" and predicted == "malicious":
            fp += 1
        elif expected == "malicious" and predicted == "safe":
            fn += 1
    
    total = tp + tn + fp + fn
    if total == 0:
        return {
            "accuracy": 0, "precision": 0, "recall": 0, "f1": 0,
            "tp": 0, "tn": 0, "fp": 0, "fn": 0
        }
    
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    return {
        "accuracy": round(accuracy * 100, 2),
        "precision": round(precision * 100, 2),
        "recall": round(recall * 100, 2),
        "f1": round(f1 * 100, 2),
        "tp": tp, "tn": tn, "fp": fp, "fn": fn
    }

def get_detailed_analysis():
    """
    获取详细的评估分析报告
    
    Returns:
        dict: 包含每个模型在每个模态上的详细指标
    """
    results = get_test_results()
    
    if not results:
        return {"models": [], "analysis": {}}
    
    models = list(set(r["model"] for r in results))
    modalities = ["url", "text", "image"]
    
    analysis = {}
    for model in models:
        analysis[model] = {}
        for modality in modalities:
            model_modality_results = [
                r for r in results 
                if r["model"] == model and r["modality"] == modality
            ]
            
            if model_modality_results:
                metrics = calculate_metrics(model_modality_results)
                avg_score = sum(r.get("final_score", 0) for r in model_modality_results) / len(model_modality_results)
                avg_time = sum(r.get("elapsed_time", 0) for r in model_modality_results) / len(model_modality_results)
                
                analysis[model][modality] = {
                    **metrics,
                    "total": len(model_modality_results),
                    "avg_score": round(avg_score, 1),
                    "avg_time": round(avg_time, 2)
                }
    
    return {"models": models, "analysis": analysis}
