# TLS certificates

Managed MySQL providers (Aiven, and most others on free tiers) require TLS and
provide a CA certificate so the client can verify the server.

1. Aiven Console -> your MySQL service -> **Overview** -> *Connection information*
2. Next to **CA Certificate**, click **Download**
3. Save the downloaded file here as `database/certs/ca.pem`
4. Point the app at it in `.env`:

   ```ini
   DB_ssl_ca=database/certs/ca.pem
   ```

Notes:
- This is a **public** CA certificate, so it is safe to commit to the repository.
  Never commit the service *password*, though -- that belongs in `.env`
  (gitignored) or in Streamlit secrets.
- The path is resolved relative to the project root, so it works no matter which
  directory you launch the app from.
- **Aiven shortcut:** if `DATABASE_URL` points at a `*.aivencloud.com` host and
  `DB_ssl_ca` is not set, the app automatically uses this file. So for Aiven,
  setting `DATABASE_URL` alone is enough.
- If the file is missing, `database/config.py` raises a clear
  `ConfigurationError` before any connection is attempted.
