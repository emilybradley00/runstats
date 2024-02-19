#!/usr/bin/env python

#extracts lap data from a txc file, and general activity stats (total distance, time, avg pace, avg HR)

from datetime import datetime, timedelta
import pytz
from timezonefinder import TimezoneFinder
from typing import Dict, Optional, Any, Union, Tuple
import sys

import lxml.etree
import pandas as pd
import dateutil.parser as dp


NAMESPACES = {
    'ns': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2',
    'ns2': 'http://www.garmin.com/xmlschemas/UserProfile/v2',
    'ns3': 'http://www.garmin.com/xmlschemas/ActivityExtension/v2',
    'ns4': 'http://www.garmin.com/xmlschemas/ProfileExtension/v1',
    'ns5': 'http://www.garmin.com/xmlschemas/ActivityGoals/v1'
}

# The names of the columns we will use in our points DataFrame
POINTS_COLUMN_NAMES = ['latitude', 'longitude', 'elevation', 'time', 'heart_rate', 'cadence', 'speed', 'lap']

# The names of the columns we will use in our laps DataFrame
LAPS_COLUMN_NAMES = ['number', 'start_time', 'distance', 'total_time', 'max_speed', 'max_hr', 'avg_hr']

def get_tcx_lap_data(lap):
    """
    Extract some data from an XML element representing a lap and return it as a dict.
    """
    
    data = {}
    
    # Note that because each element's attributes and text are returned as strings, we need to convert those strings
    # to the appropriate datatype (datetime, float, int, etc).
    
    start_time_str = lap.attrib['StartTime']
    data['start_time'] = dp.parse(start_time_str)
    
    distance_elem = lap.find('ns:DistanceMeters', NAMESPACES)
    if distance_elem is not None:
        data['distance'] = float(distance_elem.text)
    
    total_time_elem = lap.find('ns:TotalTimeSeconds', NAMESPACES)
    if total_time_elem is not None:
        data['total_time'] = timedelta(seconds=float(total_time_elem.text))
    
    max_speed_elem = lap.find('ns:MaximumSpeed', NAMESPACES)
    if max_speed_elem is not None:
        data['max_speed'] = float(max_speed_elem.text)
    
    max_hr_elem = lap.find('ns:MaximumHeartRateBpm', NAMESPACES)
    if max_hr_elem is not None:
        data['max_hr'] = float(max_hr_elem.find('ns:Value', NAMESPACES).text)
    
    avg_hr_elem = lap.find('ns:AverageHeartRateBpm', NAMESPACES)
    if avg_hr_elem is not None:
        data['avg_hr'] = float(avg_hr_elem.find('ns:Value', NAMESPACES).text)
    
    return data

def get_tcx_point_data(point):
    """
    Extract some data from an XML element representing a track point and return it as a dict.
    """
    
    data = {}
    #data: Dict[str, Union[float, int, str, datetime]] = {}
    
    position = point.find('ns:Position', NAMESPACES)
    if position is None:
        # This Trackpoint element has no latitude or longitude data (could be a treadmill activity)
        data['latitude'] = None
        data['longitude'] = None
        return None
    else:
        data['latitude'] = float(position.find('ns:LatitudeDegrees', NAMESPACES).text)
        data['longitude'] = float(position.find('ns:LongitudeDegrees', NAMESPACES).text)
    
    time_str = point.find('ns:Time', NAMESPACES).text
    data['time'] = dp.parse(time_str)
        
    elevation_elem = point.find('ns:AltitudeMeters', NAMESPACES)
    if elevation_elem is not None:
        data['elevation'] = float(elevation_elem.text)
    
    hr_elem = point.find('ns:HeartRateBpm', NAMESPACES)
    if hr_elem is not None:
        data['heart_rate'] = int(hr_elem.find('ns:Value', NAMESPACES).text)
        
    cad_elem = point.find('ns:Cadence', NAMESPACES)
    if cad_elem is not None:
        data['cadence'] = int(cad_elem.text)
    
    # The ".//" here basically tells lxml to search recursively down the tree for the relevant tag, rather than just the
    # immediate child elements of speed_elem. See https://lxml.de/tutorial.html#elementpath
    speed_elem = point.find('.//ns3:Speed', NAMESPACES)
    if speed_elem is not None:
        data['speed'] = float(speed_elem.text)
    
    return data
    

