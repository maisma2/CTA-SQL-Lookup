# NOTE: Some content is AI generated

import pandas as pd

# Path to your local CSV file
CSV_PATH = "originals/CTA_L_Daily_Ridership.csv"

# Columns that define the PK in SQL Server
PK_COLS = ["station_id", "date"]

def main():
    # Read the CSV
    df = pd.read_csv(CSV_PATH)

    # Parse date column into real dates (handles 12/22/2017, 2011-07-18, etc.)
    df["date"] = pd.to_datetime(df["date"], errors="coerce", infer_datetime_format=True)

    # Basic sanity check for bad dates
    bad_dates = df[df["date"].isna()]
    if not bad_dates.empty:
        print("Some rows have invalid or unparsed dates:")
        print(bad_dates.head())
        print()

    # Detect duplicates *by PK only* (station_id + date)
    dup_mask = df.duplicated(subset=PK_COLS, keep=False)
    dup_rows = df[dup_mask].sort_values(PK_COLS)

    if dup_rows.empty:
        print("No duplicate (station_id, date) combinations found in the CSV.")
    else:
        print("Duplicate (station_id, date) combinations found in the CSV!")
        print("Here are some of them:\n")
        # Show just a small sample to avoid flooding the console
        print(dup_rows.head(20).to_string(index=False))

        # Save all duplicates to a separate CSV
        dup_rows.to_csv("CTA_L_Daily_Ridership_PK_duplicates.csv", index=False)
        print("\nAll duplicates saved to: CTA_L_Daily_Ridership_PK_duplicates.csv")

    # Aggregate by PK and keep max rides
    # For station_name/day_type, we keep the first observed value in each group.
    agg_df = (
        df.sort_values(PK_COLS)  # so "first" is deterministic
          .groupby(PK_COLS, as_index=False)
          .agg({
              "station_name": "first",
              "day_type": "first",
              "rides": "max"   # <--- key line: max rides for each (station_id, date)
          })
    )

    # Write the cleaned, PK-safe file
    output_path = "CTA_L_Daily_Ridership_clean_max.csv"
    agg_df.to_csv(output_path, index=False)

    print(f"\n Cleaned (aggregated) file written to: {output_path}")
    print(f"   Original rows: {len(df)}, After aggregation: {len(agg_df)}")

    # Final check: ensure no PK duplicates remain
    final_dup_mask = agg_df.duplicated(subset=PK_COLS, keep=False)
    if final_dup_mask.any():
        print(" Unexpected: Still found duplicates in cleaned data!")
        print(agg_df[final_dup_mask].sort_values(PK_COLS).to_string(index=False))
    else:
        print(" Cleaned file has unique (station_id, date) — safe for your PK.")

if __name__ == "__main__":
    main()
