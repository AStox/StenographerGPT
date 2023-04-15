import curses

# Define the menu function
def menu():
    # Initialize the curses library
    screen = curses.initscr()

    # Turn off echoing of keys, and enter cbreak mode,
    # where no buffering is performed on keyboard input
    curses.noecho()
    curses.cbreak()

    # Enable the keypad so the user can use arrow keys
    screen.keypad(True)

    # Define the menu options
    options = ["Option 1", "Option 2", "Option 3", "Exit"]

    # Set the initial selected option to 0
    selected_option = 0

    # Loop until the user selects "Exit"
    while True:
        # Clear the screen
        screen.clear()

        # Display the menu options
        for index, option in enumerate(options):
            # If this is the selected option, highlight it
            if index == selected_option:
                screen.addstr(index, 0, "> " + option, curses.A_REVERSE)
            else:
                screen.addstr(index, 0, "  " + option)

        # Get user input
        key = screen.getch()

        # Handle arrow key presses
        if key == curses.KEY_UP and selected_option > 0:
            selected_option -= 1
        elif key == curses.KEY_DOWN and selected_option < len(options) - 1:
            selected_option += 1
        elif key == curses.KEY_ENTER or key in [10, 13]:
            # If the user selects "Exit", exit the loop
            if selected_option == len(options) - 1:
                break
            # Otherwise, display the selected option and wait for input
            screen.clear()
            screen.addstr(0, 0, "You selected: " + options[selected_option])
            screen.addstr(2, 0, "Press any key to continue...")
            screen.getch()

    # Clean up the curses library
    curses.nocbreak()
    screen.keypad(False)
    curses.echo()
    curses.endwin()

# Call the menu function to start the program
menu()
