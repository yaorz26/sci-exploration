class MusicPlayer:
    def __init__(self):
        self.playlist = []
        self.current_song = None
        self.volume = 50

    def add_song(self, song):
        self.playlist.append(song)

    def remove_song(self, song):
        if song in self.playlist:
            self.playlist.remove(song)
            if self.current_song == song:
                self.stop()

    def play(self):
        if self.playlist and self.current_song:
            return self.playlist[0]
        elif len(self.playlist): 
            return False

    def stop(self):
        if self.current_song:
            self.current_song = None
            return True
        else:
            return False

    def switch_song(self):
        if self.current_song:
            current_index = self.playlist.index(self.current_song)
            if current_index < len(self.playlist) - 1:
                self.current_song = self.playlist[current_index + 1]
                return True
            else:
                return False
        else:
            return False

    def previous_song(self):
        if self.current_song:
            current_index = self.playlist.index(self.current_song)
            if current_index > 0:
                self.current_song = self.playlist[current_index - 1]
                return True
            else:
                return False
        else:
            return False

    def set_volume(self, volume):
        if 0 <= volume <= 100:
            self.volume = volume
        else:
            return False

    def shuffle(self):
        if self.playlist:
            import random
            random.shuffle(self.playlist)
            return True
        else:
            return False

import unittest

class MusicPlayerTestAddSong(unittest.TestCase):
    def test_add_song(self):
        musicPlayer = MusicPlayer()
        musicPlayer.add_song("song1")
        self.assertEqual(musicPlayer.playlist, ["song1"])

    def test_add_song2(self):
        musicPlayer = MusicPlayer()
        musicPlayer.add_song("song1")
        musicPlayer.add_song("song2")
        self.assertEqual(musicPlayer.playlist, ["song1", "song2"])

    def test_add_song3(self):
        musicPlayer = MusicPlayer()
        musicPlayer.add_song("song1")
        musicPlayer.add_song("song2")
        musicPlayer.add_song("song3")
        self.assertEqual(musicPlayer.playlist, ["song1", "song2", "song3"])

    def test_add_song4(self):
        musicPlayer = MusicPlayer()
        musicPlayer.add_song("song1")
        musicPlayer.add_song("song2")
        musicPlayer.add_song("song3")
        musicPlayer.add_song("song4")
        self.assertEqual(musicPlayer.playlist, ["song1", "song2", "song3", "song4"])

    def test_add_song5(self):
        musicPlayer = MusicPlayer()
        musicPlayer.add_song("song1")
        musicPlayer.add_song("song2")
        musicPlayer.add_song("song3")
        musicPlayer.add_song("song4")
        musicPlayer.add_song("song5")
        self.assertEqual(musicPlayer.playlist, ["song1", "song2", "song3", "song4", "song5"])

