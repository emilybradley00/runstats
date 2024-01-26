#!/usr/bin/env python

#Use: ./graph.py -m (month range to be displayed)

from rTSS import scoremyrun
from readtcx import get_dataframes
import sys
import glob
import matplotlib as mpl
mpl.use('tkagg')
from matplotlib import dates as mdates
import matplotlib.pyplot as plt, mpld3
from datetime import date, timedelta, datetime
from dateutil import relativedelta
import time
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from numpy import linspace
from mpld3 import plugins
import argparse
import logging

#fivekm = argv[1]
#graph length (months) = argv[2], default is to use all available data

def parse_arguments(argv):
    """
    Setup the argument parser and parse the command line arguments.
    """

    parser = argparse.ArgumentParser(description='Garmin Connect Exporter')

    parser.add_argument('-s', '--save', default='/Users/emilybradley/Desktop/runstats/traininggraph.html',
        help='directory location and name under which the graph will be saved, e.g. /Users/emilybradley/Desktop/runstats/traininggraph.html')
    parser.add_argument('-m', '--months', default='all',
        help='how many months of data would you like the graph to display, default is to use all available data')

    return parser.parse_args(argv[1:])


def main(argv):
    """
    Main entry point for graph.py
    """
    args = parse_arguments(argv)

    logging.info('Building your form graph!')

    try:
        run_scores_df = pd.read_csv('runscores.csv')
        #convert date column from string to pandas timestamp type
        run_scores_df['date'] = pd.to_datetime(run_scores_df['date'])
    except:
        logging.error("Couldn't find the csv file of run scores in the current directory.")
        sys.exit(0)

    run_dates = run_scores_df['date'].tolist()

    #find the range of dates that are possible to calculate forms for (dates for which there is 42 days of data preceeding them)
    day_count = (max(run_dates)-min(run_dates)).days

    if args.months == 'all':
        date_range = [min(run_dates) + timedelta(n) for n in range(day_count)]
        date_range = date_range[42:]
    elif args.months.isdigit() and int(args.months >0):
        #use custom month length for the graph, check if that much data is availale first
        graph_start_date = datetime.today() - timedelta(int(args.months)*30)
        month_range_to_days = (datetime.today() - graph_start_date).days
        if month_range_to_days + 42 < day_count:
            date_range = [graph_start_date.date() + timedelta(n) for n in range(month_range_to_days)]
        else:
            #if not use all available data
            logging.error('insufficient data available for requested month range, using all available data.')
            date_range = [min(run_dates) + timedelta(n) for n in range(day_count)]
            date_range = date_range[42:]
    else:
        logging.error('Invalid graph length argument, please enter an integer or "all". Using all available data.')
        date_range = [min(run_dates) + timedelta(n) for n in range(day_count)]
        date_range = date_range[42:]
    
    mask = run_scores_df['date'].isin(date_range)
    run_scores_to_plot = run_scores_df[mask]
    run_scores_to_plot_sorted = run_scores_to_plot.sort_values(by='date', ascending=False)

    date_labels = []
    score_labels = []
    distance_labels = []
    duration_labels = []
    pace_labels = []

    for index, row in run_scores_to_plot_sorted.iterrows():
        date_labels.append(row['date'])
        score_labels.append(row['rTSS'])
        distance_labels.append(row['distance'])
        duration_labels.append(row['duration'])
        pace_labels.append(row['average pace'])

    labels = ['<p style="font-family: Arial;font-size: 12px">{title1}<br>rTSS: {title2}<br>{third}<br>{fourth}<br>{fifth}</p>'.format(
            title1=date_labels[x].strftime("%d/%m/%Y"), title2=str(score_labels[x]), third=distance_labels[x], fourth=time.strftime('%H:%M:%S', time.gmtime(duration_labels[x])), fifth=pace_labels[x]) for x in range(len(run_scores_to_plot.index))]
    
    forms_rolling = []
    forms_weekly = []
    form_delta = []

    weighting = linspace(1.5,0.5,42)

    forms_experiment = [] #day scores, starting from the current day and working backwards in time
    count = 1
    for single_date in date_range: #date range starts at the oldest date
        form_r = 0
        form_w = 0
        if count==1:
            for date1 in (single_date - timedelta(n) for n in range(42)):
                day_score = 0
                if date1 in (single_date - timedelta(n) for n in range(7)):
                    for index, row in run_scores_df.iterrows():
                        if row['date'] == date1:
                            days_since = (single_date - date1).days
                            form_r += row['rTSS']*weighting[days_since]
                            form_w += row['rTSS']
                            day_score += row['rTSS']
                else:
                    for index, row in run_scores_df.iterrows():
                        if row['date'] == date1:
                            days_since = (single_date - date1).days
                            form_r += row['rTSS']*weighting[days_since]
                            day_score += row['rTSS']
                forms_experiment.append(day_score)
        else:
            day_score = 0
            for index, row in run_scores_df.iterrows():
                if row['date'] == single_date:
                    days_since = 0
                    form_r += row['rTSS']*weighting[days_since]
                    form_w += row['rTSS']
                    day_score += row['rTSS']
            #take off the oldest day score and add the new day score to the start of the list
            forms_experiment.pop()
            forms_experiment.insert(0,day_score)
            form_r = sum(forms_experiment*weighting)
            form_w = sum(forms_experiment[:7])

        forms_rolling.append((single_date,form_r/42))
        forms_weekly.append((single_date,form_w/7))
        count += 1
        
    for form in forms_rolling:
        index = forms_rolling.index(form)
        form_delta.append((form[0],form[1]-forms_weekly[index][1]))
    
    fig, ax = plt.subplots()
    points = ax.scatter(x=run_scores_to_plot_sorted['date'], y=run_scores_to_plot_sorted['rTSS'], s=2, c='r')
    ax.plot(list(zip(*forms_rolling))[0], list(zip(*forms_rolling))[1], c='b')
    ax.plot(list(zip(*forms_weekly))[0], list(zip(*forms_weekly))[1], c='m', linewidth=0.5)
    ax.plot(list(zip(*form_delta))[0], list(zip(*form_delta))[1], c='y', linewidth=0.5)
    plt.gcf().autofmt_xdate()
    plt.ylim(-30,180)
    plt.ylabel('rTSS')

    tooltip = plugins.PointHTMLTooltip(points, labels)

    plugins.connect(fig, tooltip)

    mpld3.show()

    mpld3.save_html(fig, args.save)



if __name__ == "__main__":
    try:
        main(sys.argv)
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)