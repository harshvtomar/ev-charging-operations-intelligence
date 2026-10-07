from common import *

def generate(seed=107):
    rng=np.random.default_rng(seed)
    stations=pd.DataFrame({'station_id':range(1,25),'zone':np.repeat(['Commercial','Residential','Highway','Campus'],6),'ports':rng.integers(3,9,24),'power_kw':rng.choice([22,60,120],24)})
    sessions=[];ops=[]
    for date in pd.date_range('2025-01-01','2025-06-30'):
        for st in stations.itertuples():
            planned=st.ports*24
            outage=float(min(planned,rng.gamma(.6,2)*(2 if st.zone=='Highway' else 1)))
            available=planned-outage
            demand={'Commercial':3.5,'Residential':2.2,'Highway':4.5,'Campus':1.7}[st.zone]
            n=int(rng.poisson(st.ports*demand*(1+.20*np.sin(date.dayofyear/45))))
            used=0
            for _ in range(n):
                if used>=available: break
                success=int(rng.random()>(.08 if st.zone=='Highway' else .035))
                kwh=float(rng.gamma(3,7)) if success else 0.0
                hours=min(available-used,max(.07,kwh/(st.power_kw*.70)+rng.exponential(.15)))
                # Respect connector-hour capacity at the station-day grain; no timestamp queue model.
                kwh=min(kwh,hours*st.power_kw*.70)
                used+=hours
                tariff={'Commercial':.39,'Residential':.30,'Highway':.48,'Campus':.27}[st.zone]
                revenue=kwh*tariff
                # Session hour is sampled separately for peak tariff allocation.
                hour=int(rng.choice(range(24),p=np.array([1]*7+[3]*10+[5]*4+[2]*3)/sum([1]*7+[3]*10+[5]*4+[2]*3)))
                energy_cost=kwh*(.23 if 17<=hour<=20 else .15)
                sessions.append([len(sessions)+1,st.station_id,date.strftime('%Y-%m-%d'),hour,success,round(kwh,4),round(hours,5),round(revenue,4),round(energy_cost,4)])
            ops.append([st.station_id,date.strftime('%Y-%m-%d'),planned,round(outage,5),round(available,5),round(used,5),st.ports*1.8])
    sessions=pd.DataFrame(sessions,columns=['session_id','station_id','date','start_hour','success','energy_kwh','occupied_hours','revenue','energy_cost'])
    ops=pd.DataFrame(ops,columns=['station_id','date','planned_port_hours','outage_port_hours','available_port_hours','occupied_port_hours','fixed_operating_cost'])
    for name,frame in [('stations',stations),('sessions',sessions),('station_days',ops)]: frame.to_csv(DATA/(name+'.csv'),index=False)
    return stations,sessions,ops

