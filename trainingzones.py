#!/usr/bin/env python
#creates training zones from a prediction of current 5km time
#threshold pace in seconds per km

def zones(racetime):
    racetime = racetime.split(':')
    racetime = [int(x) for x in racetime] 
    racetime_seconds = 60*racetime[0] + racetime[1]
    km_pace = racetime_seconds/5
    threshold_pace = 1.07*km_pace
    return threshold_pace