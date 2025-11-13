
# load JSON file as dict

# go over every entry in the JSON file

    # note the size 
    # connect to the remote client (user @ ip_address)

    # does the file path exist

        # Y: compare local file size to JSON file size

            # Y: is equal -> 

                # (1) save new file (async)  [append or overwrite?]
                # (2) update JSON file ( e.g. timestamp)
                # (3) send email notification (zmq) 

            # N: log size mismatch (dont update just yet) -> skip to next entry

        # N: log file not found (already ingested) -> skip to next entry

import os
import json

from datetime import datetime
from Backend import LogIngestor

class LogIngestionJob:
    def __init__(self, json_path, ssh_key_path, base_dir):
        self.json_path = json_path
        self.ssh_key_path = ssh_key_path
        self.base_dir = base_dir
        self._load_json()

    def _load_json(self):
        if not os.path.exists(self.json_path):
            return []
        with open(self.json_path, 'r') as f:
            return json.load(f)
        
    def _save_json(self, data):
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=4)

    def run(self):
        data = self._load_json()
        for entry in data:
            station = entry.get("station")
            label = entry.get("label")
            user = entry.get("user")
            ip_address = entry.get("ip_address")
            log_file_path = entry.get("log_file_path")
            emails = entry.get("email_to", [])
            expected_size = entry.get("log_size_mb", 0)

            if not all([station, label, user, ip_address, log_file_path]):
                continue

            ingestor = LogIngestor(
                ssh_user=user,
                client_ip=ip_address,
                base_dir=self.base_dir,
                ssh_key_path=self.ssh_key_path
            )

            cmd = (
                f'ssh -i {self.ssh_key_path} {user}@{ip_address} '
                f'"test -f {log_file_path} && stat -c %s {log_file_path}"'
            )

            result = os.popen(cmd).read().strip()
            if not result:
                print(f"[!] File not found: {log_file_path} on {ip_address}")
                continue

            remote_size_bytes = int(result)
            remote_size_bytes_mb = remote_size_bytes // (1024 * 1024)

            if remote_size_bytes_mb != expected_size: # >= ??? 
                print(
                    f"[!] Size mismatch for {log_file_path} "
                    f"(remote {remote_size_bytes_mb}MB != expected {expected_size}MB) (skip)"
                )
                continue

            try:
                ingestor.ingestLogs(label, station, log_file_path, emails)
                entry["timestamp"] = datetime.now().isoformat()
                print(f"[+] Ingested {log_file_path} from {ip_address}")

                self._save_json(data)
                print(f"[+] Updated JSON for {label} ({station})")

            except Exception as e:
                print(f"[-] Error ingesting {log_file_path}: {e}")
                continue

if __name__ == "__main__":
    job = LogIngestionJob(
        json_path="~/testingCron/dummy.jso",
        base_dir="~/logs",
        ssh_key_path="~/.ssh/id_rsa"
    )

    job.run()