import rumps
import subprocess
from record_and_transcribe import start_recording, stop_recording
from audio_device_manager import switch_to_blackhole, switch_to_previous_device
from utils import create_timestamped_directory


class RecorderApp(rumps.App):
    def __init__(self):
        super(RecorderApp, self).__init__("Recorder")
        self.start_button = rumps.MenuItem(title="Start Recording", callback=self.start)
        self.stop_button = rumps.MenuItem(title="Stop Recording", callback=self.stop)
        self.menu = [self.start_button, self.stop_button]
        self.stop_button.set_callback(None)
        self.current_archive_directory = None

    @rumps.clicked("Start Recording")
    def start(self, _):
        switch_to_blackhole()
        self.start_button.set_callback(None)
        self.stop_button.set_callback(self.stop)
        self.current_archive_directory = create_timestamped_directory("archive")
        start_recording(self.current_archive_directory)

    @rumps.clicked("Stop Recording")
    def stop(self, _):
        switch_to_previous_device()
        self.start_button.set_callback(self.start)
        self.stop_button.set_callback(None)
        stop_recording(self.current_archive_directory)

if __name__ == "__main__":
    RecorderApp().run()