from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from analytics import prepare, metrics, filter_data, summarize, time_summary

st.set_page_config(page_title='Ad Campaign Analyzer', page_icon='📊', layout='wide')
SOURCE = 'https://exploremydata.com/datasets/marketing-campaigns'
DATA = Path(__file__).parent / 'data' / 'marketing-campaigns.csv'
LABELS = {'spend':'Spend', 'revenue':'Revenue', 'clicks':'Clicks', 'conversions':'Conversions',
          'impressions':'Impressions', 'ctr':'CTR', 'cpc':'CPC', 'cpm':'CPM', 'cvr':'CVR',
          'cpa':'CPA', 'roas':'ROAS', 'roi':'Advertising ROI',
          'revenue_less_ad_cost':'Revenue less ad cost', 'revenue_per_conversion':'Revenue per conversion',
          'revenue_per_click':'Revenue per click'}

@st.cache_data
def load_file(path):
    return pd.read_csv(path)

def display_value(key, value):
    if pd.isna(value): return 'N/A'
    if key in ['ctr', 'cvr', 'roi']: return f'{value:,.2f}%'
    if key == 'roas': return f'{value:,.2f}×'
    if key in ['impressions', 'clicks', 'conversions']: return f'{value:,.0f}'
    return f'${value:,.2f}'

def cards(values, keys):
    for col, key in zip(st.columns(len(keys)), keys):
        col.metric(LABELS[key], display_value(key, values[key]))

def chart(df, x, y, title, kind='line'):
    fn = px.line if kind == 'line' else px.bar
    fig = fn(df, x=x, y=y, title=title, labels={**LABELS, 'value':'Value', 'variable':'Metric'},
             **({'barmode':'group'} if kind == 'bar' else {}))
    fig.update_layout(legend_title_text='', margin=dict(l=10,r=10,t=55,b=10))
    st.plotly_chart(fig, width="stretch")

def download(df, label, filename, key):
    st.download_button(label, df.to_csv(index=False).encode(), filename, 'text/csv', key=key)

st.title('Ad Campaign Analyzer')
st.caption('Compare advertising activity, efficiency, and returns with consistent shared filters.')
with st.sidebar:
    st.header('Data & shared filters')
    uploaded = st.file_uploader('Upload a campaign CSV', type='csv')
try:
    raw = pd.read_csv(uploaded) if uploaded else load_file(str(DATA))
    clean, excluded, issues, quality = prepare(raw)
except Exception as exc:
    st.error(f'Unable to load dataset: {exc}. Upload a CSV with date, campaign, channel, impressions, clicks, spend, conversions, revenue.')
    st.stop()
if clean.empty:
    st.warning('No usable records remain. Review missing, invalid, or negative values.')
    st.dataframe(issues)
    st.stop()

# Changing sources clears selections so filters never retain stale categories.
signature = (uploaded.name, uploaded.size, hash(uploaded.getvalue())) if uploaded else ('default',)
if st.session_state.get('source_signature') != signature:
    for key in ['dates', 'channels', 'campaigns', 'detail_campaign']:
        st.session_state.pop(key, None)
    st.session_state.source_signature = signature
with st.sidebar:
    if st.button('Reset filters'):
        for key in ['dates', 'channels', 'campaigns', 'detail_campaign']:
            st.session_state.pop(key, None)
    dates = st.date_input('Date range (inclusive)', value=(clean.date.min().date(), clean.date.max().date()),
                          min_value=clean.date.min().date(), max_value=clean.date.max().date(), key='dates')
    channels = st.multiselect('Channels — clear selection means no records', sorted(clean.channel.unique()),
                              default=sorted(clean.channel.unique()), key='channels')
    campaigns = st.multiselect('Campaigns — clear selection means no records', sorted(clean.campaign.unique()),
                               default=sorted(clean.campaign.unique()), key='campaigns')
    with st.expander('Metric definitions'):
        st.markdown('''All ratios use summed components. Zero denominators produce N/A.

CTR = clicks / impressions × 100; CPC = spend / clicks; CPM = spend / impressions × 1,000.

CVR = conversions / clicks × 100; CPA = spend / conversions.

ROAS = revenue / spend; advertising ROI = (revenue − spend) / spend × 100.

Revenue per conversion = revenue / conversions; revenue per click = revenue / clicks.

Share = segment total / filtered overall total × 100.''')
    with st.expander('Source data quality'):
        st.json(quality)
        st.dataframe(issues)
        st.caption('Exact duplicates are reported and retained. Funnel violations are flagged, not altered.')
        if not excluded.empty: st.dataframe(excluded.head(100))
if len(dates) != 2:
    st.info('Select both a start and end date.')
    st.stop()
filtered = filter_data(clean, dates[0], dates[1], channels, campaigns)
st.caption(f'{dates[0]} to {dates[1]} · {len(filtered):,} filtered rows · source: {quality["included"]:,} included / {quality["excluded"]:,} excluded')
st.info('Advertising ROI and revenue less ad cost exclude product costs, staffing, overhead, taxes, and other expenses. They are not net business profit.')
if not uploaded:
    st.caption(f'Synthetic demonstration data · CC0 · [ExploreMyData source]({SOURCE})')
else:
    st.caption('Uploaded data: currency is assumed USD. Confirm attribution, currency, and conversion definitions before interpreting returns.')
if quality['clicks_above_impressions'] or quality['conversions_above_clicks']:
    st.warning('Source contains funnel inconsistencies. They remain unchanged; interpret rates with care.')