def get_dataframes(fname):
#def get_dataframes(fname: str) -> Tuple[pd.DataFrame, pd.DataFrame]:  
    """Takes the path to a TCX file (as a string) and returns two Pandas
        DataFrames: one containing data about the laps, and one containing general stats.
    """
    
    tree = lxml.etree.parse(fname)
    root = tree.getroot()
    activity = root.find('ns:Activities', NAMESPACES)[0]  # Assuming we know there is only one Activity in the TCX file
                                                          # (or we are only interested in the first one)

    #check that the activity type is running
    if activity.attrib == {'Sport': 'Running'}:
        starting_point = {}
        laps_data = []
        lap_no = 1
        for lap in activity.findall('ns:Lap', NAMESPACES):
            # Get data about the lap itself
            single_lap_data = get_tcx_lap_data(lap)
            single_lap_data['number'] = lap_no
            laps_data.append(single_lap_data)
        
            # if it's the first lap and there is gps data available (not a treadmill activity), store the starting point
            if lap_no == 1 and len(activity.findall('ns:Position', NAMESPACES)) > 0:
                track = lap.find('ns:Track', NAMESPACES) 
                single_point_data = get_tcx_point_data(track.findall('ns:Trackpoint', NAMESPACES)[0])
                if single_point_data:
                    starting_point = single_point_data
            elif lap_no == 1:
                # treadmill or non-gps activity, get starting time only
                track = lap.find('ns:Track', NAMESPACES)
                single_point_data = track.findall('ns:Trackpoint', NAMESPACES)[0]
                if single_point_data is not None:
                    time_str = single_point_data.find('ns:Time', NAMESPACES).text
                    starting_time = dp.parse(time_str)
            lap_no += 1
    
        # Create DataFrames from the data we have collected. If any information is missing from a particular lap or track
        # point, it will show up as a null value or "NaN" in the DataFrame.
    
        laps_df = pd.DataFrame(laps_data, columns=LAPS_COLUMN_NAMES)
        laps_df.set_index('number', inplace=True)
        
        hr_lap = 0
        distance_total = laps_df["distance"].sum()/1000
        total_duration = laps_df["total_time"].sum()
        for x in range(1,len(laps_df)+1):
            hr_lap += laps_df.loc[x].at["avg_hr"]*laps_df.loc[x].at["total_time"].total_seconds()

        hr_average = int(round(hr_lap/total_duration.total_seconds()))
        avg_pace = timedelta(seconds=int(round((total_duration.total_seconds()/distance_total))))
        
        if len(activity.findall('ns:Position', NAMESPACES)) > 0:
            starting_lat = starting_point["latitude"]
            starting_long = starting_point["longitude"]
            starting_time = starting_point["time"]
            # Find timezone based on longitude and latitude and convert starting_time to local time
            tf = TimezoneFinder()
            local_time_zone = tf.timezone_at(lng=starting_long, lat=starting_lat)
            tz = pytz.timezone(local_time_zone)
            starting_time = starting_time.replace(tzinfo=pytz.utc).astimezone(tz)

        stats_dict = {
            "duration":total_duration.round(freq='s').total_seconds(),
            "distance":str(round(distance_total,2))+' km',
            "average heart rate":str(hr_average)+' bpm',
            "average pace":str(avg_pace)+' mins/km',
            "starting time":starting_time
        }

    else:
        laps_df = None
        stats_dict = None
    
    return laps_df, stats_dict

def get_swim_dataframes(fname):
    """Takes the path to a TCX file (as a string) and returns two Pandas
        DataFrames: one containing data about the laps, and one containing general stats.
    """
    
    tree = lxml.etree.parse(fname)
    root = tree.getroot()
    activity = root.find('ns:Activities', NAMESPACES)[0]  # Assuming we know there is only one Activity in the TCX file
                                                          # (or we are only interested in the first one)

    #check that the activity type is swimming
    if activity.attrib == {'Sport': 'Other'}:
        laps_data = []
        lap_no = 1
        for lap in activity.findall('ns:Lap', NAMESPACES):
            # Get data about the lap itself
            single_lap_data = get_tcx_lap_data(lap)
            single_lap_data['number'] = lap_no
            laps_data.append(single_lap_data)

            # if it's the first lap store the date
            if lap_no == 1:
                track = lap.find('ns:Track', NAMESPACES) 
                single_point_data = track.findall('ns:Trackpoint', NAMESPACES)[0]
                if single_point_data is not None:
                    time_str = single_point_data.find('ns:Time', NAMESPACES).text
                    starting_time = dp.parse(time_str)
            lap_no += 1
    
        # Create DataFrames from the data we have collected. If any information is missing from a particular lap or track
        # point, it will show up as a null value or "NaN" in the DataFrame.
    
        laps_df = pd.DataFrame(laps_data, columns=LAPS_COLUMN_NAMES)
        laps_df.set_index('number', inplace=True)

        distance_total = laps_df["distance"].sum()
        total_duration = laps_df["total_time"].sum()
    
        avg_pace = timedelta(seconds=int(round((total_duration.total_seconds()*100/distance_total))))

        stats_dict = {
            "duration":total_duration.round(freq='s').total_seconds(),
            "distance":str(round(distance_total,2))+' m',
            "average pace":str(avg_pace)+' mins/100m',
            "starting time":starting_time
        }

    else:
        laps_df = None
        stats_dict = None
    
    return laps_df, stats_dict


if __name__ == '__main__':
    
    from sys import argv
    fname = argv[1]  # Path to TCX file to be given as first argument to script
    laps_df, stats_dict = get_dataframes(fname)
