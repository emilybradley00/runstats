#!/usr/bin/env python

#Use: ./graph.py (5km predicted time at the moment) (directory location of tcx files)

from rTSS import scoremyrun
from readtcx import get_dataframes
import sys
import glob
import matplotlib as mpl
mpl.use('tkagg')
from matplotlib import dates as mdates
import matplotlib.pyplot as plt, mpld3
from datetime import date, timedelta
import time
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()
from numpy import linspace
from mpld3 import plugins
import argparse


#fivekm = argv[1]
#directory = argv[2]

def parse_arguments(argv):
    """
    Setup the argument parser and parse the command line arguments.
    """

    parser = argparse.ArgumentParser(description='Garmin Connect Exporter')

    parser.add_argument('-d', '--directory',
        help='the directory where the tcx files are stored (e.g. Users/emilybradley/Desktop/runstats/em_files_updated_Nov11)')
    parser.add_argument('-f', '--fivekm',
        help='estimation of current 5km race time')
    parser.add_argument('-s', '--save', default='/Users/emilybradley/Desktop/runstats/traininggraph.html',
        help='directory location and name under which the graph will be saved, e.g. /Users/emilybradley/Desktop/runstats/traininggraph.html')

    return parser.parse_args(argv[1:])



def main(argv):
    """
    Main entry point for graph.py
    """
    args = parse_arguments(argv)

    print('Building your form graph!')

    listofactivitydicts = []

    activity_list = glob.glob("/" + args.directory + "/*.tcx")

    for activity_path in activity_list:
        laps_df, points_df, stats_dict = get_dataframes(activity_path)

        if laps_df is not None:
            rTSS = scoremyrun(args.fivekm, laps_df)
            stats_dict['rTSS'] = rTSS
            listofactivitydicts.append(stats_dict)

    run_scores = []
    for run in listofactivitydicts:
        run_scores.append((run['starting time'].date(), run['rTSS'], run['distance'], run['duration'], run['average pace']))

    #sort run_scores (a list of lists) by date (newest to oldest)
    run_scores = sorted(run_scores, key=lambda x: x[0], reverse = True)
    date_labels = list(zip(*run_scores))[0]
    score_labels = list(zip(*run_scores))[1]
    distance_labels = list(zip(*run_scores))[2]
    duration_labels = list(zip(*run_scores))[3]
    pace_labels = list(zip(*run_scores))[4]

    labels = ['<p style="font-family: Arial;font-size: 12px">{title1}<br>rTSS: {title2}<br>{third}<br>{fourth}<br>{fifth}</p>'.format(
            title1=date_labels[x].strftime("%d/%m/%Y"), title2=str(score_labels[x]), third=distance_labels[x], fourth=time.strftime('%H:%M:%S', time.gmtime(duration_labels[x])), fifth=pace_labels[x]) for x in range(len(run_scores))]

    #labels = [date_labels[x].strftime("%d/%m/%Y")+', '+'rTSS: '+str(score_labels[x])+', '+ distance_labels[x]+', '+time.strftime('%H:%M:%S', time.gmtime(duration_labels[x]))+', '+pace_labels[x] for x in range(len(run_scores))]

    day_count = (run_scores[0][0] - run_scores[-1][0]).days

    forms = []

    date_range = [run_scores[-1][0] + timedelta(n) for n in range(day_count)]

    weighting = linspace(1.5,0.5,42)

    for single_date in date_range[42:]:
        form = 0
        for date1 in (single_date - timedelta(n) for n in range(42)):
            for x in range(len(list(zip(*run_scores))[0])):
                if date1 == list(zip(*run_scores))[0][x]:
                    days_since = (single_date - date1).days
                    form += list(zip(*run_scores))[1][x]*weighting[days_since]
        forms.append((single_date,form/42))

    fig, ax = plt.subplots()
    points = ax.scatter(list(zip(*run_scores))[0], list(zip(*run_scores))[1], s=2.5, c='r')
    ax.plot(list(zip(*forms))[0], list(zip(*forms))[1], c='b')
    plt.gcf().autofmt_xdate()
    plt.ylim(0,150)
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