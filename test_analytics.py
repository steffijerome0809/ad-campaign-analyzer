import unittest
import pandas as pd
from analytics import metrics, prepare, filter_data, time_summary

class AnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.df = pd.DataFrame({'date':pd.to_datetime(['2025-01-01','2025-01-02']),
            'campaign':['A','B'],'channel':['Search','Social'],'impressions':[100,900],
            'clicks':[10,9],'spend':[20,30],'conversions':[2,1],'revenue':[100,50]})
    def test_weighted_ratios(self):
        m=metrics(self.df)
        self.assertAlmostEqual(m['ctr'],1.9)
        self.assertAlmostEqual(m['cpa'],50/3)
        self.assertEqual(m['roas'],3)
        self.assertEqual(m['roi'],200)
    def test_zero_denominator(self):
        zero=self.df.copy(); zero['spend']=0; zero['clicks']=0
        self.assertTrue(pd.isna(metrics(zero)['roas']))
        self.assertTrue(pd.isna(metrics(zero)['cvr']))
    def test_missing_is_not_zero(self):
        df=self.df.copy(); df.loc[0,'spend']=None
        clean,excluded,_,q=prepare(df)
        self.assertEqual(len(clean),1); self.assertEqual(q['excluded'],1)
        self.assertTrue(pd.isna(excluded.iloc[0].spend))
    def test_filter_inclusive_and_empty(self):
        self.assertEqual(len(filter_data(self.df,'2025-01-01','2025-01-02',['Search','Social'],['A','B'])),2)
        self.assertEqual(len(filter_data(self.df,'2025-01-02','2025-01-02',['Social'],['B'])),1)
        self.assertTrue(filter_data(self.df,'2025-01-01','2025-01-02',[],['A']).empty)
    def test_period_ratios(self):
        monthly=time_summary(self.df,'Monthly').iloc[0]
        self.assertAlmostEqual(monthly.ctr,1.9)
        self.assertEqual(time_summary(self.df,'Weekly').iloc[0].period,pd.Timestamp('2024-12-30'))
    def test_duplicates_and_violations_retained(self):
        df=pd.concat([self.df,self.df.iloc[:1]],ignore_index=True)
        df.loc[0,'conversions']=20
        clean,_,_,q=prepare(df)
        self.assertEqual(len(clean),3)
        self.assertEqual(q['conversions_above_clicks'],1)
    def test_negative_excluded(self):
        df=self.df.copy(); df.loc[0,'spend']=-1
        self.assertEqual(prepare(df)[3]['excluded'],1)

if __name__ == '__main__': unittest.main()
