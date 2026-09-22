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

###Date: 22-September-2026

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

#import reliability

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





paf['censor']=1





# In[5]:





for a in range(len(paf)):

    if paf.REMARKS.iloc[a] == 'CURRENTLY INSTALLED':

        paf.censor.iloc[a]=0

    else:

        paf.censor.iloc[a]=1





# In[6]:





wb.fit(durations=paf.TSN,event_observed=paf['censor'])





# wb.survival_function_.plot(kind='line')

# plt.xlabel('Hours')

# plt.ylabel('Reliability')

# plt.vlines(2000,0,wb.predict(2000),linestyle='--',color='r')

# plt.hlines(wb.predict(2000),2000,4000,linestyle='--',color='r')

# plt.text(100, 0.89,'Reliability (T=2K) = 89.69%')

# plt.show()



# In[7]:





print(wb.lambda_,wb.rho_)

scale = wb.lambda_

shape = wb.rho_





# print(f'Reliablity(T=1000) = {wb.predict(1000):.2%}\nReliablity(T=1500) = {wb.predict(1500):.2%}\nReliablity(T=2000) = {wb.predict(2000):.2%}\n')



# print(f'Failure Probability(T=1000) = {1-wb.predict(1000):.2%}\nFailure Probability(T=1500) = {1-wb.predict(1500):.2%}\nFailure Probability(T=2000) = {1-wb.predict(2000):.2%}')



# In[8]:





failures=paf[paf.censor==1].TSN

suspensions=paf[paf.censor==0].TSN





# In[9]:





#Assuming 15hrs/month utilization

util = 15

paf['removal_date'] = '06-Sep-26'

paf['removal_date'] = pd.to_datetime(paf['removal_date'],format='mixed')





# In[10]:





#based on Weibull reliability rate 0f 89.69% @2K hours

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





# In[11]:





#starting net spare count

net = len(paf[paf['REMARKS'] == 'SERVICEABLE'])





# In[12]:





#Assuming 90 days WTW TAT

tat=90





# In[13]:





paf['tat']=tat

paf['rfi_date'] = '06-Sep-26'

paf['rfi_date'] = pd.to_datetime(paf['rfi_date'],format='mixed')

for c in range (len(paf)):

    paf['rfi_date'].iloc[c]= paf['removal_date'].iloc[c] + timedelta(days = (paf['tat'].iloc[c])/1.0)





# In[14]:





datetime_series = pd.Series(pd.date_range("2026-10-01", periods=72, freq="ME"))





# In[15]:





paf1 = datetime_series.to_frame(name="TPP_date")





# In[16]:





paf1['removal_count']=0

paf2 = paf1.groupby(paf1['TPP_date'].dt.to_period('M'))['removal_count'].sum().to_frame().reset_index()





# In[17]:





paf2['return_count']=0





# In[18]:





paf['removal_count']=1

paf['return_count']=1





# In[19]:





paf3 = paf.groupby(paf['removal_date'].dt.to_period('M'))['removal_count'].sum().to_frame().reset_index()

paf4 = paf.groupby(paf['rfi_date'].dt.to_period('M'))['return_count'].sum().to_frame().reset_index()

paf3.rename(columns={'removal_date': 'TPP_date'}, inplace=True)

paf4.rename(columns={'rfi_date': 'TPP_date'}, inplace=True)

paf5 = pd.merge(paf3, paf4, on='TPP_date', how='outer')

paf5.fillna(0, inplace=True)

paf5 = paf5.astype({'removal_count': int, 'return_count': int})





# In[20]:





paf6 = pd.concat([paf2, paf5], ignore_index=True, join='outer')

paf6.fillna(0, inplace=True)





# In[21]:





paf7 = paf6.groupby('TPP_date').sum().reset_index()





# In[22]:





paf7['Net_Spare_Count']=net

for a in range (len(paf7)):

    if a > 0:

        paf7.Net_Spare_Count.iloc[a] = paf7['Net_Spare_Count'].iloc[a-1] + (paf7['return_count'].iloc[a] - paf7['removal_count'].iloc[a])





# In[23]:





paf7['TPP_date'] = paf7['TPP_date'].dt.to_timestamp()





# In[24]:





rcParams['figure.figsize'] = 18, 6





# In[25]:





paf8 = paf7.head(72)





# In[26]:





st.set_page_config(layout="wide")





# In[27]:





st.title("PAF T700 Fleet Weibull and LOB")





# In[28]:





fig, ax = plt.subplots(2,1, figsize=(20, 10))

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

ax.set_yticks([0, 1, 2, 3, 4])

ax.plot(paf8['TPP_date'], paf8['Net_Spare_Count'])



plt.axhline(y=1, color='red', linestyle='--', linewidth=1.5)

plt.axvspan(paf8.TPP_date.iloc[46],paf8.TPP_date.iloc[49], color='yellow', alpha=0.2)

plt.xlabel("Date")

plt.ylabel("Net Spare Count")

plt.legend()

plt.title("Customer PAF T700 Line of Balance (LOB) Baseline Scenario")

plt.legend()

plt.show()





# In[30]:





col1, col2 = st.columns([3, 3])





# In[31]:





with col1:

    st.dataframe(paf)





# In[32]:





with col2:

    st.pyplot(fig)





# In[33]:





st.pyplot(fig2)





# In[34]:





paf





# In[35]:





paf.to_csv(r'C:\Users\212554084\Box\Python_data\PAF_updated.csv')





# In[36]:





st.stop()





# In[38]:





get_ipython().system('jupyter nbconvert --to script --output-dir="C:\\Users\\212554084\\Downloads" beta_st.ipynb')





# In[ ]:









