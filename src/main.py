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
        self.output = ""
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
        curses.init_color(3, 1000, 0, 0)  # RED

        curses.init_pair(1, 1, 2) # BLACK ON GREEN
        curses.init_pair(2, 2, 1) # GREEN ON BLACK
        curses.init_pair(3, 3, 1) # RED ON BLACK

        # Set screen attributes
        stdscr.bkgd(curses.color_pair(2))
        stdscr.attron(curses.color_pair(2))

        # Set Title window attributes
        title_window_height = 11
        title_window_width = curses.COLS + 1
        title_window = curses.newwin(title_window_height, title_window_width, 0, 0)
        title_window.bkgd(curses.color_pair(2))
        title_window.attron(curses.color_pair(2))

        # Set Menu window attributes
        self.menu_window_height = curses.LINES - title_window_height
        self.menu_window_width = curses.COLS // 2
        self.menu_window = curses.newwin(self.menu_window_height, self.menu_window_width, title_window_height, 0)
        self.menu_window.bkgd(curses.color_pair(2))
        self.menu_window.attron(curses.color_pair(2))

        # Set Output window attributes
        self.output_window_height = curses.LINES - title_window_height
        self.output_window_width = curses.COLS // 2
        self.output_window = curses.newwin(self.output_window_height,  self.output_window_width, title_window_height, self.menu_window_width + 1)
        self.output_window.bkgd(curses.color_pair(2))
        self.output_window.attron(curses.color_pair(2))

        # Set Overlay window attributes
        overlay_window_height = curses.LINES - title_window_height + 1
        overlay_window_width = curses.COLS
        overlay_window = curses.newwin(overlay_window_height, overlay_window_width, title_window_height - 1, 0)
        overlay_window.bkgd(curses.color_pair(2))
        overlay_window.attron(curses.color_pair(2))

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
            stdscr.refresh()

            title_window.clear()
            ASCII_line_length = 143
            offset = (curses.COLS - ASCII_line_length) // 2
            title_window.addstr(0, offset,'''                                                                                                                 .~~~~.              ''')
            title_window.addstr(1, offset,'''.d88888b    dP                                                                  dP                              {  _  _|             ''')
            title_window.addstr(2, offset,'''88.    "'   88                                                                  88                              lv ◕ |◕)             ''')
            title_window.addstr(3, offset,'''`Y88888b. d8888P .d8888b. 88d888b. .d8888b. .d8888b. 88d888b. .d8888b. 88d888b. 88d888b. .d8888b. 88d888b.       l  ‿‿ j             ''')
            title_window.addstr(4, offset,'''      `8b   88   88ooood8 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88'  `88 88ooood8 88'  `88    _.-/\ - /\-.           ''')
            title_window.addstr(5, offset,'''d8'   .8P   88   88.  ... 88    88 88.  .88 88.  .88 88       88.  .88 88.  .88 88    88 88.  ... 88         r   \_\ /_/  |          ''')
            title_window.addstr(6, offset,''' Y88888P    dP   `88888P' dP    dP `88888P' `8888P88 dP       `88888P8 88Y888P' dP    dP `88888P' dP         |  `---.--.`.--.        ''')
            title_window.addstr(7, offset,'''                                                 .88                   88          .-. .-. -.-               `------`\__''__' .--.   ''')
            title_window.addstr(8, offset,'''                                             d8888P                    dP          \_- |-'  |                         .------'^\  \  ''')
            title_window.addstr(9, offset,'''                                                                                                                      \_______| |  | ''')

            title_window.refresh()

            overlay_window.clear()
            separator = "━" * (curses.COLS // 2) + "┯" + "━" * (curses.COLS // 2)
            overlay_window.addstr(0, 0, separator)
            for i in range(1, self.menu_window_height + 1):
                overlay_window.addstr(i, self.menu_window_width, "│")
            overlay_window.refresh()

            self.refresh_menu_window()

            self.refresh_output_window()

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

    def refresh_menu_window(self):
        self.menu_window.clear()
        self.menu_window.addstr(0, 5, "Use arrow keys to navigate, Enter to select")
        self.menu_window.addstr(2, 5, "Current state: " + self.current_state)
        self.menu_window.refresh()

    def refresh_output_window(self):
        self.output_window.clear()
        if (self.current_state == "error"):
            self.output_window.attron(curses.color_pair(3))
            self.output_window.addstr(0, 5, "ERROR")
            self.output_window.addstr(2, 5, self.output)
            self.output_window.attroff(curses.color_pair(3))
        else:
            self.output_window.addstr(0, 5, "Output")
            self.output_window.addstr(2, 5, self.output)
            self.output_window.refresh()

    def start_recording_wrapper(self):
        try:
            self.current_state = "recording"
            self.refresh_menu_window()
            switch_to_blackhole()
            self.current_archive_directory = create_timestamped_directory("archive")
            start_recording(self.current_archive_directory)
        except Exception as e:
            # output = str(e)
            self.output = traceback.format_exc()
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
            self.refresh_menu_window()
            transcription = transcribe_audio(merged_output)

            transcript_file = os.path.join(output_directory, "transcript.txt")
            with open(transcript_file, "w") as f:
                f.write(transcription)
            print('Transcription:', transcription)
            self.output = transcription
            self.refresh_output_window()

            # self.current_state = "summarizing"
            # self.refresh_menu_window()
            # summary_file = os.path.join(output_directory, "summary.txt")
            # summary = summarize_text(transcription)
            # with open(summary_file, "w") as f:
            #     f.write(summary)
            # print('Summary:', summary)

            self.current_state = "idle"
            self.refresh_menu_window()

        except Exception as e:
            self.current_state = "error"
            self.refresh_menu_window()
            self.output = traceback.format_exc()

if __name__ == "__main__":
    Stenographer()
