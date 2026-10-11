import re

class SplitSentence:
    """
    The class allows to split sentences, count words in a sentence, and process a text file to find the maximum word count.
    """

    def split_sentences(self, sentences_string):
        """
        Split a string into a list of sentences. Sentences end with . or ? and with a space after that. Please note that Mr. also end with . but are not sentences.
        :param sentences_string: string, string to split
        :return:list, split sentence list
        >>> ss = SplitSentence()
        >>> ss.split_sentences("aaa aaaa. bb bbbb bbb? cccc cccc. dd ddd?")
        ['aaa aaaa.', 'bb bbbb bbb?', 'cccc cccc.', 'dd ddd?']
        """
        return re.findall(r'[^.?!]+[.?!]\s*(?!(?:Mr\.|Dr\.|Mrs\.|Ms\.|Jr\.|Sr\.))', sentences_string)

    def count_words(self, sentence):
        """
        Count the number of words in a sentence. Note that words are separated by spaces and that punctuation marks and numbers are not counted as words.
        :param sentence:string, sentence to be counted, where words are separated by spaces
        :return:int, number of words in the sentence
        >>> ss.count_words("abc def")
        2
        """
        return len(re.findall(r'\b\w+\b', sentence))

    def process_text_file(self, sentences_string):
        """
        Given a text, return the number of words in the longest sentence
        :param sentences_string: string, undivided long sentence
        :return:int, the number of words in the longest sentence
        >>> ss.process_text_file("aaa aaaa. bb bbbb bbb? cccc ccccccc cc ccc. dd ddd?")
        4
        """
        sentences = self.split_sentences(sentences_string)
        max_words = 0
        for sentence in sentences:
            word_count = self.count_words(sentence)
            if word_count > max_words:
                max_words = word_count
        return max_words

import unittest


class SplitSentenceTestSplitSentences(unittest.TestCase):
    def test_split_sentences_1(self):
        ss = SplitSentence()
        lst = ss.split_sentences("aaa aaaa. bb bbbb bbb? cccc cccc. dd ddd?")
        self.assertEqual(lst, ['aaa aaaa.', 'bb bbbb bbb?', 'cccc cccc.', 'dd ddd?'])

    def test_split_sentences_2(self):
        ss = SplitSentence()
        lst = ss.split_sentences("Who is Mr. Smith? He is a teacher.")
        self.assertEqual(lst, ['Who is Mr. Smith?', 'He is a teacher.'])

    def test_split_sentences_3(self):
        ss = SplitSentence()
        lst = ss.split_sentences("Who is A.B.C.? He is a teacher.")
        self.assertEqual(lst, ['Who is A.B.C.?', 'He is a teacher.'])

    def test_split_sentences_4(self):
        ss = SplitSentence()
        lst = ss.split_sentences("aaa aaaa. bb bbbb bbb? cccc cccc.")
        self.assertEqual(lst, ['aaa aaaa.', 'bb bbbb bbb?', 'cccc cccc.'])

    def test_split_sentences_5(self):
        ss = SplitSentence()
        lst = ss.split_sentences("aaa aaaa. bb bbbb bbb?")
        self.assertEqual(lst, ['aaa aaaa.', 'bb bbbb bbb?'])


class SplitSentenceTestCountWords(unittest.TestCase):
    def test_count_words_1(self):
        ss = SplitSentence()
        cnt = ss.count_words("abc def")
        self.assertEqual(cnt, 2)

    def test_count_words_2(self):
        ss = SplitSentence()
        cnt = ss.count_words("abc def 1")
        self.assertEqual(cnt, 2)

    def test_count_words_3(self):
        ss = SplitSentence()
        cnt = ss.count_words("abc 1")
        self.assertEqual(cnt, 1)

    def test_count_words_4(self):
        ss = SplitSentence()
        cnt = ss.count_words("abc def bbb1")
        self.assertEqual(cnt, 3)

    def test_count_words_5(self):
        ss = SplitSentence()
        cnt = ss.count_words("abc def 111")
        self.assertEqual(cnt, 2)

if __name__ == '__main__':
    unittest.main()
