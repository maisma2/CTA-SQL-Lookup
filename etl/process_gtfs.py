import pandas as pd

# MAKING STATIONS.CSV -------------------------------------------------------------
stops = pd.read_csv("data/raw/stops.txt")

stations = stops[stops["location_type"] == 1].copy()

stations_clean = stations[[
    "stop_id",
    "stop_name",
    "stop_lat",
    "stop_lon",
    "wheelchair_boarding"
]].rename(columns={
    "stop_id": "station_id",
    "stop_name": "name",
    "stop_lat": "latitude",
    "stop_lon": "longitude",
    "wheelchair_boarding": "wheelchair"
})

stations_clean.to_csv("data/cleaned/stations.csv", index=False)

print("stations.csv created!")

# ---------------------------------------------------------------------------------

# MAKING STOPS.CSV ----------------------------------------------------------------
stops_clean = stops[
    (stops["location_type"] == 0) &
    (stops["parent_station"].notnull())
].copy()

stops_clean = stops_clean[[
    "stop_id",
    "parent_station",
    "stop_name",
    "stop_desc",
    "stop_lat",
    "stop_lon"
]].rename(columns={
    "parent_station": "station_id",
    "stop_desc": "direction",
    "stop_lat": "latitude",
    "stop_lon": "longitude"
})

stops_clean.to_csv("data/cleaned/stops.csv", index=False)

print("stops.csv created!")
# ---------------------------------------------------------------------------------

# MAKING LINES.CSV
routes = pd.read_csv("data/raw/routes.txt")

rail_lines = routes[routes["route_type"] == 1].copy()

lines_clean = rail_lines[[
    "route_id",
    "route_long_name",
    "route_color"
]].rename(columns={
    "route_id": "line_id",
    "route_long_name": "name",
    "route_color": "color"
})

lines_clean.to_csv("data/cleaned/lines.csv", index=False)

print("lines.csv created!")
# ---------------------------------------------------------------------------------
# MAKING STATION_LINE.CSV 
trips = pd.read_csv("data/raw/trips.txt")
stop_times = pd.read_csv("data/raw/stop_times.txt")
stops = pd.read_csv("data/raw/stops.txt")

rail_trips = trips[trips["route_id"].isin(lines_clean["line_id"])]

rail_stop_times = rail_trips.merge(stop_times, on="trip_id")

rail_stop_times = rail_stop_times.merge(
    stops[["stop_id", "parent_station"]],
    on="stop_id",
    how="left"
)

rail_stop_times = rail_stop_times[rail_stop_times["parent_station"].notnull()]

station_line = rail_stop_times[["parent_station", "route_id"]].drop_duplicates()

station_line = station_line.rename(columns={
    "parent_station": "station_id",
    "route_id": "line_id"
})

station_line.to_csv("data/cleaned/station_line.csv", index=False)

print("station_line.csv created!")
# ---------------------------------------------------------------------------------
# MAKING RIDERSHIP.CSV
ridership_raw = pd.read_csv(
    "data/raw/CTA_-_Ridership_-_'L'_Station_Entries_-_Daily_Totals_20251125.csv"
)

ridership_clean = ridership_raw[[
    "station_id",
    "date",
    "daytype",
    "rides"
]].rename(columns={
    "daytype": "day_type",
    "rides": "total_riders"
})

ridership_clean.to_csv("data/cleaned/ridership.csv", index=False)

print("ridership.csv created!")
# ---------------------------------------------------------------------------------
