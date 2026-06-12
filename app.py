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
spec_df["Equipment No"] = spec_df["Equipment No"].astype(str).str.upper()
spec_df = spec_df.sort_values(by="Equipment No")


time_df = pd.read_excel(file, sheet_name="TIME")
price_df = pd.read_excel(file, sheet_name="PRICE_MASTER")
Tube_OD_df = pd.read_excel(file, sheet_name="SPEC")
Tube_Length_mm_df = pd.read_excel(file, sheet_name="SPEC")
Tube_Qty_df = pd.read_excel(file, sheet_name="SPEC")


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

    He_type = row["He_type"]
    tube_qty = int(row["Tube_Qty"])
    Tube_OD = int(row["Tube_OD"])
    Tube_Length_mm = int(row["Tube_Length_mm"])

    st.write("Type:", He_type)
    st.write("Tube Qty:", tube_qty)

    st.write("Tube OD:", Tube_OD)

else:
    eq = "Manual"
    He_type = st.selectbox("HE Type", ["Floating","Fixed", "U-Tube"])
    tube_OD = st.selectbox("Tube OD", [19.05, 25.4])
    tube_qty = st.number_input("Tube Qty", value=1000)
    
    if    He_type == "U-tube":
        tube_Length_mm = st.selectbox("Tube Lenth (mm)", ["100-200U", "201-400U", "401-600U", "601-800U", "801-1000U"])
    else:
        tube_Length_mm = st.selectbox("Tube Lenth (m)", ["0-4.88 m", "4.88 m - 7.32 m"])
        
    
# =========================
# SCOPE
# =========================
scope = st.selectbox("Scope", ["Pull & Clean" , "Clean at site"])
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
    (price_df["Scope"] == scope) &
    (price_df["Lump_sum"] == 1)
]

if not lump.empty:
    total_cost = lump["Price"].sum()

else:
    unit = price_df[

        (price_df["He_type"] == He_type) &
        (price_df["Tube_OD"] == Tube_OD) &
        (price_df["Tube_Length_mm"] == Tube_Length_mm) &
        (price_df["Tube_Qty"] == Tube_Qty) &
        (price_df["Scope"] == scope) &
        (price_df["Lump_sum"] == 0)
    ].iloc[0]




    
    total_cost = unit["Price"].sum()
    total_cost = unit["Price"] + 150000

# minimum
total_cost = max(total_cost, 9999)


# =========================
# COST BREAKDOWN TABLE
# =========================

cost_breakdown = []

# LUMP CASE
if not lump.empty:
    for _, r in lump.iterrows():
        cost_breakdown.append({
            "Item": r["Scope"],
            "Type": r["He_type"],
            "Unit Cost": r["Price"],
            "Qty": 1,
            "Total": r["Price"]
        })

# UNIT CASE
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

st.subheader("💰 Cost Breakdown")
st.dataframe(cost_df)


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
        "Type": He_type,
        "Tube Qty": tube_qty,
        "Scope": scope,
        "Work Mode": mode_time,
        "Days": days,
        "Cost (THB)": total_cost
    })

# =========================
# DISPLAY + DELETE
# =========================

df = pd.DataFrame(st.session_state.records)   # ✅ FIX 1

st.subheader("Saved Records")

if not df.empty:
    for i, r in enumerate(st.session_state.records):   # ✅ FIX 2
        cols = st.columns([6,1])

        cols[0].write(r)

        if cols[1].button("❌", key=f"del_{i}"):
            st.session_state.records.pop(i)
            st.rerun()

    st.dataframe(pd.DataFrame(st.session_state.records))

else:
    st.info("No records yet")   # ✅ FIX 3


# =========================
# CLEAR ALL
# =========================
if st.button("🗑 Clear All Records"):
    st.session_state.records = []
    st.rerun()

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
