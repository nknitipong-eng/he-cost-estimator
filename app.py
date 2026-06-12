import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Heat Exchanger Cost Estimator", layout="wide")

st.title("🔥 Heat Exchanger Cost Estimator")

# =========================
# LOAD DATA
# =========================
file = "HE_Database_PRO_FINAL.xlsx"

spec_df = pd.read_excel(file, sheet_name="SPEC")
time_df = pd.read_excel(file, sheet_name="TIME")
price_df = pd.read_excel(file, sheet_name="PRICE_MASTER")

# ✅ FIX 1: clean column names (กัน KeyError)
for df_temp in [spec_df, time_df, price_df]:
    df_temp.columns = df_temp.columns.str.strip()

# ✅ FIX 2: normalize Equipment No
spec_df["Equipment No"] = spec_df["Equipment No"].astype(str).str.upper()
spec_df = spec_df.sort_values(by="Equipment No")

# =========================
# SESSION
# =========================
if "records" not in st.session_state:
    st.session_state.records = []

if "cost_table" not in st.session_state:
    st.session_state.cost_table = pd.DataFrame()

# =========================
# INPUT
# =========================
mode = st.radio("Mode", ["Select Equipment", "Manual"])

if mode == "Select Equipment":
    eq = st.selectbox("Equipment No", spec_df["Equipment No"].unique())

    row = spec_df[spec_df["Equipment No"] == eq].iloc[0]

    # ✅ FIX 3: column name ถูกต้อง
    he_type = row.get("Type", "Unknown")
    tube_qty = int(row.get("Tube_Qty", 0))
    tube_OD = row.get("Tube_OD", 0)
    tube_length = row.get("Tube_Length_mm", 0)

else:
    eq = "Manual"
    he_type = st.selectbox("HE Type", ["Floating", "Fixed", "U-Tube"])
    tube_OD = st.selectbox("Tube OD", [19.05, 25.4])
    tube_qty = st.number_input("Tube Qty", value=1000)
    tube_length = 6000

# =========================
# SCOPE
# =========================
scope = st.selectbox("Scope", ["Pull & Clean", "Clean at site"])
mode_time = st.selectbox("Working Mode", ["24 hr", "08:00-23:00"])

# =========================
# TIME CALC
# =========================
def calc_days(tube, scope, mode):
    row = time_df[
        (time_df["Mode"] == mode) &
        (time_df["Scope"] == scope)
    ].iloc[0]

    if tube < 1000:
        return row["<1000"]
    elif tube <= 2000:
        return row["1000-2000"]
    else:
        return row[">2000"]

days = calc_days(tube_qty, scope, mode_time)

# =========================
# COST CALC
# =========================

# ✅ FIX 4: column name ให้ตรง excel (Scope ตัวเดียว)
lump = price_df[
    (price_df["EQ"] == eq) &
    (price_df["Scope"] == scope) &
    (price_df["Lump_sum"] == 1)
]

cost_breakdown = []

if not lump.empty:
    for _, r in lump.iterrows():
        cost_breakdown.append({
            "Item": r["Scope"],
            "Type": r["Type"],
            "Unit Cost": r["Price"],
            "Qty": 1,
            "Total": r["Price"]
        })
else:
    unit = price_df[
        (price_df["Scope"] == scope) &
        (price_df["Lump_sum"] == 0)
    ].iloc[0]

    cost_breakdown.append({
        "Item": scope,
        "Type": "UNIT",
        "Unit Cost": unit["Price"],
        "Qty": tube_qty,
        "Total": tube_qty * unit["Price"]
    })

cost_df = pd.DataFrame(cost_breakdown)

# =========================
# ✅ EDITABLE COST TABLE
# =========================
st.subheader("💰 Cost Breakdown")

if len(st.session_state.cost_table) == 0:
    st.session_state.cost_table = cost_df.copy()

edited = st.data_editor(
    st.session_state.cost_table,
    num_rows="dynamic",
    use_container_width=True
)

edited["Total"] = edited["Unit Cost"] * edited["Qty"]

st.session_state.cost_table = edited
total_cost = edited["Total"].sum()

# =========================
# OUTPUT
# =========================
st.header("Result")
st.metric("Duration (Days)", days)
st.metric("Total Cost (THB)", f"{total_cost:,.0f}")

# =========================
# SAVE
# =========================
if st.button("Add Record"):
    st.session_state.records.append({
        "Equipment": eq,
        "Type": he_type,
        "Tube Qty": tube_qty,
        "Scope": scope,
        "Work Mode": mode_time,
        "Days": days,
        "Cost (THB)": total_cost
    })

# =========================
# DISPLAY + DELETE
# =========================
df = pd.DataFrame(st.session_state.records)

st.subheader("Saved Records")

if not df.empty:
    for i, r in df.iterrows():
        cols = st.columns([6,1])
        cols[0].write(r.to_dict())

