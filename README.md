# RedisTimeSeries Device Simulator

This project simulates the behavior of embedded devices using [RedisTimeSeries](https://redis.io/docs/latest/develop/data-types/timeseries/) to store and aggregate time series data.

The goal is to evaluate memory usage and compaction strategies (e.g. hourly average, daily max) over a realistic use case involving thousands of devices and millions of datapoints collected over 3 years.

---

## 💡 Use Case

Simulate:
- **1000 devices**
- 5 metrics per device: `temp`, `volt`, `current`, `gaz`, `alarme`
- Measurements every **10 minutes**
- Historical retention: **3 years**
- Configurable compaction rules 

### 📊 Volume Simulated

This simulation inserts:

- **1000 devices**
- **5 metrics per device**
- **1 data point every 10 minutes** → 144 points/day
- **3 years of history**

Which results in:

- `24*(60/10) × 365 × 3 = 157,680` points of measure over 3 years
- `157,680 × 5 metrics × 1000 devices = 788,400,000` TS.ADD operations


You can adjust this volume using command-line arguments.

### 📦 Without vs With Compaction

#### 🔹 Without compaction

Only raw time series are created:

```bash
TS.CREATE device:42:temp
```

No retention or aggregation is applied, which means all data is stored at full resolution indefinitely unless manually deleted.

#### 🔸 With compaction enabled

RedisTimeSeries creates:
- The raw series with 90-day retention
- Two aggregated series (`1h_avg`, `1d_max`) for long-term trends

```bash
# Raw series with 90-day retention (in milliseconds)
TS.CREATE device:42:temp RETENTION 7776000000

# Aggregated series (no retention)
TS.CREATE device:42:temp:1h_avg
TS.CREATE device:42:temp:1d_max

# Compaction rules
TS.CREATERULE device:42:temp device:42:temp:1h_avg AGGREGATION avg 3600000
TS.CREATERULE device:42:temp device:42:temp:1d_max AGGREGATION max 86400000
```

This setup reduces memory usage significantly while still allowing visualization and long-term monitoring.

Compare:
- Raw time series vs. aggregated compaction
- Memory footprint with or without retention policy

### 📉 Compaction Strategy

When enabled, raw time series data is retained for **90 days** (default value, can be overriden with `--raw_retention_days XX` days ).

This short-term retention keeps full-resolution datapoints (10-minute intervals) only for the most recent period. 
For longer-term analysis, RedisTimeSeries applies *compaction rules* which store:

- **1h average**: aggregated hourly mean values
- **1d max**: daily maximums

These aggregated series preserve historical trends while drastically reducing memory usage compared to full-resolution storage over 3 years.

This enables fast queries and visualization while controlling resource usage on memory-constrained systems.

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
```
