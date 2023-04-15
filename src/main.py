import curses
import os
import traceback
import subprocess
import threading
from record_and_transcribe import start_recording, stop_recording, merge_audio_files, transcribe_audio, summarize_text
from audio_device_manager import switch_to_blackhole, switch_to_previous_device
from utils import create_timestamped_directory

class Stenographer(object):
    def __init__(self):
        self.current_archive_directory = None
        self.current_state = "idle"
        curses.wrapper(self.menu)

    def menu(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)

        height, width = stdscr.getmaxyx()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
        curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)

        option = 0
        options = ["Start Recording", "Stop Recording"]

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "StenographerGPT", curses.color_pair(1) | curses.A_BOLD)
            stdscr.addstr(2, 0, "Use arrow keys to navigate, Enter to select")
            stdscr.addstr(4, 0, "Current state: " + self.current_state)
            for i in range(len(options)):
                if i == option:
                    stdscr.addstr(6 + i, 0, options[i], curses.color_pair(2))
                else:
                    stdscr.addstr(6 + i, 0, options[i])

            key = stdscr.getch()

            if key == curses.KEY_UP:
                option = (option - 1) % len(options)
            elif key == curses.KEY_DOWN:
                option = (option + 1) % len(options)
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if option == 0:
                    self.start_recording_wrapper()
                elif option == 1:
                    self.stop_recording_wrapper()
            elif key == ord('q'):
                break

    def start_recording_wrapper(self):
        try:
            self.current_state = "recording"
            switch_to_blackhole()
            self.current_archive_directory = create_timestamped_directory("archive")
            start_recording(self.current_archive_directory)
        except Exception as e:
            print(e)
            traceback.print_exc()
            self.current_state = "error"

    def stop_recording_wrapper(self):
        switch_to_previous_device()
        stop_recording(self.current_archive_directory)
        process_audio_thread = threading.Thread(target=self.process_audio, args=(self.current_archive_directory, self.current_archive_directory))
        process_audio_thread.start()

    def process_audio(self, input_directory, output_directory):
        try:
            mic_output = os.path.join(input_directory, "mic_output.wav")
            system_output = os.path.join(input_directory, "system_output.wav")
            merged_output = os.path.join(output_directory, "merged_output.wav")

            merge_audio_files(mic_output, system_output, merged_output)

            self.current_state = "transcribing"
            transcription = transcribe_audio(merged_output)

            transcript_file = os.path.join(output_directory, "transcript.txt")
            with open(transcript_file, "w") as f:
                f.write(transcription)

            self.current_state = "summarizing"
            summary_file = os.path.join(output_directory, "summary.txt")
            summary = summarize_text(transcription)
            with open(summary_file, "w") as f:
                f.write(summary)
            print('Summary:', summary)

            self.current_state = "idle"

        except Exception as e:
            self.current_state = "error"
            print(f"An error occurred: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    Stenographer()
