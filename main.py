import os
import subprocess

# Get the current working directory
cwd = os.getcwd()

# Define the command to run
path = 'src/main.py'

# Get the user's shell
user_shell = os.environ.get('SHELL', '/bin/bash').split('/')[-1]

# Define the appropriate shell option to skip the initialization files
skip_rc_option = '--noprofile --norc' if user_shell == 'bash' else '--no-rcs'

# Define the AppleScript command to open a new Terminal window
applescript_command = f'''
tell application "Terminal"
    set newWindow to do script "{user_shell} {skip_rc_option} -c 'python3 {os.path.join(cwd, path)}'"
    set number of columns of newWindow to 200
    set number of rows of newWindow to 60
    activate
end tell
'''

# Open a new Terminal window and run the command
subprocess.Popen(['osascript', '-e', applescript_command])
