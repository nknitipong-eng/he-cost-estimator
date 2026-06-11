import streamlit as st
import pandas as pd

st.set_page_config(page_title="Heat Exchanger Cost Estimator (PRO)", layout="wide")

st.title("🔥 Heat Exchanger Cost Estimator (PRO)")

# =========================
# SESSION STORAGE
# =========================
if "records" not in st.session_state:
    st.session_state.records = []

# =========================
# INPUT MODE
# =========================
mode = st.radio("Select Mode", ["Manual Input", "Select from Equipment No."])

# (mock data – ถ้าคุณ upload Excel จริง เดี๋ยวผม map ให้เพิ่ม)
equipment_data = pd.DataFrame({
    "Equipment No": ["E-101", "E-102"],
    "Type": ["Floating", "U-Tube"],
    "Tube Qty": [1200, 800]
})

if mode == "Select from Equipment No.":
    eq = st.selectbox("Equipment No", equipment_data["Equipment No"])
    selected = equipment_data[equipment_data["Equipment No"] == eq].iloc[0]

    he_type = selected["Type"]
    tube_qty = int(selected["Tube Qty"])

    st.write("Type:", he_type)
    st.write("Tube Qty:", tube_qty)

else:
    he_type = st.selectbox("HE Type", ["Fixed", "U-Tube", "Floating"])
    tube_qty = st.number_input("Tube Quantity", value=1000)

# =========================
# SCOPE
# =========================
st.header("Scope")

scope = st.selectbox("Cleaning Type", ["Clean at site", "Pull & Clean"])
work_mode = st.selectbox("Working Mode", ["24 hr", "08:00–23:00"])

# =========================
# TIME CALCULATION
# =========================
def calc_days(tube, scope, mode):

    if tube < 1000:
        idx = 0
    elif tube <= 2000:
        idx = 1
    else:
        idx = 2

    if mode == "08:00–23:00":
        table = {
            "Pull & Clean": [6, 7, 8],
            "Clean at site": [5, 6, 7]
        }
    else:
        table = {
            "Pull & Clean": [5, 6, 7],
            "Clean at site": [4, 5, 6]
        }

    return table[scope][idx]

days = calc_days(tube_qty, scope, work_mode)

# =========================
# COST (THB)
# =========================
price = {
    "Clean at site": 150,   # THB per tube
    "Pull & Clean": 250
}

base_cost = tube_qty * price[scope]

# Factor
factor = {
    "Fixed": 1.0,
    "U-Tube": 1.15,
    "Floating": 1.25
}[he_type]

total_cost = base_cost * factor

# minimum
total_cost = max(total_cost, 10000)

# =========================
# OUTPUT
# =========================
st.header("Result")

st.metric("Duration (Days)", days)
st.metric("Total Cost (THB)", f"{total_cost:,.0f}")

# =========================
# SAVE RECORD
# =========================
if st.button("✅ Add to Record"):
    st.session_state.records.append({
        "Equipment": eq if mode != "Manual Input" else "Manual",
        "Type": he_type,
        "Tube Qty": tube_qty,
        "Scope": scope,
        "Work Mode": work_mode,
        "Days": days,
        "Cost (THB)": total_cost
    })

# =========================
# SHOW TABLE
# =========================
st.header("Saved Records")

df = pd.DataFrame(st.session_state.records)
st.dataframe(df)

# =========================
# EXPORT EXCEL
# =========================
def convert_df(df):
    return df.to_excel(index=False, engine="openpyxl")

if not df.empty:
    file_name = "HE_estimation.xlsx"
    buffer = pd.ExcelWriter(file_name, engine="openpyxl")
    df.to_excel(buffer, index=False)
    buffer.close()

    with open(file_name, "rb") as f:
        st.download_button(
            "📥 Download Excel",
            f,
            file_name=file_name
        )
``
