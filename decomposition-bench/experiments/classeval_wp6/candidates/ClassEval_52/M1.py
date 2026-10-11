import nltk
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag, word_tokenize
import string

nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')
nltk.download('wordnet')

class Lemmatization:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()

    def remove_punctuation(self, sentence):
        return ''.join([char for char in sentence if char not in string.punctuation])

    def get_pos_tag(self, sentence):
        sentence = self.remove_punctuation(sentence)
        return pos_tag(word_tokenize(sentence))

    def lemmatize_sentence(self, sentence):
        sentence = self.remove_punctuation(sentence)
        pos_tags = pos_tag(word_tokenize(sentence))
        lemmatized_words = [self.lemmatizer.lemmatize(word, pos=self.get_wordnet_pos(pos)) for word, pos in pos_tags]
        return lemmatized_words

    def get_wordnet_pos(self, pos_tag):
        if pos_tag.startswith('J'):
            return 'a'
        elif pos_tag.startswith('V'):
            return 'v'
        elif pos_tag.startswith('N'):
            return 'n'
        elif pos_tag.startswith('R'):
            return 'r'
        else:
            return 'n'