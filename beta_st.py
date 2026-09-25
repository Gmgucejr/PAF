#!/usr/bin/env python
# coding: utf-8

# pip list

# pip install lifelines

# pip install reliability

# pip freeze > requirement.txt

# In[1]:


#############################
###Script by: Galileo Guce Jr.
###Email: galileo.guce@geaerospace.com
###Date: 23-September-2026
#############################

import numpy as np
import pandas as pd
import datetime
import seaborn as sb
from pylab import rcParams
from matplotlib.dates import DateFormatter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import streamlit as st
import reliability
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)


# In[2]:


import warnings
warnings.filterwarnings("ignore")

from lifelines import WeibullFitter
wb = WeibullFitter()

from reliability.Fitters import Fit_Weibull_2P
from reliability.Probability_plotting import Weibull_probability_plot


# In[3]:


paf = pd.read_csv('https://raw.githubusercontent.com/Gmgucejr/PAF/refs/heads/main/PAF.csv')
paf.info()


# In[4]:


paf.columns = ['AIRCRAFT NR', 'PART NUMBER', 'SERIAL NUMBER', 'TSN', 'REMARKS']


# In[5]:


st.set_page_config(layout="wide")


# In[6]:


st.markdown(
    "<h1 style='font-family: Courier New; font-style: italic; font-weight: bold; font-size: 40px;color:red'>PAF T700 Fleet Weibull and LOB Projection</h1>",
    unsafe_allow_html=True,)


# In[7]:


paf['censor']=1


# In[8]:


for a in range(len(paf)):
    if paf.REMARKS.iloc[a] == 'CURRENTLY INSTALLED':
        paf.censor.iloc[a]=0
    else:
        paf.censor.iloc[a]=1


# In[9]:


wb.fit(durations=paf.TSN,event_observed=paf['censor'])


# wb.survival_function_.plot(kind='line')
# plt.xlabel('Hours')
# plt.ylabel('Reliability')
# plt.vlines(2000,0,wb.predict(2000),linestyle='--',color='r')
# plt.hlines(wb.predict(2000),2000,4000,linestyle='--',color='r')
# plt.text(100, 0.89,'Reliability (T=2K) = 89.69%')
# plt.show()

# In[10]:


print(wb.lambda_,wb.rho_)
scale = wb.lambda_
shape = wb.rho_


# print(f'Reliablity(T=1000) = {wb.predict(1000):.2%}\nReliablity(T=1500) = {wb.predict(1500):.2%}\nReliablity(T=2000) = {wb.predict(2000):.2%}\n')

# print(f'Failure Probability(T=1000) = {1-wb.predict(1000):.2%}\nFailure Probability(T=1500) = {1-wb.predict(1500):.2%}\nFailure Probability(T=2000) = {1-wb.predict(2000):.2%}')

# In[11]:


failures=paf[paf.censor==1].TSN
suspensions=paf[paf.censor==0].TSN


# In[12]:


paf['removal_date'] = '06-Sep-26'
paf['removal_date'] = pd.to_datetime(paf['removal_date'],format='mixed')


# In[13]:


#based on Weibull reliability rate 0f 89.69% @2K hours
#default utilization of 15hours/month/ESN
#default TAT of 180 days
tat=180
util=15
from datetime import datetime, timedelta
paf['current_date'] = '06-Sep-26'
paf['current_date'] = pd.to_datetime(paf['current_date'],format='mixed')
paf['TSLSV'] = 0
for b in range (len(paf)):
    if paf['TSN'].iloc[b]>2000:
        paf['TSLSV'].iloc[b] = paf['TSN'].iloc[b] - 2000
    else:
        paf['TSLSV'].iloc[b] = paf['TSN'].iloc[b]
    paf['removal_date'].iloc[b] = paf['current_date'].iloc[b] + timedelta(days = (2000 - (paf['TSLSV'].iloc[b]))/(util/30))


# In[14]:


#starting net spare count
net = len(paf[paf['REMARKS'] == 'SERVICEABLE'])


# In[15]:


paf['tat']=tat
paf['rfi_date'] = '06-Sep-26'
paf['rfi_date'] = pd.to_datetime(paf['rfi_date'],format='mixed')
for c in range (len(paf)):
    paf['rfi_date'].iloc[c]= paf['removal_date'].iloc[c] + timedelta(days = (paf['tat'].iloc[c])/1.0)


# In[16]:


