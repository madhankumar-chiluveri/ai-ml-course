# 2.2 — Pandas (Panel Data / DataFrames)

# import numpy as np
# import pandas as pd

# # ❌ The Raw Messy Data (What real-world data looks like)
# raw_data = {
#     "user": ["Alice", "Bob", "Charlie", "David"],
#     "raw_salary": ["$95,000", "$120,000", None, "$85,000"],
#     "join_date": ["2024-01-15", "2023-06-20", "2024-03-01", "invalid_date"],
#     "churned": ["no", "yes", "no", "yes"]
# }
# df = pd.DataFrame(raw_data)

# # 🛠️ The Pandas Wrangling Pipeline (3 vectorized steps):
# # 1. Clean Salary: Strip '$' and ',', convert to float, fill missing with median
# df["salary_clean"] = (
#     df["raw_salary"]
#     .str.replace("$", "", regex=False)
#     .str.replace(",", "", regex=False)
#     .astype(float)
# )
# df["salary_clean"] = df["salary_clean"].fillna(df["salary_clean"].median())

# print(df.to_string())

# # Before Cleaning (Messy Data)
# print("--- BEFORE CLEANING (Messy Data) ---")
# print(df[["raw_salary", "join_date", "churned"]].to_string())

# # 2. Parse Dates: Coerce errors into NaT, extract tenure in days
# df["join_date_parsed"] = pd.to_datetime(df["join_date"], errors="coerce")
# print(df["join_date_parsed"])
# df["tenure_days"] = (pd.Timestamp("2026-08-16") - df["join_date_parsed"]).dt.days.fillna(0)
# print(df["tenure_days"])

# # 3. Encode Categorical Label: Convert "yes"/"no" to 1 / 0 for ML
# df["target_churn"] = (df["churned"] == "yes").astype(int)
# print(df["target_churn"])

# # Select only the clean numerical features for the ML model
# ml_features = df[["salary_clean", "tenure_days", "target_churn"]]
# print("--- CLEAN WRANGLED DATA (Model-Ready) ---")
# print(ml_features)

# 2.3 — Matplotlib (The Foundation of Plotting in Python)

# import matplotlib
# matplotlib.use("Agg")  # Headless rendering for cloud/CI environments
# import matplotlib.pyplot as plt
# import numpy as np

# # Plotting loss curve over training epochs
# epochs = np.array([1, 2, 3, 4, 5])
# loss = np.array([0.85, 0.42, 0.25, 0.15, 0.08])

# fig, ax = plt.subplots(figsize=(6, 3))
# ax.plot(epochs, loss, marker="o", color="crimson", label="Train Loss")
# ax.set_title("Training Loss Curve")
# ax.set_xlabel("Epoch")
# ax.set_ylabel("Loss")
# ax.grid(True)
# fig.savefig("loss_curve.png")
# print(f"Rendered {len(epochs)} epoch points to loss_curve.png successfully.")

# 2.8 — Series, DataFrame & Index

# import pandas as pd

# df = pd.DataFrame({
#     "price": [10.0, 20.0],
#     "category": ["A", "B"]
# }, index=["item_1", "item_2"])

# print("DataFrame:\n", df)

# # 2.9 — `.loc` vs. `.iloc`

# import pandas as pd

# df = pd.DataFrame({"val": [10, 20, 30]}, index=[2, 1, 0])

# print("DataFrame with custom index [2, 1, 0]:")
# print(df)

# # .loc uses LABELS (Names)
# # df.loc[row_label, column_label] -> looks for index label 0 (which is the LAST row)
# val_loc = df.loc[0, "val"]

# # .iloc uses INTEGER POSITIONS (0, 1, 2...)
# # df.iloc[row_pos, col_pos] -> looks for row position 0 (FIRST row) and column position 0 ('val')
# val_iloc = df.iloc[0, 0]

# print("\n--- RESULTS ---")
# print("loc[0, 'val'] (by label):", val_loc)      # Outputs 30 (from index row named '0')
# print("iloc[0, 0]   (by position):", val_iloc)   # Outputs 10 (from position 0 / first row)

# 2.10 — ​groupby​ (Split-Apply-Combine)

# import pandas as pd

# df = pd.DataFrame({
#     "category": ["A", "B", "A", "B"],
#     "sales": [100, 200, 300, 400]
# })

# res = df.groupby("category")["sales"].agg(["sum", "mean"])
# print(res)

# 2.12 — ​Agg​ Backend (Matplotlib)

# import matplotlib
# matplotlib.use("Agg")
# import matplotlib.pyplot as plt

# fig, ax = plt.subplots()
# ax.plot([1, 2], [3, 4])
# fig.savefig("test_output.png")

# print("Saved figure headlessly to test_output.png")

import pandas as pd
import numpy as np

df = pd.DataFrame({
        "vendor":    ["Acme", "Beta", "Acme", "Gamma", "Beta", "Acme", "Delta"],
        "amount":    [51000, 9000, 12000, 78000, 45000, 63000, 150000],
        "status":    ["OPEN", "PAID", "OPEN", "OVERDUE", "PAID", "OPEN", "OVERDUE"],
        "days_late": [12, 0, 3, 45, 0, 7, np.nan],
    })


def demo_pandas_inspection(df: pd.DataFrame) -> None:
    print("  df.head(3)\n", df.head(3).to_string(index=False), sep="")
    print("\n  df.describe() [numeric only]")
    print(df.describe().to_string())
    print("\n  df.isna().sum()   <- drives every 2.2 decision")
    print(df.isna().sum().to_string())
    print(f"\n  dtypes: {dict(df.dtypes.astype(str))}")

demo_pandas_inspection(df)
