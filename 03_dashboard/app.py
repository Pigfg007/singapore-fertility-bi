"""Deliverable 3. Launch: streamlit run 03_dashboard/app.py"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import json
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from project_config import DATA, RESULTS, FEATURES, LABELS, UNITS, START, END
from analysis_core import association_table, transform

st.set_page_config(page_title='Singapore fertility evidence',page_icon='📊',layout='wide')
st.markdown('''<style>
.stApp {background:#f7f8fa;} h1,h2,h3 {color:#073b4c;}
[data-testid="stMetricValue"] {color:#073b4c;}
[data-testid="stSidebar"] {background:#eaf0f3;}
</style>''',unsafe_allow_html=True)


@st.cache_data
def load():
    return pd.read_csv(DATA/'analysis_dataset.csv',index_col='year')


def chart(fig):
    fig.update_layout(template='plotly_white',font=dict(family='Arial',size=14),
                      paper_bgcolor='rgba(0,0,0,0)',margin=dict(l=30,r=25,t=45,b=30))
    st.plotly_chart(fig,width='stretch')


d=load()
st.title('Singapore fertility: evidence for policy')
st.caption('Government export snapshots through 2025. Six candidate factors. National annual data.')
st.sidebar.header('Explore the evidence')
years=st.sidebar.slider('Analysis years',START,END,(START,END))
target=st.sidebar.selectbox('Outcome',['tfr','crude_birth_rate'],format_func=lambda x:LABELS[x])
mode=st.sidebar.radio('Association method',['Levels','Annual changes','After removing linear trends'],index=1)
feature=st.sidebar.selectbox('Candidate factor',FEATURES,format_func=lambda x:LABELS[x])
exclude=st.sidebar.checkbox('Exclude pandemic years 2020–2021',value=False)
st.sidebar.caption('Annual changes use absolute differences in the original units. Removing linear trends subtracts each series’ fitted straight-line trend.')
filtered=d.loc[years[0]:years[1]].copy()
if exclude: filtered=filtered.drop(index=[2020,2021],errors='ignore')
if len(filtered)<6:
    st.warning('Select at least six observed years to calculate associations. Trend charts remain descriptive.')
first,last=filtered.iloc[0],filtered.iloc[-1]
a,b,c,e=st.columns(4)
a.metric(f'TFR in {int(filtered.index[-1])}',f'{last.tfr:.2f}',f'{last.tfr-first.tfr:+.2f} since {int(filtered.index[0])}')
b.metric('Crude birth rate',f'{last.crude_birth_rate:.1f}','per 1,000 residents',delta_color='off')
c.metric('Resident live births',f'{last.resident_live_births:,.0f}')
e.metric('Observed years',len(filtered))
st.info('Associations describe national patterns. They do not establish causes, individual family decisions, or the birth-rate impact of a policy.')
overview,explore,predict,policy,sources=st.tabs(['Fertility trends','Factor explorer','Model backtest','Policy priorities','Sources and data'])

with overview:
    st.subheader('The fertility decline and its age pattern')
    chart(px.line(filtered.reset_index(),x='year',y=target,labels={'year':'Year',target:LABELS[target]},markers=True))
    agecols=['asfr_20_24','asfr_25_29','asfr_30_34','asfr_35_39','asfr_40_44']
    age=filtered[agecols].rename(columns={x:x.replace('asfr_','').replace('_','–') for x in agecols})
    age=age.rename_axis('year').reset_index().melt(id_vars='year',var_name='Age',value_name='Births per 1,000 women')
    chart(px.line(age,x='year',y='Births per 1,000 women',color='Age',labels={'year':'Year'}))
    st.caption('TFR is a period measure based on prevailing age-specific fertility rates. Crude birth rate divides births by the resident population and also reflects population structure. Age patterns suggest timing shifts but do not identify individual postponement.')

with explore:
    st.subheader(f'{LABELS[feature]} and {LABELS[target]}')
    dictionary=pd.read_csv(DATA/'data_dictionary.csv').set_index('variable')
    st.caption(dictionary.loc[feature,'limitation'])
    table=association_table(filtered,target=target,mode=mode)
    pair=transform(filtered[[target,feature]],mode).dropna()
    if len(pair)>=6 and not table.empty and feature in table.variable.to_list():
        row=table.set_index('variable').loc[feature]
        p,q,r=st.columns(3)
        p.metric('Correlation',f'{row.correlation:+.3f}')
        q.metric('Paired years',int(row.n))
        r.metric('Slope per 1 unit',f'{row.slope:+.4f}')
        st.caption(f'Outcome units: {UNITS[target]}. Factor units: {UNITS[feature]}. '+
            f'Approximate 95% HAC interval for the slope: [{row.ci_low:+.4f}, {row.ci_high:+.4f}]. '+
            'Separate one-factor regression, not a joint causal effect.')
        scatter=px.scatter(pair.reset_index(),x=feature,y=target,color='year',
                           labels={feature:f'{LABELS[feature]} ({UNITS[feature]})',target:LABELS[target]},hover_data=['year'])
        line_x=np.linspace(pair[feature].min(),pair[feature].max(),50)
        intercept=pair[target].mean()-row.slope*pair[feature].mean()
        scatter.add_trace(go.Scatter(x=line_x,y=intercept+row.slope*line_x,mode='lines',name='Fitted association',line=dict(color='#b64b35')))
        chart(scatter)
        comparison=table.assign(Factor=table.variable.map(LABELS))
        chart(px.bar(comparison,x='correlation',y='Factor',orientation='h',range_x=[-1,1],color='correlation',color_continuous_scale='RdBu',range_color=[-1,1]))
        st.dataframe(comparison[['Factor','n','correlation','slope','ci_low','ci_high','bh_q']].round(4),hide_index=True,width='stretch')
        st.caption('HAC intervals allow autocorrelation at lag 1. BH q-values adjust six comparisons within the selected method. These are exploratory screens with a small annual sample. Detrended intervals do not include uncertainty from estimating trends.')
    else:st.warning('Insufficient paired observations or no variation in this selection.')
    st.subheader('Do the variables share a long-term trend?')
    levels=filtered[[target,feature]].dropna()
    if not levels.empty:
        normalized=levels/levels.iloc[0]*100
        normalized.columns=[LABELS[x] for x in normalized.columns]
        chart(px.line(normalized.rename_axis('year').reset_index().melt(id_vars='year'),x='year',y='value',color='variable',labels={'value':f'Index ({int(levels.index[0])}=100)','variable':'Series'}))
    st.download_button('Download selected analysis data',filtered.to_csv().encode(),'selected_data.csv','text/csv')

with predict:
    st.subheader('Can six indicators predict next-year fertility?')
    st.caption('Fixed evaluation: TFR, training history from 2005, test years 2021–2025. Sidebar filters apply to EDA only. The backtest uses the prior year’s six indicators and a calendar trend. It refits before each test year. All tuning ends by 2020.')
    pred=pd.read_csv(RESULTS/'backtest_predictions.csv')
    scores=pd.read_csv(RESULTS/'backtest_scores.csv')
    chart(px.line(pred.melt(id_vars='year'),x='year',y='value',color='variable',markers=True,labels={'value':'TFR (births per woman)','variable':'Series'}))
    st.dataframe(scores.round(4),hide_index=True,width='stretch')
    best=scores.sort_values('mae').iloc[0]
    st.write(f'The lowest average absolute error in this five-year test is {best["model"].replace("_"," ")} ({best.mae:.4f} births per woman).')
    st.caption('This is a retrospective backtest with revised source snapshots. Publication delays and original data vintages are not reproduced. Five test years cannot establish stable predictive performance. No policy simulation is provided because the model does not identify intervention effects.')

with policy:
    st.subheader('Policy priorities and the evidence needed next')
    st.write('Use this analysis to prioritise further measurement and pilot evaluation. The data cannot estimate the number of births a subsidy or infrastructure investment would generate.')
    actions=pd.DataFrame([
        ['Family formation','Investigate barriers to marriage and first births','NPTD with research partners','Marriage timing, intentions and first-birth transitions'],
        ['Housing','Evaluate existing support for young families','MND / HDB','Income-adjusted housing costs, waiting times and first-birth timing'],
        ['Caregiving and work','Measure childcare access and workplace constraints','MSF / ECDA / MOM','Net fees, available places, hours, leave use and parental earnings'],
        ['Financial resilience','Segment young households before designing support','DOS with authorised data partners','Age-specific assets, debt-service burden and income'],
    ],columns=['Priority','Proposed action','Suggested owner','Additional evidence'])
    st.dataframe(actions,hide_index=True,width='stretch')
    st.caption('These proposals complement Singapore’s announced 2026 marriage and parenthood measures. Historical observations end in 2025 and cannot evaluate those measures.')
    st.markdown('[2026 policy context](https://www.population.gov.sg/media-centre/helping-singaporeans-start-and-raise-families-with-confidence/)')
    st.write('12-month programme: months 1–2 agree definitions and data access; months 3–4 validate sources and publish EDA; months 5–6 design pilots and evaluation; months 7–9 implement and track uptake; months 10–12 report adoption, burden and feasibility. Track fertility outcomes beyond month 12 because birth responses take longer.')

with sources:
    st.subheader('Trace every measure to its source')
    st.dataframe(pd.read_csv(DATA/'data_dictionary.csv'),hide_index=True,width='stretch')
    st.dataframe(pd.read_csv(DATA/'data_quality.csv'),hide_index=True,width='stretch')
    for source in json.loads((DATA/'source_manifest.json').read_text()):
        st.markdown(f'**{source["title"]}** — [{source["table"]}]({source["url"]})')
        st.caption(f'{source["agency"]}. Source update: {source["data_last_updated"]}. Export date: {source["export_generated"]}.')
    st.write('Extraction rules: twelve observed months per year for CPI; Q4 stocks for balance sheets; annual values for births, marriage and transport. No interpolation or missing-value imputation. Actual-rent CPI is supplementary because it starts in 2015. The household balance-sheet series matches official table M700981, but the original CSV download timestamp is unavailable.')
    st.download_button('Download the complete project dataset',d.to_csv().encode(),'analysis_dataset.csv','text/csv')
