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

- Linux operating system (tested on x86/AMD and ARM/Raspberry Pi)
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
  Core  0: 3736.03 MHz (100.0%)             Core 16: 3736.06 MHz (100.0%)
  Core  1: 3735.97 MHz (100.0%)             Core 17: 3735.97 MHz (100.0%)
  Core  2: 3736.01 MHz (100.0%)             Core 18: 3736.01 MHz (100.0%)
  Core  3: 3736.03 MHz (100.0%)             Core 19: 3735.94 MHz (100.0%)
  Core  4: 3735.98 MHz (100.0%)             Core 20: 3735.99 MHz (100.0%)
  Core  5: 3736.03 MHz (100.0%)             Core 21: 3736.06 MHz (100.0%)
  Core  6: 3736.01 MHz (100.0%)             Core 22: 3735.98 MHz (100.0%)
  Core  7: 3736.00 MHz (100.0%)             Core 23: 3735.95 MHz (100.0%)
  Core  8: 3784.60 MHz (100.0%)             Core 24: 3784.59 MHz (100.0%)
  Core  9: 3784.56 MHz (100.0%)             Core 25: 3784.58 MHz (100.0%)
  Core 10: 3784.60 MHz (100.0%)             Core 26: 3784.60 MHz (100.0%)
  Core 11: 3784.62 MHz (100.0%)             Core 27: 3784.59 MHz (100.0%)
  Core 12:  624.19 MHz (  2.0%)             Core 28: 2062.45 MHz (  4.9%)
  Core 13: 1945.14 MHz (  1.0%)             Core 29: 2487.30 MHz (  1.0%)
  Core 14:  624.19 MHz (  0.0%)             Core 30: 1925.91 MHz (  1.0%)
  Core 15:  624.19 MHz (  1.0%)             Core 31: 1905.73 MHz (  1.0%)

Temperatures (°C):                          Voltages (V):
  amdgpu_edge:  68.0                          amdgpu_vddgfx: 0.965
  k10temp_Tctl:  85.1                         amdgpu_vddnb: 1.189
  nct6799_AUXTIN0:  46.0                      nct6799_in0: 1.000
  nct6799_AUXTIN1:  14.0                      nct6799_in1: 1.856
  nct6799_AUXTIN2:  18.0                      nct6799_in2: 3.440
  nct6799_AUXTIN3:  19.0                      nct6799_in3: 3.344
  nct6799_AUXTIN4:  20.0                      nct6799_in4: 1.664
  nct6799_CPUTIN:  64.0                       nct6799_in5: 1.104
  nct6799_SMBUSMASTER 0:  85.0                nct6799_in6: 0.648
  nct6799_SYSTIN:  44.0                       nct6799_in7: 3.424
  nct6799_TSI0_TEMP:  85.1                    nct6799_in8: 3.376
  nvme_Composite:  51.9                       nct6799_in9: 1.840
  nvme_Sensor 1:  73.8                        nct6799_in10: 1.216
  nvme_Sensor 2:  50.9                        nct6799_in11: 1.136
  r8169_0_a00:00_temp1:  55.5                 nct6799_in12: 1.024
  spd5118_temp1:  42.2                        nct6799_in13: 0.904
                                              nct6799_in14: 1.120
Fan Speeds (RPM):                             nct6799_in15: 0.680
  Fan1:    0rpm (N/A)                         nct6799_in16: 1.856
  Fan2: 2705rpm (100%)                        nct6799_in17: 2.032
  Fan3: 3417rpm (100%)
  Fan4: 1962rpm (100%)                      Power (W):
  Fan5: 1920rpm (100%)                        amdgpu_PPT:  0.028
  Fan6:    0rpm (N/A)
  Fan7: 2727rpm (100%)

Additional CPU Info:
  Thread(s) per core: 2
  Core(s) per socket: 16
  Stepping: 0
  Frequency boost: enabled
  CPU(s) scaling MHz: 61%
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
