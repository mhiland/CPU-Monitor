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
- Access to `/proc/cpuinfo`, `/proc/stat` and `/sys/class/hwmon/`

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
  Core  0: 3774.78 MHz (100.0%)
  Core  1: 3774.74 MHz (100.0%)
  Core  2: 3774.68 MHz (100.0%)
  Core  3: 3774.51 MHz (100.0%)
  Core  4: 3774.75 MHz (100.0%)
  Core  5: 3774.78 MHz (100.0%)
  Core  6: 3774.63 MHz (100.0%)
  Core  7: 3774.75 MHz (100.0%)
  Core  8: 3820.64 MHz (100.0%)
  Core  9: 3821.13 MHz (100.0%)
  Core 10: 3821.10 MHz (100.0%)
  Core 11: 3820.66 MHz (100.0%)
  Core 12:  624.19 MHz (  1.0%)
  Core 13:  624.19 MHz (  0.0%)
  Core 14:  624.19 MHz (  0.0%)
  Core 15:  624.19 MHz (  0.0%)
  Core 16: 3774.74 MHz (100.0%)
  Core 17: 3774.62 MHz (100.0%)
  Core 18: 3774.65 MHz (100.0%)
  Core 19: 3774.79 MHz (100.0%)
  Core 20: 3774.66 MHz (100.0%)
  Core 21: 3774.66 MHz (100.0%)
  Core 22: 3774.59 MHz (100.0%)
  Core 23: 3774.66 MHz (100.0%)
  Core 24: 3820.55 MHz (100.0%)
  Core 25: 3820.64 MHz (100.0%)
  Core 26: 3820.55 MHz (100.0%)
  Core 27: 3820.68 MHz (100.0%)
  Core 28: 1907.13 MHz (  5.0%)
  Core 29:  624.19 MHz (  3.9%)
  Core 30:  624.19 MHz (  0.0%)
  Core 31: 1938.71 MHz (  0.0%)

Temperatures (°C):
  amdgpu_temp1:  67.0
  k10temp_temp1:  85.1
  nvme_temp1:  48.9
  nvme_temp2:  70.8
  nvme_temp3:  47.9
  r8169_0_a00:00_temp1:  54.0
  spd5118_temp1:  40.2

Additional CPU Info:
  Thread(s) per core: 2
  Core(s) per socket: 16
  Stepping: 0
  Frequency boost: enabled
  CPU(s) scaling MHz: 53%
  CPU max MHz: 5756.4521
  CPU min MHz: 624.1940


Press 'q' to exit
```
\* Yes this system is thermally constrained (hence this project)

## Data Sources

- **CPU Info**: Retrieved from `lscpu` command
- **Per-core frequencies**: Read from `/proc/cpuinfo`
- **CPU utilization**: Read from `/proc/stat`
- **Temperatures**: Read from `/sys/class/hwmon/` sensors


## Supported Sensors

The tool automatically detects and displays data from various hardware monitoring sources:

### Available Sensor Types
- **Temperatures**: CPU, GPU, NVMe SSDs, network adapters, memory modules
- **Voltages**: GPU voltages (vddgfx, vddnb) and other voltage rails
- **Power**: GPU power consumption and other power sensors
- **Fan Speeds**: Detected when available through hwmon

### Fan Speed Detection Issues

**Common Issue on Newer Motherboards (ASRock X870, etc.):**

Fan sensors may not be detected because newer Super I/O chips (like Nuvoton NCT6798D) aren't fully supported in current kernels. If `sensors-detect` finds your chip but fan speeds don't appear, try:

```bash
# Manually load the driver module
sudo modprobe nct6775

# Check if fans now appear
sensors
```

**Note**: This workaround may only partially work until the driver is updated for your specific chip. Fan detection depends on:
- Kernel version and driver support
- Motherboard manufacturer implementation
- Super I/O chip compatibility

## Notes

- Requires root privileges on some systems to access certain temperature sensors
- Sensor availability depends on your hardware and kernel drivers
- The display adapts to terminal size - resize your terminal if content appears truncated
- Fan speeds require compatible hardware monitoring drivers
