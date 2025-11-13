import paramiko
import smtplib
from pathlib import Path
from email.message import EmailMessage

class LogIngestor:
    def __init__(self, ssh_host, ssh_user, ssh_key_path, remote_base_dir,
                smtp_host, smtp_port, smtp_user, smtp_password, email_to,
                ssh_port = 22, ssh_passphrase = None):
        
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user
        self.ssh_key_path = Path(ssh_key_path).expanduser()
        self.remote_base_dir = remote_base_dir

        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.email_to = email_to

        self.ssh_port = ssh_port
        self.ssh_passphrase = ssh_passphrase

    def _SSHconnect(self):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            pkey = paramiko.Ed25519Key.from_private_key_file(str(self.ssh_key_path), password=self.ssh_passphrase)
        except Exception as e:
            pkey = paramiko.RSAKey.from_private_key_file(str(self.ssh_key_path), password=self.ssh_passphrase)

        client.connect(self.ssh_host, port=self.ssh_port, username=self.ssh_user, pkey=pkey, timeout=15)

        return client, client.open_sftp()
    
    # ask to modify based on structure there 
    def _build_remote_path(self, station_name, log_file_name):
        return f"{self.remote_base_dir}/{station_name}/{log_file_name}"
    
    def _send_email(self, subject, body):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.smtp_user # opposed to specific in case reused across different servers ?
        msg["To"] = self.email_to
        msg.set_content(body)

        with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
            #server.ehlo()
            #server.starttls()
            #server.ehlo()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)

    def ingest_log(self, station_name, log_file_path):
        local_path = Path(log_file_path).expanduser()
        if not local_path.exists():
            raise FileNotFoundError(f"Log file not found: {local_path}")

        ssh, sftp = self._SSHconnect()
        try:
            remote_path = self._build_remote_path(station_name, local_path.name)
            remote_dir = "/".join(remote_path.split("/")[:-1])  

            try: 
                sftp.chdir(remote_dir)
            except IOError:
                parts = remote_dir.strip("/").split("/")
                cur = ""
                for part in parts:
                    cur = f"{cur}/{part}" if cur else part
                    try:
                        sftp.mkdir(cur)
                    except IOError:
                        pass
                sftp.chdir(remote_dir)
            sftp.put(str(local_path), remote_path)
            print(f"Uploaded {local_path} ==> {remote_path}")
        finally:
            sftp.close()
            ssh.close()

        try: 
            self._send_email(
                subject=f"Log Ingestion - {station_name}",
                body=f"Log file {local_path} has been ingested successfully."
            )
        except Exception as e:
            print(f"Error sending email: {e}")

        return remote_path
