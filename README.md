Here’s a complete, runnable Python example showing how to use the curses module to handle mouse events in a terminal application.
It demonstrates enabling mouse support, capturing clicks, and displaying their coordinates.

Pythonimport curses

def main(stdscr):
    # Clear screen
    stdscr.clear()

    # Enable keypad mode to capture special keys
    stdscr.keypad(True)

    # Enable mouse events (all buttons)
    curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

    # Optional: make cursor invisible
    curses.curs_set(0)

    # Instructions
    stdscr.addstr(0, 0, "Click anywhere or press 'q' to quit.")
    stdscr.refresh()

    while True:
        try:
            key = stdscr.getch()

            # Exit on 'q'
            if key == ord('q'):
                break

            # Handle mouse events
            if key == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, bstate = curses.getmouse()
                    stdscr.addstr(2, 0, f"Mouse clicked at ({mx}, {my}) - State: {bstate}   ")
                    stdscr.refresh()
                except curses.error:
                    # This can happen if getmouse() fails
                    stdscr.addstr(3, 0, "Mouse event error.")
                    stdscr.refresh()

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    curses.wrapper(main)


How It Works


curses.mousemask(...)
Enables mouse event reporting.
ALL_MOUSE_EVENTS captures clicks, scrolls, and movements;
REPORT_MOUSE_POSITION reports movement events.


curses.KEY_MOUSE
Returned by getch() when a mouse event occurs.


curses.getmouse()
Returns a tuple:
(id, x, y, z, bstate)

x, y: coordinates
bstate: bitmask describing which button was pressed/released.



Error Handling
curses.error is caught in case getmouse() fails.



Run Instructions
Save as mouse_demo.py and run in a terminal (not in IDLE or Windows cmd without proper terminal emulation):
Bashpython3 mouse_demo.py


✅ This code works in Linux/macOS terminals and in Windows if using a terminal that supports mouse reporting (e.g., Windows Terminal with WSL).
If you want, I can extend this example to detect double-clicks and scroll wheel events in curses.
Do you want me to make that version?
