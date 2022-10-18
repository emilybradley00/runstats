#!/usr/bin/env python

from rTSS import scoremyrun
from readtcx import get_dataframes
from sys import argv
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

fivekm = argv[1]

listofactivitydicts = []

activity_list = glob.glob("/Users/emilybradley/Desktop/runstats/garmin-connect-export/2022-10-09_garmin_connect_export/*.tcx")
#activity_list = glob.glob("/Users/emilybradley/Desktop/runstats/activity_files/*.tcx")

for activity_path in activity_list:
    laps_df, points_df, stats_dict = get_dataframes(activity_path)

    if laps_df is not None:
        rTSS = scoremyrun(fivekm, laps_df)
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

#tooltip = plugins.PointHTMLTooltip(points[0], labels, hoffset=-tooltipwidth/2, voffset=-tooltipheight, css=css)
#plugins.connect(fig, tooltip)

#mpld3.save_html(fig, '/Users/emilybradley/Desktop/runstats/traininggraph.html')