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

def get_base_frequency():
    """Get base CPU frequency from ACPI CPPC or CPUfreq sysfs interface"""
    try:
        # Try ACPI CPPC nominal frequency first (more accurate for AMD)
        with open('/sys/devices/system/cpu/cpu0/acpi_cppc/nominal_freq', 'r') as f:
            base_freq_mhz = int(f.read().strip())
            # Convert MHz to GHz
            base_freq_ghz = base_freq_mhz / 1000
            return f"{base_freq_ghz:.2f} GHz"
    except (OSError, ValueError):
        try:
            # Fallback to CPUfreq max frequency
            with open('/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq', 'r') as f:
                base_freq_khz = int(f.read().strip())
                # Convert kHz to GHz
                base_freq_ghz = base_freq_khz / 1000000
                return f"{base_freq_ghz:.2f} GHz"
        except (OSError, ValueError):
            return None

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

def parse_cpu_stats():
    """Parse CPU usage statistics from /proc/stat"""
    stats = {}
    try:
        with open('/proc/stat', 'r') as f:
            for line in f:
                if line.startswith('cpu') and line[3:4].isdigit():
                    parts = line.split()
                    cpu_id = int(parts[0][3:])  # Extract number from 'cpu0', 'cpu1', etc.
                    times = [int(x) for x in parts[1:]]
                    stats[cpu_id] = times
    except (OSError, ValueError, IndexError) as e:
        print(f"Error reading /proc/stat: {e}")
    return stats

def calculate_cpu_usage(prev_stats, curr_stats):
    """Calculate CPU usage percentage for each core"""
    usage = {}
    for cpu_id in curr_stats:
        if cpu_id not in prev_stats:
            continue

        prev_times = prev_stats[cpu_id]
        curr_times = curr_stats[cpu_id]

        # Calculate deltas
        prev_total = sum(prev_times)
        curr_total = sum(curr_times)

        prev_idle = prev_times[3]  # idle is the 4th field (index 3)
        curr_idle = curr_times[3]

        total_delta = curr_total - prev_total
        idle_delta = curr_idle - prev_idle

        if total_delta > 0:
            usage_percent = ((total_delta - idle_delta) / total_delta) * 100
            usage[cpu_id] = max(0, min(100, usage_percent))  # Clamp between 0-100
        else:
            usage[cpu_id] = 0

    return usage

