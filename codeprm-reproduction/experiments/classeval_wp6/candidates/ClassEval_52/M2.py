import nltk
from nltk.stem import WordNetLemmatizer
from nltk import pos_tag, word_tokenize
import string


nltk.download('averaged_perceptron_tagger')
nltk.download('punkt')
nltk.download('wordnet')

class Lemmatization:
    """
    This is a class about Lemmatization, which utilizes the nltk library to perform lemmatization and part-of-speech tagging on sentences, as well as remove punctuation.
    """

    def __init__(self):
        """
        creates a WordNetLemmatizer object and stores it in the self.lemmatizer member variable.
        """
        self.lemmatizer = WordNetLemmatizer()

    def lemmatize_sentence(self, sentence):
        """
        Remove punctuations of the sentence and tokenizes the input sentence, mark the part of speech tag of each word,
        lemmatizes the words with different parameters based on their parts of speech, and stores in a list.
        :param sentence: a sentence str
        :return: a list of words which have been lemmatized.
        >>> lemmatization = Lemmatization()
        >>> lemmatization.lemmatize_sentence("I am running in a race.")
        ['I', 'be', 'run', 'in', 'a', 'race']
        """
        sentence = self.remove_punctuation(sentence)
        words = word_tokenize(sentence)
        pos_tags = pos_tag(words)
        lemmatized_words = [self.lemmatizer.lemmatize(word, pos=self.get_wordnet_pos(pos)) for word, pos in pos_tags]
        return lemmatized_words

    def get_wordnet_pos(self, pos_tag):
        """
        Maps the part-of-speech tag to the corresponding WordNet POS tag.
        :param pos_tag: a part-of-speech tag
        :return: a WordNet POS tag
        """
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