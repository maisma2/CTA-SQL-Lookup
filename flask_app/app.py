from flask import Flask, render_template, request
from db import get_connection

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stations")
def stations():
    """
    Show a list of all stations (id + name).
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT station_id, stop_name AS name
        FROM dbo.Station
        ORDER BY stop_name;
    """)

    stations = cursor.fetchall()  # list of dicts: {"station_id": ..., "name": ...}

    cursor.close()
    conn.close()

    return render_template("stations.html", stations=stations)


@app.route("/station/<int:station_id>")
def station_detail(station_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Base station info
    cursor.execute("""
        SELECT *
        FROM dbo.Station
        WHERE station_id = ?;
    """, (station_id,))
    station = cursor.fetchone()

    # 2) Lines serving this station
    cursor.execute("""
        SELECT s.*
        FROM dbo.Station AS s
        INNER JOIN dbo.StationLine AS sl
            ON s.stop_id = sl.stop_id
        WHERE sl.stop_id = ?
        ORDER BY s.stop_name, s.station_id;
    """, (station_id,))
    lines = cursor.fetchall()

    # 3) Recent ridership
    cursor.execute("""
        SELECT TOP 30
            [date] AS date,
            StationRidership.rides AS total_riders
        FROM dbo.StationRidership
        WHERE station_id = ?
        ORDER BY [date] DESC;
    """, (station_id,))
    ridership = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "station_detail.html",
        station=station,
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
            SELECT station_id, stop_name
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


if __name__ == "__main__":
    app.run(debug=True)