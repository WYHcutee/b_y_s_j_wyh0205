from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from backend.services.detect_service import detect_website
import datetime
import os
import glob

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")
CORS(app)

KNOWLEDGE_BASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "knowledge_base")

def get_rag_engine():
    from backend.fusion.rag_engine import get_rag_engine as _get_rag_engine
    return _get_rag_engine()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/rag")
def rag_manager():
    return render_template("rag_manager.html")

@app.route("/rag/add", methods=["POST"])
def add_knowledge():
    try:
        data = request.json
        source = data.get("source", "手动添加")
        content = data.get("content", "")
        
        if not content:
            return jsonify({"success": False, "error": "内容不能为空"})
        
        rag_engine = get_rag_engine()
        result = rag_engine.add_document(content, {"source": source, "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        
        return jsonify({"success": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/rag/add-url", methods=["POST"])
def add_knowledge_from_url():
    try:
        data = request.json
        url = data.get("url", "")
        
        if not url:
            return jsonify({"success": False, "error": "URL不能为空"})
        
        rag_engine = get_rag_engine()
        result = rag_engine.add_url(url)
        
        return jsonify({"success": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/rag/list")
def list_knowledge():
    try:
        documents_path = os.path.join(KNOWLEDGE_BASE_PATH, "documents")
        items = []
        
        if os.path.exists(documents_path):
            for file_path in glob.glob(os.path.join(documents_path, "*.txt")):
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                items.append({
                    "name": file_name,
                    "size": file_size,
                    "path": file_path
                })
        
        return jsonify({
            "items": items,
            "knowledge_base_path": KNOWLEDGE_BASE_PATH,
            "message": f"知识库路径: {KNOWLEDGE_BASE_PATH}"
        })
    except Exception as e:
        return jsonify({"items": [], "error": str(e)})

@app.route("/rag/init", methods=["POST"])
def init_knowledge_base():
    try:
        rag_engine = get_rag_engine()
        documents_path = os.path.join(KNOWLEDGE_BASE_PATH, "documents")
        loaded_count = 0
        
        if os.path.exists(documents_path):
            for file_path in glob.glob(os.path.join(documents_path, "*.txt")):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if content.strip():
                        rag_engine.add_document(content, {
                            "source": os.path.basename(file_path),
                            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        loaded_count += 1
                except Exception as e:
                    print(f"加载文档失败 {file_path}: {e}")
        
        return jsonify({
            "success": True,
            "loaded_count": loaded_count,
            "message": f"成功加载 {loaded_count} 个文档到知识库"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/rag/retrieve", methods=["POST"])
def retrieve_knowledge():
    try:
        data = request.json
        query = data.get("query", "")
        
        if not query:
            return jsonify({"knowledge": ""})
        
        rag_engine = get_rag_engine()
        knowledge = rag_engine.get_relevant_knowledge(query)
        
        return jsonify({"knowledge": knowledge})
    except Exception as e:
        return jsonify({"knowledge": "", "error": str(e)})

@app.route("/rag/delete", methods=["POST"])
def delete_knowledge():
    try:
        data = request.json
        filename = data.get("filename", "")
        
        if not filename:
            return jsonify({"success": False, "error": "文件名不能为空"})
        
        rag_engine = get_rag_engine()
        result = rag_engine.delete_document(filename)
        
        return jsonify({"success": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/rag/update", methods=["POST"])
def update_knowledge():
    try:
        data = request.json
        filename = data.get("filename", "")
        content = data.get("content", "")
        
        if not filename:
            return jsonify({"success": False, "error": "文件名不能为空"})
        if not content:
            return jsonify({"success": False, "error": "内容不能为空"})
        
        rag_engine = get_rag_engine()
        result = rag_engine.update_document(filename, content)
        
        return jsonify({"success": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/rag/get/<filename>")
def get_knowledge_file(filename):
    try:
        rag_engine = get_rag_engine()
        result = rag_engine.get_document(filename)
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/rag/documents")
def list_all_documents():
    try:
        rag_engine = get_rag_engine()
        documents = rag_engine.list_documents()
        return jsonify({"success": True, "documents": documents})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/rag/status")
def rag_status():
    try:
        from backend.fusion.rag_engine import get_rag_status
        status = get_rag_status()
        return jsonify({"success": True, "status": status})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/detect", methods=["POST"])
def detect():
    data = request.json
    input_type = data.get("input_type", "url")
    model_name = data.get("model", "glm-4v-flash")
    
    print(f"[检测] input_type: {input_type}, model: {model_name}")
    
    if input_type == "url":
        url = data.get("url")
        print(f"[检测] URL: {url}")
        if not url:
            return jsonify({"error": "URL不能为空"}), 400
        result = detect_website(input_type=input_type, url=url, model_name=model_name)
    elif input_type == "text":
        text_content = data.get("text_content") or data.get("text")
        image_base64 = data.get("image_base64") or data.get("image")
        print(f"[检测] 文本长度: {len(text_content) if text_content else 0}")
        print(f"[检测] 图片: {'有(' + str(len(image_base64)) + '字符)' if image_base64 else '无'}")
        if not text_content:
            return jsonify({"error": "文本内容不能为空"}), 400
        result = detect_website(input_type=input_type, text_content=text_content, image_base64=image_base64, model_name=model_name)
    elif input_type == "image":
        image_base64 = data.get("image_base64") or data.get("image")
        if not image_base64:
            return jsonify({"error": "图片不能为空"}), 400
        result = detect_website(input_type=input_type, image_base64=image_base64, model_name=model_name)
    else:
        return jsonify({"error": "不支持的输入类型"}), 400

    return jsonify(result)

@app.route("/batch_detect", methods=["POST"])
def batch_detect():
    """
    批量URL检测
    """
    try:
        data = request.json
        urls = data.get("urls", [])
        model_name = data.get("model", "glm-4v-flash")
        
        if isinstance(urls, str):
            urls = [u.strip() for u in urls.split('\n') if u.strip()]
        
        urls = urls[:10]
        
        if not urls:
            return jsonify({"error": "URL列表不能为空"}), 400
        
        print(f"[批量检测] 收到 {len(urls)} 个URL, 模型: {model_name}")
        
        results = []
        for i, url in enumerate(urls):
            print(f"[批量检测] 处理第 {i+1}/{len(urls)} 个: {url}")
            try:
                result = detect_website(input_type='url', url=url, model_name=model_name)
                result['url'] = url
                result['index'] = i + 1
                results.append(result)
            except Exception as e:
                results.append({
                    'url': url,
                    'index': i + 1,
                    'error': str(e),
                    'final_score': 0,
                    'risk_level': 'Error',
                    'url_analysis': {'score': 0},
                    'text_analysis': {'score': 0},
                    'image_analysis': {'score': 0},
                    'reason': f'检测失败: {str(e)}',
                    'checked_urls': [],
                    'rag_knowledge': ''
                })
        
        return jsonify({
            'success': True,
            'total': len(urls),
            'model': model_name,
            'results': results
        })
    except Exception as e:
        print(f"[批量检测] 错误: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/models", methods=["GET"])
def get_models():
    """
    获取支持的模型列表
    """
    return jsonify({
        "models": [
            {"id": "glm-4v-flash", "name": "智谱 GLM-4V-Flash", "description": "智谱最新多模态模型，速度快"},
            {"id": "glm-4v", "name": "智谱 GLM-4V", "description": "智谱多模态模型，功能全面"},
            {"id": "ernie-bot", "name": "百度千帆", "description": "百度大语言模型"},
            {"id": "qwen-vl-plus", "name": "阿里 通义千问", "description": "阿里多模态模型"},
            {"id": "hunyuan-lite", "name": "腾讯混元", "description": "腾讯混元免费模型，256K上下文"},
            {"id": "step-1v", "name": "阶跃星辰", "description": "阶跃星辰大语言模型"},
            {"id": "deepseek-vl", "name": "DeepSeek", "description": "DeepSeek大语言模型"}
        ]
    })

@app.route("/test")
def test_page():
    return render_template("test.html")

@app.route("/test/dataset", methods=["GET"])
def get_test_dataset():
    from backend.utils.test_dataset import get_test_data
    modality = request.args.get("modality", None)
    return jsonify(get_test_data(modality))

@app.route("/test/run", methods=["POST"])
def run_test():
    import time
    from backend.utils.test_dataset import save_test_result
    from backend.services.detect_service import detect_website
    
    data = request.json
    model_id = data.get("model")
    modality = data.get("modality")
    test_item = data.get("test_item")
    
    if not all([model_id, modality, test_item]):
        return jsonify({"error": "缺少参数"}), 400
    
    start_time = time.time()
    
    try:
        if modality == "url":
            result = detect_website(
                url=test_item["input"],
                model_name=model_id,
                input_type="url"
            )
        elif modality == "text":
            result = detect_website(
                text_content=test_item["input"],
                model_name=model_id,
                input_type="text"
            )
        elif modality == "image":
            is_real_image = test_item.get("is_real_image", False)
            image_input = test_item["input"]
            
            if is_real_image and len(image_input) > 200:
                result = detect_website(
                    image_base64=image_input,
                    model_name=model_id,
                    input_type="image"
                )
            else:
                result = detect_website(
                    text_content=f"请分析以下网站截图描述并判断风险等级：{image_input}",
                    model_name=model_id,
                    input_type="text"
                )
        else:
            return jsonify({"error": "未知模态"}), 400
        
        elapsed_time = time.time() - start_time
        
        final_score = result.get("final_score", 0)
        predicted = "malicious" if final_score >= 40 else "safe"
        expected = test_item.get("expected", "unknown")
        is_correct = predicted == expected
        
        test_result = {
            "model": model_id,
            "modality": modality,
            "test_id": test_item.get("id"),
            "description": test_item.get("description"),
            "input": test_item["input"][:100] + "..." if len(test_item["input"]) > 100 else test_item["input"],
            "expected": expected,
            "predicted": predicted,
            "is_correct": is_correct,
            "final_score": final_score,
            "url_score": result.get("url_analysis", {}).get("score", 0),
            "text_score": result.get("text_analysis", {}).get("score", 0),
            "image_score": result.get("image_analysis", {}).get("score", 0),
            "elapsed_time": round(elapsed_time, 2),
            "reason": result.get("reason", "")[:200]
        }
        
        save_test_result(test_result)
        
        return jsonify({
            "success": True,
            "result": test_result
        })
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        return jsonify({
            "success": False,
            "error": str(e),
            "elapsed_time": round(elapsed_time, 2)
        })

@app.route("/test/results", methods=["GET"])
def get_test_results():
    from backend.utils.test_dataset import get_test_results
    return jsonify(get_test_results())

@app.route("/test/results/clear", methods=["POST"])
def clear_test_results():
    from backend.utils.test_dataset import clear_test_results
    clear_test_results()
    return jsonify({"success": True})

@app.route("/test/analysis", methods=["GET"])
def analyze_test_results():
    from backend.utils.test_dataset import get_test_results, calculate_metrics
    
    results = get_test_results()
    
    if not results:
        return jsonify({
            "models": [],
            "modalities": ["url", "text", "image"],
            "analysis": {}
        })
    
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
            else:
                analysis[model][modality] = {
                    "accuracy": 0, "precision": 0, "recall": 0, "f1": 0,
                    "tp": 0, "tn": 0, "fp": 0, "fn": 0,
                    "total": 0, "avg_score": 0, "avg_time": 0
                }
    
    return jsonify({
        "models": models,
        "modalities": modalities,
        "analysis": analysis,
        "total_tests": len(results)
    })

if __name__ == "__main__":
    app.run(debug=True)