import time

from vlc import Instance


class VLC:
    def __init__(self):
        self.vlc_instance = Instance()
        self.media_list_player = self.vlc_instance.media_list_player_new()

    def add_media_list(self, media_list):
        self.media_list = self.vlc_instance.media_list_new(mrls=media_list)
        return self.media_list

    def play_music_from_list(self, media_list):
        self.media_list_player.set_media_list(self.add_media_list(media_list))
        self.media_list_player.play()
        return self.media_list_player

    def stop_music(self):

        self.media_list_player.stop()


if __name__ == "__main__":

    # Test that the media player is working
    vlc_inst = VLC()
    player = vlc_inst.play_music_from_list(["https://powerhitz.com/office.pls"])
