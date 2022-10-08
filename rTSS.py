#!/usr/bin/env python

#calculates the running training stress score from the lap data of an activity

from trainingzones import zones

def scoremyrun(fivekm):
    threshold = zones(fivekm)
    lapscores = []
    for lap in run:
        intensity = pace/threshold
        lapscores.append(100*(duration*intensity*gap)/(3600*threshold))
    totalscore = sum(lapscores)
    