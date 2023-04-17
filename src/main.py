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
    menuItems = {
        'RECORD': "Start New Recording",
        'STOP': "Stop Recording",
        'QUIT': "Quit",
    }

    def __init__(self):
        self.current_archive_directory = None
        self.current_state = "idle"
        curses.wrapper(self.menu)

    def get_center(self, window):
        height, width = window.getmaxyx()
        center_row = height // 2
        center_col = width // 2
        return center_row, center_col

    def draw_menu_item(self, stdscr, y, x, text, is_selected):
        text = " " + text + " "
        box_width = len(text) + 2

        if is_selected:
            text_color = 1
            border_characters = {'tl': '┏', 'tr': '┓', 'bl': '┗', 'br': '┛', 'h': '━', 'v': '┃'}
        else:
            text_color = 2
            border_characters = {'tl': '┌', 'tr': '┐', 'bl': '└', 'br': '┘', 'h': '─', 'v': '│'}

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(y, x, border_characters['tl'] + border_characters['h'] * box_width + border_characters['tr'])
        stdscr.addstr(y + 1, x, border_characters['v'])
        stdscr.addstr(y + 1, x + box_width + 1, border_characters['v'])
        stdscr.addstr(y + 2, x, border_characters['bl'] + border_characters['h'] * box_width + border_characters['br'])
        stdscr.attroff(curses.color_pair(2))

        stdscr.attron(curses.color_pair(text_color))
        stdscr.addstr(y + 1, x + 1 + (box_width - len(text)) // 2, text)
        stdscr.attroff(curses.color_pair(text_color))

    def findIndex(self, arr, item):
        try:
            index = arr.index(item)
            return index
        except ValueError:
            return -1

    def menu(self, stdscr):
        # Set cursor to invisible
        curses.curs_set(0)

        # Enable keypad mode
        stdscr.keypad(True)

        # Initialize colours
        curses.start_color()


        # Colours
        curses.init_color(1, 0, 0, 0)  # BLACK
        curses.init_color(2, 0, 1000, 0)  # GREEN

        curses.init_pair(1, 1, 2)
        curses.init_pair(2, 2, 1)

        # Set screen attributes
        stdscr.bkgd(curses.color_pair(2))
        stdscr.attron(curses.color_pair(2))

        # Set Title window attributes
        title_window = curses.newwin(11, curses.COLS, 0, 0)
        title_window.bkgd(curses.color_pair(2))
        title_window.attron(curses.color_pair(2))

        # Menu logic
        option = 0
        options = []

        while True:
            if self.current_state == "idle":
                options = [self.menuItems['RECORD'], self.menuItems['QUIT']]
            elif self.current_state == "recording":
                options = [self.menuItems['STOP'], self.menuItems['QUIT']]
            elif self.current_state == "transcribing":
                options = [self.menuItems['QUIT']]
            elif self.current_state == "summarizing":
                options = [self.menuItems['QUIT']]
            elif self.current_state == "error":
                options = [self.menuItems['QUIT']]
            else:
                options = [self.menuItems['QUIT']]
            stdscr.clear()
            title_window.clear()
            ASCII_line_length = 143
            offset = (curses.COLS - ASCII_line_length) // 2
            title_window.addstr(0, offset,'''                                                                                                                 .~~~~.              ''')
            title_window.addstr(1, offset,'''.d88888b    dP                                                                  dP                              {  _  _|             ''')
            title_window.addstr(2, offset,'''88.    "'   88                                                                  88                              lv(◕ |◕)             ''')
            title_window.addstr(3, offset,'''`Y88888b. d8888P .d8888b. 88d888b. .d8888b. .d8888b. 88d888b. .d8888b. 88d888b. 88d888b. .d8888b. 88d888b.       l  ‿‿ j             ''')
            title_window.addstr(4, offset,'''      `8b   88   88ooood8 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88ooood8 88'  `88    _.-/\ - /\-.           ''')
            title_window.addstr(5, offset,'''d8'   .8P   88   88.  ... 88    88 88.  .88 88.  .88 88       88.  .88 88.  .88 88    88 88.  ... 88         r   \_\ /_/  l          ''')
            title_window.addstr(6, offset,''' Y88888P    dP   `88888P' dP    dP `88888P' `8888P88 dP       `88888P8 88Y888P' dP    dP `88888P' dP         |  `---.--.`.--.        ''')
            title_window.addstr(7, offset,'''                                                 .88                   88          .-. .-. -.-               `------`\__''__' .--.   ''')
            title_window.addstr(8, offset,'''                                             d8888P                    dP          \_- |-'  |                         .------'^\  \  ''')
            title_window.addstr(9, offset,'''                                                                                                                      \_______| |  | ''')
            title_window.addstr(10, offset,'  ')

            stdscr.refresh()
            title_window.refresh()

            separator = "━" * curses.COLS

            stdscr.addstr(10, 0, separator)
            stdscr.addstr(11, 5, "Use arrow keys to navigate, Enter to select")
            stdscr.addstr(13, 5, "Current state: " + self.current_state)

            for i in range(len(options)):
                if i == option:
                    self.draw_menu_item(stdscr, 15 + i * 4, 5, options[i], option == i)
                else:
                    self.draw_menu_item(stdscr, 15 + i * 4, 5, options[i], option == i)

            key = stdscr.getch()

            if key == curses.KEY_UP:
                option = (option - 1) % len(options)
            elif key == curses.KEY_DOWN:
                option = (option + 1) % len(options)
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if option == self.findIndex(options, self.menuItems['RECORD']):
                    self.start_recording_wrapper()
                elif option == self.findIndex(options, self.menuItems['STOP']):
                    self.stop_recording_wrapper()
                elif option == self.findIndex(options, self.menuItems['QUIT']):
                    break
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
