import datetime
import os
import subprocess
import zmq

class LogIngestor:
    def __init__(self, ssh_user, client_ip, base_dir, ssh_key_path):
        self.ssh_user = ssh_user
        self.client_ip = client_ip
        self.base_dir = base_dir    
        self.ssh_key_path = os.path.expanduser(ssh_key_path)
    
    def _SSHConnect(self):
        subprocess.run([
            "ssh", "-i", self.ssh_key_path,
            f"{self.ssh_user}@{self.client_ip}"
        ], check=True)

    def _createRemoteDir(self, station_name, client_file_path):

        log_file_name = os.path.basename(client_file_path)
        # remote_dir = os.path.join(self.base_dir, station_name)
        # os.makedirs(remote_dir, exist_ok=True)  
        # destination_path = os.path.join(remote_dir, log_file_name)
        # return destination_path
        
        name, ext = os.path.splitext(log_file_name)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_file_name = f"{name}_{timestamp}{ext}"

        remote_dir = os.path.join(self.base_dir, station_name)
        os.makedirs(remote_dir, exist_ok=True)  
        destination_path = os.path.join(remote_dir, new_file_name)

        return destination_path

    def _sendEmails(self, label, emails, local_path, station_name):
        context = zmq.Context()
        socket = context.socket(zmq.PUSH)
        socket.connect("")

        sender = "it@sesame.org.jo"
        recipient = "; ".join(emails)
        CCAddresses = ""
        subject = f"Logs Ingestion Notification - {label}"
        body = (
            f"Hi,\n\n"
            f"The log file has been ingested successfully.\n\n"
            f"Station: {station_name}\n"
            f"File: {os.path.basename(local_path)}\n"
            f"Stored at: {local_path}\n\n"
            f"Best Regards,\n"
            f"Log Ingestor Service"
        )

        socket.send_multipart([sender.encode(), recipient.encode(), CCAddresses.encode(), subject.encode(), body.encode()])

        socket.close()
        context.term()

    def ingestLogs(self, label, station_name, client_file_path, emails):
        destination_path = self._createRemoteDir(station_name, client_file_path)

        # RSYNC from client to server and remove source file
        subprocess.run([
            "rsync", "-avz", "--remove-source-files",
            "-e", f"ssh -i {self.ssh_key_path}",
            f"{self.ssh_user}@{self.client_ip}:{client_file_path}",
            destination_path
        ], check=True)

        print(f"[+] Pulled {client_file_path} from {self.client_ip} ==> {destination_path}")
        print(f"[+] Removed source file {client_file_path} from {self.client_ip}")

        self._sendEmails(label, emails, destination_path, station_name)
        print(f"[+] Sent email notifications for {emails}")

