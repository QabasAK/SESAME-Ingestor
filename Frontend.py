import streamlit as st

from email_validator import validate_email, EmailNotValidError
from datetime import datetime
import ipaddress 
import json
import os 

import getpass
import pandas as pd

from Backend import LogIngestor

st.set_page_config(page_title="Logs Ingestion", layout="wide")

LABEL_DB = "labels.json"

if os.path.exists(LABEL_DB):
    with open(LABEL_DB, "r") as f:
        try:
            database = json.load(f) 
        except json.JSONDecodeError:
            database = []
else:
    database = []

saved_labels = {entry["label"] for entry in database}

col1, col2 = st.columns(2)
with col1:
    st.title("Previous Log Entries")
    if database:
        df = pd.DataFrame(database)
        display_columns = ["station", "label", "user", "ip_address", "log_size_mb", "timestamp"]
        df = df.sort_values(by="timestamp", ascending=False)

        m1, m2, m3 = st.columns(3)
        m1.metric("Total Logs", len(df))
        m2.metric("Stations", df["station"].nunique())
        m3.metric("Total Size (MB)", df["log_size_mb"].sum())

        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            station_filter = st.selectbox("Filter by station", ["All"] + df["station"].unique().tolist())
        with colf2:
            user_filter = st.selectbox("Filter by user", ["All"] + df["user"].unique().tolist())
        with colf3:
            label_filter = st.selectbox("Filter by label", ["All"] + df["label"].unique().tolist())

        if station_filter != "All":
            df = df[df["station"] == station_filter]
        if user_filter != "All":
            df = df[df["user"] == user_filter]
        if label_filter != "All":
            df = df[df["label"] == label_filter]

        page_size = 10
        total_pages = (len(df) - 1) // page_size + 1 if len(df) else 1
        page = st.number_input("Page", 1, total_pages, 1)
        start, end = (page-1)*page_size, page*page_size
        page_df = df.iloc[start:end]

        grouped = page_df.groupby("station")
        for station, group in grouped:
            with st.expander(f"Station: {station} ({len(group)} logs)", expanded=False):
                st.dataframe(group[display_columns], use_container_width=True, hide_index=True)

                for _, row in group.iterrows():
                    if st.toggle(f"Show details for '{row['label']}'", key=row['label']):
                        st.json(row.to_dict())

    else:
        st.info("No log entries yet.")


with col2:
    st.title("Logs Ingestion")

    if 'show_form' not in st.session_state:
        st.session_state.show_form = False
    if 'category' not in st.session_state:
        st.session_state.category = None

    def toggle_form():
        st.session_state.show_form = not st.session_state.show_form

    def check_ip(ip_address):
        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    def check_email(email):
        try:
            email = email.strip() 
            validate_email(email, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False

    VALID_STATIONS = ["IR", "XAFS/XRF", "MS/XPD", "BEATS", "HESEB", "TXPES"]

    # main
    if st.button(r"\+", key="upload_log", help="Add new log entry"):
        toggle_form()


    if st.session_state.show_form:
        with st.form("log_form"):
            st.subheader("Add Log Entry")
            
            station_name = st.selectbox(
                "Select the station name:",
                options=VALID_STATIONS,
                index=None,
                placeholder="Choose a station..."
            )

            label = st.text_input("Enter a label for the log entry:", placeholder="e.g. IR_EXP_10_SCIENTIST")

            if label:
                if label in saved_labels:
                    st.info(f"Label '{label}' already exists. Update it?")

            login_id = st.text_input("Enter the remote login identifier:", placeholder="e.g. ubuntu@192.168.1.1")
            
            user, ip_address = None, None
            if "@" in login_id:
                user, ip_address = login_id.split("@", 1) 
            else:
                ip_address = login_id

            log_file_path = st.text_input("Enter the path to the log file:", placeholder="/path/to/logfile.log")

            email_to = st.text_input("Enter the email addresses to send logs:", placeholder="e.g. user1@example.com, user2@example.com, ...")
            if email_to:
                emails = [e.strip() for e in email_to.split(",") if e.strip()]

            log_file_size = st.number_input("Enter the size of the log file (in MB):", min_value=0) # is this for the cron job ??

            col1, col2 = st.columns([6, 1])
            with col1:
                if label and label in saved_labels:
                    submitted = st.form_submit_button("Update", type="primary")
                else:
                    submitted = st.form_submit_button("Submit", type="primary")

            with col2:
                cancelled = st.form_submit_button("Cancel")
                
            if submitted:

                if not station_name:
                    st.error("Please select a station name")
                elif not label:
                    st.error("Please enter a label")
                elif not login_id:
                    st.error("Please enter a valid login ID")
                elif not ip_address: 
                    st.error("Please enter a valid login ID")
                elif ip_address and not check_ip(ip_address):
                    st.error("Please enter a valid IP address")
                elif not log_file_path:
                    st.error("Please enter a log file path")
                elif email_to and not all(check_email(e) for e in emails):
                    st.error("Please enter valid email addresses")
                elif log_file_size <= 0:
                    st.error("Please enter a valid log file size")
                else:
                    user = user if "@" in login_id else getpass.getuser()
                    emails = [e.strip() for e in email_to.split(",") if e.strip()]
                    entry = {
                        "station": station_name,
                        "label": label,
                        "user": user,
                        "ip_address": ip_address,
                        "log_file_path": log_file_path,
                        "email_to": emails,
                        "log_size_mb": log_file_size,
                        "timestamp": datetime.now().isoformat()
                    }

                    if label in saved_labels:
                        database = [e if e["label"] != label else entry for e in database]
                    else:
                        database.append(entry)
                        saved_labels.add(label)

                    with open(LABEL_DB, "w") as f:
                        json.dump(database, f, indent=4)

                    # Trigger log ingestion
                    ingestor = LogIngestor(
                        ssh_user=user,
                        client_ip=ip_address,
                        base_dir="/home/qabas/logs", # those are on my (server) side
                        ssh_key_path="~/.ssh/id_rsa" # where public key is stored for authentication
                    )
                    ingestor.ingestLogs(label, station_name, log_file_path, emails)

                    st.success("Log entry submitted successfully!")
                    st.session_state.show_form = False
                    
            if cancelled:
                st.session_state.show_form = False
                st.rerun()
