from flask import Flask, render_template, request
from db import get_connection
import math

app = Flask(__name__)

@app.route("/")
def index():
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Weekday vs weekend ridership (overall)
    cursor.execute("""
        SELECT
            day_type,
            AVG(CAST(rides AS float)) AS avg_rides
        FROM dbo.StationRidership
        GROUP BY day_type;
    """)
    day_stats = cursor.fetchall()

    # 2) Ridership by line color
    # Use BIGINT for sums to avoid overflow
    cursor.execute("""
        WITH station_color AS (
            SELECT
                r.station_id,
                sl.color,
                SUM(CAST(r.rides AS bigint)) AS total_rides_station_color
            FROM dbo.StationRidership r
            JOIN dbo.Station s
                ON r.station_id = s.station_id
            JOIN dbo.StationLine sl
                ON sl.stop_id = s.stop_id
            GROUP BY r.station_id, sl.color
        )
        SELECT
            color,
            SUM(CAST(total_rides_station_color AS bigint)) AS total_rides
        FROM station_color
        WHERE color IS NOT NULL
        GROUP BY color
        ORDER BY total_rides DESC;
    """)
    line_stats = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "index.html",
        day_stats=day_stats,
        line_stats=line_stats
    )


@app.route("/stations")
def stations():
    color = request.args.get("color") or None
    ada_only = request.args.get("ada_only") == "1"

    conn = get_connection()
    cursor = conn.cursor()

    # Get list of available colors for the filter dropdown
    cursor.execute("""
        SELECT DISTINCT color
        FROM dbo.StationLine
        WHERE color IS NOT NULL
        ORDER BY color;
    """)
    color_rows = cursor.fetchall()
    colors = [row["color"] for row in color_rows]  # assuming as_dict=True

    # Now fetch stations with optional filters
    if color or ada_only:
        cursor.execute("""
            SELECT
                sn.station_id,
                sn.station_name,
                MAX(CASE WHEN s.ada = 1 THEN 1 ELSE 0 END) AS has_ada
            FROM dbo.StationName sn
            JOIN dbo.Station s
                ON sn.station_id = s.station_id
            LEFT JOIN dbo.StationLine sl
                ON s.stop_id = sl.stop_id
            WHERE (%s IS NULL OR sl.color = %s)
            GROUP BY sn.station_id, sn.station_name
            HAVING (%s = 0 OR MAX(CASE WHEN s.ada = 1 THEN 1 ELSE 0 END) = 1)
            ORDER BY sn.station_name;
        """, (color, color, 1 if ada_only else 0))
    else:
        cursor.execute("""
            SELECT
                sn.station_id,
                sn.station_name,
                MAX(CASE WHEN s.ada = 1 THEN 1 ELSE 0 END) AS has_ada
            FROM dbo.StationName sn
            JOIN dbo.Station s
                ON sn.station_id = s.station_id
            GROUP BY sn.station_id, sn.station_name
            ORDER BY sn.station_name;
        """)

    stations = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template(
        "stations.html",
        stations=stations,
        colors=colors,
        selected_color=color,
        ada_only=ada_only
    )


@app.route("/station/<int:station_id>")
def station_detail(station_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Base station info from StationName
    cursor.execute("""
        SELECT
            station_id,
            station_name AS name
        FROM dbo.StationName
        WHERE station_id = %s;
    """, (station_id,))
    station = cursor.fetchone()  # dict if as_dict=True

    if not station:
        cursor.close()
        conn.close()
        return render_template("station_not_found.html", station_id=station_id), 404

    # 2) Stops at this station (from Station)
    cursor.execute("""
        SELECT
            stop_id,
            stop_name,
            direction,
            ada,
            latitude,
            longitude
        FROM dbo.Station
        WHERE station_id = %s
        ORDER BY stop_name;
    """, (station_id,))
    stops = cursor.fetchall()  # list[dict]

    # Use first stop's coordinates as station coordinates
    station_lat = None
    station_lng = None
    bbox_min_lat = bbox_min_lng = bbox_max_lat = bbox_max_lng = None

    if stops:
        station_lat = float(stops[0]["latitude"])
        station_lng = float(stops[0]["longitude"])

        delta = 0.005
        bbox_min_lng = station_lng - delta
        bbox_min_lat = station_lat - delta
        bbox_max_lng = station_lng + delta
        bbox_max_lat = station_lat + delta

    # 3) Lines serving this station (from StationLine using color)
    cursor.execute("""
        SELECT DISTINCT
            sl.color AS name
        FROM dbo.StationLine AS sl
        JOIN dbo.Station AS s
            ON sl.stop_id = s.stop_id
        WHERE s.station_id = %s
        ORDER BY sl.color;
    """, (station_id,))
    lines = cursor.fetchall()

    # 4) Recent ridership (last 30 rows) from StationRidership
    cursor.execute("""
        SELECT TOP 30
            [date]  AS date,
            rides   AS total_riders
        FROM dbo.StationRidership
        WHERE station_id = %s
        ORDER BY [date] DESC;
    """, (station_id,))
    ridership = cursor.fetchall()

    # 5) Total ridership (all time) for this station
    cursor.execute("""
        SELECT
            SUM(CAST(rides AS bigint)) AS total_rides
        FROM dbo.StationRidership
        WHERE station_id = %s;
    """, (station_id,))
    total_row = cursor.fetchone()
    total_rides = total_row["total_rides"] or 0

    # 6) Compute importance score: log10(total_rides + 1) + num_lines
    num_lines = len(lines)
    importance_score = math.log10(total_rides + 1) + num_lines

    # 7) Station's contribution to each line it serves
    line_contributions = []
    if lines and total_rides > 0:
        colors = [l["name"] for l in lines if l["name"] is not None]
        if colors:
            placeholders = ",".join(["%s"] * len(colors))
            cursor.execute(f"""
                SELECT
                    sl.color,
                    SUM(CAST(r.rides AS bigint)) AS total_rides
                FROM dbo.StationRidership r
                JOIN dbo.Station s
                    ON r.station_id = s.station_id
                JOIN dbo.StationLine sl
                    ON sl.stop_id = s.stop_id
                WHERE sl.color IN ({placeholders})
                GROUP BY sl.color;
            """, tuple(colors))
            rows = cursor.fetchall()
            totals_by_color = {row["color"]: row["total_rides"] for row in rows}

            for c in colors:
                line_total = totals_by_color.get(c, 0) or 0
                if line_total > 0:
                    percent = (total_rides / float(line_total)) * 100.0
                else:
                    percent = None
                line_contributions.append({
                    "color": c,
                    "line_total_rides": line_total,
                    "percent": percent,
                })

    cursor.close()
    conn.close()

    return render_template(
        "station_detail.html",
        station=station,
        stops=stops,
        lines=lines,
        ridership=ridership,
        station_lat=station_lat,
        station_lng=station_lng,
        bbox_min_lat=bbox_min_lat,
        bbox_min_lng=bbox_min_lng,
        bbox_max_lat=bbox_max_lat,
        bbox_max_lng=bbox_max_lng,
        importance_score=importance_score,
        total_rides=total_rides,
        num_lines=num_lines,
        line_contributions=line_contributions,
    )



@app.route("/search")
def search():
    """
    Search stations by name. Uses ?q= in the query string.
    """
    query = request.args.get("q", "").strip()

    conn = get_connection()
    cursor = conn.cursor()

    if query:
        cursor.execute("""
            SELECT station_id, stop_name AS name
            FROM dbo.Station
            WHERE stop_name LIKE %s
            ORDER BY stop_name;
        """, (f"%{query}%",))
    else:
        cursor.execute("""
            SELECT TOP 50 station_id, stop_name
            FROM dbo.Station
            ORDER BY stop_name;
        """)

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("search_results.html", query=query, results=results)

@app.route("/top_stations")
def top_stations():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        WITH totals AS (
            SELECT
                station_id,
                SUM(rides) AS total_rides
            FROM dbo.StationRidership
            GROUP BY station_id
        ),
        lines AS (
            SELECT
                s.station_id,
                COUNT(DISTINCT sl.color) AS num_lines
            FROM dbo.Station AS s
            LEFT JOIN dbo.StationLine AS sl
                ON s.stop_id = sl.stop_id
            GROUP BY s.station_id
        ),
        combined AS (
            SELECT
                sn.station_id,
                sn.station_name,
                t.total_rides,
                ISNULL(l.num_lines, 0) AS num_lines,
                (LOG10(CAST(t.total_rides + 1 AS float)) + ISNULL(l.num_lines, 0)) AS importance_score
            FROM dbo.StationName sn
            JOIN totals t
                ON sn.station_id = t.station_id
            LEFT JOIN lines l
                ON sn.station_id = l.station_id
        )
        SELECT TOP 10
            station_id,
            station_name,
            total_rides,
            num_lines,
            importance_score
        FROM combined
        ORDER BY importance_score DESC;
    """)

    stations = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("top_stations.html", stations=stations)

if __name__ == "__main__":
    app.run(debug=True)
