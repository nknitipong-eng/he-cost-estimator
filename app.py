import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Heat Exchanger Cost Estimator", layout="wide")

st.title("🔥 Heat Exchanger Cost Estimator by NTK")

# =========================
# LOAD DATA
# =========================
file = "HE_Database_PRO_FINAL.xlsx"

spec_df = pd.read_excel(file, sheet_name="SPEC")
time_df = pd.read_excel(file, sheet_name="TIME")
price_df = pd.read_excel(file, sheet_name="PRICE_MASTER")

# =========================
# SESSION
# =========================
if "records" not in st.session_state:
    st.session_state.records = []

# =========================
# INPUT
# =========================
mode = st.radio("Mode", ["Select Equipment", "Manual"])

if mode == "Select Equipment":
    eq = st.selectbox("Equipment No", spec_df["Equipment No"])
    row = spec_df[spec_df["Equipment No"] == eq].iloc[0]

    he_type = row["Type"]
    tube_qty = int(row["Tube_Qty"])

    st.write("Type:", he_type)
    st.write("Tube Qty:", tube_qty)

else:
    eq = "Manual"
    he_type = st.selectbox("HE Type", ["Fixed", "U-Tube", "Floating"])
    tube_qty = st.number_input("Tube Qty", value=1000)

# =========================
# SCOPE
# =========================
scope = st.selectbox("Scope", ["Clean at site", "Pull & Clean"])
mode_time = st.selectbox("Working Mode", ["24-hr", "08:00-23:00"])

# =========================
# TIME CALC
# =========================
def calc_days(tube, scope, mode):
    row = time_df[(time_df["Mode"] == mode) & (time_df["Scope"] == scope)].iloc[0]

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

# 1. check lump sum
lump = price_df[
    (price_df["EQ"] == eq) &
    (price_df["Time"] == mode_time) &
    (price_df["SCOPE"] == scope) &
    (price_df["Lump_sum"] == 1)
]

if not lump.empty:
    total_cost = lump["Price"].sum()

else:
    unit = price_df[
        (price_df["Scope"] == scope) &
        (price_df["Lump_sum"] == 0)
    ].iloc[0]

    total_cost = 1 * unit["Price"]

# minimum
total_cost = max(total_cost, 9999)

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
# DISPLAY
# =========================
df = pd.DataFrame(st.session_state.records)
st.subheader("Saved Records")
st.dataframe(df)

# =========================
# EXPORT EXCEL
# =========================
if not df.empty:
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)

    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name="HE_estimation.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