datetime_series = pd.Series(pd.date_range("2026-10-01", periods=72, freq="ME"))


# In[17]:


paf1 = datetime_series.to_frame(name="TPP_date")


# In[18]:


paf1['removal_count']=0
paf2 = paf1.groupby(paf1['TPP_date'].dt.to_period('M'))['removal_count'].sum().to_frame().reset_index()


# In[19]:


paf2['return_count']=0


# In[20]:


paf['removal_count']=1
paf['return_count']=1


# In[21]:


paf3 = paf.groupby(paf['removal_date'].dt.to_period('M'))['removal_count'].sum().to_frame().reset_index()
paf4 = paf.groupby(paf['rfi_date'].dt.to_period('M'))['return_count'].sum().to_frame().reset_index()
paf3.rename(columns={'removal_date': 'TPP_date'}, inplace=True)
paf4.rename(columns={'rfi_date': 'TPP_date'}, inplace=True)
paf5 = pd.merge(paf3, paf4, on='TPP_date', how='outer')
paf5.fillna(0, inplace=True)
paf5 = paf5.astype({'removal_count': int, 'return_count': int})


# In[22]:


paf6 = pd.concat([paf2, paf5], ignore_index=True, join='outer')
paf6.fillna(0, inplace=True)


# In[23]:


paf7 = paf6.groupby('TPP_date').sum().reset_index()


# In[24]:


paf7['Net_Spare_Count']=net
for a in range (len(paf7)):
    if a > 0:
        paf7.Net_Spare_Count.iloc[a] = paf7['Net_Spare_Count'].iloc[a-1] + (paf7['return_count'].iloc[a] - paf7['removal_count'].iloc[a])


# In[25]:


paf7['TPP_date'] = paf7['TPP_date'].dt.to_timestamp()


# In[26]:


rcParams['figure.figsize'] = 18, 6


# In[27]:


paf8 = paf7.head(72)


# In[28]:


fig, ax = plt.subplots(1,2, figsize=(20, 10))
wb.survival_function_.plot(kind='line',ax=ax[0])
ax[0].set_title('Reliability (T=2K) = 89.69%')
ax[0].set_xlabel('Hours')
ax[0].set_ylabel('Reliability')

ax[0].vlines(2000,0,wb.predict(2000),linestyle='--',color='r')
ax[0].hlines(wb.predict(2000),2000,4000,linestyle='--',color='r')
ax[0].text(100, 0.89,'Reliability (T=2K) = 89.69%')
ax[0].text(0, 0.2, f'Shape={shape:.2F} \nScale={scale:.2F}')
ax[1] = Weibull_probability_plot(failures=failures.to_numpy(),right_censored=suspensions.to_numpy(), CI=0.95)
plt.tight_layout(h_pad=5)
plt.show()


# Weibull_probability_plot(failures=failures.to_numpy(),right_censored=suspensions.to_numpy(), CI=0.95)

# In[29]:


fig2, ax = plt.subplots()
ax.set_yticks([-2, -1, 0, 1, 2, 3, 4])
ax.plot(paf8['TPP_date'], paf8['Net_Spare_Count'])

ax.text(min(paf8['TPP_date']), min(paf8['Net_Spare_Count']), f'WTW TAT ={tat} days \n\nUtilization={util:}hrs/mo', c='blue')

plt.axhline(y=1, color='red', linestyle='--', linewidth=1.5)
plt.axvspan(paf8.TPP_date.iloc[46],paf8.TPP_date.iloc[49], color='yellow', alpha=0.2)
plt.xlabel("Date")
plt.ylabel("Net Spare Count")
plt.legend()
plt.title("Customer PAF T700 Line of Balance (LOB) Baseline Scenario")
plt.legend()
plt.show()


# In[30]:


paf2=paf[['AIRCRAFT NR', 'PART NUMBER', 'SERIAL NUMBER', 'TSN', 'REMARKS','removal_date', 'current_date', 'TSLSV', 'tat', 'rfi_date']]
paf2.columns = ['AIRCRAFT NR', 'PART NUMBER', 'SERIAL NUMBER', 'TSN', 'REMARKS', 'Weibull_Removal_Date', 'Current_Date', 'TSLSV', 'WTW_TAT', 'RFI_date']


# In[31]:


