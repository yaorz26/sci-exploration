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
