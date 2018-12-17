import numpy as np
from math import sqrt, acos, pi


class Similarity:
    def __init__(self, src_file):
        self._word_to_vec = self._read_file(src_file)

    @staticmethod
    def _read_file(map_file):
        word_to_vec = {}
        map_file = open(map_file, "rt")
        for row in map_file:
            word, vec = row.split(" ", 1)
            word_to_vec[word] = np.fromstring(vec, dtype="float", sep=" ")
        return word_to_vec

    def _dist(self, u, v):
        val = np.dot(u, v) / (sqrt(np.dot(u, u)) * sqrt(np.dot(v, v)))
        val = 1 if val > 1 else val
        val = -1 if val < -1 else val
        res_temp = acos(val)
        return abs(res_temp)

    def most_similar(self, word, k):
        word_vec = self._word_to_vec[word]
        best_scores = {word_i: self._dist(word_vec, word_i_vec) for word_i, word_i_vec in self._word_to_vec.items()}
        return [(w, s) for w, s in sorted(best_scores.items(), key=lambda x:x[1])][:k]


if __name__ == "__main__":
    import os
    sim = Similarity(os.path.join("..", "data", "word_to_vec", "bow5.contexts"))
    # sim = Similarity(os.path.join("..", "data", "word_to_vec", "bow5.words"))
    print(sim.most_similar("explode", 20))
    words = ["explode", "england", "office", "john", "dog"]
    out = open("context_word_to_vec-file", "wt")
    for w in words:
        out.write(str(sim.most_similar(w, 6)) + "\n")
    e = 0
