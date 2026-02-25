def weighted_fusion(url_score, text_score, image_score,
                    alpha=0.3, beta=0.4, gamma=0.3):

    final_score = (
        alpha * url_score +
        beta * text_score +
        gamma * image_score
    )

    return int(final_score)