if filtered.empty:
    st.warning('No records match these filters. Select channels/campaigns or reset filters.')
    st.stop()
m = metrics(filtered)
channel_table = summarize(filtered, 'channel')
campaign_table = summarize(filtered, 'campaign')
overview, platform, details, trends = st.tabs(['Overview', 'Platform / Channel Comparison', 'Campaign Details', 'Time Series'])
with overview:
    cards(m, ['spend','revenue','clicks','conversions','roas','roi'])
    cards(m, ['impressions','ctr','cpc','cpm','cvr','cpa'])
    cards(m, ['revenue_less_ad_cost','revenue_per_conversion','revenue_per_click'])
    chart(time_summary(filtered,'Daily'), 'period', ['spend','revenue'], 'Daily spend and revenue (USD)')
    left, right = st.columns(2)
    with left:
        st.plotly_chart(go.Figure(go.Funnel(y=['Impressions','Clicks','Conversions'],
                         x=[m['impressions'],m['clicks'],m['conversions']], textinfo='value+percent previous')),
                         width="stretch")
    with right:
        chart(channel_table,'channel',['spend_share_pct','revenue_share_pct'],'Share of filtered spend and revenue (%)','bar')
    st.subheader('Descriptive insights')
    top = channel_table.loc[channel_table.revenue.idxmax()]
    best = channel_table.dropna(subset=['roas']).sort_values('roas',ascending=False)
    st.write(f'• {top.channel} records the most revenue: ${top.revenue:,.2f}, from {top.conversions:,.0f} conversions.')
    if not best.empty:
        b=best.iloc[0]
        st.write(f'• {b.channel} has the highest observed ROAS: {b.roas:.2f}×, on ${b.spend:,.2f} spend and {b.conversions:,.0f} conversions.')
    st.write(f'• The filtered selection converts {m["cvr"]:.2f}% of clicks; CPA is {display_value("cpa",m["cpa"])}.')
    st.caption('Descriptive comparisons do not establish causal lift or predict the effect of increasing spend.')
    download(filtered,'Download filtered records','filtered_campaigns.csv','all_export')
with platform:
    st.caption('This dataset identifies channels, not named ad platforms such as Google Ads or Meta.')
    chart(channel_table,'channel',['spend','revenue'],'Channel spend and revenue (USD)','bar')
    left,right=st.columns(2)
    with left: chart(channel_table,'channel','cpa','Channel CPA (USD)','bar')
    with right: chart(channel_table,'channel','roas','Channel ROAS (×)','bar')
    st.plotly_chart(px.scatter(channel_table,x='spend',y='revenue',size='conversions',color='channel',
                              hover_data=['clicks','cpa','roas'],title='Spend vs revenue (USD); bubble size = conversions'),width="stretch")
    minimum=st.number_input('Minimum conversions for ranking only',min_value=0,value=30,step=10)
    eligible=channel_table[channel_table.conversions>=minimum].dropna(subset=['roas'])
    if eligible.empty: st.info('No channels qualify for this ranking threshold.')
    else:
        winner=eligible.sort_values('roas',ascending=False).iloc[0]
        st.write(f'Highest ROAS among channels with at least {minimum} conversions: {winner.channel}, {winner.roas:.2f}×, {winner.conversions:,.0f} conversions, ${winner.spend:,.2f} spend.')
    st.dataframe(channel_table,width="stretch",hide_index=True)
    download(channel_table,'Download channel summary','channel_summary.csv','channel_export')
with details:
    options=sorted(filtered.campaign.unique())
    if st.session_state.get('detail_campaign') not in options:
        st.session_state.pop('detail_campaign',None)
    selected=st.selectbox('Inspect a campaign',options,key='detail_campaign')
    part=filtered[filtered.campaign==selected]
    cards(metrics(part),['spend','clicks','conversions','revenue','roas','roi'])
    st.subheader('Campaign breakdown by channel')
    st.dataframe(summarize(part,'channel'),width="stretch",hide_index=True)
    daily=time_summary(part,'Daily')
    chart(daily,'period',['spend','revenue'],'Campaign spend and revenue (USD)')
    chart(daily,'period','conversions','Campaign conversions')
    st.subheader('Daily campaign detail')
    st.dataframe(daily,width="stretch",hide_index=True)
    download(part,'Download selected campaign records','campaign_records.csv','campaign_export')
    st.subheader('Compare all campaigns in shared selection')
    st.dataframe(campaign_table,width="stretch",hide_index=True)
with trends:
    frequency=st.radio('Aggregation',['Daily','Weekly','Monthly'],horizontal=True)
    series=time_summary(filtered,frequency)
    st.caption('Weeks start Monday. First and last periods may be partial. Missing reporting dates are not assumed to have zero activity.')
    chart(series,'period',['spend','revenue'],'Spend and revenue (USD)')
    chart(series,'period',['clicks','conversions'],'Clicks and conversions (counts)')
    chart(series,'period',['ctr','cvr'],'CTR and CVR (%)')
    chart(series,'period','cpa','Cost per conversion (USD)')
    chart(series,'period','roas','ROAS (×)')
    chart(series,'period','roi','Advertising ROI (%)')
    st.dataframe(series,width="stretch",hide_index=True)
    download(series,'Download time-series summary','time_series.csv','time_export')
st.divider()
st.caption(f'[Dataset documentation]({SOURCE}) · Default dataset is generated synthetic data under CC0. Campaign names may span multiple channels. No causal or profitability claims are implied.')
