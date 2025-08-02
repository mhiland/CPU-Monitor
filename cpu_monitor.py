import curses
import subprocess
import re
import os
import time

# Mouse/scroll event codes (may vary by terminal; update as needed)
MOUSE_SCROLL_CODES = (curses.KEY_MOUSE, 410, 411, 412, 413, 414, 415)

def get_lscpu_info():
    try:
        result = subprocess.run(['lscpu'], capture_output=True, text=True, check=True)
        info = {}
        for line in result.stdout.splitlines():
            if ':' in line:
                key, val = map(str.strip, line.split(':', 1))
                info[key] = val
        return info
    except Exception as e:
        import sys
        print(f"Error in get_lscpu_info: {e}", file=sys.stderr)
        return {}

def parse_cpu_frequencies():
    freqs = {}
    cpu_id = None
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('processor'):
                    cpu_id = int(line.split(':')[1].strip())
                elif line.startswith('cpu MHz') and cpu_id is not None:
                    freq = float(line.split(':')[1].strip())
                    freqs[cpu_id] = freq
    except OSError as e:
        print(f"Error reading /proc/cpuinfo: {e}")
    except Exception as e:
        print(f"Unexpected error in parse_cpu_frequencies: {e}")
    return freqs

def read_temperatures():
    temps = {}
    hwmon_path = '/sys/class/hwmon'
    try:
        for hwmon in os.listdir(hwmon_path):
            name_path = os.path.join(hwmon_path, hwmon, 'name')
            if os.path.exists(name_path):
                with open(name_path) as f:
                    label = f.read().strip()
                for i in range(10):
                    temp_path = os.path.join(hwmon_path, hwmon, f'temp{i}_input')
                    if os.path.exists(temp_path):
                        with open(temp_path) as f:
                            temp_milli = int(f.read().strip())
                            temps[f"{label}_temp{i}"] = temp_milli / 1000
    except Exception:
        pass
    return temps

def alphanum_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split('([0-9]+)', s)]

def safe_addstr(stdscr, y, x, text, max_y, max_x):
    """Safely add string to screen with bounds checking"""
    if y >= max_y - 1 or x >= max_x:
        return False
    try:
        # Truncate text if it would exceed screen width
        if x + len(text) >= max_x:
            text = text[:max_x - x - 1]
        stdscr.addstr(y, x, text, curses.color_pair(1))
        return True
    except curses.error:
        return False

def draw(stdscr):
    curses.curs_set(0)
    stdscr.nodelay(False)  # Block until input or timeout
    stdscr.timeout(1000)   # 1 second timeout

    # Initialize colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1)  # Green text on default background
    
    # Disable mouse events completely
    try:
        curses.mousemask(0)
        curses.mouseinterval(0)
    except:
        pass

    lscpu_info = get_lscpu_info()
    model_name = lscpu_info.get('Model name', 'Unknown CPU')

    last_update = 0
    freqs = {}
    temps = {}

    while True:
        current_time = time.time()

        # Only update data every second, regardless of input events
        if current_time - last_update >= 1.0:
            freqs = parse_cpu_frequencies()
            temps = read_temperatures()
            last_update = current_time
            need_refresh = True
        else:
            need_refresh = False

        # Always redraw the screen
        stdscr.erase()
        max_y, max_x = stdscr.getmaxyx()

        line = 0
        safe_addstr(stdscr, line, 0, f"CPU Model: {model_name}", max_y, max_x)
        line += 1

        safe_addstr(stdscr, line, 0, "-" * min(40, max_x-1), max_y, max_x)
        line += 1
        for cpu_id in sorted(freqs.keys()):
            if line >= max_y - 2:  # Leave room for exit message
                break
            safe_addstr(stdscr, line, 2, f"Core {cpu_id:2}: {freqs[cpu_id]:7.2f} MHz", max_y, max_x)
            line += 1

        # Show additional CPU info first (more important)
        line += 1
        if line < max_y - 1:
            safe_addstr(stdscr, line, 0, "Additional CPU Info:", max_y, max_x)
            line += 1

            # Display additional lscpu fields
            additional_fields = [
                "Thread(s) per core",
                "Core(s) per socket", 
                "Stepping",
                "Frequency boost",
                "CPU(s) scaling MHz",
                "CPU max MHz",
                "CPU min MHz"
            ]

            for field in additional_fields:
                if line >= max_y - 2:
                    break
                if field in lscpu_info:
                    safe_addstr(stdscr, line, 2, f"{field}: {lscpu_info[field]}", max_y, max_x)
                    line += 1

        # Show temperatures if there's space
        line += 1
        if line < max_y - 2:
            safe_addstr(stdscr, line, 0, "Temperatures (°C):", max_y, max_x)
            line += 1

            for label in sorted(temps.keys(), key=alphanum_sort_key):
                if line >= max_y - 2:
                    break
                safe_addstr(stdscr, line, 2, f"{label}: {temps[label]:5.1f}", max_y, max_x)
                line += 1

        # Always show exit message at bottom - ensure it's visible
        try:
            stdscr.addstr(max_y - 1, 0, "Press 'q' to exit", curses.color_pair(1))
        except curses.error:
            # If bottom line fails, try one line up
            try:
                stdscr.addstr(max_y - 2, 0, "Press 'q' to exit", curses.color_pair(1))
            except curses.error:
                pass

        stdscr.refresh()

        # Handle input - only check for quit
        try:
            key = stdscr.getch()
            if key in (ord('q'), ord('Q')):
                break
            # Explicitly ignore mouse wheel and other events
            elif key in (curses.KEY_MOUSE, 410, 411, 412, 413, 414, 415):  # Various mouse/scroll codes
                continue
        except curses.error:
            continue

def main():
    if not os.path.exists('/proc/cpuinfo'):
        print("This script only works on Linux with /proc/cpuinfo")
        return

    # Use curses.wrapper to safely initialize and clean up the curses environment
    curses.wrapper(draw)

if __name__ == "__main__":
    main()

