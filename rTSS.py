#!/usr/bin/env python

#calculates the running training stress score from the lap data of an activity

from trainingzones import zones
from readtcx import get_dataframes
import argparse
from sys import argv, exit
import pandas as pd
from cache_pandas import cache_to_csv
import glob
import logging

def parse_arguments(argv):
    """
    Setup the argument parser and parse the command line arguments.
    """

    parser = argparse.ArgumentParser(description='rTSS calculator')

    parser.add_argument('-d', '--directory',
        help='the directory where the tcx files are stored (e.g. em_files)', required=True)
    parser.add_argument('-f', '--fivekm',
        help='estimation of current 5km race time', required=True)

    return parser.parse_args(argv[1:])

def scoremyrun(fivekm,laps_df):
    threshold = zones(fivekm)
    lapscores = []
    for x in range(1,len(laps_df)+1):
        if laps_df.loc[x].at["distance"] > 0:
            gap = laps_df.loc[x].at["total_time"].total_seconds()*(1000/laps_df.loc[x].at["distance"])
            intensity = threshold/gap
            #should intensity be linear in relation to threshold? doesn't give enough points to speed work?
            duration = laps_df.loc[x].at["total_time"].total_seconds()
            #not actually GAP at the moment, just normal pace (in seconds per km)
            lapscores.append(100*(duration*intensity*intensity)/(3600))
    totalscore = int(round(sum(lapscores)))
    return totalscore


@cache_to_csv("runscores.csv", refresh_time=1)
def main(argv):
    """
    Main entry point for rTSS.py
    """

    args = parse_arguments(argv)

    listofactivitydicts = []

    activity_list =  glob.glob('/Users/emilybradley/Desktop/runstats/' + args.directory + '/*.tcx')

    for activity_path in activity_list:
        try:
            laps_df = get_dataframes(activity_path)[0]
            stats_dict = get_dataframes(activity_path)[1]
        except:
            logging.error('error with ' + activity_path)
        else:
            if laps_df is not None:
                rTSS = scoremyrun(args.fivekm, laps_df)
                stats_dict['rTSS'] = rTSS
                stats_dict['date'] = stats_dict['starting time'].date()
                listofactivitydicts.append(stats_dict)

    run_scores_df = pd.DataFrame(listofactivitydicts)

    return pd.DataFrame.from_dict(run_scores_df)


if __name__ == "__main__":
    try:
        main(argv)
    except KeyboardInterrupt:
        print('Interrupted')
        exit(0)