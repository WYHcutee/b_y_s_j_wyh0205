'''from flask import Flask, request, jsonify
from backend.services.detect_service import detect_website

app = Flask(__name__)

@app.route("/detect", methods=["POST"])
def detect():

    data = request.json
    url = data.get("url")

    if not url:
        return jsonify({"error": "URL不能为空"}), 400

    result = detect_website(url)

    return jsonify(result)

from flask import Flask, render_template

def create_app():
    app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

    @app.route("/")
    def index():
        return render_template("index.html")

    from backend.services.detect_service import detect_website

    @app.route("/detect", methods=["POST"])
    def detect():
        url = request.json.get("url")
        result = detect_website(url)
        return jsonify(result)

    return app


if __name__ == "__main__":
    app.run(debug=True)'''
from flask import Flask, request, jsonify, render_template
from backend.services.detect_service import detect_website

app = Flask(__name__, template_folder="../frontend/templates", static_folder="../frontend/static")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/detect", methods=["POST"])
def detect():
    data = request.json
    input_type = data.get("input_type", "url")
    model_name = data.get("model", "glm-4v-flash")

    if input_type == "url":
        url = data.get("url")
        if not url:
            return jsonify({"error": "URL不能为空"}), 400
        result = detect_website(input_type=input_type, url=url, model_name=model_name)
    elif input_type == "text":
        text_content = data.get("text_content")
        if not text_content:
            return jsonify({"error": "文本内容不能为空"}), 400
        result = detect_website(input_type=input_type, text_content=text_content, model_name=model_name)
    elif input_type == "image":
        image_base64 = data.get("image_base64")
        if not image_base64:
            return jsonify({"error": "图片不能为空"}), 400
        result = detect_website(input_type=input_type, image_base64=image_base64, model_name=model_name)
    else:
        return jsonify({"error": "不支持的输入类型"}), 400

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)