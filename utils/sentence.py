from utils.parameters import ROOT, SON, PARENT, SENTENCE, WIN, TREE


class Sentence:
    # http://u.cs.biu.ac.il/~89-680/dep_trees.pdf - example tree link
    # words: the sentence itself                        ["a", "yellow", "garbage", "can"]
    # is Prep: True/false list                          [False, False, False, False]
    # semantic_tree:  [ .. (parent_idx, context) ..]    [ (2, "det"), (2, "amod"), (3, "nsubj"), (-1, ROOT)]

    def __init__(self, words: list, lemma_words: list, is_prep: list, semantic_tree: list):
        self._all_words = words
        self._lemma = lemma_words
        self._is_prep = is_prep
        self._tree = semantic_tree

    # semantic_tree_parse: create list of connections for each word (P: parent, S:Son)
    #       "a"                      "yellow"
    # [<"a", <"det", P>>] , [<"garbage", <"amod", P>>],
    # ...
    #               "garbage"                                                       "can"
    # [<"a", <"det", S>>, <"yellow", <"amod", S>>, <"can", <"nsubj", P>>], ["garbage", <"nsubj", S>>]
    def _parse_semantic_tree(self):
        words_semantics = [[] for _ in self._all_words]  # create list of semantics for eac word
        for i, (parent_idx, context) in enumerate(self._tree):
            # if parent is root -> IGNORE
            if context == ROOT:
                continue
            # add context to parent and son respectively
            words_semantics[parent_idx].append((self._lemma[i], (context, SON)))
            words_semantics[i].append((self._lemma[parent_idx], (context, PARENT)))
            # handle prepositions
            if self._is_prep[parent_idx]:           # parent is prep
                parent_prep = self._tree[parent_idx][0]
                # although not supposed to happen check parent is not root
                if parent_prep != -1:
                    # create bridge parent --> prep --> son
                    words_semantics[parent_prep].append((self._lemma[i], (context, SON)))
                    words_semantics[i].append((self._lemma[parent_prep], (context, PARENT)))
        return words_semantics

    def words_semantics(self, semantic_type=SENTENCE):
        if semantic_type == SENTENCE:
            for i, lem in enumerate(self._lemma):
                yield self._all_words[i], lem, self._lemma[:i] + self._lemma[i+1:]

        if semantic_type == WIN:
            for i, lem in enumerate(self._lemma):
                yield self._all_words[i], lem, self._lemma[i-2:i] + self._lemma[i+1:i+3]

        if semantic_type == TREE:
            words_semantics = self._parse_semantic_tree()
            for i, lem in enumerate(self._lemma):
                yield self._all_words[i], lem, words_semantics[i]


if __name__ == "__main__":
    words = ["a", "yellow", "garbage", "can"]
    lemma_words = ["a", "yellow", "garbage", "can"]
    is_prep = [False, False, False, False]
    tree = [(2, "det"), (2, "amod"), (3, "nsubj"), (-1, ROOT)]
    s = Sentence(words, lemma_words, is_prep, tree)

    sen = [i for i in s.words_semantics(semantic_type=SENTENCE)]
    win = [i for i in s.words_semantics(semantic_type=WIN)]
    tr = [i for i in s.words_semantics(semantic_type=TREE)]

    e = 0


