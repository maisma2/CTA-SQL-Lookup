DROP TABLE IF EXISTS StationLine;
DROP TABLE IF EXISTS Ridership;
DROP TABLE IF EXISTS Station;
DROP TABLE IF EXISTS Line;


CREATE TABLE Line (
    line_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    color VARCHAR(30)
);


CREATE TABLE Station (
    station_id INT PRIMARY KEY,
    name VARCHAR(100),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6)
);


CREATE TABLE StationLine (
    station_id INT,
    line_id INT,
    FOREIGN KEY (station_id) REFERENCES Station(station_id),
    FOREIGN KEY (line_id) REFERENCES Line(line_id)
);


CREATE TABLE Ridership (
    station_id INT,
    date VARCHAR(10),       
    day_type CHAR(1),
    total_riders INT,
    FOREIGN KEY (station_id) REFERENCES Station(station_id)
);
