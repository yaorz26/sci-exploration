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

    def remove_punctuation(self, sentence):
        """
        Removes punctuation from the input text.
        :param sentence: a sentence str
        :return: str, sentence without any punctuation
        """
        return ''.join(char for char in sentence if char not in string.punctuation)

    def get_pos_tag(self, sentence):
        """
        Remove punctuations of the sentence and tokenizes the input sentence, mark the part of speech tag of each word.
        :param sentence: a sentence str
        :return: list, part of speech tag of each word in the sentence.
        """
        sentence = self.remove_punctuation(sentence)
        tokens = word_tokenize(sentence)
        return pos_tag(tokens)

    def lemmatize_sentence(self, sentence):
        """
        Remove punctuations of the sentence and tokenizes the input sentence, mark the part of speech tag of each word,
        lemmatizes the words with different parameters based on their parts of speech, and stores in a list.
        :param sentence: a sentence str
        :return: a list of words which have been lemmatized.
        """
        sentence = self.remove_punctuation(sentence)
        tokens = word_tokenize(sentence)
        pos_tags = self.get_pos_tag(sentence)
        lemmatized_words = []
        for token, pos in pos_tags:
            if pos.startswith('V'):
                lemmatized_words.append(self.lemmatizer.lemmatize(token, pos='v'))
            elif pos.startswith('N'):
                lemmatized_words.append(self.lemmatizer.lemmatize(token, pos='n'))
            elif pos.startswith('J'):
                lemmatized_words.append(self.lemmatizer.lemmatize(token, pos='a'))
            elif pos.startswith('R'):
                lemmatized_words.append(self.lemmatizer.lemmatize(token, pos='r'))
            else:
                lemmatized_words.append(self.lemmatizer.lemmatize(token))
        return lemmatized_words

import unittest

class LemmatizationTestLemmatizeSentence(unittest.TestCase):
    def test_lemmatize_sentence_1(self):
        lemmatization = Lemmatization()
        result = lemmatization.lemmatize_sentence("I am running in a race.")
        expected = ['I', 'be', 'run', 'in', 'a', 'race']
        self.assertEqual(result, expected)

    def test_lemmatize_sentence_2(self):
        lemmatization = Lemmatization()
        result = lemmatization.lemmatize_sentence("Until the beating, Cantanco's eyesight had been weak, but adequate.")
        expected = ['Until', 'the', 'beating', 'Cantancos', 'eyesight', 'have', 'be', 'weak', 'but', 'adequate']
        self.assertEqual(result, expected)

    def test_lammatize_sentence_3(self):
        lemmatization = Lemmatization()
        result = lemmatization.lemmatize_sentence("The dog's barked at the mailman.")
        expected = ['The', 'dog', 'bark', 'at', 'the', 'mailman']
        self.assertEqual(result, expected)

    def test_lemmatize_sentence_4(self):
        lemmatization = Lemmatization()
        result = lemmatization.lemmatize_sentence("He was running and eating at same time. ")
        expected = ['He', 'be', 'run', 'and', 'eat', 'at', 'same', 'time']
        self.assertEqual(result, expected)

    def test_lemmatize_sentence_5(self):
        lemmatization = Lemmatization()
        result = lemmatization.lemmatize_sentence("I was taking a ride in the car.")
        expected = ['I', 'be', 'take', 'a', 'ride', 'in', 'the', 'car']
        self.assertEqual(result, expected)

class LemmatizationTestGetPosTag(unittest.TestCase):
    def test_get_pos_tag_1(self):
        lemmatization = Lemmatization()
        result = lemmatization.get_pos_tag("I am running in a race.")
        expected = ['PRP', 'VBP', 'VBG', 'IN', 'DT', 'NN']
        self.assertEqual(result, expected)

    def test_get_pos_tag_2(self):
        lemmatization = Lemmatization()
        result = lemmatization.get_pos_tag("Cantanco's eyesight had been weak, but adequate.")
        expected = ['NNP', 'NN', 'VBD', 'VBN', 'JJ', 'CC', 'JJ']
        self.assertEqual(result, expected)

    def test_get_pos_tag_3(self):
        lemmatization = Lemmatization()
        result = lemmatization.get_pos_tag("The dog's barked at the mailman.")
        expected = ['DT', 'NNS', 'VBD', 'IN', 'DT', 'NN']
        self.assertEqual(result, expected)

    def test_get_pos_tag_4(self):
        lemmatization = Lemmatization()
        result = lemmatization.get_pos_tag("He was running and eating at same time. ")
        expected = ['PRP', 'VBD', 'VBG', 'CC', 'VBG', 'IN', 'JJ', 'NN']
        self.assertEqual(result, expected)

    def test_get_pos_tag_5(self):
        lemmatization = Lemmatization()
        result = lemmatization.get_pos_tag("I was taking a ride in the car.")
        expected = ['PRP', 'VBD', 'VBG', 'DT', 'NN', 'IN', 'DT', 'NN']
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
