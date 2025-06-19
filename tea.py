import streamlit as st
import json
import os
import math
from datetime import datetime
import pandas as pd
from fpdf import FPDF

# ---- Authentication ----
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# Load users from Streamlit secrets
users = st.secrets["users"]

# Login form
if not st.session_state.logged_in:
    st.title("🔒 Login to 7 Star Tea")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username in users and users[username] == password:
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")
    
    st.stop()
# ---- Constants ----
DATA_FILE = "data.json"

# ---- Load or initialize data ----
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f:
        json.dump({"offices": [], "tea_entries": []}, f)

with open(DATA_FILE, 'r') as f:
    data = json.load(f)

offices = data["offices"]
tea_entries = data["tea_entries"]

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump({"offices": offices, "tea_entries": tea_entries}, f, indent=4)

# ---- Sidebar Navigation ----
menu = st.sidebar.radio("Menu", ["Dashboard", "Add Office", "Manage Offices", "Tea Entry", "Tea Report"])

# ---- Dashboard ----
if menu == "Dashboard":
    st.title("📊 Dashboard")

    total_offices = len(offices)
    total_tea = sum(entry.get("TeaCount", 0) for entry in tea_entries)
    total_coffee = sum(entry.get("CoffeeCount", 0) for entry in tea_entries)
    total_revenue = sum(entry["TotalAmount"] for entry in tea_entries)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Offices", total_offices)
    col2.metric("Total Tea", total_tea)
    col3.metric("Total Coffee", total_coffee)
    col4.metric("Total Revenue (Rs.)", f"{total_revenue:.2f}")

    df = pd.DataFrame(tea_entries)
    if not df.empty:
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.to_period("M").astype(str)

        st.subheader("Monthly Beverage Count")
        monthly_tea = df.groupby("Month")["TeaCount"].sum()
        monthly_coffee = df.groupby("Month")["CoffeeCount"].sum()
        st.line_chart(pd.DataFrame({"Tea": monthly_tea, "Coffee": monthly_coffee}))

        st.subheader("Beverage Count by Office")
        office_tea = df.groupby("OfficeName")["TeaCount"].sum()
        office_coffee = df.groupby("OfficeName")["CoffeeCount"].sum()
        st.bar_chart(pd.DataFrame({"Tea": office_tea, "Coffee": office_coffee}))

# ---- Add Office ----
elif menu == "Add Office":
    st.title("🏢 Add New Office")
    name = st.text_input("Office Name")
    contact = st.text_input("Mobile Number")
    address = st.text_area("Address")

    if st.button("Add Office"):
        if name and contact:
            offices.append({"Name": name, "Mobile": contact, "Address": address})
            save_data()
            st.success("Office added successfully!")
        else:
            st.error("Please enter name and mobile.")

# ---- Manage Offices ----
elif menu == "Manage Offices":
    st.title("📋 Manage Offices")
    df = pd.DataFrame(offices)
    if df.empty:
        st.warning("No office data found.")
    else:
        st.dataframe(df)
        selected_name = st.selectbox("Select Office to Delete", [o["Name"] for o in offices])
        if st.button("Delete Office"):
            offices[:] = [o for o in offices if o["Name"] != selected_name]
            save_data()
            st.success(f"Deleted office: {selected_name}")

# ---- Tea Entry ----
elif menu == "Tea Entry":
    st.title("🍵 New Tea/Coffee Entry")
    office_names = [o["Name"] for o in offices]
    selected_office = st.selectbox("Select Office", office_names)
    tea_count = st.number_input("Tea Count", min_value=0, step=1)
    coffee_count = st.number_input("Coffee Count", min_value=0, step=1)
    tea_price = st.number_input("Tea Price", min_value=0.0, step=1.0)
    coffee_price = st.number_input("Coffee Price", min_value=0.0, step=1.0)
    date = st.date_input("Date", datetime.now())

    if st.button("Save Entry"):
        total = (tea_count * tea_price) + (coffee_count * coffee_price)
        tea_entries.append({
            "OfficeName": selected_office,
            "TeaCount": tea_count,
            "CoffeeCount": coffee_count,
            "TeaPrice": tea_price,
            "CoffeePrice": coffee_price,
            "TotalAmount": total,
            "Date": str(date)
        })
        save_data()
        st.success("Entry saved successfully!")

