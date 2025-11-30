import csv

# Line ID > Color map, based on dataset
line_map = {
    1: "Red",
    2: "Blue",
    3: "Green",
    4: "Brown",
    5: "Purple",
    6: "Purple-Express",
    7: "Yellow",
    8: "Pink",
    9: "Orange"
}

input_file = "StationLine.csv"
output_file = "StationLine_color.csv"

with open(input_file, newline='') as infile, open(output_file, "w", newline='') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.writer(outfile)

    # Write header
    writer.writerow(["stop_id", "color"])

    for row in reader:
        stop_id = row["stop_id"]
        line_id = int(row["line_id"])

        color = line_map.get(line_id, "UNKNOWN")

        writer.writerow([stop_id, color])

print("Done! Created:", output_file)
