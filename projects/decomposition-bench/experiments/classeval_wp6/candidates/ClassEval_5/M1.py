class AutomaticGuitarSimulator:
    def __init__(self, text) -> None:
        """
        Initialize the score to be played
        :param text:str, score to be played
        """
        self.play_text = text
        self.play_list = self.interpret()

    def interpret(self, display=False):
        """
        Interpret the music score to be played
        :param display:Bool, representing whether to print the interpreted score
        :return: list of dict, The dict includes two fields, Chord and Tune, which are letters and numbers, respectively. If the input is empty or contains only whitespace, an empty list is returned.
        """
        if not self.play_text.strip():
            return []

        play_list = []
        for item in self.play_text.split():
            chord, tune = item[:2], item[2:]
            play_list.append({'Chord': chord, 'Tune': tune})

        if display:
            for entry in play_list:
                self.display(entry['Chord'], entry['Tune'])

        return play_list

    def display(self, key, value):
        """
        Print out chord and play tune with following format: Normal Guitar Playing -- Chord: %s, Play Tune: %s
        :param key:str, chord
        :param value:str, play tune
        :return: str
        """
        print(f"Normal Guitar Playing -- Chord: {key}, Play Tune: {value}")