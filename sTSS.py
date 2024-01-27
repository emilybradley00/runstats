#!/usr/bin/env python

#calculates the swim training stress score (sTSS) from the lap data of an activity
#iterate through activities.csv first and identify swim files
#put those activitiy numbers in a list
#score those activities

from readtcx import get_swim_dataframes
import argparse
from sys import argv, exit
import pandas as pd
from cache_pandas import cache_to_csv
import glob
import logging
import re
import sys

def parse_arguments(argv):
    """
    Setup the argument parser and parse the command line arguments.
    """

    parser = argparse.ArgumentParser(description='sTSS calculator')

    parser.add_argument('-d', '--directory',
        help='the directory where the tcx files are stored (e.g. em_files)', required=True)
    parser.add_argument('-c', '--css',
        help='estimation of current css pace (e.g. 1:42)', required=True)

    return parser.parse_args(argv[1:])


def scoremyswim(css_seconds,laps_df):
    lapscores = []
    for x in range(1,len(laps_df)+1):
        if laps_df.loc[x].at["distance"] != 0 and laps_df.loc[x].at["total_time"].total_seconds() > 0:
            gap = laps_df.loc[x].at["total_time"].total_seconds()*(100/laps_df.loc[x].at["distance"])
            intensity = css_seconds/gap
            #should intensity be linear in relation to threshold? doesn't give enough points to speed work?
            duration = laps_df.loc[x].at["total_time"].total_seconds()
            lapscores.append(100*(duration*intensity*intensity)/(3600))
    totalscore = int(round(sum(lapscores)))
    return totalscore


@cache_to_csv("swimscores.csv", refresh_time=1)
def main(argv):
    """
    Main entry point for sTSS.py
    """

    args = parse_arguments(argv)

    css = args.css.split(':')
    css = [int(x) for x in css] 
    css_seconds = 60*css[0] + css[1]

    listofactivitydicts = []

    try:
        activityies_csv_df = pd.read_csv(args.directory+'/activities.csv')
    except:
        logging.error("Couldn't find the csv file of activities in the folder of activities.")
        sys.exit(0)
    
    swim_activities_df = activityies_csv_df[activityies_csv_df['Activity Type'].str.contains('Swimming')]
    swim_activity_numbers = swim_activities_df['Activity ID'].tolist()
    swim_activities = []
    #swim_activities = ['/Users/emilybradley/Desktop/runstats/em_files/activity_9348173715.tcx']

    for activity in swim_activity_numbers:
        swim_activities.append('/Users/emilybradley/Desktop/runstats/' + args.directory + '/activity_' + str(activity) + '.tcx')

    for activity_path in swim_activities:
        try:
            laps_df = get_swim_dataframes(activity_path)[0]
            stats_dict = get_swim_dataframes(activity_path)[1]
        except:
            logging.error('error with ' + activity_path)
        else:
            if laps_df is not None:
                sTSS = scoremyswim(css_seconds, laps_df)
                stats_dict['sTSS'] = sTSS
                stats_dict['date'] = stats_dict['starting time'].date()
                listofactivitydicts.append(stats_dict)

    swim_scores_df = pd.DataFrame(listofactivitydicts)

    return pd.DataFrame.from_dict(swim_scores_df)


if __name__ == "__main__":
    try:
        main(argv)
    except KeyboardInterrupt:
        print('Interrupted')
        exit(0)