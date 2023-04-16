import curses
import os
import traceback
import subprocess
import time
import threading
from record_and_transcribe import start_recording, stop_recording, merge_audio_files, transcribe_audio, summarize_text
from audio_device_manager import switch_to_blackhole, switch_to_previous_device
from utils import create_timestamped_directory

class Stenographer(object):
    def __init__(self):
        self.current_archive_directory = None
        self.current_state = "idle"
        curses.wrapper(self.menu)

    def get_center(self, window):
        height, width = window.getmaxyx()
        center_row = height // 2
        center_col = width // 2
        return center_row, center_col

    def menu(self, stdscr):
        curses.curs_set(0)
        stdscr.keypad(True)

        center_row, center_col = self.get_center(stdscr)

        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, -1, curses.COLOR_BLACK)
        stdscr.bkgd(curses.color_pair(1))

        curses.init_color(1, 0, 1000, 0)  # set bright green color
        curses.init_pair(2, 1, -1)

        option = 0
        options = ["Start Recording", "Stop Recording"]

        art_win = curses.newwin(9, curses.COLS, 0, 0)
        art_win.attron(curses.color_pair(2))
        stdscr.attron(curses.color_pair(2))

        while True:
            art_win.clear()
            ASCII_line_length = 143
            offset = (curses.COLS - ASCII_line_length) // 2
            art_win.addstr(0, offset,'''                                                                                                           MMMMMMMMMMM MMMMMMMMMMMM MMMMMMMMMM ''')
            art_win.addstr(1, offset,'''.d88888b    dP                                                                  dP                         MM'"""""`MM MM"""""""`YM M""""""""M ''')
            art_win.addstr(2, offset,'''88.    "'   88                                                                  88                         M' .mmm. `M MM  MMMMm  M Mmmm  mmmM ''')
            art_win.addstr(3, offset,'''`Y88888b. d8888P .d8888b. 88d888b. .d8888b. .d8888b. 88d888b. .d8888b. 88d888b. 88d888b. .d8888b. 88d888b. M  MMMMMMMM M'        .M MMMM  MMMM ''')
            art_win.addstr(4, offset,'''      `8b   88   88ooood8 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88ooood8 88'  `88 M  MMM   `M MM  MMMMMMMM MMMM  MMMM ''')
            art_win.addstr(5, offset,'''d8'   .8P   88   88.  ... 88    88 88.  .88 88.  .88 88       88.  .88 88.  .88 88    88 88.  ... 88       M. `MMM' .M MM  MMMMMMMM MMMM  MMMM ''')
            art_win.addstr(6, offset,''' Y88888P    dP   `88888P' dP    dP `88888P' `8888P88 dP       `88888P8 88Y888P' dP    dP `88888P' dP       MM.     .MM MM  MMMMMMMM MMMM  MMMM ''')
            art_win.addstr(7, offset,'''                                                 .88                   88                                  MMMMMMMMMMM MMMMMMMMMMMM MMMMMMMMMM ''')
            art_win.addstr(8, offset,'''                                             d8888P                    dP                                                                      ''')

            stdscr.refresh()
            art_win.refresh()

            separator = "━" * curses.COLS

            stdscr.addstr(9, 0, separator)
            stdscr.addstr(11, 0, "Use arrow keys to navigate, Enter to select")
            stdscr.addstr(13, 0, "Current state: " + self.current_state)

            for i in range(len(options)):
                if i == option:
                    stdscr.addstr(15 + i, 0, "> " + options[i])
                else:
                    stdscr.addstr(15 + i, 0, "  " + options[i])

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
            time.sleep(0.1)

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