class MusicPlayerTestRemoveSong(unittest.TestCase):
    def test_remove_song(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.remove_song("song1")
        self.assertEqual(musicPlayer.playlist, ["song2"])

    def test_remove_song2(self):
        musicPlayer = MusicPlayer()
        musicPlayer.current_song = "song1"
        musicPlayer.playlist = ["song1", "song2", "song3"]
        musicPlayer.remove_song("song1")
        self.assertEqual(musicPlayer.playlist, ["song2", "song3"])

    def test_remove_song3(self):
        musicPlayer = MusicPlayer()
        musicPlayer.current_song = "song1"
        musicPlayer.playlist = ["song1", "song2", "song3", "song4"]
        musicPlayer.remove_song("song1")
        self.assertEqual(musicPlayer.playlist, ["song2", "song3", "song4"])

    def test_remove_song4(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2", "song3", "song4", "song5"]
        musicPlayer.remove_song("song1")
        self.assertEqual(musicPlayer.playlist, ["song2", "song3", "song4", "song5"])

    def test_remove_song5(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2", "song3", "song4", "song5"]
        musicPlayer.remove_song("song1")
        musicPlayer.remove_song("song2")
        self.assertEqual(musicPlayer.playlist, ["song3", "song4", "song5"])

    def test_remove_song6(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = []
        musicPlayer.remove_song("song1")
        self.assertEqual(musicPlayer.playlist, [])


class MusicPlayerTestPlay(unittest.TestCase):
    def test_play(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.play(), "song1")

    def test_play_2(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = []
        musicPlayer.current_song = "song2"
        self.assertEqual(musicPlayer.play(), None)

    def test_play_3(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        self.assertEqual(musicPlayer.play(),False)

    def test_play_4(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song3"
        self.assertEqual(musicPlayer.play(), "song1")

    def test_play_5(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.play(), "song1")

class MusicPlayerTestStop(unittest.TestCase):
    def test_stop(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.stop(), True)

    def test_stop_2(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = []
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.stop(), True)

    def test_stop_3(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        self.assertEqual(musicPlayer.stop(), False)

    def test_stop_4(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.stop(), True)

    def test_stop_5(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song2"
        self.assertEqual(musicPlayer.stop(), True)

import unittest

class MusicPlayerTestSwitchSong(unittest.TestCase):
    def test_switch_song(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.switch_song(), True)

    def test_switch_song2(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song2"
        self.assertEqual(musicPlayer.switch_song(), False)

    def test_switch_song3(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2", "song3"]
        musicPlayer.current_song = "song3"
        self.assertEqual(musicPlayer.switch_song(), False)

    def test_switch_song4(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        self.assertEqual(musicPlayer.switch_song(), False)

    def test_switch_song5(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = []
        self.assertEqual(musicPlayer.switch_song(), False)

class MusicPlayerTestPreviousSong(unittest.TestCase):
    def test_previous_song(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2", "song3"]
        musicPlayer.current_song = "song2"
        self.assertEqual(musicPlayer.previous_song(), True)

    def test_previous_song2(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2", "song3"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.previous_song(), False)

    def test_previous_song3(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2", "song3"]
        musicPlayer.current_song = "song3"
        self.assertEqual(musicPlayer.previous_song(), True)

    def test_previous_song4(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2", "song3"]
        self.assertEqual(musicPlayer.previous_song(), False)

    def test_previous_song5(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = []
        self.assertEqual(musicPlayer.previous_song(), False)

class MusicPlayerTestSetVolume(unittest.TestCase):
    def test_set_volume(self):
        musicPlayer = MusicPlayer()
        self.assertEqual(musicPlayer.set_volume(50), None)
        self.assertEqual(musicPlayer.volume, 50)

    def test_set_volume2(self):
        musicPlayer = MusicPlayer()
        self.assertEqual(musicPlayer.set_volume(100), None)
        self.assertEqual(musicPlayer.volume, 100)

    def test_set_volume3(self):
        musicPlayer = MusicPlayer()
        self.assertEqual(musicPlayer.set_volume(0), None)
        self.assertEqual(musicPlayer.volume, 0)

    def test_set_volume4(self):
        musicPlayer = MusicPlayer()
        self.assertEqual(musicPlayer.set_volume(101), False)
        self.assertEqual(musicPlayer.volume, 50)

    def test_set_volume5(self):
        musicPlayer = MusicPlayer()
        self.assertEqual(musicPlayer.set_volume(-1), False)
        self.assertEqual(musicPlayer.volume, 50)

class MusicPlayerTestShuffle(unittest.TestCase):
    def test_shuffle(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        self.assertEqual(musicPlayer.shuffle(), True)

    def test_shuffle_2(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = []
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.shuffle(), False)

    def test_shuffle_3(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song2"
        self.assertEqual(musicPlayer.shuffle(), True)

    def test_shuffle_4(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song3"
        self.assertEqual(musicPlayer.shuffle(), True)

    def test_shuffle_5(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.shuffle(), True)

class MusicPlayerTestMain(unittest.TestCase):
    def test_main(self):
        musicPlayer = MusicPlayer()
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.play(), "song1")
        self.assertEqual(musicPlayer.stop(), True)
        musicPlayer.playlist = ["song1", "song2"]
        musicPlayer.current_song = "song1"
        self.assertEqual(musicPlayer.switch_song(), True)
        self.assertEqual(musicPlayer.previous_song(), True)
        musicPlayer.set_volume(50)
        self.assertEqual(musicPlayer.volume, 50)

if __name__ == '__main__':
    unittest.main()
