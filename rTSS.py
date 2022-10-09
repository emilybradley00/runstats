#!/usr/bin/env python

#calculates the running training stress score from the lap data of an activity

from trainingzones import zones
from readtcx import get_dataframes

def scoremyrun(fivekm,laps_df):
    threshold = zones(fivekm)
    lapscores = []
    for x in range(1,len(laps_df)+1):
        gap = laps_df.loc[x].at["total_time"].total_seconds()*(1000/laps_df.loc[x].at["distance"])
        intensity = threshold/gap
        #should intensity be linear in relation to threshold? doesn't give enough points to speed work?
        duration = laps_df.loc[x].at["total_time"].total_seconds()
        #not actually GAP at the moment, just normal pace (in seconds per km)
        lapscores.append(100*(duration*intensity)/(3600))
    totalscore = int(round(sum(lapscores)))
    return totalscore
    
if __name__ == '__main__':
    
    from sys import argv
    fname = argv[1]  # Path to TCX file to be given as first argument to script
    fivekm = argv[2]
    laps_df, points_df, stats_dict = get_dataframes(fname)
    rTSS = scoremyrun(fivekm,laps_df)
    print(rTSS)