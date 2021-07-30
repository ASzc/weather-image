# Weather Images

## Overview

Static charts of hourly weather forecast data, from [OpenWeatherMap](https://openweathermap.org/).

These are good for many purposes. One example is filling in gaps on your [security camera monitor](https://github.com/SvenVD/rpisurv) with useful information.

The images are updated hourly.

## Usage

You can access the images through HTTP on the Github Pages site:

```bash
TODO curl
```

For all available cities, please see the index [here](TODO).

### Is your city not available?

Please file a PR to have a new city added.

Alternatively, run `weather_image.py` on your own computer. You will need a free API Key from [OpenWeatherMap](https://openweathermap.org/api), placed in a file at `~/.openweathermap_api_key`.
