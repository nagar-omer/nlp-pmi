
# params for file reading
ROOT = "ROOT"           # token for dependency to root
SON = "DOWN_ARROW"      # token for down arrow in dependency tree
PARENT = "UP_ARROW"     # token for up arrow in dependency tree
PREP = ["IN"]           # preposition list

# params for types of semantics
SENTENCE = "sentence"   # all words in same sentence
WIN = "window"          # all words in window of 5 words
TREE = "semantic_tree"  # related words in semantic tree

# params PMI algorithm
WORD_TOP_BAR = 30    # min word count threshold
WORD_BOTTOM_BAR = 5    # min word count threshold
FEATURE_FREQ_BAR = 1  # min feature count threshold
CO_OCCURRENCE_BAR = 1  # min co occurrence threshold