# ---- Tea Report ----
elif menu == "Tea Report":
    st.title("📄 Tea Report")
    df = pd.DataFrame(tea_entries)
    if df.empty:
        st.warning("No tea entry data found.")
    else:
        df["Date"] = pd.to_datetime(df["Date"])
        df.fillna(0, inplace=True)

        office_filter = st.selectbox("Select Office", ["All"] + [o["Name"] for o in offices])
        from_date = st.date_input("From Date", df["Date"].min().date())
        to_date = st.date_input("To Date", df["Date"].max().date())

        filtered_df = df[(df["Date"] >= pd.to_datetime(from_date)) & (df["Date"] <= pd.to_datetime(to_date))]
        if office_filter != "All":
            filtered_df = filtered_df[filtered_df["OfficeName"] == office_filter]

        st.dataframe(filtered_df)
        grand_total = filtered_df["TotalAmount"].sum()
        st.markdown(f"### Grand Total: Rs.{grand_total:.2f}")

        if st.button("Download Invoice PDF"):
            pdf = FPDF()
            pdf.add_page()

            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "7 Star Chai", ln=1, align="C")
            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 10, "2/635, Udhana Darwaja, Malezaiwhar Mohalla, Rustompura, Surat, Gujarat, 395002", ln=1, align="C")
            pdf.cell(0, 5, "Mobile: 9021579599", ln=1, align="C")
            pdf.ln(5)

            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 10, f"Invoice No.: 001", ln=1)
            pdf.cell(0, 10, f"Invoice Date: {datetime.now().strftime('%d/%m/%Y')}", ln=1)
            pdf.cell(0, 10, f"Due Date: {(datetime.now()).strftime('%d/%m/%Y')}", ln=1)

            office = next((o for o in offices if o["Name"] == office_filter), {})
            pdf.ln(5)
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, "BILL TO", ln=1)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 8, f"{office.get('Name', '')}", ln=1)
            pdf.cell(0, 8, f"Mobile: {office.get('Mobile', '')}", ln=1)

            pdf.ln(5)
            pdf.set_font("Arial", 'B', 11)
            pdf.cell(50, 8, "ITEMS", 1)
            pdf.cell(40, 8, "Date", 1)
            pdf.cell(30, 8, "QTY.", 1)
            pdf.cell(30, 8, "RATE", 1)
            pdf.cell(30, 8, "AMOUNT", 1)
            pdf.ln()

            pdf.set_font("Arial", '', 11)
            for _, row in filtered_df.iterrows():
                items = []
                if row.get("TeaCount", 0):
                    items.append(("7 STAR CHAI", row["TeaCount"]))
                if row.get("CoffeeCount", 0):
                    items.append(("7 STAR COFFEE", row["CoffeeCount"]))

                for item, qty in items:
                    qty_int = 0
                    if isinstance(qty, (int, float)) and not math.isnan(qty):
                        qty_int = int(qty)

                    price = 0
                    if item == "7 STAR CHAI":
                        price = row.get("TeaPrice", 0)
                    elif item == "7 STAR COFFEE":
                        price = row.get("CoffeePrice", 0)

                    pdf.cell(50, 8, item, 1)
                    pdf.cell(40, 8, row["Date"].strftime("%d/%m/%Y"), 1)
                    pdf.cell(30, 8, f"{qty_int} PC3", 1)
                    pdf.cell(30, 8, f"{price:.2f}", 1)
                    pdf.cell(30, 8, f"{price * qty_int:.2f}", 1)
                    pdf.ln()

            pdf.set_font("Arial", 'B', 11)
            pdf.cell(150, 8, "SUBTOTAL", 1)
            pdf.cell(30, 8, f"Rs.{grand_total:.2f}", 1)
            pdf.ln()
            pdf.cell(150, 8, "TOTAL AMOUNT", 1)
            pdf.cell(30, 8, f"Rs.{grand_total:.2f}", 1)
            pdf.ln()
            pdf.cell(150, 8, "Current Balance", 1)
            pdf.cell(30, 8, f"Rs.{grand_total:.2f}", 1)
            pdf.ln(10)

            pdf.set_font("Arial", 'B', 11)
            pdf.cell(0, 10, f"Total Amount (in words)", ln=1)
            pdf.set_font("Arial", '', 11)
            pdf.cell(0, 10, f"{grand_total:.2f} Rupees Only", ln=1)

            pdf.ln(15)
            pdf.cell(0, 10, "AUTHORISED SIGNATORY FOR", ln=1, align="R")
            pdf.cell(0, 5, "7 Star Chai", ln=1, align="R")

            pdf.output("Invoice.pdf")
            with open("Invoice.pdf", "rb") as f:
                st.download_button("Download Invoice", f, file_name="Invoice.pdf")

        # ---- Monthly Office-wise Summary ----
        st.subheader("📆 Monthly Report Summary")
        monthly_summary = filtered_df.copy()
        monthly_summary["Month"] = monthly_summary["Date"].dt.to_period("M").astype(str)

        monthly_grouped = monthly_summary.groupby(["Month", "OfficeName"]).agg({
            "TeaCount": "sum",
            "CoffeeCount": "sum",
            "TotalAmount": "sum"
        }).rese
