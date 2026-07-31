import numpy as np


def cosine_similarity(vec1, vec2):
    dot_product = np.dot(vec1, vec2)

    magnitude1 = np.linalg.norm(vec1)

    magnitude2 = np.linalg.norm(vec2)

    similarity = dot_product / (magnitude1 * magnitude2)

    return similarity