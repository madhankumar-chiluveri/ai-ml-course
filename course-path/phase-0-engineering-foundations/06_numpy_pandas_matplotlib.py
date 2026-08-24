"""
0.6 — Scientific Python: NumPy, Pandas, Matplotlib.

Runnable: `python 06_numpy_pandas_matplotlib.py`
Requires: numpy pandas matplotlib

Writes one PNG (eda_0_6.png) next to this script. Everything else prints.

What this proves practically:
  1. Vectorized ops are ~20-100x faster than Python loops, on real timings.
  2. axis=0 collapses ROWS (one result per column). Shapes shown.
  3. Broadcasting stretches a (2,) across a (3,2) — no manual tiling.
  4. .loc and .iloc DIVERGE after a filter. The silent wrong-row bug.
  5. `and` on a Series RAISES. You must use & with parentheses.
  6. Three fillna strategies encode three DIFFERENT assumptions.
"""

import time

import matplotlib
matplotlib.use("Agg")          # headless: no window, works over SSH (0.10)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path

SEP = "=" * 70
rng = np.random.default_rng(42)      # seeded -> reproducible (7.10)


# ====================================================================== 1
def demo_vectorization() -> None:
    print(SEP)
    print("DEMO 1 — vectorization: the same filter, three ways")
    print(SEP)

    n = 2_000_000
    data = list(range(n))
    arr = np.arange(n)

    t0 = time.perf_counter()
    out_loop = []
    for x in data:
        if x > 1_000_000:
            out_loop.append(x)
    t_loop = time.perf_counter() - t0

    t0 = time.perf_counter()
    out_comp = [x for x in data if x > 1_000_000]
    t_comp = time.perf_counter() - t0

    t0 = time.perf_counter()
    out_np = arr[arr > 1_000_000]        # BOOLEAN MASK — the key idiom
    t_np = time.perf_counter() - t0

    print(f"  n = {n:,}")
    print(f"  python loop + append : {t_loop*1000:8.1f} ms")
    print(f"  list comprehension   : {t_comp*1000:8.1f} ms   ({t_loop/t_comp:.2f}x)")
    print(f"  numpy boolean mask   : {t_np*1000:8.1f} ms   ({t_loop/t_np:.1f}x)")
    print(f"  all same length?     : {len(out_loop)==len(out_comp)==len(out_np)}")
    print("\n  The mask arr > 1_000_000 is itself an array of True/False:")
    print(f"    (arr > 1_000_000)[:8] -> {(arr > 1_000_000)[:8]}")
    print("  Indexing WITH that array selects the True positions. One idiom")
    print("  replaces most filtering loops you would otherwise write.")


# ====================================================================== 2
def demo_axis_and_broadcasting() -> None:
    print(SEP)
    print("DEMO 2 — axis = the dimension that DISAPPEARS")
    print(SEP)

    X = np.array([[1.0, 2.0],
                  [3.0, 4.0],
                  [5.0, 6.0]])          # 3 samples, 2 features (the ML convention)

    print(f"  X =\n{X}")
    print(f"  X.shape            : {X.shape}   (rows=samples, cols=features)")
    print(f"  X.mean(axis=0)     : {X.mean(axis=0)}  shape {X.mean(axis=0).shape}")
    print("                       ^ collapsed ROWS -> one value PER COLUMN")
    print(f"  X.mean(axis=1)     : {X.mean(axis=1)}  shape {X.mean(axis=1).shape}")
    print("                       ^ collapsed COLS -> one value PER ROW")
    print("\n  For feature scaling (2.2) you want axis=0: the per-FEATURE mean.")

    print(SEP)
    print("DEMO 3 — broadcasting: (3,2) - (2,) with no manual tiling")
    print(SEP)
    col_mean = X.mean(axis=0)            # shape (2,)
    centered = X - col_mean              # (3,2) - (2,) -> (3,2)
    print(f"  col_mean shape {col_mean.shape}, X shape {X.shape}")
    print(f"  X - col_mean =\n{centered}")
    print(f"  new column means   : {centered.mean(axis=0)}   <- all ~0, as intended")
    print("\n  NumPy stretched (2,) down 3 rows automatically. Doing this by")
    print("  hand with np.tile is what broadcasting removes. Formalised in 1.14.")

    # Shape discipline: the error you WILL hit.
    try:
        _ = X + np.array([1.0, 2.0, 3.0])     # (3,2) + (3,) -> incompatible
    except ValueError as e:
        print(f"\n  X + shape-(3,) array -> ValueError: {e}")
        print("  Fix: reshape to (3,1) so it broadcasts along columns:")
        print(f"    X + np.array([1,2,3]).reshape(-1,1) =\n{X + np.array([1.,2.,3.]).reshape(-1,1)}")


