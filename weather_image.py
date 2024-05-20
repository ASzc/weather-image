#!/usr/bin/env python3

import argparse
import collections
import datetime
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

import pygal

pytz_available = True
try:
    import pytz
    import tzlocal
except ModuleNotFoundError as e:
    pytz_available = False

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
        for i in range(1,6,2):
            try:
                with urllib.request.urlopen(f"{root_url}/{method}?{params}") as f:
                    data = json.loads(f.read().decode("utf-8"))
            except urllib.error.HTTPError as e:
                print(e)
                time.sleep(2 ** i)
            else:
                break
        else:
            print("Unable to contact OWM API after several attempts, aborting")
            return None
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
    aqi=True
    def add_ap(data):
        ap_by_hour[data["dt"]] = data["components"]
    try:
        add_ap(ap["list"][0])
    except IndexError:
        aqi=False
    else:
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
                data[key] = localize(datetime.datetime.fromtimestamp(data[key]))
        # Convert Kelvin to Celcius
        for key in ("dew_point", "feels_like", "temp"):
            data[key] = round(data[key] - 273.15, 2)
        # Add AQHI
        if aqi:
            try:
                c = ap_by_hour[dt]
            except KeyError:
                # Find closest match for those missing exact match
                c = ap_by_hour[min(ap_by_hour.keys(), key=lambda x: abs(x - dt))]
            data["pollution"] = c
            data["aqhi"] = calculate_aqhi(c["o3"], c["no2"], c["pm2_5"])
        # Flatten weather key
        data["weather"] = data["weather"][0]

    localtz = None
    desttz = None
    def localize(dt):
        nonlocal localtz
        nonlocal desttz

        if pytz_available:
            if localtz is None:
                localtz = pytz.timezone(tzlocal.get_localzone().key)
                desttz = pytz.timezone(w["timezone"])
            return localtz.localize(dt).astimezone(desttz)
        else:
            return dt

    #add_hour(w["current"])
    for hour in w["hourly"]:
        add_hour(hour)

    #import pprint
    #pprint.pprint(hourly)
    return hourly

#
# Chart and Rendering
#

def generate_charts(weather, width=None, height=None):
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
        if "aqhi" in data:
            aqhi.append(data["aqhi"] * 10)

        hours += 1
        if hours >= 24:
            break

    min_temp = round(min_temp)
    max_temp = round(max_temp)
    y_min = min_temp - (min_temp % temp_major)
    y_max = temp_major * (round(max_temp / temp_major) + 1)
    y_labels = list(range(y_min, y_max + 1, 1))

    charts = {}

    chart = pygal.Line(
        width=width,
        height=height,
        #interpolate="cubic",
        style=pygal.style.DarkSolarizedStyle,
        x_labels = x_labels,
        y_labels = y_labels,
        y_labels_major_every=temp_major,
        show_legend=False,
    )

    chart.add("°C", temps)
    charts["temperature"] = chart

    chart = pygal.Line(
        width=width,
        height=height,
        #interpolate="cubic",
        style=pygal.style.DarkSolarizedStyle,
        x_labels = x_labels,
        y_labels = range(0, 110, 10),
        y_labels_major_every=10,
    )

    chart.add("PoP", pop)
    if aqhi:
        chart.add("AQHI", aqhi)
    charts["pop"] = chart

    return charts

def render_images(charts, output_path, dpi=72):
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)
    root, ext = os.path.splitext(output_path)
    for name, chart in charts.items():
        if ext == ".png":
            # PNG
            def r(path):
                chart.render_to_png(path, dpi=dpi)
        else:
            # SVG
            r = chart.render_to_file
        path = f"{root}_{name}{ext}"
        r(path)

#
# Main
#

def main(raw_args):
    default_api_key = "~/.openweathermap_api_key"
    parser = argparse.ArgumentParser(description="Create an image showing weather data for location")
    parser.add_argument("location", type=geocode, help="Location for the weather. Use lat,lon. Example: 51.046,-114.065 If geopy is installed, you can also just give a location textually. Example: Calgary")
    parser.add_argument("output", help="Output path for the image. The filename in the path serves as a prefix for the multiple images that will be produced. Defaults to svg format. If cairosvg is installed, you can also specify .png extension in the path for png formatted output.")
    parser.add_argument("-w", "--width", default=640, help="Horizonal size in pixels. Default 640")
    parser.add_argument("-v", "--height", default=360, help="Vertical size in pixels. Default 360")
    parser.add_argument("-d", "--dpi", default=72, help="Render scaling in dots-per-inch. Only applicable when output has a .png extension. Default 72")
    parser.add_argument("-k", "--api-key", help=f"Override API key file location. Ignored if OWM_API_KEY is present in environment variables. Default {default_api_key}")

    args = parser.parse_args(raw_args)

    if "OWM_API_KEY" in os.environ:
        api_key = os.environ["OWM_API_KEY"].strip()
    else:
        with open(args.api_key or os.path.expanduser(default_api_key)) as f:
            api_key = f.read().strip()

    weather = get_weather_data(args.location, owm(api_key))
    charts = generate_charts(weather, args.width, args.height)
    render_images(charts, args.output, args.dpi)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
