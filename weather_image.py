#!/usr/bin/env python3

import argparse
import sys

#
# Optional geopy dependency
#

try:
    import geopy.geocoders
    nominatim = geopy.geocoders.Nominatim(user_agent="weather_image.py")
    def geocode(location):
        loc = nominatim.geocode
        return (loc.latitude, loc.longitude)
except ModuleNotFoundError:
    def geocode(location):
        parts = location.split(",")
        if len(parts) == 2:
            return (parts[0], parts[1])
        else:
            raise Exception("geopy module not installed, specify location as lat,lon only")

#
# OpenWeatherMap API
#

def get_weather_data(location):
    pass

#
# Rendering
#

def render_image(weather):
    pass

#
# Main
#

def main(raw_args):
    default_api_key = "~/.openweathermap_api_key"
    parser = argparse.ArgumentParser(description="Create an image showing weather data for location")
    parser.add_argument("location", help="Location for the weather. Use lat,lon. Example: 51.046,-114.065 If geopy is installed, you can also just give a location textually. Example: Calgary")
    parser.add_argument("-k", "--api-key", help=f"Override API key file location. Default {default_api_key}")

    args = parser.parse_args(raw_args)

    with open(args.api_key or os.path.expanduser(default_api_key)) as f:
        api_key = f.read()

    weather = get_weather_data(location)
    # TODO output path
    render_image(weather, outputTODO)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
