-- Aggregate sessions before joining station-day availability to avoid fanout.
WITH s AS (SELECT station_id,date,COUNT(*) AS sessions,SUM(success) AS successes,
 SUM(energy_kwh) AS energy_kwh,SUM(revenue-energy_cost) AS energy_margin FROM sessions GROUP BY 1,2)
SELECT substr(d.date,1,7) AS month,st.zone,
 SUM(COALESCE(s.sessions,0)) AS sessions,SUM(COALESCE(s.energy_kwh,0)) AS energy_kwh,
 SUM(d.available_port_hours)/SUM(d.planned_port_hours) AS uptime,
 SUM(d.occupied_port_hours)/SUM(d.available_port_hours) AS utilization,
 SUM(COALESCE(s.energy_margin,0)-d.fixed_operating_cost) AS contribution
FROM station_days d JOIN stations st USING(station_id)
LEFT JOIN s ON s.station_id=d.station_id AND s.date=d.date GROUP BY 1,2 ORDER BY 1,2;

-- Station reliability rank within a zone.
WITH rel AS (SELECT st.zone,d.station_id,SUM(outage_port_hours)/SUM(planned_port_hours) AS outage_rate
FROM station_days d JOIN stations st USING(station_id) GROUP BY 1,2)
SELECT *,DENSE_RANK() OVER(PARTITION BY zone ORDER BY outage_rate DESC) AS repair_priority FROM rel;
