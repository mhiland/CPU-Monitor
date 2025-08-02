# CPU Monitor

A real-time CPU monitoring tool for Linux that displays per-core frequencies, temperatures, and detailed CPU information in a terminal interface.

## Features

- **Real-time monitoring**: Updates every second with current CPU data
- **Per-core frequencies**: Shows individual core frequencies in MHz
- **Temperature monitoring**: Displays temperatures from various sensors (CPU, GPU, NVMe, etc.)
- **Detailed CPU info**: Shows additional CPU specifications from `lscpu`
- **Terminal UI**: Clean, organized display using ncurses
- **Responsive**: Adapts to terminal size with proper bounds checking

## Requirements

- Linux operating system
- Python 3.x
- `lscpu` command available
- Access to `/proc/cpuinfo` and `/sys/class/hwmon/`

## Installation

1. Clone or download the `cpu_monitor.py` file
2. Make it executable (optional):
   ```bash
   chmod +x cpu_monitor.py
   ```

## Usage

Run the monitor:
```bash
python3 cpu_monitor.py
```

Press `q` to quit the application.

## Example Output

```
CPU Model: AMD Ryzen 9 9950X 16-Core Processor
----------------------------------------
Per-Core Frequencies (MHz):
  Core  0: 3728.92
  Core  1: 3728.94
  Core  2: 3728.93
  Core  3: 3728.94
  Core  4: 3728.97
  Core  5: 3728.97
  Core  6: 3728.95
  Core  7: 3728.95
  Core  8: 3773.77
  Core  9: 3773.78
  Core 10: 3773.79
  Core 11: 3773.79
  Core 12: 3767.92
  Core 13:  624.19
  Core 14:  624.19
  Core 15:  624.19
  Core 16: 3728.96
  Core 17: 3729.31
  Core 18: 3728.95
  Core 19: 3728.95
  Core 20: 3728.94
  Core 21: 3728.92
  Core 22: 3728.96
  Core 23: 3728.96
  Core 24: 3773.79
  Core 25: 3773.75
  Core 26: 3773.80
  Core 27: 3773.76
  Core 28: 3774.49
  Core 29:  624.19
  Core 30:  624.19
  Core 31:  624.19

Temperatures (°C):
  amdgpu_temp1:  68.0
  k10temp_temp1:  85.1
  nvme_temp1:  50.9
  nvme_temp2:  72.8
  nvme_temp3:  49.9
  r8169_0_a00:00_temp1:  54.5
  spd5118_temp1:  41.2

Additional CPU Info:
  Thread(s) per core: 2
  Core(s) per socket: 16
  Stepping: 0
  Frequency boost: enabled
  CPU(s) scaling MHz: 56%
  CPU max MHz: 5756.4521
  CPU min MHz: 624.1940

Press 'q' to exit
```

## Data Sources

- **CPU Info**: Retrieved from `lscpu` command
- **Per-core frequencies**: Read from `/proc/cpuinfo`
- **Temperatures**: Read from `/sys/class/hwmon/` sensors


## Supported Temperature Sensors

The tool automatically detects and displays temperatures from various hardware monitoring sources:
- CPU package temperatures (k10temp, coretemp)
- GPU temperatures (amdgpu, nvidia)
- NVMe SSD temperatures
- Network adapter temperatures
- Memory module temperatures (spd5118)
- Other available hwmon sensors

## Notes

- Requires root privileges on some systems to access certain temperature sensors
- Temperature availability depends on your hardware and kernel drivers
- The display adapts to terminal size - resize your terminal if content appears truncated
