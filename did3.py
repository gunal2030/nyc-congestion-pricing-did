import duckdb
import numpy as np
import pandas as pd

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
df = df[df["days"] == 7].set_index("week_start")
df["log_ratio"] = np.log(df["treated"] / df["control"])


def effects(first, last):
    """Treated-vs-control change versus the same week 364 days earlier, in percent."""
    weeks = df[(df.index >= first) & (df.index <= last)]
    prev = df.loc[weeks.index - pd.Timedelta(days=364), "log_ratio"]
    return pd.Series(100 * (weeks["log_ratio"].values - prev.values), index=weeks.index)


real = effects(pd.Timestamp(2025, 1, 5), pd.Timestamp(2025, 6, 22))
fake = effects(pd.Timestamp(2024, 7, 7), pd.Timestamp(2024, 12, 22))

# Weeks where a moving holiday lands in different weeks in the two years being compared.
# Thanksgiving: Nov 23 2023 vs Nov 28 2024. Easter: Mar 31 2024 vs Apr 20 2025.
thanksgiving = pd.to_datetime(["2024-11-17", "2024-11-24"])
easter = pd.to_datetime(["2025-03-30", "2025-04-20"])
fake_clean = fake.drop(thanksgiving)
real_clean = real.drop(easter)

print("                              weeks   mean   median")
for name, s in [("Real, all weeks", real), ("Real, Easter weeks dropped", real_clean),
                ("Placebo, all weeks", fake), ("Placebo, Thanksgiving dropped", fake_clean)]:
    print(f"{name:30s}{len(s):4d}  {s.mean():6.1f}  {s.median():6.1f}")

net = real_clean.mean() - fake_clean.mean()
print()
print(f"Net effect (real minus placebo baseline): {net:.1f} points")

# Block bootstrap (blocks of 4 weeks, so neighbouring weeks stay together)
rng = np.random.default_rng(0)


def boot_means(x, block=4, reps=5000):
    x = np.asarray(x)
    n = len(x)
    k = int(np.ceil(n / block))
    out = np.empty(reps)
    for i in range(reps):
        starts = rng.integers(0, n - block + 1, size=k)
        out[i] = np.concatenate([x[s:s + block] for s in starts])[:n].mean()
    return out


diff = boot_means(real_clean.values) - boot_means(fake_clean.values)
lo, hi = np.percentile(diff, [2.5, 97.5])
print(f"Rough 95% interval: {lo:.1f} to {hi:.1f} points")
print("(Rough: it ignores the fact that the dropped holiday weeks leave gaps.)")