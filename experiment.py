import csv
from backend.services.detect_service import detect_website


def evaluate_mode(mode):

    total = 0
    correct = 0

    TP = TN = FP = FN = 0

    with open("dataset.csv", newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            url = row["url"]
            true_label = int(row["label"])

            result = detect_website(url)

            url_score = result["url_analysis"]["score"]
            text_score = result["text_analysis"]["score"]
            image_score = result["image_analysis"]["score"]

            # ======================
            # 模态选择
            # ======================
            if mode == "url":
                final_score = url_score

            elif mode == "url_text":
                final_score = (url_score + text_score) / 2

            elif mode == "multimodal":
                final_score = result["final_score"]

            else:
                raise ValueError("模式错误")

            predicted_label = 1 if final_score > 0.5 else 0

            total += 1

            if predicted_label == true_label:
                correct += 1

            if predicted_label == 1 and true_label == 1:
                TP += 1
            elif predicted_label == 0 and true_label == 0:
                TN += 1
            elif predicted_label == 1 and true_label == 0:
                FP += 1
            elif predicted_label == 0 and true_label == 1:
                FN += 1

    accuracy = correct / total if total else 0
    precision = TP / (TP + FP) if (TP + FP) else 0
    recall = TP / (TP + FN) if (TP + FN) else 0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0

    return accuracy, precision, recall, f1


if __name__ == "__main__":

    print("===== 单模态（URL） =====")
    print(evaluate_mode("url"))

    print("\n===== 双模态（URL+文本） =====")
    print(evaluate_mode("url_text"))

    print("\n===== 三模态融合 =====")
    print(evaluate_mode("multimodal"))