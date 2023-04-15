import subprocess

# Define the command to run
command = ['x-terminal-emulator', '-e', 'python3', 'src/main_curses.py']

# Open a new terminal window and run the command
subprocess.Popen(command)