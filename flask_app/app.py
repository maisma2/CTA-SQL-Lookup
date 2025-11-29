from flask import Flask, render_template, request
from db import get_connection

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/stations")
def stations():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT station_id, station_name FROM dbo.StationName; ORDER BY name;")
    stations = [{"station_id": row[0], "station_name": row[1]} for row in cursor.fetchall()]


    cursor.close()
    conn.close()

    return render_template("stations.html", stations=stations)



@app.route("/station/<int:station_id>")
def station_detail(station_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Station WHERE station_id = %s", (station_id,))
    station = cursor.fetchone()

    cursor.execute("""
        SELECT l.name 
        FROM Line l
        JOIN StationLine sl ON l.line_id = sl.line_id
        WHERE sl.station_id = %s
    """, (station_id,))
    lines = cursor.fetchall()

    cursor.execute("""
        SELECT 
            STR_TO_DATE(date, '%m/%d/%Y') AS date,
            total_riders
        FROM Ridership
        WHERE station_id = %s
        ORDER BY STR_TO_DATE(date, '%m/%d/%Y') DESC
        LIMIT 30
    """, (station_id,))
    ridership = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "station_detail.html",
        station=station,
        lines=lines,
        ridership=ridership
    )


@app.route("/search")
def search():
    query = request.args.get("q", "")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT station_id, name 
        FROM Station
        WHERE name LIKE %s
        ORDER BY name
    """, (f"%{query}%",))

    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("search_results.html", query=query, results=results)



if __name__ == "__main__":
    app.run(debug=True)
