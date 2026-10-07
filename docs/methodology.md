# Methodology and limitations


1. Seed 107 simulates 24 stations, 181 operating days, connectors, outages, and charging sessions. Capacity is enforced at station-day connector-hour grain. Start hours are sampled for demand and tariff analysis; no port-level chronology or wait-time inference is available.
2. Uptime sums available connector hours / planned connector hours. Utilization sums occupied connector hours / available connector hours. Session success is completed energy-delivery sessions / all sessions.
3. SQL aggregates sessions to station/day before joining availability. This avoids multiplying planned or available hours by session count. Zero-session days are retained with a left join.
4. Contribution = charging revenue - peak/offpeak electricity energy cost - fixed connector operating cost. USD rates are illustrative; demand charges, capex, rent, tax, and depreciation are excluded.
5. Station screening score is utilization × uptime. It does not incorporate local demand, queueing, grid constraints, or investment payback.
6. Adding two connectors costs $3.60/day for 181 days. Additional energy is an explicit scenario of 0%, 10%, or 25% of baseline demand. Per-kWh contribution is held constant; assumptions require external validation. No recovered demand is inferred from observed sessions.
7. Daily anomaly score compares network energy with the last eight earlier observations for the same weekday. A four-observation warmup applies. A |z| > 3 flag prompts investigation; multiple comparisons and changing demand patterns may generate false positives.
