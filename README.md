# RedisTimeSeries Device Simulator

This project simulates the behavior of embedded devices using [RedisTimeSeries](https://redis.io/docs/latest/develop/data-types/timeseries/) to store and aggregate time series data.

The goal is to evaluate memory usage and compaction strategies (e.g. hourly average, daily max) over a realistic use case involving thousands of devices and millions of datapoints collected over 3 years.

---

## 💡 Use Case

Simulate:
- Up to **1000 devices**
- 5 metrics per device: `temp`, `volt`, `current`, `gaz`, `alarme`
- Measurements every **10 minutes**
- Historical retention: **3 years**
- Configurable compaction rules

Compare:
- Raw time series vs. aggregated compaction
- Memory footprint with or without retention policy

---

## ⚙️ Prerequisites

- Docker installed locally
- Internet access to pull the [RedisTimeSeries Docker image](https://hub.docker.com/r/redislabs/redistimeseries)

---

## 🚀 How to Run

```bash
# 1. Clone the repository
git clone https://github.com/<your_user>/RedisTimeSeriesDevice.git
cd RedisTimeSeriesDevice

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start RedisTimeSeries container
./docker_run.sh

# 4. Run the default simulation
./run_script.sh

# 5. Run the simulation with compaction enabled
./run_script_compaction.sh
