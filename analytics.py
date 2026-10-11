"""Shared preparation, filtering, aggregation, and KPI definitions."""
import pandas as pd

NUMERIC = ['impressions', 'clicks', 'spend', 'conversions', 'revenue']
REQUIRED = ['date', 'campaign', 'channel', *NUMERIC]

def prepare(raw):
    df = raw.copy()
    df.columns = df.columns.str.strip().str.lower()
    if df.columns.duplicated().any():
        raise ValueError('Duplicate column names after normalization.')
    missing = set(REQUIRED) - set(df.columns)
    if missing:
        raise ValueError('Missing required columns: ' + ', '.join(sorted(missing)))
    duplicates = int(df.duplicated().sum())
    df['date'] = pd.to_datetime(df['date'], errors='coerce', format='mixed').dt.normalize()
    for col in ['campaign', 'channel']:
        df[col] = df[col].astype('string').str.strip().replace('', pd.NA)
    for col in NUMERIC:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].replace([float('inf'), -float('inf')], float('nan'))
    valid = df[REQUIRED].notna().all(axis=1) & df[NUMERIC].ge(0).all(axis=1)
    issues = pd.DataFrame({'missing_or_invalid': df[REQUIRED].isna().sum()})
    quality = {'total': len(df), 'included': int(valid.sum()), 'excluded': int((~valid).sum()),
               'duplicates': duplicates, 'negative_rows': int(df[NUMERIC].lt(0).any(axis=1).sum()),
               'clicks_above_impressions': int((df.clicks > df.impressions).sum()),
               'conversions_above_clicks': int((df.conversions > df.clicks).sum())}
    return df.loc[valid].copy(), df.loc[~valid].copy(), issues, quality

def safe_ratio(a, b, factor=1):
    return a / b * factor if b > 0 else float('nan')

def metrics(df):
    s = df[NUMERIC].sum().to_dict()
    s.update(ctr=safe_ratio(s['clicks'], s['impressions'], 100),
             cpc=safe_ratio(s['spend'], s['clicks']),
             cpm=safe_ratio(s['spend'], s['impressions'], 1000),
             cvr=safe_ratio(s['conversions'], s['clicks'], 100),
             cpa=safe_ratio(s['spend'], s['conversions']),
             roas=safe_ratio(s['revenue'], s['spend']),
             roi=safe_ratio(s['revenue']-s['spend'], s['spend'], 100),
             revenue_less_ad_cost=s['revenue']-s['spend'],
             revenue_per_conversion=safe_ratio(s['revenue'], s['conversions']),
             revenue_per_click=safe_ratio(s['revenue'], s['clicks']))
    return s

def filter_data(df, start, end, channels, campaigns):
    return df.loc[df.date.between(pd.Timestamp(start), pd.Timestamp(end)) &
                  df.channel.isin(channels) & df.campaign.isin(campaigns)].copy()

def summarize(df, by):
    rows = []
    for key, part in df.groupby(by, sort=True):
        rows.append({by: key, 'rows': len(part), **metrics(part)})
    result = pd.DataFrame(rows)
    totals = metrics(df)
    for measure in ['spend', 'revenue', 'conversions']:
        result[measure+'_share_pct'] = result[measure].map(lambda x: safe_ratio(x, totals[measure], 100))
    return result

def time_summary(df, frequency):
    work = df.copy()
    if frequency == 'Daily':
        work['period'] = work.date
    else:
        work['period'] = work.date.dt.to_period('W-SUN' if frequency == 'Weekly' else 'M').dt.start_time
    return summarize(work, 'period')
