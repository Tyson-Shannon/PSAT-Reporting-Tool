#for proof point simulated attack training (PSAT) phising campaign reports
#plots 5 years of report, click, credential submission, no actins, and training message data
#nice high level report to show training over time that can be generated at any time
#change data and column names as needed

#Copyright (c) 2024 Tyson Shannon - MIT license

import requests
import pandas as pd
import time
import datetime
import matplotlib.pyplot as plt 
import csv
import numpy as np

#get data in csv form
today = datetime.date.today()
first = today.replace(day=1)
last_month = first - datetime.timedelta(days=1)
first_year = last_month.year-5

start_date = str(first_year)+"-01-01" #"yyyy-MM-dd" (5 years ago)
end_date = last_month.strftime("%Y-%m")+"-28" #"yyyy-MM-dd" (28th day of previous month)
api_key = 'Enter API Key Here'#CHANGE ME!!!!

def connect_to_api(page_number, start_date, end_date, api_key):
    url = f'Enter API URL here with necessary variables i.e.: {page_number} {start_date} {end_date}'#CHANGE ME!!!!
    headers = {'x-apikey-token': api_key}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        print(f'Success: {response.status_code}')
        json_response = response.json()
        return json_response
    else:
        print(f'Error: {response.status_code}')
        return None  #return None when the request fails

#loop over pages of data until page is empty
page_number = 1
while(True):
    json_contents = connect_to_api(page_number, start_date, end_date, api_key)
    
    #check if json_contents is None before trying to access its 'data' field
    if json_contents is not None:
        #convert JSON to DataFrame
        df = pd.json_normalize(json_contents['data'])
        
        #remove "attributes." prefix from column names
        df.columns = df.columns.astype(str).str.replace('attributes.', '', regex=True)
        
        #breaks once page is empty
        if "Empty DataFrame" in str(df):
            break

        #write column names in the first iteration, append without headers in the following iterations
        if page_number == 1:
            df.to_csv(end_date+' phishing_extended_output_past_5yr.csv', index=False)
        else:
            df.to_csv(end_date+' phishing_extended_output_past_5yr.csv', mode='a', header=False, index=False)

        print(df)
    else:
        print(f'Failed to get data for page {page_number}')
        break
    
    #add a delay between requests to avoid hitting the rate limit
    time.sleep(1)  #delay for 1 second
    #move to next page
    page_number = page_number+1

#read csv file
df_total = pd.read_csv(end_date+' phishing_extended_output_past_5yr.csv')
total_rows = df_total.shape[0]  # or use len(df_total)
print(f'Total number of rows: {total_rows}')

#plot our csv data yearly
#remove duplicate rows from multiple link clicks and such
df_total = df_total.drop_duplicates(subset=['useremailaddress', 'campaignname', 'eventtype'])

#extract date
df_total['campaignstartdate'] = pd.to_datetime(df_total['campaignstartdate'])
df_total['year'] = df_total['campaignstartdate'].dt.year

#exclude rows where 'year' is None
df_total = df_total[df_total['year'].notna()]

#filter the data to include only the specified event types for bar graph
df_bars = df_total[df_total['eventtype'].isin(["Reported", "Email Click", "Data Submission", "No Action"])]
#filter the data to include only the specified event types for line graph
df_line = df_total[df_total['eventtype'].isin(["TM Sent"])]

#group the data by 'year' and 'eventtype', and count the number of each combination
grouped = df_bars.groupby(['year', 'eventtype']).size().reset_index(name='counts')
groupedLine = df_line.groupby(['year', 'eventtype']).size().reset_index(name='counts')

#calculate the total number of events for each year
total_counts = grouped.groupby('year')['counts'].sum()

#create a new DataFrame that includes all years and event types
all_data = pd.DataFrame([(year, event_type) for year in grouped['year'].unique() for event_type in grouped['eventtype'].unique()], columns=['year', 'eventtype'])
all_data_for_line = pd.DataFrame([(year, event_type) for year in grouped['year'].unique() for event_type in groupedLine['eventtype'].unique()], columns=['year', 'eventtype'])

#merge the new DataFrame with the grouped data, filling in a percentage of 0 where no events occurred
all_data = all_data.merge(grouped, on=['year', 'eventtype'], how='left').fillna(0)
all_data_for_line = all_data_for_line.merge(groupedLine, on=['year', 'eventtype'], how='left').fillna(0)

#convert the counts to percentages relative to "Email View" events
all_data['percentage'] = all_data.apply(lambda row: row['counts'] / total_counts[row['year']] * 100, axis=1)