def read_sensors():
    sensors = {'temps': {}, 'fans': {}, 'voltages': {}, 'power': {}, 'pwm': {}}
    hwmon_path = '/sys/class/hwmon'
    try:
        for hwmon in os.listdir(hwmon_path):
            hwmon_dir = os.path.join(hwmon_path, hwmon)
            name_path = os.path.join(hwmon_dir, 'name')
            if os.path.exists(name_path):
                with open(name_path) as f:
                    device_name = f.read().strip()
                
                # Get all files in hwmon directory
                for filename in os.listdir(hwmon_dir):
                    file_path = os.path.join(hwmon_dir, filename)
                    
                    # Temperature sensors
                    if filename.startswith('temp') and filename.endswith('_input'):
                        try:
                            with open(file_path) as f:
                                temp_milli = int(f.read().strip())
                                temp_id = filename[4:-6]  # Extract number from temp{N}_input
                                
                                # Try to get sensor label
                                label_path = os.path.join(hwmon_dir, f'temp{temp_id}_label')
                                if os.path.exists(label_path):
                                    try:
                                        with open(label_path) as label_f:
                                            label = label_f.read().strip()
                                            sensor_name = f"{device_name}_{label}"
                                    except OSError:
                                        sensor_name = f"{device_name}_temp{temp_id}"
                                else:
                                    sensor_name = f"{device_name}_temp{temp_id}"
                                
                                sensors['temps'][sensor_name] = temp_milli / 1000
                        except (ValueError, OSError):
                            continue
                    
                    # Fan sensors
                    elif filename.startswith('fan') and filename.endswith('_input'):
                        try:
                            with open(file_path) as f:
                                fan_rpm = int(f.read().strip())
                                fan_id = filename[3:-6]  # Extract number from fan{N}_input
                                
                                # Try to get fan label
                                label_path = os.path.join(hwmon_dir, f'fan{fan_id}_label')
                                if os.path.exists(label_path):
                                    try:
                                        with open(label_path) as label_f:
                                            label = label_f.read().strip()
                                            sensor_name = f"{device_name}_{label}"
                                    except OSError:
                                        sensor_name = f"{device_name}_fan{fan_id}"
                                else:
                                    sensor_name = f"{device_name}_fan{fan_id}"
                                
                                sensors['fans'][sensor_name] = fan_rpm
                        except (ValueError, OSError):
                            continue
                    
                    # Voltage sensors
                    elif filename.startswith('in') and filename.endswith('_input'):
                        try:
                            with open(file_path) as f:
                                voltage_milli = int(f.read().strip())
                                in_id = filename[2:-6]  # Extract number from in{N}_input
                                
                                # Try to get voltage label
                                label_path = os.path.join(hwmon_dir, f'in{in_id}_label')
                                if os.path.exists(label_path):
                                    try:
                                        with open(label_path) as label_f:
                                            label = label_f.read().strip()
                                            sensor_name = f"{device_name}_{label}"
                                    except OSError:
                                        sensor_name = f"{device_name}_in{in_id}"
                                else:
                                    sensor_name = f"{device_name}_in{in_id}"
                                
                                sensors['voltages'][sensor_name] = voltage_milli / 1000
                        except (ValueError, OSError):
                            continue
                    
                    # Power sensors
                    elif filename.startswith('power') and filename.endswith('_input'):
                        try:
                            with open(file_path) as f:
                                power_micro = int(f.read().strip())
                                power_id = filename[5:-6]  # Extract number from power{N}_input
                                
                                # Try to get power label
                                label_path = os.path.join(hwmon_dir, f'power{power_id}_label')
                                if os.path.exists(label_path):
                                    try:
                                        with open(label_path) as label_f:
                                            label = label_f.read().strip()
                                            sensor_name = f"{device_name}_{label}"
                                    except OSError:
                                        sensor_name = f"{device_name}_power{power_id}"
                                else:
                                    sensor_name = f"{device_name}_power{power_id}"
                                
                                sensors['power'][sensor_name] = power_micro / 1000000
                        except (ValueError, OSError):
                            continue
                    
                    # PWM sensors (fan speed control)
                    elif filename.startswith('pwm') and not '_' in filename:
                        try:
                            with open(file_path) as f:
                                pwm_value = int(f.read().strip())
                                pwm_id = filename[3:]  # Extract number from pwm{N}
                                
                                # Convert PWM value (0-255) to percentage
                                pwm_percentage = (pwm_value / 255.0) * 100
                                sensors['pwm'][f"{device_name}_pwm{pwm_id}"] = pwm_percentage
                        except (ValueError, OSError):
                            continue
    except Exception:
        pass
    return sensors

def alphanum_sort_key(s):
    return [int(t) if t.isdigit() else t.lower() for t in re.split('([0-9]+)', s)]

def organize_fan_data(sensors):
    """Organize fan data with associated temperatures and filter main temp sensors"""
    fan_cooling_data = []
    essential_temps = {}
    
    # Essential temperature sensors to keep in main temp section
    essential_keywords = ['k10temp', 'nvme', 'amdgpu', 'spd5118', 'r8169', 'coretemp', 
                         'systin', 'cputin', 'tsi0_temp', 'smbusmaster', 'auxtin']
    
    # Copy essential temperatures to main section (filter out invalid readings)
    for temp_name, temp_value in sensors['temps'].items():
        if any(keyword in temp_name.lower() for keyword in essential_keywords):
            # Filter out clearly invalid temperatures
            if temp_value > 0 and temp_value < 150:  # Reasonable temperature range
                essential_temps[temp_name] = temp_value
    
    # Group fans by device and try to associate with temps
    fan_devices = {}
    for fan_name, fan_rpm in sensors['fans'].items():
        # Extract device name (e.g., 'nct6799' from 'nct6799_fan1')
        if '_fan' in fan_name:
            device_name = fan_name.split('_fan')[0]
            fan_id = fan_name.split('_fan')[1]
            
            if device_name not in fan_devices:
                fan_devices[device_name] = []
            
            # Look for corresponding PWM percentage
            pwm_percentage = None
            pwm_key = f"{device_name}_pwm{fan_id}"
            if pwm_key in sensors['pwm']:
                pwm_percentage = sensors['pwm'][pwm_key]
            
            fan_devices[device_name].append({
                'name': f"Fan{fan_id}",
                'rpm': fan_rpm,
                'pwm_percentage': pwm_percentage
            })
    
    # Convert to display format with PWM percentages
    for device_name, fans in fan_devices.items():
        for fan_data in sorted(fans, key=lambda x: x['name']):
            if fan_data['pwm_percentage'] is not None:
                # Show N/A for PWM when RPM is 0 (likely disconnected fan)
                if fan_data['rpm'] == 0:
                    display_text = f"{fan_data['name']}: {fan_data['rpm']:4.0f}rpm (N/A)"
                else:
                    display_text = f"{fan_data['name']}: {fan_data['rpm']:4.0f}rpm ({fan_data['pwm_percentage']:3.0f}%)"
            else:
                display_text = f"{fan_data['name']}: {fan_data['rpm']:4.0f}rpm"
            fan_cooling_data.append(display_text)
    
    return fan_cooling_data, essential_temps

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

