DROP TABLE IF EXISTS StationLine;
DROP TABLE IF EXISTS Ridership;
DROP TABLE IF EXISTS Station;
DROP TABLE IF EXISTS Line;


CREATE TABLE Line (
    -- Changed AUTO_INCREMENT to IDENTITY(1,1) for Azure SQL
    line_id INT PRIMARY KEY IDENTITY(1,1),
    name VARCHAR(50),
    color VARCHAR(30)
);


CREATE TABLE Station (
    station_id INT PRIMARY KEY,
    name VARCHAR(100),
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    wheelchair INT
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

-- Table Station needs WHeelchair column
ALTER TABLE Station
ADD wheelchair TINYINT NULL;

-- Lines needs changes too
DROP TABLE IF EXISTS Line;
CREATE TABLE Line (
    -- Change this to match your CSV data and use it as PK
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50),
    color VARCHAR(30)
);