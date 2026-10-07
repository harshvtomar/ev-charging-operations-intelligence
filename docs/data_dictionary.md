# Source data dictionary

All datasets are synthetic; blank values mean missing, not zero.

## sessions.csv

| Field | Meaning |
|---|---|
| `session_id` | Unique session identifier. |
| `station_id` | Station identifier; foreign key in operational tables. |
| `date` | ISO operating date. |
| `start_hour` | Sampled integer hour 0–23; does not represent a port schedule. |
| `success` | 1 = energy delivered, 0 = failed. |
| `energy_kwh` | Delivered energy, kWh. |
| `occupied_hours` | Occupied connector time, hours. |
| `revenue` | Charging revenue, USD. |
| `energy_cost` | Electricity energy cost, USD. |

## station_days.csv

| Field | Meaning |
|---|---|
| `station_id` | Station identifier; foreign key in operational tables. |
| `date` | ISO operating date. |
| `planned_port_hours` | Connector count × 24 hours. |
| `outage_port_hours` | Unavailable connector hours. |
| `available_port_hours` | Planned minus outage connector hours. |
| `occupied_port_hours` | Aggregate occupied connector hours. |
| `fixed_operating_cost` | Daily USD connector operating cost. |

## stations.csv

| Field | Meaning |
|---|---|
| `station_id` | Station identifier; foreign key in operational tables. |
| `zone` | Station site type. |
| `ports` | Number of connectors. |
| `power_kw` | Rated per-connector power in kW. |
