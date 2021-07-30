#!/usr/bin/env python3

import argparse
import os
import sys

#
# Location Parsing
#

geocoder = None
def geocode(location):
    global geocoder

    parts = location.split(",")
    if len(parts) == 2:
        return (float(parts[0]), float(parts[1]))
    else:
        try:
            import geopy.geocoders
        except ModuleNotFoundError:
            raise Exception("geopy module not installed, specify location as lat,lon only")

        if not geocoder:
            geocoder = geopy.geocoders.Nominatim(user_agent="weather_image.py")
        loc = geocoder.geocode(location)
        return (loc.latitude, loc.longitude)

#
# OpenWeatherMap API
#

def get_weather_data(latlon, api):
    pass

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
        api_key = f.read()

    weather = get_weather_data(args.location, api_key)
    chart = generate_chart(weather)
    render_image(chart, args.output)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