#get the unique years and event types
years = all_data['year'].unique()
event_types = ["Reported", "Email Click", "Data Submission"]

#assign a unique color to each event type
colors = {"Reported": (0.8, 0.8, 0.8), "Email Click": "black", "Data Submission": "red"}

#create a bar chart for each year
bar_width = 0.2
for j, event_type in enumerate(event_types):
    percentages = []
    for i, year in enumerate(years):
        data = all_data[all_data['year'] == year]
        event_data = data[data['eventtype'] == event_type]['percentage']
        percentage = event_data.values[0] if len(event_data) > 0 else 0
        percentages.append(percentage)
    plt.bar(np.arange(len(years)) + j * bar_width, percentages, color=colors[event_type], width=bar_width, label=event_type, edgecolor="black", zorder=2)

#calculate the percentage of "TM Sent" events relative to "Email Clicked" events for each year
tm_sent_data = all_data_for_line[all_data_for_line['eventtype'] == "TM Sent"].sort_values('year')
email_clicked_data = all_data[all_data['eventtype'] == "Email Click"].sort_values('year')
tm_sent_percentages = tm_sent_data['counts'].values / email_clicked_data['counts'].values * 100

#create a line graph for the "TM Sent" event type
plt.plot(np.arange(len(years)), tm_sent_percentages, color='blue', marker='o', label='Training Complete', zorder=3)

#set the x-ticks to be the years
plt.xticks(np.arange(len(years)) + bar_width, years)

#set the y-ticks to go up by tens
plt.yticks(np.arange(0, 110, 10))

plt.title(end_date+' Phishing and Awareness')
plt.xlabel('Years')
plt.ylabel('Percentage')
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(axis='y', color=(0.9, 0.9, 0.9), zorder=1)

plt.show()

#plot our csv data monthly
#read csv file
df_total = pd.read_csv(end_date+' phishing_extended_output_past_5yr.csv')

#remove duplicate rows from multiple link clicks and such
df_total = df_total.drop_duplicates(subset=['useremailaddress', 'campaignname', 'eventtype'])

#extract month
df_total['campaignstartdate'] = pd.to_datetime(df_total['campaignstartdate'])
df_total['month'] = df_total['campaignstartdate'].dt.to_period('M')
#filter to include only the last 12 months
df_total = df_total[df_total['campaignstartdate'] >= (pd.to_datetime('today') - pd.DateOffset(months=12))]
#exclude rows where 'month' is None
df_total = df_total[df_total['month'].notna()]
#change month names to shorthand format
df_total['month_name'] = df_total['month'].dt.strftime('%b')

#filter the data to include only the specified event types for bar graph
df_bars = df_total[df_total['eventtype'].isin(["Reported", "Email Click", "Data Submission", "No Action"])]
#filter the data to include only the specified event types for line graph
df_line = df_total[df_total['eventtype'].isin(["TM Sent"])]

#group data by month and event type
grouped_monthly = df_bars.groupby(['month', 'eventtype']).size().reset_index(name='counts')
groupedLine_monthly = df_line.groupby(['month', 'eventtype']).size().reset_index(name='counts')

#number of events each month
total_counts_monthly = grouped_monthly.groupby('month')['counts'].sum()

#new data frame
all_data_monthly = pd.DataFrame([(month, event_type) for month in grouped_monthly['month'].unique() for event_type in grouped_monthly['eventtype'].unique()], columns=['month', 'eventtype'])
all_data_for_line_monthly = pd.DataFrame([(month, event_type) for month in grouped_monthly['month'].unique() for event_type in groupedLine_monthly['eventtype'].unique()], columns=['month', 'eventtype'])

#merge the new DataFrame with the grouped data, filling in a percentage of 0 where no events occurred
all_data_monthly = all_data_monthly.merge(grouped_monthly, on=['month', 'eventtype'], how='left').fillna(0)
all_data_for_line_monthly = all_data_for_line_monthly.merge(groupedLine_monthly, on=['month', 'eventtype'], how='left').fillna(0)

#counts to percentages
all_data_monthly['percentage'] = all_data_monthly.apply(lambda row: row['counts'] / total_counts_monthly[row['month']] * 100, axis=1)

#bar chart for each month (colors and event_types same variables as yearly)
months = all_data_monthly['month'].unique()
for j, event_type in enumerate(event_types):
    percentages = []
    for i, month in enumerate(months):
        data = all_data_monthly[all_data_monthly['month'] == month]
        event_data = data[data['eventtype'] == event_type]['percentage']
        percentage = event_data.values[0] if len(event_data) > 0 else 0
        percentages.append(percentage)
    plt.bar(np.arange(len(months)) + j * bar_width, percentages, color=colors[event_type], width=bar_width, label=event_type, edgecolor="black", zorder=2)

