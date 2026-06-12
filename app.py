import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Heat Exchanger Cost Estimator", layout="centered")

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
# =========================

lump = price_df[
    (price_df["EQ"] == eq) &
    (price_df["Scope"] == scope) &
    ((price_df["Time"] == mode_time) | (price_df["Time"] == "All")) &
    (price_df["Lump_sum"] == 1)
]

# =========================
# COST FILTER (ตาม Scope)
# =========================


cost_filter = price_df[price_df["EQ"] == eq]

# filter scope
if scope == "Pull & Clean":
    cost_filter = cost_filter[
        cost_filter["Scope"] != "Clean at site"
    ]
else:
    cost_filter = cost_filter[
        cost_filter["Scope"] != "Pull & Clean"
    ]

# filter time
if mode_time == "08:00-23:00":
    cost_filter = cost_filter[
        cost_filter["Time"] != "24-hr"
    ]
else:
    cost_filter = cost_filter[
        cost_filter["Time"] != "08:00-23:00"
    ]


# 2. Non lump sum
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
# COST TABLE (TABLE เดียว)
# =========================


if "cost_table" not in st.session_state:
    st.session_state.cost_table = None


st.subheader("💰 Cost Breakdown")

# ✅ เตรียม DataFrame
####cost_df = cost_filter.copy()
if st.session_state.cost_table is None:
    cost_df = cost_filter.copy()

    cost_df = cost_df.rename(columns={"Price": "Unit Rate"})

    if "Qty" not in cost_df.columns:
        cost_df["Qty"] = 1

    cost_df["Unit Rate"] = cost_df["Unit Rate"].astype(float)
    cost_df["Qty"] = cost_df["Qty"].astype(int)

    st.session_state.cost_table = cost_df
else:
    cost_df = st.session_state.cost_table

# map column
cost_df = cost_df.rename(columns={
    "Price": "Unit Rate"
})

# ✅ ensure column
if "Qty" not in cost_df.columns:
    cost_df["Qty"] = 1

cost_df["Unit Rate"] = cost_df["Unit Rate"].astype(float)
cost_df["Qty"] = cost_df.get("Qty", 1).astype(int)

# คำนวณ
cost_df["Total Cost"] = cost_df["Unit Rate"] * cost_df["Qty"]

# =========================
# ✅ EDITABLE TABLE (ตัวเดียวพอ)
# =========================

all_cols = cost_df.columns.tolist()

hidden_cols = ["#", "#PO", "Lump_sum", "Clean_Type", "OD", "Tube", "Length", "Description","Note","He_type"]

# ✅ ตัด column ที่ต้องการซ่อนออก
default_cols = [c for c in all_cols if c not in hidden_cols]


# ✅ PRE-CALC
# =========================
cost_df["Total Cost"] = cost_df.apply(
    lambda r: r["Unit Rate"] if r["UoM"] == "LUMP"
    else r["Unit Rate"] * r["Qty"],
    axis=1
)

edited_df = st.data_editor(
    st.session_state.cost_table,
    key="cost_editor",   # ✅ IMPORTANT
    column_order=default_cols,
    use_container_width=True,
    num_rows="dynamic",
    disabled=False, 
    
    column_config={
        "EQ": st.column_config.TextColumn(disabled=True),
        "Scope": st.column_config.TextColumn(disabled=True),
        "He_type": st.column_config.TextColumn(disabled=True),
        "Time": st.column_config.TextColumn(disabled=True),

        "UoM": st.column_config.TextColumn(disabled=True),
        "Note": st.column_config.TextColumn(disabled=True),

        "Unit Rate": st.column_config.NumberColumn(
            format="%,d",
            disabled=True
        ),

        "Qty": st.column_config.NumberColumn(
            format="%,d",
            min_value=1,
            step=1
        ),

        "Total Cost": st.column_config.NumberColumn(
            format="%,d",
            disabled=True
        ),
    }
)

# ✅ RECALC หลัง edit
# =========================
edited_df["Total Cost"] = edited_df.apply(
    lambda r: r["Unit Rate"] if r["UoM"] == "LUMP"
    else r["Unit Rate"] * r["Qty"],
    axis=1
)

# =========================
# ✅ TOTAL
# =========================
total_cost = edited_df["Total Cost"].sum()

st.metric("Total Cost (THB)", f"{int(total_cost):,}")



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
