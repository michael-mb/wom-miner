'''Helper functions for keyword extraction'''

import numpy as np

def normalize_scores(scores):
    scores = np.array(scores)

    if scores.size == 0:
        return scores

    score_range = np.ptp(scores)

    if score_range == 0:
        return np.zeros_like(scores)
    else:
        normalized_scores = np.round((scores - scores.min()) / score_range, 3)
        return normalized_scores