#line graph for training data
tm_sent_data_monthly = all_data_for_line_monthly[all_data_for_line_monthly['eventtype'] == "TM Sent"].sort_values('month')
email_clicked_data_monthly = all_data_monthly[all_data_monthly['eventtype'] == "Email Click"].sort_values('month')
tm_sent_percentages_monthly = tm_sent_data_monthly['counts'].values / email_clicked_data_monthly['counts'].values * 100
plt.plot(np.arange(len(months)), tm_sent_percentages_monthly, color='blue', marker='o', label='Training Complete', zorder=3)

month_names = df_total['month_name'].unique()

#xticks set to months
plt.xticks(np.arange(len(months)) + bar_width, month_names)

#set the y-ticks to go up by tens
plt.yticks(np.arange(0, 110, 10))

plt.title(end_date+' Phishing and Awareness (Monthly)')
plt.xlabel('Months')
plt.ylabel('Percentage')
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(axis='y', color=(0.9, 0.9, 0.9), zorder=1)

plt.show()

#plot our csv data quarterly
#read csv file
df_total = pd.read_csv(end_date+' phishing_extended_output_past_5yr.csv')

#remove duplicate rows from multiple link clicks and such
df_total = df_total.drop_duplicates(subset=['useremailaddress', 'campaignname', 'eventtype'])

#extract quarter
df_total['campaignstartdate'] = pd.to_datetime(df_total['campaignstartdate'])
df_total['quarter'] = df_total['campaignstartdate'].dt.to_period('Q')
#filter to include only the last 4 quarters
df_total = df_total[df_total['campaignstartdate'] >= (pd.to_datetime('today') - pd.DateOffset(months=12))]
# Exclude rows where 'month' is None
df_total = df_total[df_total['quarter'].notna()]

#filter the data to include only the specified event types for bar graph
df_bars = df_total[df_total['eventtype'].isin(["Reported", "Email Click", "Data Submission", "No Action"])]
#filter the data to include only the specified event types for line graph
df_line = df_total[df_total['eventtype'].isin(["TM Sent"])]

#group data by quarter and event type
grouped_quarterly = df_bars.groupby(['quarter', 'eventtype']).size().reset_index(name='counts')
groupedLine_quarterly = df_line.groupby(['quarter', 'eventtype']).size().reset_index(name='counts')

#total number of events per quarter
total_counts_quarterly = grouped_quarterly.groupby('quarter')['counts'].sum()

#new data frame
all_data_quarterly = pd.DataFrame([(quarter, event_type) for quarter in grouped_quarterly['quarter'].unique() for event_type in grouped_quarterly['eventtype'].unique()], columns=['quarter', 'eventtype'])
all_data_for_line_quarterly = pd.DataFrame([(quarter, event_type) for quarter in grouped_quarterly['quarter'].unique() for event_type in groupedLine_quarterly['eventtype'].unique()], columns=['quarter', 'eventtype'])

#merge the new DataFrame with the grouped data, filling in a percentage of 0 where no events occurred
all_data_quarterly = all_data_quarterly.merge(grouped_quarterly, on=['quarter', 'eventtype'], how='left').fillna(0)
all_data_for_line_quarterly = all_data_for_line_quarterly.merge(groupedLine_quarterly, on=['quarter', 'eventtype'], how='left').fillna(0)

#counts to percents
all_data_quarterly['percentage'] = all_data_quarterly.apply(lambda row: row['counts'] / total_counts_quarterly[row['quarter']] * 100, axis=1)

#bar chart for each quarter (colors and event_types same variables as yearly)
quarters = all_data_quarterly['quarter'].unique()
for j, event_type in enumerate(event_types):
    percentages = []
    for i, quarter in enumerate(quarters):
        data = all_data_quarterly[all_data_quarterly['quarter'] == quarter]
        event_data = data[data['eventtype'] == event_type]['percentage']
        percentage = event_data.values[0] if len(event_data) > 0 else 0
        percentages.append(percentage)
    plt.bar(np.arange(len(quarters)) + j * bar_width, percentages, color=colors[event_type], width=bar_width, label=event_type, edgecolor="black", zorder=2)

#line graph for training data
tm_sent_data_quarterly = all_data_for_line_quarterly[all_data_for_line_quarterly['eventtype'] == "TM Sent"].sort_values('quarter')
email_clicked_data_quarterly = all_data_quarterly[all_data_quarterly['eventtype'] == "Email Click"].sort_values('quarter')
tm_sent_percentages_quarterly = tm_sent_data_quarterly['counts'].values / email_clicked_data_quarterly['counts'].values * 100
plt.plot(np.arange(len(quarters)), tm_sent_percentages_quarterly, color='blue', marker='o', label='Training Complete', zorder=3)

