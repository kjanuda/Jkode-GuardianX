import pandas as pd

path = r"E:\GuardianX\data\ml\rca_dataset.csv"

df = pd.read_csv(path)

df = df[
    df["training_eligible"]
    .astype(str)
    .str.lower()
    .eq("true")
].copy()

features = [
    "population_affected_ratio",
    "device_model_pattern",
    "population_sample_quality",
    "congestion_signature",
    "coverage_signature",
    "interference_signature",
    "outage_signature",
    "terrain_context",
    "vegetation_context",
    "weather_context",
    "historical_context",
    "total_devices",
    "affected_devices",
    "healthy_devices",
    "mean_los_blocked_pct",
    "mean_geo_vulnerability",
    "mean_fresnel_occupancy_pct",
    "mean_max_fresnel_intrusion_m",
    "mean_minimum_clearance_ratio",
    "mean_environmental_vulnerability",
    "mean_weather_score",
]

print("ROWS:", len(df))
print()

for column in features:
    print("=" * 72)
    print("FEATURE:", column)
    print("dtype:", df[column].dtype)
    print("missing:", int(df[column].isna().sum()))

    values = df[column].dropna().unique()

    if len(values) <= 15:
        print("values:", sorted(map(str, values)))
    else:
        print("unique_count:", len(values))
        print("sample:", values[:10])

print()
print("=" * 72)
print("GROUP COUNT:", df["split_group"].nunique())

print()
print("ROWS PER GROUP:")
print(
    df.groupby("split_group")
      .size()
      .sort_index()
      .to_string()
)
