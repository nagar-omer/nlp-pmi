from utils.data_loader import SemanticsDataLoader
from utils.parameters import SENTENCE, WORD_TOP_BAR, WORD_BOTTOM_BAR, FEATURE_FREQ_BAR, CO_OCCURRENCE_BAR
import math
import os


class PMICalculator:
    def __init__(self, src_file, semantics_type=SENTENCE):
        self._semantic_type = semantics_type
        self._dl = SemanticsDataLoader(src_file)                                            # data loader
        self._ftr_to_lemma = {}                                                             # { ftr:   {lemma: score}
        self._context_vectors = {lemma: {} for lemma in self._dl.lemma_list()               # { lemma: {ftr: score}}
                                 if WORD_BOTTOM_BAR <= self._dl.lemma_count(lemma) < WORD_TOP_BAR}
        self._ftr_list = {}                                                                 # { ftr: True/False }
        self._ftr_count = {}                                                                # { ftr: count_ftr }
        self._calculate_context()
        self._norm_words = {lemma: self._norm(lemma) for lemma in self._dl.lemma_list()     # { lemma: norm(lemma) }
                            if WORD_BOTTOM_BAR <= self._dl.lemma_count(lemma) < WORD_TOP_BAR}

    def _calculate_context(self):

        for word, lemma, ftr_list in self._dl.data(semantic_type=self._semantic_type):
            if not(WORD_BOTTOM_BAR <= self._dl.lemma_count(lemma) < WORD_TOP_BAR):                # word appearance threshold
                continue
            # count for each lemma a dictionary { ... ftr: count ... }
            for ftr in ftr_list:
                self._context_vectors[lemma][ftr] = self._context_vectors[lemma].get(ftr, 0) + 1
                self._ftr_count[ftr] = self._ftr_count.get(ftr, 0) + 1    # count ftr

                # reversed dict from ftr to lemma (same score update, different dictionary)
                if ftr not in self._ftr_to_lemma:
                    self._ftr_to_lemma[ftr] = {}
                if lemma not in self._ftr_to_lemma[ftr]:
                    self._ftr_to_lemma[ftr][lemma] = self._ftr_to_lemma[ftr].get(lemma, 0) + 1    # count ftr

        # filter ftr if ftr count < FEATURE_FREQ_BAR
        for ftr, count in self._ftr_count.items():
            self._ftr_list[ftr] = False if count < FEATURE_FREQ_BAR else True

    def _norm(self, lemma):
        norm = 0
        for ftr, score in self._context_vectors[lemma].items():
            if not self._ftr_list[ftr] or score < CO_OCCURRENCE_BAR:       # filter ftr or if score is too low
                continue
            norm += score**2
        return norm**0.5

    def _dist(self, lemma1, lemma2):
        norm = 0
        for ftr, score in self._context_vectors[lemma1]:
            # filter ftr or if score is too low
            if not self._ftr_list[ftr] or score < CO_OCCURRENCE_BAR \
                    or self._context_vectors[lemma2][ftr] < CO_OCCURRENCE_BAR:
                continue
            norm += score * self._context_vectors[lemma2][ftr]
        return norm ** 0.5

    def calc_cosin_dist(self, lemma, lemma_2=None):
        if (not WORD_BOTTOM_BAR <= self._dl.lemma_count(lemma) < WORD_TOP_BAR) or \
                (lemma_2 and (not WORD_BOTTOM_BAR <= self._dl.lemma_count(lemma_2) < WORD_TOP_BAR)):
            return {}
        # option_1 calc distance between 2 lemmas
        if lemma_2:
            norm1 = self._norm_words[lemma]
            norm2 = self._norm_words[lemma_2]
            dist = self._dist(lemma, lemma_2)
            temp_calc = dist / (norm1 * norm2)
            return abs(math.acos(temp_calc if abs(temp_calc) < 1 else round(temp_calc)))

        # option_2 calc dist between one lemma to the rest of the words
        score_vec = {lem: 0 for lem in self._dl.lemma_list()            # score_vec: {lemma2: dist_from_lemma1}
                     if WORD_BOTTOM_BAR <= self._dl.lemma_count(lem) < WORD_TOP_BAR}
        for ftr, score_1 in self._context_vectors[lemma].items():               # calc : { lemma2: sum(dist1*dist2) }
            if not self._ftr_list[ftr] or score_1 < CO_OCCURRENCE_BAR:  # filter ftr and co_occurrence for score1
                for lemma, score_2 in self._ftr_to_lemma[ftr]:
                    if score_2 < CO_OCCURRENCE_BAR:                     # filter co_occurrence for score2
                        score_vec[lemma] += score_1 * score_2

        norm1 = self._norm_words[lemma]
        for lem2, val in score_vec.items():                              # final calc: { lemma2: dist(lemma1, lemma2) }
            if not WORD_BOTTOM_BAR <= self._dl.lemma_count(lem2) < WORD_TOP_BAR:
                continue
            temp_calc = val**0.5 / (norm1 * self._norm_words[lem2])
            score_vec[lem2] = abs(math.acos(temp_calc if abs(temp_calc) < 1 else round(temp_calc)))
        return score_vec


if __name__ == "__main__":
    calc = PMICalculator(os.path.join("..", "data", "wiki_sample"), SENTENCE)
    d = calc.calc_cosin_dist("article")
    print([w for w, v in sorted(d.items(), key=lambda x: -x[1])][:5])
    e = 0