#set xticks to quarters
plt.xticks(np.arange(len(quarters)) + bar_width, quarters)

#set the y-ticks to go up by tens
plt.yticks(np.arange(0, 110, 10))

plt.title(end_date+' Phishing and Awareness (Quarterly)')
plt.xlabel('Quarters')
plt.ylabel('Percentage')
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(axis='y', color=(0.9, 0.9, 0.9), zorder=1)

plt.show()

#plot our csv data to compare last two years
#read csv file
df_total = pd.read_csv(end_date+' phishing_extended_output_past_5yr.csv')

#remove duplicate rows from multiple link clicks and such
df_total = df_total.drop_duplicates(subset=['useremailaddress', 'campaignname', 'eventtype'])

#extract year
df_total['campaignstartdate'] = pd.to_datetime(df_total['campaignstartdate'])
df_total['year'] = df_total['campaignstartdate'].dt.year
#filter to include only the last 2 years
df_total = df_total[df_total['campaignstartdate'] >= (pd.to_datetime(str(last_month.year-1)+'-01-01'))]
# Exclude rows where 'month' is None
df_total = df_total[df_total['year'].notna()]

#filter the data to include only the specified event types for bar graph
df_bars = df_total[df_total['eventtype'].isin(["Reported", "Email Click", "Data Submission", "No Action"])]
#filter the data to include only the specified event types for line graph
df_line = df_total[df_total['eventtype'].isin(["TM Sent"])]

#group data by year and event type
grouped_yearly = df_bars.groupby(['year', 'eventtype']).size().reset_index(name='counts')
groupedLine_yearly = df_line.groupby(['year', 'eventtype']).size().reset_index(name='counts')

#total number of events per year
total_counts_yearly = grouped_yearly.groupby('year')['counts'].sum()

#new data frame
all_data_yearly = pd.DataFrame([(year, event_type) for year in grouped_yearly['year'].unique() for event_type in grouped_yearly['eventtype'].unique()], columns=['year', 'eventtype'])
all_data_for_line_yearly = pd.DataFrame([(year, event_type) for year in grouped_yearly['year'].unique() for event_type in groupedLine_yearly['eventtype'].unique()], columns=['year', 'eventtype'])

#merge the new DataFrame with the grouped data, filling in a percentage of 0 where no events occurred
all_data_yearly = all_data_yearly.merge(grouped_yearly, on=['year', 'eventtype'], how='left').fillna(0)
all_data_for_line_yearly = all_data_for_line_yearly.merge(groupedLine_yearly, on=['year', 'eventtype'], how='left').fillna(0)

#counts to percents
all_data_yearly['percentage'] = all_data_yearly.apply(lambda row: row['counts'] / total_counts_yearly[row['year']] * 100, axis=1)

#bar chart for each year (colors and event_types same variables as yearly)
years = all_data_yearly['year'].unique()
for j, event_type in enumerate(event_types):
    percentages = []
    for i, year in enumerate(years):
        data = all_data_yearly[all_data_yearly['year'] == year]
        event_data = data[data['eventtype'] == event_type]['percentage']
        percentage = event_data.values[0] if len(event_data) > 0 else 0
        percentages.append(percentage)
    plt.bar(np.arange(len(years)) + j * bar_width, percentages, color=colors[event_type], width=bar_width, label=event_type, edgecolor="black", zorder=2)

#line graph for training data
tm_sent_data_yearly = all_data_for_line_yearly[all_data_for_line_yearly['eventtype'] == "TM Sent"].sort_values('year')
email_clicked_data_yearly = all_data_yearly[all_data_yearly['eventtype'] == "Email Click"].sort_values('year')
tm_sent_percentages_yearly = tm_sent_data_yearly['counts'].values / email_clicked_data_yearly['counts'].values * 100
plt.plot(np.arange(len(years)), tm_sent_percentages_yearly, color='blue', marker='o', label='Training Complete', zorder=3)

#set xticks to years
plt.xticks(np.arange(len(years)) + bar_width, years)

#set the y-ticks to go up by tens
plt.yticks(np.arange(0, 110, 10))

plt.title(end_date+' Phishing and Awareness (Year to Year)')
plt.xlabel('years')
plt.ylabel('Percentage')
plt.legend(loc='upper left', bbox_to_anchor=(1, 1))
plt.grid(axis='y', color=(0.9, 0.9, 0.9), zorder=1)

plt.show()
