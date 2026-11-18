# Did NYC congestion pricing change Uber/Lyft demand in the zone?

**Short answer:** A naive year-over-year comparison says Uber/Lyft trips touching the Congestion Relief Zone fell ~8.4% relative to trips that never touch it after the fee began on Jan 5, 2025. But a placebo test on a period with no fee (Jul-Dec 2024 vs 2023) shows the same comparison already reading about -7%. Net of that pre-existing drift, the estimated effect is **about -1.2 points (rough 95% interval -2.6 to +0.9)**, so these data cannot distinguish a small negative effect from no effect.

## The question
On January 5, 2025, NYC began charging a per-trip fee for vehicles entering Manhattan's Central Business District. There was no randomized test, so a before/after comparison mixes the fee's effect with weather, holidays and trends that were already under way.

## Data
- NYC TLC High Volume For-Hire Vehicle (Uber/Lyft) trip records, Jul 2023 - Jun 2025 (24 monthly parquet files).
- MTA's list of the 38 taxi zones inside the Congestion Relief Zone.
- Queried with DuckDB (SQL directly on parquet) and analyzed in Python.

## Method
1. **Who is treated?** I first assumed pickups in the zone. Checking the `cbd_congestion_fee` column (Feb 2025) showed that was wrong: 98-99.5% of trips that start OR end in the zone are charged, while trips touching neither end are charged only 2.8% of the time.
   - **Treated:** trips that start or end in one of the 38 zones (~34% of trips).
   - **Control:** trips that start and end outside it.
2. **Weekly totals, Sunday-start weeks**, so the Jan 5 launch falls on a week boundary. Partial weeks are dropped.
3. **Naive estimate:** for each post-launch week, the change in log(treated / control trips) versus the same week 364 days earlier (removes weekly and seasonal patterns).
4. **Placebo:** the same calculation on Jul-Dec 2024 vs Jul-Dec 2023, when no fee existed.
5. **Net effect:** real-period mean minus placebo mean, with a block bootstrap (4-week blocks) for a rough interval.

## Findings
| | Weeks | Mean | Median |
|---|---|---|---|
| Real (Jan-Jun 2025 vs 2024) | 25 | -8.4% | -8.7% |
| Real, Easter-shifted weeks dropped | 23 | -8.4% | -8.7% |
| Placebo (Jul-Dec 2024 vs 2023) | 25 | -7.0% | -7.4% |
| Placebo, Thanksgiving weeks dropped | 23 | -7.2% | -7.4% |

- **Net effect: -1.2 points, rough 95% interval -2.6 to +0.9.**
- Trips touching the zone were already falling relative to the rest of the city before the fee. A naive comparison would credit the fee with an effect that is mostly that drift.
- Total weekly trips barely moved (about 4.4-4.9M a week in both spring 2024 and spring 2025).
- [YOUR WORDS: one sentence on what you think this means.]

## How this could be wrong
- **The placebo assumes the drift would have continued at the same rate into 2025.** If it faded or sped up, the net estimate shifts.
- **The interval is rough.** Block bootstrap with 23 weeks per period, and dropping holiday weeks leaves gaps.
- **Contaminated control.** Some people may have changed trips because of the fee (for example, choosing a Brooklyn destination over a Manhattan one), which would inflate control and make the effect look larger.
- **Moving holidays.** Thanksgiving (Nov 23, 2023 vs Nov 28, 2024) produced +18% and -28% placebo weeks. Easter (Mar 31, 2024 vs Apr 20, 2025) likely affects the real period. I dropped those weeks and checked that the means barely changed. I assumed the holidays caused the swings; I did not verify it.
- **Only one comparison year.** Anything else that changed between years and hit the zone differently would show up here.
- **Data quirk:** the week of Dec 29, 2024 shows 0.1% of treated trips charged, before the fee started. Likely trips crossing midnight; not verified.

## What I'd do next
1. Add Jan-Jun 2023 data so the placebo covers the same months as the real period.
2. Event-study plot with a fitted pre-trend instead of a single placebo mean.
3. Synthetic control using groups of non-treated zones.
4. Check boundary zones just north of 60th St for spillover.
5. Estimate demand response per dollar of fee. News coverage reported a $1.50 per-trip surcharge for for-hire vehicles; I'd confirm that against an official source first.

## How this was built
I used AI assistance (Claude) for code scaffolding and design discussion, and I ran and checked every step myself. Three places where checking changed the answer:
- A single odd base week made my first comparison chart misleading, so I rebased on a 4-week average.
- My first treatment definition (pickups only) was wrong; the fee column showed trips *arriving* in the zone are charged too, so I rebuilt the groups.
- My first headline (-8.4%) did not survive the placebo test; most of it was drift that existed before the fee.

## Reproduce
```
python build_weekly3.py   # builds weekly_by_group.csv from the parquet files
python did2.py            # real period vs placebo, with chart
python did3.py            # net effect and rough interval
```
Raw parquet files are not committed (about 10 GB). `download_data.ps1` fetches Jan 2024 - Jun 2025 and `download_2023.ps1` fetches Jul - Dec 2023. The MTA zone list and TLC zone lookup are in `data/raw/`, and the small weekly summary `weekly_by_group.csv` is committed, so `did2.py` and `did3.py` run without the big download.
