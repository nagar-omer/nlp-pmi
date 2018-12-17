import os
from utils.parameters import PREP, SENTENCE
from utils.sentence import Sentence


class SemanticsDataLoader:
    def __init__(self, src_file):
        self._len, self._lemma_count, self._data = self._read_file(src_file)

    def data(self, semantic_type=SENTENCE):
        for sentence in self._data:
            for sample in sentence.words_semantics(semantic_type=semantic_type):
                yield sample

    def lemma_count(self, word):
        return self._lemma_count[word]

    def lemma_list(self):
        return list(self._lemma_count.keys())

    def __len__(self):
        return self._len

    @staticmethod
    def _read_file(src_file):
        data = []
        lemma_count = {}
        total_samples = 0
        src = open(src_file, "rt", encoding="utf-8")
        # init lists
        words = []
        lemma_words = []
        is_prep = []
        tree = []
        for row in src:
            if row == "\n":
                # create sentence object
                data.append(Sentence(words, lemma_words, is_prep, tree))
                # init lists
                words = []
                lemma_words = []
                is_prep = []
                tree = []
                continue
            # read file
            tree_id, word, lemma, _,  pos, _, parent_idx, context, _, _ = row.split()
            total_samples += 1
            lemma_count[lemma] = lemma_count.get(lemma, 0) + 1
            # fill list with relevant data from the file
            words.append(word)
            lemma_words.append(lemma)
            is_prep.append(True if pos in PREP else False)
            tree.append((int(parent_idx) - 1, context))
        return total_samples, lemma_count, data


if __name__ == "__main__":
    dl = SemanticsDataLoader(os.path.join("..", "data", "wikipedia.txt"))
    data = [i for i in dl.data(semantic_type="tree")]

    e = 0
