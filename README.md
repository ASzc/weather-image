# Weather Images

## Overview

Static charts of hourly weather forecast data, from [OpenWeatherMap](https://openweathermap.org/).

These are good for many purposes. One example is filling in gaps on your [security camera monitor](https://github.com/SvenVD/rpisurv) with useful information.

## Usage

### Hosted images

You can access the images through HTTP on the Github Pages site:

```bash
TODO curl
```

The images are updated hourly.

For all available locations, please see the index [here](TODO).

### Is your location not available?

Please file a PR to have a new location added.

Alternatively, run `weather_image.py` on your own computer:

### Running on your own computer

You will need a free API Key from [OpenWeatherMap](https://openweathermap.org/api), placed in a file at `~/.openweathermap_api_key`.

Install the following Python 3 modules:

  - `pyowm` is required
  - `cairosvg` is optional, but allows for .png image output
  - `geopy` is optional, but allows human-readable locations to be used

```bash
pip3 install pyowm cairosvg geopy
```

Then call the script, with a location and a path to write the image to:

```bash
$ ./weather_image.py Calgary weather.png
```