# ====================================================================== 4
def build_df() -> pd.DataFrame:
    return pd.DataFrame({
        "vendor":    ["Acme", "Beta", "Acme", "Gamma", "Beta", "Acme", "Delta"],
        "amount":    [51000, 9000, 12000, 78000, 45000, 63000, 150000],
        "status":    ["OPEN", "PAID", "OPEN", "OVERDUE", "PAID", "OPEN", "OVERDUE"],
        "days_late": [12, 0, 3, 45, 0, 7, np.nan],
    })


def demo_pandas_inspection(df: pd.DataFrame) -> None:
    print(SEP)
    print("DEMO 4 — the four commands to run on EVERY new dataset")
    print(SEP)
    print("  df.head(3)\n", df.head(3).to_string(index=False), sep="")
    print("\n  df.describe() [numeric only]")
    print(df.describe().to_string())
    print("\n  df.isna().sum()   <- drives every 2.2 decision")
    print(df.isna().sum().to_string())
    print(f"\n  dtypes: {dict(df.dtypes.astype(str))}")


# ====================================================================== 5
def demo_loc_vs_iloc(df: pd.DataFrame) -> None:
    print(SEP)
    print("DEMO 5 — .loc vs .iloc: the silent wrong-row bug after a filter")
    print(SEP)

    big = df[df["amount"] > 40_000]      # filtering KEEPS original index labels
    print(f"  original index : {list(df.index)}")
    print(f"  filtered index : {list(big.index)}   <- NOT 0,1,2,3!")

    print(big)

    # THE POINT: same integer 3, two DIFFERENT rows, no error either way.
    by_pos = big.iloc[3]
    by_lab = big.loc[3]
    print(f"\n  big.iloc[3] -> vendor={by_pos['vendor']!r} amount={by_pos['amount']}"
          f"   (POSITION 3)")
    print(f"  big.loc[3]  -> vendor={by_lab['vendor']!r} amount={by_lab['amount']}"
          f"   (LABEL 3)")
    print(f"  SAME INTEGER, DIFFERENT ROW: {by_pos['vendor'] != by_lab['vendor']}")
    print("  Neither raises. Nothing warns. You just read the wrong invoice.")

    # And a label that no longer exists DOES raise — the luckier failure.
    try:
        big.loc[1]
    except KeyError:
        print("\n  big.loc[1] -> KeyError: 1   (label 1 was filtered out)")
        print("  ^ this one at least fails loudly")

    reset = big.reset_index(drop=True)
    print(reset)
    print(f"\n  after reset_index(drop=True), index = {list(reset.index)}")
    print(f"  now .loc[3] and .iloc[3] agree: "
          f"{reset.loc[3]['vendor']!r} == {reset.iloc[3]['vendor']!r}")
    print("\n  ^ Forgetting reset_index is how you silently read the wrong row.")


