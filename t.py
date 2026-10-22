import curses

def main(stdscr):
    # Clear screen
    stdscr.clear()

    # Enable keypad mode to capture special keys
    stdscr.keypad(True)

    # Enable mouse events
   

    # Optional: make cursor invisible
    curses.curs_set(0)

    stdscr.addstr(0, 0, "Click anywhere or press 'q' to quit.")
    stdscr.refresh()

    while True:
        try:
            key = stdscr.getch()

            # Exit on 'q'
            if key == ord('q'):
                break

            # Check for mouse event
            if key == curses.KEY_MOUSE:
                _, x, y, _, button_state = curses.getmouse()

                # Display mouse click info
                stdscr.addstr(2, 0, f"Mouse clicked at X={x}, Y={y}, State={button_state}   ")
                stdscr.refresh()

        except curses.error:
            # Ignore curses errors (e.g., writing outside screen bounds)
            pass

# Run curses application
if __name__ == "__main__":
    curses.wrapper(main)
