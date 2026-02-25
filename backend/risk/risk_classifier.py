def classify_risk(score):

    if score < 40:
        return "Safe"
    elif score < 70:
        return "Medium Risk"
    else:
        return "High Risk"