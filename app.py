import streamlit as st

st.set_page_config(page_title="HE Cost Estimator", layout="wide")

st.title("🔥 Heat Exchanger Cost Estimator (PRO)")

# ========================
# INPUT SECTION
# ========================
st.header("Input Parameters")

col1, col2 = st.columns(2)

with col1:
    he_type = st.selectbox("HE Type", ["Fixed", "U-Tube", "Floating"])
    tube_qty = st.number_input("Tube Quantity", value=1000)
    tube_length = st.number_input("Tube Length (m)", value=6.0)

with col2:
    shell_dia = st.number_input("Shell Diameter (mm)", value=900)
    tube_od = st.selectbox("Tube OD", ["1/2\"", "3/4\"", "1\""])

# ========================
# SCOPE
# ========================
st.header("Scope Selection")

cleaning = st.checkbox("Cleaning")
retubing = st.checkbox("Retubing")
plugging = st.checkbox("Plugging")
hydrotest = st.checkbox("Hydrotest")
bundle_pull = st.checkbox("Bundle Pull")

# ========================
# PRICE TABLE
# ========================
price = {
    "Cleaning": {"mat": 2, "lab": 3},
    "Retubing": {"mat": 12, "lab": 8},
    "Plugging": {"mat": 1, "lab": 2},
    "Hydrotest": {"mat": 200, "lab": 300},
    "Bundle Pull": {"mat": 300, "lab": 500},
}

# ========================
# FACTORS
# ========================
type_factor = {
    "Fixed": 1.0,
    "U-Tube": 1.15,
    "Floating": 1.25
}[he_type]

if tube_qty < 500:
    tube_factor = 1.0
elif tube_qty <= 1000:
    tube_factor = 0.95
else:
    tube_factor = 0.9

# ========================
# CALCULATION
# ========================
material = 0
labor = 0

# Cleaning logic (ลดราคา ถ้ามี Retubing)
if cleaning:
    rate = 0.3 if retubing else 1.0
    material += tube_qty * price["Cleaning"]["mat"] * rate
    labor += tube_qty * price["Cleaning"]["lab"] * rate

if retubing:
    material += tube_qty * price["Retubing"]["mat"]
    labor += tube_qty * price["Retubing"]["lab"]

if plugging:
    material += tube_qty * price["Plugging"]["mat"]
    labor += tube_qty * price["Plugging"]["lab"]

if hydrotest:
    material += price["Hydrotest"]["mat"]
    labor += price["Hydrotest"]["lab"]

if bundle_pull:
    material += price["Bundle Pull"]["mat"]
    labor += price["Bundle Pull"]["lab"]

# Apply factors
total = (material + labor) * type_factor * tube_factor

# Minimum charge
total = max(total, 300)

# ========================
# OUTPUT
# ========================
st.header("💰 Cost Summary")

col1, col2, col3 = st.columns(3)

col1.metric("Material Cost", f"${material:,.2f}")
col2.metric("Labor Cost", f"${labor:,.2f}")
col3.metric("Total Cost (USD)", f"${total:,.2f}")

# Breakdown
st.subheader("Cost Breakdown")

data = {
    "Material": material,
    "Labor": labor
}

st.bar_chart(data)

# ========================
# DEBUG INFO
# ========================
with st.expander("Show Factors"):
    st.write("Type Factor:", type_factor)
    st.write("Tube Factor:", tube_factor)