#!/usr/bin/env python3

import argparse
import collections
import datetime
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
        return math.pow(math.e, constant * variable) - 1
    aqhi = (1000 / 10.4) * (element(0.000537, ozone) + element(0.000871, dioxide) + element(0.000487, particulates))
    return round(aqhi, 1)

def get_weather_data(loc, owm):
    w = owm(loc, "onecall", exclude="minutely,daily,alerts")
    ap = owm(loc, "air_pollution")
    apf = owm(loc, "air_pollution/forecast")
    #import pprint
    #pprint.pprint(w)
    #pprint.pprint(ap)
    #pprint.pprint(apf)

    ap_by_hour = collections.OrderedDict()
    def add_ap(data):
        ap_by_hour[data["dt"]] = data["components"]
    add_ap(ap["list"][0])
    for hour in apf["list"]:
        add_ap(hour)

    hourly = []
    def add_hour(data):
        hourly.append(data)
        # Save timestamp
        dt = data["dt"]
        # Convert timestamps to native datetime object
        for key in ("dt", "sunrise", "sunset"):
            if key in data:
                data[key] = datetime.datetime.fromtimestamp(data[key])
        # Convert Kelvin to Celcius
        for key in ("dew_point", "feels_like", "temp"):
            data[key] = round(data[key] - 273.15, 2)
        # Add AQHI
        try:
            c = ap_by_hour[dt]
        except KeyError:
            # Find closest match for those missing exact match
            c = ap_by_hour[min(ap_by_hour.keys(), key=lambda x: abs(x - dt))]
        data["pollution"] = c
        data["aqhi"] = calculate_aqhi(c["o3"], c["no2"], c["pm2_5"])
        # Flatten weather key
        data["weather"] = data["weather"][0]

    add_hour(w["current"])
    for hour in w["hourly"]:
        add_hour(hour)

    #import pprint
    #pprint.pprint(hourly)
    return hourly

#
# Chart and Rendering
#

def generate_chart(weather):
    temp_major = 5

    x_labels = []
    temps = []
    min_temp = 999999
    max_temp = -999999
    pop = []
    aqhi = []
    hours = 0
    for data in weather:
        hour = data["dt"].strftime("%H")
        #desc = data["weather"]["main"]
        x_labels.append(hour)

        temp = data["temp"]
        temps.append(temp)
        if temp > max_temp:
            max_temp = temp
        if temp < min_temp:
            min_temp = temp

        pop.append(data.get("pop", 0) * 100)
        aqhi.append(data["aqhi"] * 10)

        hours += 1
        if hours >= 24:
            break

    min_temp = round(min_temp)
    max_temp = round(max_temp)
    y_min = min_temp - (min_temp % temp_major)
    y_max = temp_major * round(max_temp / temp_major)
    y_labels = list(range(y_min, y_max + 1, 1))

    chart = pygal.Line(
        #interpolate="cubic",
        style=pygal.style.DarkStyle,
        x_labels = x_labels,
        #x_label_rotation=90,
        secondary_range=(0, 100),
        y_labels = y_labels,
        y_labels_major_every=temp_major,
        #legend_at_bottom=True,
        #legend_at_bottom_columns=3,
    )

    chart.add("°C", temps)
    chart.add("PoP", pop, secondary=True)
    chart.add("AQHI", aqhi, secondary=True)

    return chart

def render_image(chart, output_path):
    if output_path.endswith(".png"):
        # PNG
        r = chart.render_to_png
    else:
        # SVG
        r = chart.render_to_file
    r(output_path)

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
