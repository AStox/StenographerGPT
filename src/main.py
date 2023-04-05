import rumps
import os
import traceback
import subprocess
import threading
from record_and_transcribe import start_recording, stop_recording, merge_audio_files, transcribe_audio, summarize_text
from audio_device_manager import switch_to_blackhole, switch_to_previous_device
from utils import create_timestamped_directory

current_state = "idle"

class MemoraiApp(rumps.App):
    def __init__(self):
        super(MemoraiApp, self).__init__("Memorai")
        self.rumps_app = rumps.App("Memorai")
        self.start_button = rumps.MenuItem(title="Start Recording", callback=self.start)
        self.stop_button = rumps.MenuItem(title="Stop Recording", callback=self.stop)
        self.menu = [self.start_button, self.stop_button]
        self.stop_button.set_callback(None)
        self.current_archive_directory = None

    def run(self):
        self.update_app_title()
        super(MemoraiApp, self).run()

    @rumps.clicked("Start Recording")
    def start(self, _):
        global current_state
        try:
            current_state = "recording"
            self.update_app_title()
            switch_to_blackhole()
            self.start_button.set_callback(None)
            self.stop_button.set_callback(self.stop)
            self.current_archive_directory = create_timestamped_directory("archive")
            start_recording(self.current_archive_directory)
        except Exception as e:
            print(e)
            traceback.print_exc()
            current_state = "error"
            self.update_app_title()

    @rumps.clicked("Stop Recording")
    def stop(self, _):
        switch_to_previous_device()
        self.start_button.set_callback(self.start)
        self.stop_button.set_callback(None)
        stop_recording(self.current_archive_directory)
        process_audio_thread = threading.Thread(target=self.process_audio, args=(self.current_archive_directory, self.current_archive_directory))
        process_audio_thread.start()

    def update_app_title(self):
        global current_state
        
        if current_state == "transcribing":
            self.title = "💭"
        elif current_state == "summarizing":
            self.title = "📝"
        elif current_state == "recording":
            self.title = "👂"
        elif current_state == "error":
            self.title = "📝"
        else:
            self.title = "🧠"

    def process_audio(self, input_directory, output_directory):
        global current_state
        try:

            mic_output = os.path.join(input_directory, "mic_output.wav")
            system_output = os.path.join(input_directory, "system_output.wav")
            merged_output = os.path.join(output_directory, "merged_output.wav")

            merge_audio_files(mic_output, system_output, merged_output)

            current_state = "transcribing"
            self.update_app_title()

            transcription = transcribe_audio(merged_output)

            transcript_file = os.path.join(output_directory, "transcript.txt")
            with open(transcript_file, "w") as f:
                f.write(transcription)

            current_state = "summarizing"
            self.update_app_title()
            summary_file = os.path.join(output_directory, "summary.txt")
            summary = summarize_text(transcription)
            with open(summary_file, "w") as f:
                f.write(summary)
            print('Summary:', summary)

            current_state = "idle"
            self.update_app_title()

        except Exception as e:
            current_state = "error"
            self.title = "❗️"
            print(f"An error occurred: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    MemoraiApp().run()