def display_two_column_sections(stdscr, sections_data, start_line, max_y, max_x):
    """Display sensor sections in two columns side by side, keeping sections together"""
    left_col_width = max_x // 2 - 2  # Leave some space between columns
    right_col_x = max_x // 2 + 1
    
    # Prepare sections as separate blocks
    left_sections = []
    right_sections = []
    
    # Manually assign sections to columns to keep them together
    section_count = len(sections_data)
    
    if section_count >= 5:
        # If we have 5 sections: Temps, Fans, Additional CPU in left; Voltages, Power in right
        left_sections = sections_data[:3]  # Temperatures, Fan Speeds, Additional CPU Info
        right_sections = sections_data[3:]  # Voltages, Power
    elif section_count == 4:
        # If we have 4 sections: Temps, Fans in left; Voltages, Power in right
        left_sections = sections_data[:2]  # Temperatures, Fans & Cooling
        right_sections = sections_data[2:]  # Voltages, Power
    elif section_count == 3:
        # If we have 3 sections: First 2 in left, last in right
        left_sections = sections_data[:2]
        right_sections = sections_data[2:]
    elif section_count == 2:
        # If we have 2 sections: One in each column
        left_sections = sections_data[:1]
        right_sections = sections_data[1:]
    else:
        # If we have 1 section: Put it in left column
        left_sections = sections_data
        right_sections = []
    
    def format_sections(sections):
        """Convert sections to display lines"""
        lines = []
        for section_title, section_items in sections:
            if section_items:
                lines.append(f"{section_title}")
                for item in section_items:
                    lines.append(f"  {item}")
                lines.append("")  # Empty line between sections
        # Remove last empty line if exists
        if lines and lines[-1] == "":
            lines.pop()
        return lines
    
    left_lines = format_sections(left_sections)
    right_lines = format_sections(right_sections)
    
    current_line = start_line
    
    # Display left column
    for i, line_text in enumerate(left_lines):
        if current_line + i >= max_y - 2:
            break
        # Truncate if too long for left column
        if len(line_text) > left_col_width:
            line_text = line_text[:left_col_width-3] + "..."
        safe_addstr(stdscr, current_line + i, 0, line_text, max_y, max_x)
    
    # Display right column
    for i, line_text in enumerate(right_lines):
        if current_line + i >= max_y - 2:
            break
        # Truncate if too long for right column
        available_width = max_x - right_col_x - 1
        if len(line_text) > available_width:
            line_text = line_text[:available_width-3] + "..."
        safe_addstr(stdscr, current_line + i, right_col_x, line_text, max_y, max_x)
    
    # Return the line after the longest column
    return current_line + max(len(left_lines), len(right_lines))

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

    # Take initial readings and wait 1 second to have data ready immediately
    prev_cpu_stats = parse_cpu_stats()
    time.sleep(1)

    last_update = 0
    freqs = {}
    sensors = {'temps': {}, 'fans': {}, 'voltages': {}, 'power': {}}
    cpu_usage = {}

    while True:
        current_time = time.time()

        # Only update data every second, regardless of input events
        if current_time - last_update >= 1.0:
            freqs = parse_cpu_frequencies()
            sensors = read_sensors()

            # Get CPU stats and calculate usage
            curr_cpu_stats = parse_cpu_stats()
            cpu_usage = calculate_cpu_usage(prev_cpu_stats, curr_cpu_stats)
            prev_cpu_stats = curr_cpu_stats

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
        
        # Use two-column layout for CPU cores if more than 8 cores
        sorted_cpu_ids = sorted(freqs.keys())
        if len(sorted_cpu_ids) > 8:
            # Two-column CPU layout
            left_col_width = max_x // 2 - 2
            right_col_x = max_x // 2 + 1
            
            # Split cores evenly between columns
            mid_point = (len(sorted_cpu_ids) + 1) // 2
            left_cores = sorted_cpu_ids[:mid_point]
            right_cores = sorted_cpu_ids[mid_point:]
            
            start_line = line
            max_cores_per_column = max(len(left_cores), len(right_cores))
            
            # Display left column cores
            for i, cpu_id in enumerate(left_cores):
                if start_line + i >= max_y - 2:
                    break
                freq_text = f"Core {cpu_id:2}: {freqs[cpu_id]:7.2f} MHz"
                if cpu_id in cpu_usage:
                    freq_text += f" ({cpu_usage[cpu_id]:5.1f}%)"
                # Truncate if too long for left column
                if len(freq_text) > left_col_width:
                    freq_text = freq_text[:left_col_width-3] + "..."
                safe_addstr(stdscr, start_line + i, 2, freq_text, max_y, max_x)
            
            # Display right column cores
            for i, cpu_id in enumerate(right_cores):
                if start_line + i >= max_y - 2:
                    break
                freq_text = f"Core {cpu_id:2}: {freqs[cpu_id]:7.2f} MHz"
                if cpu_id in cpu_usage:
                    freq_text += f" ({cpu_usage[cpu_id]:5.1f}%)"
                # Truncate if too long for right column
                available_width = max_x - right_col_x - 1
                if len(freq_text) > available_width:
                    freq_text = freq_text[:available_width-3] + "..."
                safe_addstr(stdscr, start_line + i, right_col_x, freq_text, max_y, max_x)
            
            line = start_line + max_cores_per_column
        else:
            # Single column layout for 8 or fewer cores
            for cpu_id in sorted_cpu_ids:
                if line >= max_y - 2:  # Leave room for exit message
                    break
                freq_text = f"Core {cpu_id:2}: {freqs[cpu_id]:7.2f} MHz"
                if cpu_id in cpu_usage:
                    freq_text += f" ({cpu_usage[cpu_id]:5.1f}%)"
                safe_addstr(stdscr, line, 2, freq_text, max_y, max_x)
                line += 1

        # Organize fan data and filter temperatures
        fan_cooling_data, essential_temps = organize_fan_data(sensors)
        
        # Prepare sections for two-column display
        sections_for_columns = []
        
        # Essential temperatures
        if essential_temps:
            temp_items = [f"{name}: {value:5.1f}" for name, value in sorted(essential_temps.items(), key=lambda x: alphanum_sort_key(x[0]))]
            sections_for_columns.append(("Temperatures (°C):", temp_items))
        
        # Fan Speeds  
        if fan_cooling_data:
            sections_for_columns.append(("Fan Speeds (RPM):", fan_cooling_data))
        
        # Additional CPU Info (place after fans, before voltages for better grouping)
        additional_fields = [
            "Thread(s) per core",
            "Core(s) per socket", 
            "Stepping",
            "Frequency boost",
            "CPU(s) scaling MHz",
            "CPU max MHz",
            "CPU base MHz",  # Position between max and min
            "CPU min MHz"
        ]
        
        cpu_info_items = []
        base_freq = get_base_frequency()
        
        for field in additional_fields:
            if field == "CPU base MHz":
                # Insert base frequency here if available
                if base_freq:
                    cpu_info_items.append(f"{field}: {base_freq}")
            elif field in lscpu_info:
                cpu_info_items.append(f"{field}: {lscpu_info[field]}")
        
        if cpu_info_items:
            sections_for_columns.append(("Additional CPU Info:", cpu_info_items))
        
        # Voltages
        if sensors['voltages']:
            voltage_items = [f"{name}: {value:5.3f}" for name, value in sorted(sensors['voltages'].items(), key=lambda x: alphanum_sort_key(x[0]))]
            sections_for_columns.append(("Voltages (V):", voltage_items))
        
        # Power
        if sensors['power']:
            power_items = [f"{name}: {value:6.3f}" for name, value in sorted(sensors['power'].items(), key=lambda x: alphanum_sort_key(x[0]))]
            sections_for_columns.append(("Power (W):", power_items))
        
        # Display all sensor sections in two columns
        if sections_for_columns:
            line += 1
            line = display_two_column_sections(stdscr, sections_for_columns, line, max_y, max_x)

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
            elif key in MOUSE_SCROLL_CODES:
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
