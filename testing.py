from Backend import LogIngestor

ingestor = LogIngestor(
    ssh_host="192.168.189.128",            # VM IP
    ssh_user="qabasahmad",                 # your VM user
    ssh_key_path=r"C:\Users\walki\.ssh\id_rsa",  # private key on Windows
    remote_base_dir="/home/qabasahmad/logs",    # logs folder inside VM
    smtp_host="smtp.gmail.com",                 # skip email for now
    smtp_port=465,
    smtp_user="qabaskaissi@gmail.com",
    smtp_password="oyingtbcvkuhsrax",
    #smtp_password="vfhsfzzsefqjpazw",
    email_to="qab20210786@std.psut.edu.jo"
)

ingestor.ingest_log("station1", r"C:\Users\walki\OneDrive\Desktop\logsmaybe.txt")
print("Log ingestion complete!")


# if __name__ == "__main__":
#     ingestor = LogIngestor(
#         ssh_user="qabas",
#         client_ip="10.1.50.120",
#         base_dir="/home/qabas/logs",
#         ssh_key_path="~/.ssh/id_rsa"
#     )

#     ingestor.ingestLogs("station1", "~/station1logs.txt")