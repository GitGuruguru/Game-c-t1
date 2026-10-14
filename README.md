Got it — you want to capture multiple key inputs in Python using curses and store them in an array for later use.
Here’s a complete, runnable example that demonstrates how to do this safely and robustly:

Pythonimport curses

def main(stdscr):
    # Turn off automatic echoing of keys to the screen
    curses.noecho()
    # React to keys instantly without requiring Enter
    curses.cbreak()
    # Enable special keys (e.g., arrow keys)
    stdscr.keypad(True)

    # Instructions
    stdscr.addstr(0, 0, "Press keys (ESC to quit).")
    stdscr.addstr(1, 0, "Captured keys will be stored in an array.")
    stdscr.refresh()

    key_inputs = []  # Array to store key presses

    while True:
        try:
            key = stdscr.getch()  # Get key code
            key_inputs.append(key)  # Store in array

            # Display last key pressed
            stdscr.addstr(3, 0, f"Last key code: {key}   ")
            stdscr.addstr(4, 0, f"Keys so far: {key_inputs}   ")
            stdscr.refresh()

            # Exit on ESC key
            if key == 27:  # ESC key code
                break

        except Exception as e:
            stdscr.addstr(6, 0, f"Error: {e}")
            stdscr.refresh()

    # After loop, display final array
    stdscr.clear()
    stdscr.addstr(0, 0, "Final captured keys:")
    stdscr.addstr(1, 0, str(key_inputs))
    stdscr.refresh()
    stdscr.getch()  # Wait before exit

    # Restore terminal settings
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()

# Run curses application
if __name__ == "__main__":
    curses.wrapper(main)


How It Works


Setup:

curses.noecho() prevents automatic printing of keys.
curses.cbreak() allows immediate key reading without pressing Enter.
stdscr.keypad(True) enables reading special keys like arrows.



Capturing Keys:

stdscr.getch() reads a single key code.
Each key code is appended to key_inputs (our array).



Exit Condition:

ESC key (27) stops the loop.



Cleanup:

Restores terminal settings before exit.




Example Run
Press keys (ESC to quit).
Captured keys will be stored in an array.
Last key code: 97
Keys so far: [97]

(Here 97 is 'a' in ASCII.)

✅ This code works for both normal and special keys (arrow keys, function keys, etc.) and stores them in an array for later processing.

If you want actual characters instead of numeric key codes, I can give you a version using getkey() that stores strings like "a", "KEY_LEFT", etc.
Do you want me to prepare that version?
