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
    (price_df["Time"] == mode_time) | (price_df["Time"] == "All")&
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
# COST FILTER (ตาม Scope)
# =========================

# ✅ FIX 1: filter scope ตามที่ต้องการ
if scope == "Pull & Clean":
    cost_filter = price_df[
        (price_df["EQ"] == eq) &
        (price_df["Scope"] != "Clean at site")
    ]
else:
    cost_filter = price_df[
        (price_df["EQ"] == eq) &
        (price_df["Scope"] != "Pull & Clean")
    ]

# =========================
# COST TABLE
# =========================
cost_df = cost_filter[["EQ", "Scope", "He_type", "Time", "Price"]].copy()

cost_df.rename(columns={
    "Price": "Unit Cost"
}, inplace=True)

# ✅ FIX 2: ให้ Qty แก้ได้
if "Qty" not in cost_df.columns:
    cost_df["Qty"] = 1

# คำนวณ Total
cost_df["Total"] = cost_df["Unit Cost"] * cost_df["Qty"]

# =========================
# EDITABLE TABLE
# =========================
st.subheader("💰 Cost Breakdown")

edited_df = st.data_editor(
    cost_df,
    num_rows="dynamic",   # ✅ FIX 3: เพิ่ม/ลบ row ได้
    use_container_width=True
)

# ✅ FIX 4: คำนวณใหม่หลังแก้ Qty
edited_df["Total"] = edited_df["Unit Cost"] * edited_df["Qty"]

# =========================
# FINAL COST
# =========================
total_cost = edited_df["Total"].sum()

st.metric("Total Cost (THB)", f"{total_cost:,.0f}")


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
# DISPLAY
# =========================
df = pd.DataFrame(st.session_state.records)
st.subheader("Saved Records")
st.dataframe(df)

# =========================
# CLEAR ALL
# =========================
if st.button("🗑 Clear All Records"):
    st.session_state.records = []
    st.rerun()

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