# ====================================================================== 6
def demo_boolean_ops(df: pd.DataFrame) -> None:
    print(SEP)
    print("DEMO 6 — `and` RAISES on a Series. Use & with parentheses.")
    print(SEP)
    try:
        _ = df[(df["amount"] > 10_000) and (df["status"] != "PAID")]
    except ValueError as e:
        print(f"  using `and` -> ValueError: {str(e)[:90]}...")
    mask = (df["amount"] > 10_000) & (df["status"] != "PAID")
    print(f"\n  using &     -> {mask.sum()} rows match")
    print(df[mask].to_string(index=False))
    print("\n  Parentheses are REQUIRED: & binds tighter than > in Python.")


# ====================================================================== 7
def demo_groupby(df: pd.DataFrame) -> None:
    print(SEP)
    print("DEMO 7 — groupby: split -> apply -> combine")
    print(SEP)
    simple = df.groupby("vendor")["amount"].sum()
    print("  df.groupby('vendor')['amount'].sum()")
    print(simple.to_string())

    multi = df.groupby("vendor").agg(
        total=("amount", "sum"),
        n=("amount", "size"),
        worst_delay=("days_late", "max"),
    )
    print("\n  multi-statistic .agg()")
    print(multi.to_string())

    repeat = df.groupby("vendor").filter(lambda g: len(g) > 1)
    print(f"\n  groups with more than 1 invoice: {sorted(repeat['vendor'].unique())}")


# ====================================================================== 8
def demo_missing_values(df: pd.DataFrame) -> None:
    print(SEP)
    print("DEMO 8 — three fillna strategies = three DIFFERENT assumptions")
    print(SEP)
    col = df["days_late"]
    print(f"  raw           : {list(col)}")
    print(f"  fillna(0)     : {list(col.fillna(0))}")
    print("                  assumption: missing MEANS not late")
    print(f"  fillna(median): {list(col.fillna(col.median()))}")
    print("                  assumption: missing is a TYPICAL case")
    print(f"  dropna()      : {list(col.dropna())}  (row removed entirely)")
    print("                  assumption: the row is UNUSABLE without it")
    print("\n  These give different models. Naming the assumption out loud is")
    print("  the actual skill in 2.2 — not knowing the method names.")


# ====================================================================== 9
def demo_plot(df: pd.DataFrame) -> Path:
    print(SEP)
    print("DEMO 9 — the two first plots for any dataset")
    print(SEP)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    # Histogram: FIRST plot for any numeric column. Shows skew and outliers
    # that describe() hides behind summary statistics.
    axes[0].hist(df["amount"], bins=8, edgecolor="black")
    axes[0].set_title("Invoice amount distribution")
    axes[0].set_xlabel("amount")
    axes[0].set_ylabel("count")

    # Scatter: FIRST plot for any two numeric columns. Shows the SHAPE of a
    # relationship, which decides whether 2.3 linear regression even applies.
    sub = df.dropna(subset=["days_late"])
    axes[1].scatter(sub["days_late"], sub["amount"])
    axes[1].set_title("Amount vs days late")
    axes[1].set_xlabel("days_late")
    axes[1].set_ylabel("amount")

    plt.tight_layout()                       # stops labels overlapping
    out = Path(__file__).parent / "eda_0_6.png"
    plt.savefig(out, dpi=110)                # SAVE, don't just show — EDA goes
    plt.close(fig)                           # in the Phase 8 decision log
    print(f"  wrote {out.name} ({out.stat().st_size:,} bytes)")
    print(f"  amount skew: {df['amount'].skew():.2f}  "
          f"(>0 = right tail, which the histogram shows)")
    return out


def main() -> None:
    print(f"numpy {np.__version__} | pandas {pd.__version__} | "
          f"matplotlib {matplotlib.__version__}")
    demo_vectorization()
    demo_axis_and_broadcasting()
    df = build_df()
    demo_pandas_inspection(df)
    demo_loc_vs_iloc(df)
    demo_boolean_ops(df)
    demo_groupby(df)
    demo_missing_values(df)
    demo_plot(df)
    print(SEP)
    print("If you wrote `for i in range(len(df))` anywhere above — there is a")
    print("vectorized form, and it is the notation the rest of this course uses.")
    print(SEP)


if __name__ == "__main__":
    main()
