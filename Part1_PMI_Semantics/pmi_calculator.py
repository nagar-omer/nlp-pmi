import pickle
from sys import stdout

from utils.data_loader import SemanticsDataLoader
from utils.parameters import SENTENCE, WORD_TOP_BAR, WORD_BOTTOM_BAR, FEATURE_FREQ_BAR, CO_OCCURRENCE_BAR, TREE
import math
import os


class PMICalculator:
    def __init__(self, src_file, semantics_type=SENTENCE):
        self._semantic_type = semantics_type
        self._dl = SemanticsDataLoader(src_file)                              # data loader
        self._ftr_to_lemma_pmi = {}                                           # { ftr:   {lemma: score}
        self._lemma_to_ftr_pmi = {}                                           # { lemma: {ftr: score}
        self._ftr_list = {}                                                   # { ftr: True/False }
        self._norm_words = {}                                                 # { lemma: norm(lemma) }
        self._calculate_context()

    def _calculate_context(self):
        p_u_att = {}                                                          # { lemma: {ftr: score}}
        p_att_u = {}                                                          # { lemma: {ftr: score}}
        p_u = {}                                                              # { lemma: {ftr: score}}
        p_att = {}
        total = 0
        print("counting lemma and features...")
        len_data = len(self._dl)
        for i, (word, lemma, ftr_list) in enumerate(self._dl.data(semantic_type=self._semantic_type)):
            stdout.write("\r\r\r%d" % int(100 * (i + 1) / len_data) + "%")
            stdout.flush()
            if not(WORD_BOTTOM_BAR <= self._dl.lemma_count(lemma) < WORD_TOP_BAR):       # word appearance threshold
                continue
            # count for each lemma a dictionary { ... ftr: count ... }
            for ftr in ftr_list:
                if ftr not in p_att_u:
                    p_att_u[ftr] = {}
                p_att_u[ftr][lemma] = p_att_u[ftr].get(ftr, 0) + 1            # count #(att, u)
                if lemma not in p_u_att:
                    p_u_att[lemma] = {}
                p_u_att[lemma][ftr] = p_u_att[lemma].get(ftr, 0) + 1          # count #(u, att)
                p_u[lemma] = p_u.get(lemma, 0) + 1                            # count #(u, *)
                p_att[ftr] = p_att.get(ftr, 0) + 1                            # count #(*, ftr)
                total += 1                                                    # count #(*,*)

        print("\nfilter - FEATURE_FREQ...")
        # filter ftr if ftr count < FEATURE_FREQ_BAR and update #(*,*)
        len_data = len(p_att)
        for i, (ftr, count) in enumerate(p_att.items()):
            stdout.write("\r\r\r%d" % int(100 * (i + 1) / len_data) + "%")
            stdout.flush()
            if count < FEATURE_FREQ_BAR:
                total -= count
                for lem, val in p_att_u[ftr].items():
                    p_u[lem] -= val
                self._ftr_list[ftr] = False
            else:
                self._ftr_list[ftr] = True

        print("\nfilter - CO_OCCURRENCE...")
        # filter co-occurrence and update #(*,*)
        len_data = len(p_u_att)
        for i, (lemma, ftr_vec) in enumerate(p_u_att.items()):
            stdout.write("\r\r\r%d" % int(100 * (i + 1) / len_data) + "%")
            stdout.flush()
            for ftr, val in ftr_vec.items():
                if self._ftr_list[ftr] and val < CO_OCCURRENCE_BAR:     # #(*,*) already updated for ftr not in ftr list
                    p_u_att[lemma][ftr] = 0
                    # update counters
                    total -= val
                    p_u[lemma] -= val
                    p_att[ftr] -= val

        print("\ncalculating PMI...")
        len_data = len(p_u_att)
        for i, (lemma, ftr_vec) in enumerate(p_u_att.items()):
            stdout.write("\r\r\r%d" % int(100 * (i + 1) / len_data) + "%")
            stdout.flush()
            for ftr, val in ftr_vec.items():
                if self._ftr_list[ftr] and p_att[ftr] > 0 and p_u[lemma] > 0:
                    pmi_score = math.log((val * total) / (p_u[lemma] * p_att[ftr]) + 1e-5)

                    if lemma not in self._lemma_to_ftr_pmi:
                        self._lemma_to_ftr_pmi[lemma] = {}
                    self._lemma_to_ftr_pmi[lemma][ftr] = pmi_score

                    if ftr not in self._ftr_to_lemma_pmi:
                        self._ftr_to_lemma_pmi[ftr] = {}
                    self._ftr_to_lemma_pmi[ftr][lemma] = pmi_score

        print("\ncalculating norms...")
        len_data = len(self._lemma_to_ftr_pmi)
        for i, lemma in enumerate(self._lemma_to_ftr_pmi):
            stdout.write("\r\r\r%d" % int(100 * (i + 1) / len_data) + "%")
            stdout.flush()
            self._norm_words[lemma] = self._norm(lemma)

        print("")

    def _norm(self, lemma1, lemma2=None):
        norm = 0
        if not lemma2:
            for ftr, score in self._lemma_to_ftr_pmi[lemma1].items():         # sqrt( sum( lem_i ** 2 ) )
                norm += score ** 2
        else:
            for ftr, score in self._lemma_to_ftr_pmi[lemma1].items():         # sqrt( sum( lem1_i * lem2_i ) )
                norm += score * self._lemma_to_ftr_pmi[lemma2].get(ftr, 0)
        return norm ** 0.5

    def calc_cosin_dist(self, lemma, lemma_2=None):
        if (not WORD_BOTTOM_BAR <= self._dl.lemma_count(lemma) < WORD_TOP_BAR) or \
                (lemma_2 and (not WORD_BOTTOM_BAR <= self._dl.lemma_count(lemma_2) < WORD_TOP_BAR)):
            return {}
        # option_1 calc distance between 2 lemmas
        if lemma_2:
            temp_calc = self._norm(lemma, lemma_2) / (self._norm_words[lemma] * self._norm_words[lemma_2])
            return math.acos(temp_calc if abs(temp_calc) < 1 else round(temp_calc))

        # option_2 calc dist between one lemma to the rest of the words
        score_vec = {lem: 0 for lem in self._lemma_to_ftr_pmi}                # score_vec: {lemma2: dist_from_lemma1}

        for ftr, score_1 in self._lemma_to_ftr_pmi[lemma].items():            # calc : { lemma2: sum(dist1*dist2) }
            for lem, score_2 in self._ftr_to_lemma_pmi[ftr].items():
                score_vec[lem] += score_1 * score_2

        norm1 = self._norm_words[lemma]
        for lem2, val in score_vec.items():                                   # final calc: { lemma2: dist(lem1, lem2) }
            temp_calc = val / (norm1 * self._norm_words[lem2])
            score_vec[lem2] = math.acos(temp_calc if abs(temp_calc) < 1 else round(temp_calc))
        return score_vec


if __name__ == "__main__":
    if os.path.exists("wiki_model"):
        calc = pickle.load(open("wiki_model", "rb"))
    else:
        calc = PMICalculator(os.path.join("..",  "data", "wiki", "wikipedia.txt"), TREE)
        pickle.dump(calc, open("wiki_model", "wb"))
    d = calc.calc_cosin_dist("britney")
    print([(w, v) for w, v in sorted(d.items(), key=lambda x: x[1])][:10])
    e = 0
