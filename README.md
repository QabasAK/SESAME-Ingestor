## Log Ingestion System (SESAME Beamline Data Infrastructure)

A full-stack Python system developed to automate the ingestion of experimental log files from SESAME’s distributed beamline stations into the central server farm for archival, monitoring, and analysis.

 <p align="center">
   <img src="https://github.com/user-attachments/assets/41151a15-bbe1-45c0-82e4-5596cc3b8142" alt="Flowchart" width=70%>
 </p>

 It features:
 - **Full-stack architecture**: Streamlit frontend + Python backend.
 - **Secure file transfers**: Uses SSH + rsync to pull logs from remote beamline machines.
 - **Automated email notifications**: Built on ZMQ to alert users after successful ingestion.
 - **Dynamic file organization**: Timestamped and station-based directory structure for traceability.
 - **Frontend dashboard**:
   - Add, update, and visualize log entries (JSON-based database).
   - Filter by station, user, or label; view previous logs and metadata.
 - **Automation**:
   - Cron job automatically checks for new or updated logs and synchronizes them with the server farm.
   - EPICS integration for triggering ingestion via process variables (hardware-level control).
 - **Reliability**:
  File size verification, source cleanup, and JSON metadata synchronization ensure consistent data states.

![Python](https://img.shields.io/badge/python-3.10-blue)
![License](https://img.shields.io/badge/license-MIT-green)
