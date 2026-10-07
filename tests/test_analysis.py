import unittest, json
from pathlib import Path
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
class SharedChecks(unittest.TestCase):
    def test_dashboard_weighted_kpis_reconcile(self):
        payload=json.loads((ROOT/'outputs/dashboard_data.json').read_text())
        raw=pd.read_csv(ROOT/'outputs/monthly_kpis.csv')
        embedded=pd.DataFrame(payload['rows'])
        pd.testing.assert_frame_equal(raw,embedded,check_dtype=False,atol=1e-5,rtol=1e-5)
        for segment in ['All']+list(raw.segment.unique()):
            rows=embedded if segment=='All' else embedded[embedded.segment==segment]
            self.assertGreater(len(rows),0)
            for m in payload['metrics']:
                value=rows[m['numerator']].sum()
                if 'denominator' in m: value/=rows[m['denominator']].sum()
                self.assertTrue(np.isfinite(value))
        html=(ROOT/'dashboard/index.html').read_text()
        self.assertNotIn('__PAYLOAD__',html)
        self.assertNotIn('<script src=',html)
    def test_inputs_primary_keys(self):
        for filename,key in KEYS.items():
            df=pd.read_csv(ROOT/'data'/filename)
            self.assertFalse(df[key].isna().any())
            self.assertFalse(df[key].duplicated().any())

KEYS={'stations.csv':'station_id','sessions.csv':'session_id'}
class EVChecks(unittest.TestCase):
    def test_connector_capacity_and_foreign_keys(self):
        days=pd.read_csv(ROOT/'data/station_days.csv');sessions=pd.read_csv(ROOT/'data/sessions.csv');stations=pd.read_csv(ROOT/'data/stations.csv')
        self.assertFalse(days.duplicated(['station_id','date']).any())
        self.assertTrue(sessions.station_id.isin(stations.station_id).all())
        self.assertTrue((days.occupied_port_hours<=days.available_port_hours+1e-5).all())
        np.testing.assert_allclose(days.planned_port_hours,days.available_port_hours+days.outage_port_hours,atol=1e-5)
        used=sessions.groupby(['station_id','date']).occupied_hours.sum().reset_index().merge(days,on=['station_id','date'])
        np.testing.assert_allclose(used.occupied_hours,used.occupied_port_hours,atol=.0005)
    def test_energy_and_failures(self):
        sessions=pd.read_csv(ROOT/'data/sessions.csv').merge(pd.read_csv(ROOT/'data/stations.csv'),on='station_id')
        self.assertTrue((sessions.energy_kwh<=sessions.occupied_hours*sessions.power_kw*.7+.001).all())
        self.assertEqual(sessions.loc[sessions.success==0,'energy_kwh'].sum(),0)
    def test_sql_python_reconciliation(self):
        py=pd.read_csv(ROOT/'outputs/monthly_kpis.csv').sort_values(['month','segment']);sql=pd.read_csv(ROOT/'outputs/sql_result_1.csv').sort_values(['month','zone'])
        for col in ['sessions','energy_kwh','uptime','utilization','contribution']:
            np.testing.assert_allclose(py[col],sql[col],atol=1e-5)
    def test_expansion_zero_recovery_costs_money(self):
        sc=pd.read_csv(ROOT/'outputs/capacity_scenarios.csv')
        zero=sc[sc.assumed_demand_recovery==0]
        self.assertEqual(len(zero),5);self.assertTrue((zero.incremental_contribution<0).all())
        np.testing.assert_allclose(zero.incremental_contribution,-zero.added_daily_fixed_cost*181,atol=1e-5)
    def test_anomalies_use_prior_weekday_history(self):
        days=pd.read_csv(ROOT/'outputs/demand_anomalies.csv')
        for i,row in days.iterrows():
            hist=days.iloc[:i];hist=hist[hist.weekday==row.weekday].tail(8)
            if len(hist)<4: self.assertTrue(pd.isna(row.baseline_kwh))
            else: self.assertAlmostEqual(row.baseline_kwh,hist.energy_kwh.mean(),places=4)

if __name__=='__main__': unittest.main()
