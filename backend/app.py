from flask import Flask, request, jsonify
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
    app.run(debug=True)