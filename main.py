# -*- coding: utf-8 -*-
"""
Created on Tue Aug 23 20:49:47 2022

@author: Abinash.m
"""

import streamlit as st
import pandas as pd
import numpy as np


def day_level(df):
    day = df.copy()
    day['Total'] = day.sum(axis=1)
    day.reset_index(inplace=True)
    day['Date'] = pd.to_datetime(day['Date'])
    day['wom'] = day['Date'].apply(lambda d: (d.day-1) // 7+ 1)
    day['day'] = day['Date'].dt.day_name()
    day["wk&day"] = day["wom"].astype(str) + day["day"]
    day['month'] = day['Date'].dt.month_name()
    day['month_no'] = day['Date'].dt.month
    day.drop(day.iloc[:, 1:len(day.columns)-6], inplace=True, axis=1)
    day.sort_values(by='month_no',ascending=True)
    sum_month_wise = day.groupby(['month']).agg(
                sum_month_wise=('Total', 'sum')).reset_index()
    day = day.merge(sum_month_wise, on=['month'], how='left')
    day['call_percent'] = round((day['Total']/day['sum_month_wise'])*100,2)

    day = day.sort_values(by='Date',ascending=True)
    day_4_month = day.sort_values(by="Date",ascending=True).set_index("Date").last("3M")

    distribution_by_week_pivot   = day_4_month.pivot_table(index=['wk&day'],columns= 'month', values='call_percent', aggfunc='first')
    distribution_by_week_pivot['distribution'] = distribution_by_week_pivot.mean(axis=1)
    distribution_by_week_pivot = distribution_by_week_pivot
    day= day.merge(distribution_by_week_pivot, on=['wk&day'], how='left')
    day_copy = day.copy()
    day_copy.drop(['Date','Total','sum_month_wise','call_percent','month_no'],inplace=True,axis=1)
    day_copy = day_copy.groupby('wk&day').mean()
    day_copy =day_copy.fillna(0)
    day_copy['%dict'] = (day_copy['distribution']/sum(day_copy['distribution']))*100
    day =day.fillna(0)
    sum_month_wise = sum_month_wise.fillna(0)
    day_4_month = day_4_month.fillna(0)
    distribution_by_week_pivot = distribution_by_week_pivot.fillna(0)
    day_copy = day_copy.fillna(0)
    return round(day),sum_month_wise,day_4_month,distribution_by_week_pivot,round(day_copy)

def month(df):
    day_level_func = day_level(df)
    day_4_month = day_level_func[2]
    day_copy  = day_level_func[4]
    day_4_month.reset_index(inplace=True)
    day_last_date = day_4_month['Date'].iloc[-1]
    month= pd.date_range('2022-09-01', periods=152, freq="D")
    month = pd.DataFrame(month)
    month.columns = ['future_Date']
    month_df = month.copy()
    month_df['wom'] = month_df['future_Date'].apply(lambda d: (d.day-1) // 7+ 1)
    month_df['day'] = month_df['future_Date'].dt.day_name()
    month_df["wk&day"] = month_df["wom"].astype(str) + month_df["day"]
    month_df['month'] = month_df['future_Date'].dt.month_name()
    select_distribution =(day_copy['distribution'])
    select_distribution = pd.DataFrame(select_distribution)
    month_merge = month_df.merge(select_distribution, on=['wk&day'], how='left')
    forecast = {'month':['September','October','November',"December","January"],
               'Value':[6059,5580,5827,6701,6307]}
    forecast = pd.DataFrame.from_dict(forecast)
    forecast_df = month_merge.merge(forecast, on=['month'], how='left')
    forecast_df['forecast'] = ((forecast_df['distribution']*forecast_df['Value'])/100)
    forecast_df = round(forecast_df,2)
    return month,month_df,forecast,round(forecast_df)
def interval(df):
    month_func = month(df)
    forecast_df = month_func[3]
    interval = df.copy()
    interval.reset_index(inplace=True)
    interval['Date'] = pd.to_datetime(interval['Date'])
    interval = interval.sort_values(by="Date",ascending=True).set_index("Date").last("3M")
    interval.reset_index(inplace=True)
    interval['day'] = interval['Date'].dt.day_name()
    interval_day = interval.groupby('day').mean()
    interval_day['Total'] = interval_day.sum(axis=1)
    interval_day = round(interval_day)
    forecast_df_1 = forecast_df.iloc[:,[0,2,7]]
    interval_df = interval_day.iloc[:,0:len(interval_day.columns)-1].divide(interval_day.iloc[:,-1],axis=0)
    interval_day = round(interval_day*100,2)
    interval_merge = interval_df.merge(forecast_df_1, on=['day'], how='left')
    interval_merge['month'] = interval_merge['future_Date'].dt.month_name()
    interval_merge.set_index(['day','future_Date','month'],inplace=True)
    interval_merge.reset_index(inplace=True)
    interval_merge.iloc[:,3:len(interval_merge.columns)-1] = (interval_merge.iloc[:,3:len(interval_merge.columns)-1].multiply(interval_merge.fillna(0).iloc[:,-1],axis=0))

    interval_merge = interval_merge.sort_values(by="future_Date",ascending=True)
    interval_merge_sum =  interval_merge.groupby(['month']).agg(
               sum_month_wise=('forecast', 'sum')).reset_index()
    return  interval,interval_day,round(interval_merge),interval_merge_sum
def main():
    st.header('Upload the data with date column')
    data = st.file_uploader("Upload file", type=['csv' ,'xlsx'])
    if data is not None:
        try:
            df = pd.read_excel(data) 
            df = df.iloc[:,[6,7,12]]
                    #converting Datetime to date
            df['Date'] = pd.to_datetime(df['Date'] ,errors = 'coerce',format = '%Y-%m-%d').dt.strftime("%Y-%m-%d")
                    
            df = df.pivot_table(index=['Date'],columns= 'Interval 15 Minutes', values='Queue Offered',aggfunc=sum)
            df = df.fillna(0)
            day_level_func = day_level(df)
            #day_level_func  = round(day_level_func)
            month_func = month(df)
            #month_func = round(month_func)
            interval_func = interval(df)
            #interval_func= round(interval_func)
            choice = st.radio(
             "Chhose any one option",
             ('Actual data', 'Day level', '3 month distribution','Forecast','Interval Wise'))
                    
            if choice =='Actual data':
                st.subheader("Actual DataFrame Uploaded by the user")
                st.dataframe(round(df.convert_dtypes()))
            elif choice=='Day level':
                st.subheader("Data converted to day level")
                st.dataframe((day_level_func[0].convert_dtypes()))
            elif choice=='3 month distribution':
                st.subheader("month wise distribution")
                st.dataframe((day_level_func[4].convert_dtypes()))
            elif choice=='Forecast':
                st.subheader("forecasted data converted by the past distribution")
                st.dataframe((month_func[3].convert_dtypes()))
            elif choice=='Interval Wise':
                st.subheader("forecasted data converted into interval wise")
                st.dataframe((interval_func[2].T.convert_dtypes()))
            
        except Exception:
            st.write('please upload a excel file')

    
    
main()