col3, col4 = st.columns([3, 3])
with col3:

    st.markdown(
    """
    <style>
    div[class*="stSelectbox"] label p {
        font-size: 26 !important;
        font-weight: bold !important;
        font-family: 'Courier New', monospace !important;
        font-weight: bold;
        color: green;
    }  
    div[data-baseweb="select"] span {
        font-size: 20 !important;
        font-family: 'Courier New', monospace !important;
    }
    </style>
    """,unsafe_allow_html=True)
    
    selected_record = st.selectbox("Select ESN:",options=paf2["SERIAL NUMBER"])
    selected_row = paf2[paf2["SERIAL NUMBER"]==selected_record]


# In[32]:


def highlight_row(row):
    color = 'background-color: yellow' if row["SERIAL NUMBER"] == selected_record else ''
    return [color] * len(row)
styled_df = paf2.style.apply(highlight_row, axis=1)
st.dataframe(styled_df)


# In[33]:


st.pyplot(fig2)


# In[34]:


st.pyplot(fig)


# In[35]:


st.write('<p style="font-size: 18px; color: red;">Edit Removal, RFI Dates, WTW TAT on the Table Below:</p>', unsafe_allow_html=True)


# In[36]:


col7, col8 = st.columns([3, 3])


# In[37]:


with col7:
    st.markdown(
        """
        <style>
        div[class*="stSelectbox"] label p {
            font-size: 22 !important;
            font-weight: bold !important;
            font-family: 'Courier New', monospace !important;
            font-weight: bold;
            color: green;
        }  
        div[data-baseweb="select"] span {
            font-size: 20 !important;
            font-family: 'Courier New', monospace !important;
        }
        </style>
        """,
    unsafe_allow_html=True)
    
    selected_period = st.selectbox("Select Period to Re-draw LOB Plot:",
    [24, 36, 48],
    index=0)


# In[38]:


col5, col6 = st.columns([3, 3])


# In[39]:


if "df" not in st.session_state:
    st.session_state.df=paf2

def update_column():
    # Fetch the newly selected value from the selectbox widget state
    chosen_status = st.session_state.status_select
    
    # Assign the new value to the entire column
    st.session_state.df["WTW_TAT"] = chosen_status

with col5:

    st.markdown(
        """
        <style>
        div[class*="stSelectbox"] label p {
            font-size: 20 !important;
            font-weight: bold !important;
            font-family: 'Courier New', monospace !important;
            font-weight: bold;
            color: green;
        }  
        div[data-baseweb="select"] span {
            font-size: 22 !important;
            font-family: 'Courier New', monospace !important;
        }
        </style>
        """,
    unsafe_allow_html=True)
    
    tat = st.selectbox(
    "Select an ave. shop WTW TAT (days):",
    [180, 360, 540, 730],
    key="status_select",
    on_change=update_column
    )

paf2 = st.session_state.df
st.write("Current WTW TAT Selection:", tat)


# In[40]:


with col6:

    st.markdown(
        """
        <style>
        div[class*="stSelectbox"] label p {
            font-size: 20 !important;
            font-weight: bold !important;
            font-family: 'Courier New', monospace !important;
            font-weight: bold;
            color: green;
        }  
        div[data-baseweb="select"] span {
            font-size: 22 !important;
            font-family: 'Courier New', monospace !important;
        }
        </style>
        """,
    unsafe_allow_html=True)
    
    util = st.selectbox(
    "Select an ave. utilization (hrs/month):",
    [15, 20, 25],
    index=0)
st.write("Current Utilization Selection:", util)


# In[41]:


if "df2" not in st.session_state:
    st.session_state.df2 = paf2

# 2. Define the callback function to handle calculations
def update_dependent_columns():
    # Access the raw change dictionary tracked by the data_editor's key
    changes = st.session_state["editor_changes"]
    
    # Process only the rows that were edited
    for row_index, changed_cols in changes["edited_rows"].items():
        for col, new_val in changed_cols.items():
            # Apply the user's manual change to the session state DataFrame
            st.session_state.df2.at[row_index, col] = new_val
            
        # Recalculate dependent columns for the modified row
        Weibull_Removal_Date = st.session_state.df2.at[row_index, "Weibull_Removal_Date"]
        WTW_TAT = st.session_state.df2.at[row_index, "WTW_TAT"]
        st.session_state.df2.at[row_index, "RFI_date"] = Weibull_Removal_Date + timedelta(days = WTW_TAT/1.0)

