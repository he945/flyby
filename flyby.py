"""
.. module:: flyby.py

   :synopsis: Function that uses NASA public HTTP APIs for predicting next time a satellite image will be taken
"""
import requests
import json
import re
import traceback
import sys
from datetime import datetime, timedelta
import argparse

def flyby(latitude, longitude):
    """
    function to predict next time a satellite image will be taken using NASA public HTTP API

    :param latitude: Latitude of location
    :param longitude: Longitude of location
    :return: void
    """    
    count = 0
    avg_time_delta = 0
    date_format = "%Y-%m-%dT%H:%M:%S"
    exceptMsg = "Attempted to calculate next flyby picture for coordinates ({0}, {1})".format(latitude, longitude)

    try:
        try: # check for use of floating points values for latitude and longitude
            latitude_val = float(latitude)
            longitude_val = float(longitude)
        except e as FloatException:
            print("Both latitude and longitude values must be floats.")

        # make HTTP GET request to NASA API
        data_url = 'https://api.nasa.gov/planetary/earth/assets?lon=' + str(longitude_val) + '&lat=' + str(latitude_val) + '&api_key=DEMO_KEY'
        data = requests.get(data_url)

        json_data = {}
        try:
            json_data = data.json() # check that JSON data is in HTTP response
        except Exception as JSONException:
            print(exceptMsg + "\nHTTP GET request for " + data_url + " did not return JSON data.")
            return

        if 'count' not in json_data: # check that the JSON data has a count key
            print(exceptMsg + "\nHTTP GET request for " + data_url + " did not contain 'count' key in JSON")
            return

        try:
            count = int(json_data['count'])
        except: # check that count key in JSON data is an integer
            print(exceptMsg + "\nHTTP GET request for " + data_url + " did not contain an integer for 'count' value in JSON")
            return

        if count == 0: # print error message if count is 0
            print(exceptMsg + "\nHTTP GET request for " + data_url + " had 0 count in JSON payload, could not calculate avg_time_delta")
            return
        
        # print error message if no results array found in JSON
        if 'results' not in json_data:
            print(exceptMsg + "\nHTTP GET request for " + data_url + " did not contain 'results' key in JSON")


        results = json_data['results']
        results_count = len(results)
        if results_count != count: # check that number of results match the count in JSON payload
            print(exceptMsg + "\nHTTP GET request for " + data_url + " count of {0}, did not match number of results {1}".format(count, results_count))
            return
        
        # print error message if results array is empty
        if results_count == 0:
            print(exceptMsg + "\nHTTP GET request for " + data_url + " had empty results")
            return

        # sort results by date key
        sorted_results = sorted(results, key=lambda k: k['date'])

        list_of_deltas = []

        # get last_date a satellite image was taken for this location
        last_result = sorted_results[-1]
        last_date = datetime.strptime(last_result['date'], date_format)

        # loop through results and calculate time deltas
        for index, result in enumerate(sorted_results):
            if index > 0:
                result_id = "NONE"
                if 'id' in result: # check that each result has an id key
                    result_id = result['id']
                if 'date' not in result: # check that each result has a date key
                    print(exceptMsg + "\nHTTP GET request for " + data_url + " for ID {0} did not have a corresponding date value".format(result_id))
                    return

                # calculate deltas and add to list_of_deltas
                try:
                    current_datetime = datetime.strptime(result['date'], date_format)
                    previous_result = sorted_results[index - 1]
                    previous_datetime = datetime.strptime(previous_result['date'], date_format)
                    time_delta = (current_datetime - previous_datetime)
                    list_of_deltas.append(time_delta)
                except ValueError:
                    print(exceptMsg + "\nHTTP GET request for " + data_url + " for ID {0} had a wrongly formatted date")

        # calculate average time delta
        avg_time_delta = sum(list_of_deltas, timedelta()) / len(results)

        # print next time a satellite image will be taken at this location
        print ("Next time: " + str(last_date + avg_time_delta))


    except Exception as e:
        print(exceptMsg + "\nHTTP GET request for " + data_url + " failed.")
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate next time a satellite image will be taken given latitude and longitude')
    parser.add_argument('-lat','--latitude', help='Latitude of location')
    parser.add_argument('-lon','--longitude', help='Longitude of location')
    args = parser.parse_args()

    if args.latitude is not None and args.longitude:
        flyby(args.latitude, args.longitude)