def analyze():
    stations,sessions,ops=generate();store_db({'stations':stations,'sessions':sessions,'station_days':ops})
    daily=sessions.groupby(['station_id','date']).agg(sessions=('session_id','size'),successful_sessions=('success','sum'),energy_kwh=('energy_kwh','sum'),revenue=('revenue','sum'),energy_cost=('energy_cost','sum')).reset_index()
    daily=ops.merge(daily,on=['station_id','date'],how='left',validate='one_to_one').merge(stations,on='station_id',validate='many_to_one')
    cols=['sessions','successful_sessions','energy_kwh','revenue','energy_cost'];daily[cols]=daily[cols].fillna(0)
    daily['contribution']=daily.revenue-daily.energy_cost-daily.fixed_operating_cost;daily['month']=daily.date.str[:7]
    agg=dict(sessions=('sessions','sum'),successes=('successful_sessions','sum'),energy_kwh=('energy_kwh','sum'),revenue=('revenue','sum'),contribution=('contribution','sum'),planned_hours=('planned_port_hours','sum'),available_hours=('available_port_hours','sum'),occupied_hours=('occupied_port_hours','sum'))
    monthly=daily.groupby(['month','zone']).agg(**agg).reset_index().rename(columns={'zone':'segment'})
    monthly['uptime']=monthly.available_hours/monthly.planned_hours;monthly['utilization']=monthly.occupied_hours/monthly.available_hours;save_table(monthly,'monthly_kpis')
    ranking=daily.groupby(['station_id','zone']).agg(**agg).reset_index();ranking['utilization']=ranking.occupied_hours/ranking.available_hours;ranking['uptime']=ranking.available_hours/ranking.planned_hours;ranking['priority_score']=ranking.utilization*ranking.uptime
    ranking=ranking.sort_values('priority_score',ascending=False);save_table(ranking,'station_priorities')
    # Capacity scenario holds observed demand fixed; adding ports dilutes utilization and adds costs.
    # A separate demand-recovery assumption explicitly models unobserved unmet demand.
    scenarios=[]
    for r in ranking.head(5).itertuples():
        for recovery in [0,.10,.25]:
            additional_energy=r.energy_kwh*recovery
            margin_per_kwh=(daily[daily.station_id==r.station_id].revenue.sum()-daily[daily.station_id==r.station_id].energy_cost.sum())/r.energy_kwh
            extra_cost=2*1.8*181
            scenarios.append({'station_id':r.station_id,'zone':r.zone,'added_ports':2,'assumed_demand_recovery':recovery,'additional_kwh':additional_energy,'incremental_contribution':additional_energy*margin_per_kwh-extra_cost,'added_daily_fixed_cost':3.6})
    save_table(pd.DataFrame(scenarios),'capacity_scenarios')
    outages=daily.groupby('zone').agg(outage_port_hours=('outage_port_hours','sum'),planned_hours=('planned_port_hours','sum')).reset_index();outages['outage_rate']=outages.outage_port_hours/outages.planned_hours;save_table(outages,'reliability')
    hourly=sessions.groupby('start_hour').agg(sessions=('session_id','size'),energy_kwh=('energy_kwh','sum')).reset_index();save_table(hourly,'hourly_demand')
    # Detect daily energy deviations using only earlier same-weekday observations.
    days=daily.groupby('date',as_index=False).energy_kwh.sum();days['weekday']=pd.to_datetime(days.date).dt.weekday
    expected=[]
    for i,row in days.iterrows():
        hist=days.iloc[:i];hist=hist[hist.weekday==row.weekday].tail(8)
        expected.append((hist.energy_kwh.mean(),hist.energy_kwh.std(ddof=1)) if len(hist)>=4 else (np.nan,np.nan))
    days[['baseline_kwh','baseline_std']]=expected;days['zscore']=(days.energy_kwh-days.baseline_kwh)/days.baseline_std;days['flag']=days.zscore.abs()>3;save_table(days,'demand_anomalies')
    summary={'stations':len(stations),'sessions':len(sessions),'energy_kwh':float(sessions.energy_kwh.sum()),'session_success_rate':float(sessions.success.mean()),'network_uptime':float(ops.available_port_hours.sum()/ops.planned_port_hours.sum()),'network_utilization':float(ops.occupied_port_hours.sum()/ops.available_port_hours.sum()),'contribution':float(daily.contribution.sum()),'anomaly_flags':int(days.flag.sum())}
    (OUT/'summary.json').write_text(json.dumps(summary,indent=2))
    chart(monthly.groupby('month',as_index=False).energy_kwh.sum(),'month','energy_kwh','Delivered charging energy','energy_trend.png')
    fig,ax=plt.subplots(figsize=(10,4),layout='constrained');ax.bar(hourly.start_hour,hourly.sessions,color='#0891b2');ax.set(xlabel='Sampled start hour',ylabel='Sessions',title='Session demand by hour');fig.savefig(OUT/'hourly_demand.png',dpi=140);plt.close(fig)
    metrics=[dict(label='Delivered energy',numerator='energy_kwh',unit='kwh'),dict(label='Session success',numerator='successes',denominator='sessions',unit='percent'),dict(label='Network uptime',numerator='available_hours',denominator='planned_hours',unit='percent'),dict(label='Contribution',numerator='contribution',unit='usd')]
    save_dashboard(monthly.to_dict('records'),metrics,metrics[0],'EV Charging Operations Intelligence','Station reliability, connector utilization, unit economics, and capacity planning. January–June 2025. Energy is kWh; all monetary amounts are simulated USD.',{},[dict(key='month',label='Month'),dict(key='segment',label='Zone'),dict(key='sessions',label='Sessions',unit='number'),dict(key='energy_kwh',label='Energy',unit='kwh'),dict(key='uptime',label='Uptime',unit='percent'),dict(key='utilization',label='Utilization',unit='percent'),dict(key='contribution',label='Contribution',unit='usd')])
    (OUT/'executive_brief.md').write_text(f'''# EV charging decision brief\n\nSynthetic engineering-and-analytics case study.\n\n- {summary['sessions']:,} sessions deliver {summary['energy_kwh']:,.0f} kWh across {summary['stations']} stations.\n- Connector uptime is {summary['network_uptime']:.1%}; observed utilization of available connector hours is {summary['network_utilization']:.1%}. These are ratios of summed hours, not unweighted station averages.\n- Session success is {summary['session_success_rate']:.1%}; contribution is ${summary['contribution']:,.0f}, before capex, depreciation, tax, rent, and demand charges.\n- Inspect Highway failure rates and reliability before expanding capacity. The ranking is a screening score (utilization × uptime), not an investment recommendation.\n- Expansion is unprofitable under zero recovered demand; compare 0%, 10%, and 25% assumptions with a field pilot measuring unmet demand.\n\nStation-day connector hours obey capacity constraints; sampled start hours do not encode individual port schedules or queue dynamics. No wait-time claims are made. Demand anomalies use earlier same-weekday history, with a four-observation warmup. Electricity prices are simplified peak/offpeak energy rates; session success means completed energy delivery.\n''')
    return summary

if __name__=='__main__': print(json.dumps(analyze(),indent=2))