# 3. Render the data editor
# Bind the editor to session state and hook up the callback
paf2 = st.data_editor(
    st.session_state.df2,
    key="editor_changes",
    on_change=update_dependent_columns,
    disabled=['AIRCRAFT NR', 'PART NUMBER', 'SERIAL NUMBER', 'TSN', 'REMARKS','Current_Date', 'TSLSV',
       'removal_count', 'return_count'],
    use_container_width=True,
    column_config={
        "Weibull_Removal_Date": st.column_config.DateColumn("Weibull_Removal_Date ✏️"),
        "WTW_TAT": st.column_config.NumberColumn("WTW_TAT ✏️", format="%.0f"),
        "RFI_date": st.column_config.DateColumn("RFI_date ✏️")},
    hide_index=True,
)
st.session_state.df.style.set_properties(subset=['Weibull_Removal_Date', 'WTW_TAT', 'RFI_date'], **{'background-color': '#FFFFCC'})


# In[42]:


###########Re-draw plot after manual data edits:
#for b in range (len(paf2)):

    #paf2['Weibull_Removal_Date'].iloc[b] = paf2['Current_Date'].iloc[b] + timedelta(days = (2000 - (paf2['TSLSV'].iloc[b]))/(util/30))


#starting net spare count
net=3
#net = len(paf2[paf2['REMARKS'] == 'SERVICEABLE'])


#for c in range (len(paf2)):
    #paf2['RFI_date'].iloc[c]= paf2['Weibull_Removal_Date'].iloc[c] + timedelta(days = (paf2['WTW_TAT'].iloc[c])/1.0)



datetime_series = pd.Series(pd.date_range("2026-10-01", periods=selected_period, freq="ME"))


paf10 = paf1.groupby(paf1['TPP_date'].dt.to_period('M'))['removal_count'].sum().to_frame().reset_index()


paf10['return_count']=0


paf2['removal_count']=1
paf2['return_count']=1


paf3 = paf2.groupby(paf2['Weibull_Removal_Date'].dt.to_period('M'))['removal_count'].sum().to_frame().reset_index()
paf4 = paf2.groupby(paf2['RFI_date'].dt.to_period('M'))['return_count'].sum().to_frame().reset_index()
paf3.rename(columns={'Weibull_Removal_Date': 'TPP_date'}, inplace=True)
paf4.rename(columns={'RFI_date': 'TPP_date'}, inplace=True)
paf5 = pd.merge(paf3, paf4, on='TPP_date', how='outer')
paf5.fillna(0, inplace=True)
paf5 = paf5.astype({'removal_count': int, 'return_count': int})


paf6 = pd.concat([paf10, paf5], ignore_index=True, join='outer')
paf6.fillna(0, inplace=True)


paf7 = paf6.groupby('TPP_date').sum().reset_index()


paf7['Net_Spare_Count']=net
for a in range (len(paf7)):
    if a > 0:
        paf7.Net_Spare_Count.iloc[a] = paf7['Net_Spare_Count'].iloc[a-1] + (paf7['return_count'].iloc[a] - paf7['removal_count'].iloc[a])

paf7['TPP_date'] = paf7['TPP_date'].dt.to_timestamp()


paf8 = paf7.head(selected_period)


# In[43]:


fig3, ax = plt.subplots()
ax.set_yticks([-2, -1, 0, 1, 2, 3, 4])
ax.plot(paf8['TPP_date'], paf8['Net_Spare_Count'])

ax.text(min(paf8['TPP_date']), min(paf8['Net_Spare_Count']), f'WTW TAT ={tat} days \n\nUtilization={util:}hrs/mo', c='green')

plt.axhline(y=1, color='red', linestyle='--', linewidth=1.5)
#plt.axvspan(paf8.TPP_date.iloc[46],paf8.TPP_date.iloc[49], color='yellow', alpha=0.2)
plt.xlabel("Date")
plt.ylabel("Net Spare Count")
plt.legend()
plt.title("Customer PAF T700 Line of Balance (LOB) UPDATED Scenario")
plt.legend()
plt.show()


# In[44]:


st.write('<p style="font-size: 18px; color: green;">Updated LOB Projection Scenario:</p>', unsafe_allow_html=True)
st.pyplot(fig3)


# In[45]:


paf.to_csv(r'C:\Users\212554084\Box\Python_data\PAF_updated.csv')


# In[46]:


st.stop()


# In[47]:


#get_ipython().system('jupyter nbconvert --to script --output-dir="C:\\Users\\212554084\\Downloads" beta_st3.ipynb')


# In[ ]:




