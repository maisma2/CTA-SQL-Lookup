from flask import Flask, render_template, request
from db import get_connection

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


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
    # station_name -> name (for template: station.name)
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

    # 3) Lines serving this station (from StationLine using stop_id + color)
    # We join StationLine -> Station by stop_id,
    # and alias color as "name" so the template can use line.name
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
    # rides -> total_riders (for template: r.total_riders)
    cursor.execute("""
        SELECT TOP 30
            [date]  AS date,
            rides   AS total_riders
        FROM dbo.StationRidership
        WHERE station_id = %s
        ORDER BY [date] DESC;
    """, (station_id,))
    ridership = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "station_detail.html",
        station=station,
        stops=stops,
        lines=lines,
        ridership=ridership,
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