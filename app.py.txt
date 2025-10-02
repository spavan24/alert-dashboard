import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Alert Dashboard", layout="wide")

# Auto refresh every 12 hours (12*60*60*1000 ms)
st_autorefresh(interval=43200000, key="refresh")

st.title("🚨 Alert Dashboard")

# Sidebar Menu
menu = st.sidebar.radio("📌 Menu", ["Analysis", "Specific Search"])

file = st.file_uploader("Upload Excel or CSV", type=["csv", "xlsx"])

if file:
    # Load file
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # Normalize column names
    df.columns = [c.strip().lower() for c in df.columns]
    colnames = df.columns.tolist()

    # Detect relevant columns
    owner_col = next((c for c in colnames if "owner" in c), None)
    alert_col = next((c for c in colnames if "alert" in c or "name" in c), None)
    priority_col = next((c for c in colnames if "priority" in c), None)
    change_col = next((c for c in colnames if "change" in c), None)
    date_col = next((c for c in colnames if "date" in c or "time" in c), None)

    # Ensure date column is datetime
    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # =======================
    # TAB 1: ANALYSIS
    # =======================
    if menu == "Analysis":
        st.header("📊 Analysis Overview")

        # --- Filters ---
        st.subheader("🔎 Filters")
        f_owner = st.multiselect("Select Owner", sorted(df[owner_col].dropna().unique().tolist())) if owner_col else []
        f_alert = st.multiselect("Select Alert Name", sorted(df[alert_col].dropna().unique().tolist())) if alert_col else []
        f_priority = st.multiselect("Select Priority", sorted(df[priority_col].dropna().unique().tolist())) if priority_col else []
        f_change = st.multiselect("Select Change Number", sorted(df[change_col].dropna().unique().tolist())) if change_col else []
        
        # Date filters
        if date_col:
            f_month = st.multiselect("Select Month", sorted(df[date_col].dropna().dt.month_name().unique().tolist()))
            f_quarter = st.multiselect("Select Quarter", sorted(df[date_col].dropna().dt.quarter.unique().tolist()))
            start_date = st.date_input("Start Date", value=df[date_col].min().date())
            end_date = st.date_input("End Date", value=df[date_col].max().date())
        else:
            f_month, f_quarter, start_date, end_date = [], [], None, None

        # Apply filters
        filtered = df.copy()
        if f_owner and owner_col:
            filtered = filtered[filtered[owner_col].isin(f_owner)]
        if f_alert and alert_col:
            filtered = filtered[filtered[alert_col].isin(f_alert)]
        if f_priority and priority_col:
            filtered = filtered[filtered[priority_col].isin(f_priority)]
        if f_change and change_col:
            filtered = filtered[filtered[change_col].isin(f_change)]
        if date_col:
            if f_month:
                filtered = filtered[filtered[date_col].dt.month_name().isin(f_month)]
            if f_quarter:
                filtered = filtered[filtered[date_col].dt.quarter.isin(f_quarter)]
            if start_date and end_date:
                filtered = filtered[(filtered[date_col] >= pd.to_datetime(start_date)) & (filtered[date_col] <= pd.to_datetime(end_date))]

        st.write(f"📌 Showing {len(filtered)} records after filters.")

        # --- Visualization Type ---
        chart_type = st.radio("Select Chart Type", ["Bar Chart", "Pie Chart"], horizontal=True)

        # Owner-based chart
        if owner_col:
            summary = filtered.groupby(owner_col).size().reset_index(name="Count")

            if chart_type == "Bar Chart":
                fig = px.bar(summary, x=owner_col, y="Count", title="Alerts by Owner", text="Count")
            else:
                fig = px.pie(summary, names=owner_col, values="Count", title="Alerts by Owner")

            st.plotly_chart(fig, use_container_width=True)

        # Priority-based chart
        if priority_col:
            summary = filtered.groupby(priority_col).size().reset_index(name="Count")

            if chart_type == "Bar Chart":
                fig = px.bar(summary, x=priority_col, y="Count", title="Alerts by Priority", text="Count")
            else:
                fig = px.pie(summary, names=priority_col, values="Count", title="Alerts by Priority")

            st.plotly_chart(fig, use_container_width=True)

        # --- Data Table + Download ---
        st.subheader("📄 Filtered Data")
        st.dataframe(filtered, use_container_width=True)

        # Download buttons
        csv = filtered.to_csv(index=False).encode("utf-8")
        excel_file = filtered.to_excel("filtered.xlsx", index=False)

        st.download_button("⬇️ Download CSV", csv, "filtered_data.csv", "text/csv")
        st.download_button("⬇️ Download Excel", open("filtered.xlsx", "rb"), "filtered_data.xlsx", "application/vnd.ms-excel")

    # =======================
    # TAB 2: SPECIFIC SEARCH
    # =======================
    elif menu == "Specific Search":
        st.header("🔍 Specific Search")

        # Filters
        if owner_col:
            owners = df[owner_col].dropna().unique().tolist()
            selected_owner = st.selectbox("Select Owner", ["All"] + sorted(map(str, owners)))
        else:
            selected_owner = "All"

        if priority_col:
            priorities = df[priority_col].dropna().unique().tolist()
            selected_priority = st.selectbox("Select Priority", ["All"] + sorted(map(str, priorities)))
        else:
            selected_priority = "All"

        keyword = st.text_input("Search by keyword (any column)")

        # Apply filters
        filtered = df.copy()
        if selected_owner != "All" and owner_col:
            filtered = filtered[filtered[owner_col] == selected_owner]
        if selected_priority != "All" and priority_col:
            filtered = filtered[filtered[priority_col] == selected_priority]
        if keyword:
            filtered = filtered[filtered.apply(lambda row: row.astype(str).str.contains(keyword, case=False).any(), axis=1)]

        st.write(f"🔎 {len(filtered)} results found")
        st.dataframe(filtered, use_container_width=True)

else:
    st.info("📂 Upload a file to see dashboard.")
