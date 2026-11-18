import duckdb
from glob import glob

files = sorted(glob("data/raw/fhvhv_tripdata_*.parquet"))
print("Using", len(files), "files")

con = duckdb.connect("nyc.duckdb")

con.execute("""
    CREATE OR REPLACE TABLE cbd AS
    SELECT "Taxi Zone" AS zone_id FROM read_csv('data/raw/mta_cbd_taxi_zones.csv')
""")

# Trips per day, split into treated (touches the zone) vs control (never touches it)
con.execute("""
    CREATE OR REPLACE TABLE daily_group AS
    SELECT CAST(t.pickup_datetime AS DATE) AS day,
           (p.zone_id IS NOT NULL OR d.zone_id IS NOT NULL) AS touches_cbd,
           COUNT(*) AS trips,
           SUM(CASE WHEN COALESCE(t.cbd_congestion_fee, 0) > 0 THEN 1 ELSE 0 END) AS charged_trips,
           SUM(t.base_passenger_fare) AS fare_sum
    FROM read_parquet(?, union_by_name = true) t
    LEFT JOIN cbd p ON t.PULocationID = p.zone_id
    LEFT JOIN cbd d ON t.DOLocationID = d.zone_id
    WHERE t.pickup_datetime >= '2023-07-01' AND t.pickup_datetime < '2025-07-01'
    GROUP BY 1, 2
""", [files])

# Group days into weeks that start on Sunday
con.execute("""
    CREATE OR REPLACE TABLE weekly_group AS
    SELECT CAST(date_trunc('week', day + 1) AS DATE) - 1 AS week_start,
           touches_cbd,
           COUNT(DISTINCT day) AS days,
           SUM(trips) AS trips,
           SUM(charged_trips) AS charged_trips,
           SUM(fare_sum) AS fare_sum
    FROM daily_group
    GROUP BY 1, 2
""")
con.execute("COPY weekly_group TO 'weekly_by_group.csv' (HEADER, DELIMITER ',')")

# Sanity checks
print(con.execute("""
    SELECT MIN(week_start) AS first_week, MAX(week_start) AS last_week,
           COUNT(DISTINCT week_start) AS n_weeks
    FROM weekly_group
""").df().to_string())

print(con.execute("""
    SELECT COUNT(DISTINCT week_start) AS full_weeks_before_launch,
           ROUND(MAX(100.0 * charged_trips / trips), 2) AS max_pct_charged
    FROM weekly_group
    WHERE week_start < '2025-01-05' AND days = 7
""").df().to_string())