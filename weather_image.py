#!/usr/bin/env python3

import argparse
import collections
import json
import math
import os
import sys
import urllib.parse
import urllib.request

import pygal

#
# Location Parsing
#

Location = collections.namedtuple("Location", ["lat", "lon"])
geocoder = None
def geocode(location):
    global geocoder

    parts = location.split(",")
    if len(parts) == 2:
        return Location(float(parts[0]), float(parts[1]))
    else:
        try:
            import geopy.geocoders
        except ModuleNotFoundError:
            raise Exception("geopy module not installed, specify location as lat,lon only")

        if not geocoder:
            geocoder = geopy.geocoders.Nominatim(user_agent="weather_image.py")
        loc = geocoder.geocode(location)
        return Location(loc.latitude, loc.longitude)

#
# OpenWeatherMap API
#

def owm(appid, root_url="http://api.openweathermap.org/data/2.5"):
    def get(location, method, **extra):
        p = {
            "lat": location.lat,
            "lon": location.lon,
            "appid": appid,
        }
        p.update(extra)
        params = urllib.parse.urlencode(p)
        with urllib.request.urlopen(f"{root_url}/{method}?{params}") as f:
            data = json.loads(f.read().decode("utf-8"))
        return data
    return get

# https://en.wikipedia.org/wiki/Air_Quality_Health_Index_(Canada)#Calculation
def calculate_aqhi(ozone, dioxide, particulates):
    def element(constant, variable):
        math.pow(math.e, constant * variable) - 1
    aqhi = (1000 / 10.4) * (element(0.000537, ozone) + element(0.000871, dioxide) + element(0.000487, particulates))
    return round(aqhi, 1)

def get_weather_data(loc, owm):
    w = owm(loc, "onecall", exclude="minutely,daily,alerts")
    ap = owm(loc, "air_pollution")
    apf = owm(loc, "air_pollution/forecast")

    # TODO

#
# Chart and Rendering
#

def generate_chart(weather):
    pass

def render_image(chart, output_path):
    pass

#
# Main
#

def main(raw_args):
    default_api_key = "~/.openweathermap_api_key"
    parser = argparse.ArgumentParser(description="Create an image showing weather data for location")
    parser.add_argument("location", type=geocode, help="Location for the weather. Use lat,lon. Example: 51.046,-114.065 If geopy is installed, you can also just give a location textually. Example: Calgary")
    parser.add_argument("output", help="Output path for the image. Defaults to svg format. If cairosvg is installed, you can also specify .png extension in the path for png formatted output.")
    parser.add_argument("-k", "--api-key", help=f"Override API key file location. Default {default_api_key}")

    args = parser.parse_args(raw_args)

    with open(args.api_key or os.path.expanduser(default_api_key)) as f:
        api_key = f.read().strip()

    weather = get_weather_data(args.location, owm(api_key))
    chart = generate_chart(weather)
    render_image(chart, args.output)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
