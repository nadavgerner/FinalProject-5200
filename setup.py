import os
import requests
import pandas as pd

def fetch_and_save_df(name, url, params, chunk_size=1000, data_dir="data"):
    """Requests JSON data from ArcGIS REST API url, converts to pd.DataFrame, and saves it to datafolder"""
    all_records = []
    offset = 0

    while True:
        paged_params = params.copy()
        paged_params["resultOffset"] = offset
        paged_params["resultRecordCount"] = chunk_size

        response = requests.get(url, params=paged_params)
        response.raise_for_status()
        data = response.json()
        
        features = data.get("features", [])
        if not features:
            break 

        for feature in features:
            row = feature.get("attributes", {}).copy()
            geometry = feature.get("geometry", {})
            row["geometry_path"] = geometry.get("paths") or geometry.get("rings") or geometry.get("x") or None
            all_records.append(row)

        offset += chunk_size
        print(f"Fetched {len(all_records)} records so far for {name}...")

    # Save to DataFrame and file
    df = pd.DataFrame(all_records)
    os.makedirs(data_dir, exist_ok=True)
    df.to_csv(os.path.join(data_dir, f"{name}.csv"), index=False)
    print(f"Done: {name}: {len(df)} total records saved.")

def fetch_weather_data(start, end, latitude, longitude, output_csv):
    base_url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start,
        "end_date": end,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "windspeed_10m_max",
            "weathercode"
        ],
        "timezone": "America/New_York"
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    weather = response.json()

    df = pd.DataFrame(weather["daily"])
    df["time"] = pd.to_datetime(df["time"])
    
    df.to_csv(output_csv, index=False)
    print(f"Weather data saved to {output_csv}")


#   Weather Params
start_date = "2019-01-01"
end_date = "2024-12-31"
lat, lon = 38.9, -77.04
weather_path = "data/dc_weather_2019_2024.csv"

params = {
    "where": "1=1",
    "outFields": "*",
    "outSR": "4326",
    "f": "json"
}

crash_params = {
    "where": "REPORTDATE >= DATE '2023-01-01' AND REPORTDATE < DATE '2024-01-01'",
    "outFields": "*",
    "outSR": "4326",    
    "f": "json"
}

traffic_url = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Transportation_TrafficVolume_WebMercator/MapServer/4/query"
crash_url = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Public_Safety_WebMercator/MapServer/24/query"
crash_metadata_url = "https://maps2.dcgis.dc.gov/dcgis/rest/services/DCGIS_DATA/Public_Safety_WebMercator/MapServer/25/query?where=1%3D1&outFields=*&outSR=4326&f=json" \

fetch_and_save_df("dc_traffic_volume_2023", traffic_url, params)
fetch_and_save_df("dc_crashes", crash_url, params)
fetch_and_save_df("crashes_metadata", crash_metadata_url, params)
fetch_weather_data(start_date, end_date, lat, lon, weather_path)
