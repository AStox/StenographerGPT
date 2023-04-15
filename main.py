import os
import subprocess

# Get the current working directory
cwd = os.getcwd()

# Define the command to run
path = 'src/main.py'

# Define the AppleScript command to open a new Terminal window
applescript_command = f'tell application "Terminal" to do script "python3 {os.path.join(cwd, path)}"'

# Open a new Terminal window and run the command
subprocess.Popen(['osascript', '-e', applescript_command])
subprocess.Popen(['osascript', '-e', 'tell application "Terminal" to activate'])
