#!/usr/bin/env python

from rTSS import scoremyrun
from readtcx import get_dataframes
from sys import argv
import glob
import matplotlib as mpl
mpl.use('tkagg')
from matplotlib import pyplot as plt, dates as mdates
from datetime import date, timedelta
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

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
    run_scores.append((run['starting time'].date(), run['rTSS']))

#sort run_scores (a list of tuples) by date (newest to oldest)
run_scores = sorted(run_scores, key=lambda x: x[0], reverse = True)

day_count = (run_scores[0][0] - run_scores[-1][0]).days

forms = []

date_range = [run_scores[-1][0] + timedelta(n) for n in range(day_count)]
print(date_range)

for single_date in date_range[30:]:
    form = 0
    for date1 in (single_date - timedelta(n) for n in range(30)):
        for x in range(len(list(zip(*run_scores))[0])):
            if date1 == list(zip(*run_scores))[0][x]:
                form += list(zip(*run_scores))[1][x]
    forms.append((single_date,form/30))

plt.scatter(list(zip(*run_scores))[0], list(zip(*run_scores))[1], s=2.5, c='r')
plt.plot(list(zip(*forms))[0], list(zip(*forms))[1], c='b')
plt.gcf().autofmt_xdate()
plt.ylim(0,150)
plt.ylabel('rTSS')
plt.show()