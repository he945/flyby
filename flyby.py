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
import StringIO
import unittest


def flyby(latitude, longitude):
    """
    function to predict next time a satellite image will be taken using NASA public HTTP API

    :param latitude: Latitude of location
    :param longitude: Longitude of location
    :return: void
    """    
    API_KEY = 'm1DJtfAzuR0pkYdZDa5QYurqX7T9bKAQc4GSGh1m'
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
        data_url = 'https://api.nasa.gov/planetary/earth/assets?lon=' + str(longitude_val) + '&lat=' + str(latitude_val) + '&api_key=' + API_KEY
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


def testLocation(location, expectedStr):
    """
    function to test location against expected next time

    :param location: Location list as  [lat, long]
    :param expectedStr: Expected string for next datetime
    :return: void
    """ 
    capturedOutput = StringIO.StringIO()
    print("\nTESTING LATITUDE, LONGITUDE ({0}, {1})".format(location[0], location[1]))
    sys.stdout = capturedOutput
    flyby(location[0], location[1])
    sys.stdout = sys.__stdout__
    next_time = str(capturedOutput.getvalue().strip())
    assert next_time == expectedStr

# Unit tests
class FlybyTest(unittest.TestCase):
    def test(self):
        grand_canyon_loc = [36.098592, -112.097796]
        testLocation(grand_canyon_loc, "Next time: 2017-05-12 09:52:17.638297")

        niagara_falls_loc = [43.078154, -79.075891]
        testLocation(niagara_falls_loc, "Next time: 2017-05-11 14:20:07.149253")

        four_corners_monument_loc = [36.998979, -109.045183]
        testLocation(four_corners_monument_loc, "Next time: 2017-05-04 05:09:59.609665")

        medsender_hq_loc = [40.720583, -74.001472]
        testLocation(medsender_hq_loc, "Next time: 2017-04-28 06:51:59.453947")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate next time a satellite image will be taken given latitude and longitude')
    parser.add_argument('-lat','--latitude', help='Latitude of location')
    parser.add_argument('-lon','--longitude', help='Longitude of location')
    parser.add_argument('-u', '--unittest', help='Run unit tests', action='store_true')
    args = parser.parse_args()

    # run unit tests if -u argument passed
    if args.unittest:
        print("RUNNING UNIT TESTS...")
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(unittest.makeSuite(FlybyTest))
    else:
        # check that latitude and longitude arguments have been passed in
        if args.latitude is not None and args.longitude is not None:
            flyby(args.latitude, args.longitude)
        else:
            print("USAGE: python flyby.py -lat <LATITUDE> -lon <LONGITUDE>")

