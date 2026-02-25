from flask import Blueprint, request, jsonify
from backend.services.url_service import analyze_url
from backend.services.fusion_service import get_risk_level

detect_bp = Blueprint("detect_bp", __name__)

@detect_bp.route("/detect", methods=["POST"])
def detect():
    data = request.get_json()
    input_url = data.get("url")

    if not input_url:
        return jsonify({"error": "No URL provided"}), 400

    url_result = analyze_url(input_url)

    final_score = url_result["url_score"]
    risk_level = get_risk_level(final_score)

    return jsonify({
        "input_url": input_url,
        "url_analysis": url_result,
        "final_score": final_score,
        "risk_level": risk_level
    })