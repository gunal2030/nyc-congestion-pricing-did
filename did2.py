import duckdb
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

df = duckdb.sql("""
    SELECT week_start,
           MAX(days) AS days,
           SUM(CASE WHEN touches_cbd THEN trips END) AS treated,
           SUM(CASE WHEN NOT touches_cbd THEN trips END) AS control
    FROM read_csv('weekly_by_group.csv')
    GROUP BY 1
    ORDER BY 1
""").df()

df["week_start"] = pd.to_datetime(df["week_start"])
df = df[df["days"] == 7].set_index("week_start")      # drop partial weeks
df["log_ratio"] = np.log(df["treated"] / df["control"])


def effects(first, last):
    """Treated-vs-control change versus the same week 364 days earlier, in percent."""
    weeks = df[(df.index >= first) & (df.index <= last)]
    prev = df.loc[weeks.index - pd.Timedelta(days=364), "log_ratio"]
    return pd.Series(100 * (weeks["log_ratio"].values - prev.values), index=weeks.index)


real = effects(pd.Timestamp(2025, 1, 5), pd.Timestamp(2025, 6, 22))    # the fee period
fake = effects(pd.Timestamp(2024, 7, 7), pd.Timestamp(2024, 12, 22))   # no fee existed

for name, s in [("REAL launch (Jan-Jun 2025 vs 2024)", real),
                ("PLACEBO (Jul-Dec 2024 vs 2023)", fake)]:
    print(name)
    print("  weeks:", len(s), "| mean:", round(s.mean(), 1), "% | std:", round(s.std(), 1),
          "| min:", round(s.min(), 1), "| max:", round(s.max(), 1))

print()
print("Placebo, week by week:")
print(fake.round(1).to_string())

fig, axes = plt.subplots(1, 2, figsize=(12, 4), sharey=True)
axes[0].bar(fake.index, fake.values, width=5)
axes[0].set_title("Placebo: Jul-Dec 2024 vs 2023 (no fee)")
axes[1].bar(real.index, real.values, width=5)
axes[1].set_title("Real: Jan-Jun 2025 vs 2024 (fee)")
for ax in axes:
    ax.axhline(0, color="black")
    ax.tick_params(axis="x", rotation=45)
plt.tight_layout()
plt.show()