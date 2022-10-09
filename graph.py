#!/usr/bin/env python

from rTSS import scoremyrun
from readtcx import get_dataframes
from sys import argv
import glob
import matplotlib as mpl
mpl.use('tkagg')
from matplotlib import pyplot as plt, dates as mdates
from datetime import datetime
import pandas as pd
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()

fivekm = argv[1]

listofactivitydicts = []

activity_list = glob.glob("/Users/emilybradley/Desktop/runstats/garmin-connect-export/2022-10-09_garmin_connect_export/*.tcx")
#activity_list = glob.glob("/Users/emilybradley/Desktop/runstats/activity_files/*.tcx")

for activity_path in activity_list:
    print(activity_path)
    laps_df, points_df, stats_dict = get_dataframes(activity_path)

    if laps_df is not None:
        rTSS = scoremyrun(fivekm, laps_df)
        stats_dict['rTSS'] = rTSS
        listofactivitydicts.append(stats_dict)

run_scores = []
run_dates = []
for run in listofactivitydicts:
    run_scores.append(run['rTSS'])
    run_dates.append(run['starting time'].date())

run_dates = pd.to_datetime(run_dates)

plt.scatter(run_dates, run_scores, s=2.5, c='r')
plt.gcf().autofmt_xdate()
plt.ylim(0,140)
plt.ylabel('rTSS')
plt.show()