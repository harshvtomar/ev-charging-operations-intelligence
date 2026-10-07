# EV charging decision brief

Synthetic engineering-and-analytics case study.

- 73,831 sessions deliver 1,470,146 kWh across 24 stations.
- Connector uptime is 98.8%; observed utilization of available connector hours is 12.4%. These are ratios of summed hours, not unweighted station averages.
- Session success is 94.8%; contribution is $276,161, before capex, depreciation, tax, rent, and demand charges.
- Inspect Highway failure rates and reliability before expanding capacity. The ranking is a screening score (utilization × uptime), not an investment recommendation.
- Expansion is unprofitable under zero recovered demand; compare 0%, 10%, and 25% assumptions with a field pilot measuring unmet demand.

Station-day connector hours obey capacity constraints; sampled start hours do not encode individual port schedules or queue dynamics. No wait-time claims are made. Demand anomalies use earlier same-weekday history, with a four-observation warmup. Electricity prices are simplified peak/offpeak energy rates; session success means completed energy delivery.
