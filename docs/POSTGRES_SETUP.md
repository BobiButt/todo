# ============================================================================
# FILE:       docs/POSTGRES_SETUP.md
# PURPOSE:    Step-by-step guide to install, initialize, harden, and verify a
#             local PostgreSQL server on Fedora Linux so the TaskFlow backend
#             can connect to it. Written for a beginner: every command comes
#             with a short explanation of what it does and why it is needed.
# HOW IT WORKS: Follow the numbered sections top to bottom. Each section ends
#             with a "Verify" step so you know it worked before moving on.
# USED BY / DEPENDS ON: Read by a human before Phase 2 (backend setup). The
#             connection string created in step 7 is copied into
#             `backend/.env` and `backend/.env.example`.
# KEY CONCEPTS: Fedora's `dnf` package manager, systemd services, the
#             `pg_hba.conf` client-authentication file, database roles (users),
#             and SCRAM-SHA-256 password authentication.
# ============================================================================

# PostgreSQL Setup Guide (Fedora Linux)
# ======================================
#
# NOTE: Run every command exactly as written. Commands that begin with
# `sudo` require your user password. Commands that begin with
# `sudo -u postgres psql` open an interactive SQL prompt -- when you see
# `postgres=#` you are inside psql; type SQL statements ending with `;`,
# and type `\q` + Enter to leave.

---

## 1. Check whether PostgreSQL is already installed

```bash
# 1a. Ask the package manager if the psql client binary exists and which
#     version it is. If this prints a version (e.g. "psql (PostgreSQL) 16.x")
#     the client tools are already installed. If it prints
#     "bash: psql: command not found", continue to section 2.
psql --version

# 1b. Ask systemd (Fedora's service manager) about the server unit.
#     `status` shows whether the server exists, whether it is running, and
#     whether it starts automatically at boot. Fedora names the unit
#     "postgresql" (it maps to the postgresql.service unit file).
#     NOTE: Fedora versions 40+ may report "postgresql.service" or
#     "postgresql@<version>.service" -- both are fine.
systemctl status postgresql
```

If both commands work and the service is `active (running)`, you may skip
ahead to section 4.

---

## 2. Install the PostgreSQL server and contrib modules

```bash
# 2.1 Refresh dnf's package index so it knows about the newest available
#     versions. Without this, dnf might install an outdated package.
sudo dnf makecache

# 2.2 Install two packages:
#     - postgresql-server : the actual database server (postmaster daemon).
#     - postgresql-contrib : extra bundled extensions (e.g. pgcrypto) that
#       some projects enable later; installing now avoids surprises later.
sudo dnf install postgresql-server postgresql-contrib
```

---

## 3. Initialize the database cluster and start the service

```bash
# 3.1 Create the data directory structure (the "cluster"): this writes the
#     system catalogs, the default `postgres` database, and the
#     `postgres` superuser role into /var/lib/pgsql/data.
#     --initdb performs first-time initialization; --unit tells the helper
#     which systemd unit the data directory belongs to.
#     NOTE: Only run this ONCE. Re-running it fails if the directory is
#     already initialized (that failure is safe to ignore).
sudo postgresql-setup --initdb --unit postgresql

# 3.2 Enable the service (start it now AND at every future boot) and start
#     it immediately. `--now` does both jobs in one command.
sudo systemctl enable --now postgresql

# 3.3 Confirm the server is running. Look for "Active: active (running)".
systemctl status postgresql
```

---

## 4. Switch local password authentication to SCRAM-SHA-256

# Fedora's default `pg_hba.conf` uses `ident` authentication for local TCP
# connections, which asks the operating system to vouch for your identity
# instead of checking a password -- that does NOT work for an application
# that connects over TCP with a username/password (our FastAPI backend).
# We change the two loopback rules to `scram-sha-256`, the modern,
# salted challenge-response password hashing protocol.

```bash
# 4.1 Open the client authentication configuration file in a text editor.
#     Path on Fedora: /var/lib/pgsql/data/pg_hba.conf
#     TIP: if that path does not exist, find it with:
#     sudo -u postgres psql -c "SHOW hba_file;"
sudo nano /var/lib/pgsql/data/pg_hba.conf
```

# 4.2 Inside pg_hba.conf, find these TWO lines (they may be commented with
#     a leading `#` or not -- edit whichever match):
#
#     IPv4 local connection:
#     host    all             all             127.0.0.1/32            ident
#
#     IPv6 local connection:
#     host    all             all             ::1/128                 ident
#
#     Change ONLY the last word `ident` on each line to `scram-sha-256`.
#     The result must look like this:
#
#     -- BEFORE (insecure for TCP apps: no password is checked) --
#     host    all    all    127.0.0.1/32    ident
#     host    all    all    ::1/128         ident
#
#     -- AFTER (password required, hashed with SCRAM-SHA-256) --
#     host    all    all    127.0.0.1/32    scram-sha-256
#     host    all    all    ::1/128         scram-sha-256
#
#     NOTE: Leave the lines that start with `local` alone -- those are for
#     Unix-socket connections used by the `postgres` admin user.

```bash
# 4.3 Apply the change. PostgreSQL only re-reads pg_hba.conf on restart
#     (or SIGHUP), so restart the service.
sudo systemctl restart postgresql

# 4.4 Quick sanity check: connecting now requires a password. You will get
#     a password prompt (expected!). Press Ctrl+C if you just want to test.
psql -h localhost -U postgres -d postgres
```

---

## 5. Create the application database, role (user), and grant privileges

```bash
# 5.1 Open psql as the `postgres` OS user. The `-U postgres` flag selects the
#     postgres database superuser role; `-d postgres` selects its default
#     database. You will now see the `postgres=#` prompt.
sudo -u postgres psql
```

# ---- paste the following SQL inside the psql prompt (each statement ends with ;) ----
```sql
-- 5.2 Create the login role (database user) that FastAPI will use.
--     `LOGIN` allows password connections; `PASSWORD` sets the credential
--     (CHANGE THIS to something strong -- never reuse it publicly).
--     NOTE: use only lowercase unquoted names so future SQL needs no quoting.
CREATE USER taskflow_user WITH LOGIN PASSWORD 'CHANGE_ME_strong_password';

-- 5.3 Create the database owned by that role. OWNER means this role
--     automatically has full rights (CREATE, INSERT, UPDATE, ...) on every
--     table created inside it, so we do not need extra grants later.
CREATE DATABASE taskflow OWNER taskflow_user;

-- 5.3a Create a separate database for pytest. Tests truncate its tables.
CREATE DATABASE taskflow_test OWNER taskflow_user;

-- 5.4 Belt-and-suspenders: explicitly grant database-level privileges.
--     `GRANT ALL PRIVILEGES ON DATABASE` covers CREATE/CONNECT/TEMP;
--     this is harmless even though OWNER already implies most of it, and it
--     makes the setup robust if you later switch to a non-owner role.
GRANT ALL PRIVILEGES ON DATABASE taskflow TO taskflow_user;
GRANT ALL PRIVILEGES ON DATABASE taskflow_test TO taskflow_user;

-- 5.5 Leave the interactive psql shell.
\q
```

---

## 6. Verify the connection as the application user

```bash
# 6.1 Connect exactly the way the backend will:
#     -h localhost       -> connect over TCP (triggers the scram-sha-256 rule)
#     -U taskflow_user   -> the role created in 5.2
#     -d taskflow        -> the database created in 5.3
#     You will be prompted for the password set in 5.2.
psql -h localhost -U taskflow_user -d taskflow

# 6.2 Once inside, run these meta-commands to prove you are in the right place:
#     \l   -> list all databases (confirm `taskflow` exists)
#     \du  -> list roles (confirm taskflow_user exists)
#     \q   -> quit
```

Expected result: the password is accepted and `\l` shows `taskflow`.

---

## 7. Connection string and .env files

# The backend reads its configuration from a `.env` file (never commit real
# secrets -- only `.env.example` is committed).

```bash
# 7.1 From the project root, copy the template (Phase 2 creates this file):
cp backend/.env.example backend/.env

# 7.2 Edit backend/.env and set DATABASE_URL to the credential from section 5.
```

# backend/.env  (example -- replace CHANGE_ME_strong_password)
```ini
# DATABASE_URL -- SQLAlchemy async connection string.
#   postgresql+asyncpg://  -> scheme: PostgreSQL reached through the asyncpg driver
#   taskflow_user:...      -> role : password
#   @localhost:5432        -> host : port (5432 is PostgreSQL's default port)
#   /taskflow              -> database name
DATABASE_URL=postgresql+asyncpg://taskflow_user:CHANGE_ME_strong_password@localhost:5432/taskflow

# TEST_DATABASE_URL -- isolated PostgreSQL database used by pytest.
TEST_DATABASE_URL=postgresql+asyncpg://taskflow_user:CHANGE_ME_strong_password@localhost:5432/taskflow_test

# CORS_ORIGINS -- which browser origins are allowed to call the API.
#   The Vite dev server runs at http://localhost:5173, so we allow it.
CORS_ORIGINS=["http://localhost:5173"]

# ENVIRONMENT -- toggles development conveniences (auto docs, debug logging).
ENVIRONMENT=development
```

---

## 8. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `no pg_hba.conf entry ...` | pg_hba.conf has no rule for your source address | Confirm the 127.0.0.1/32 line exists and ends with `scram-sha-256`; restart postgresql |
| `password authentication failed` | Wrong password or `ident` still set | Re-check section 4 and the password from 5.2 |
| `Connection refused` on port 5432 | Server not running | `sudo systemctl status postgresql` |
| Firewall blocks remote access | `firewalld` active (only matters for OTHER machines) | Command T.3 below |
| Permission denied on data dir | SELinux labels wrong | Command T.2 below (never disable SELinux) |
| Port already in use | Another PostgreSQL occupies 5432 | Command T.1 below |

```bash
# T.1 Inspect which process listens on 5432 (shows PID and program name).
#     If nothing prints, the server is not listening on TCP at all.
sudo ss -lntp | grep 5432

# T.2 Re-apply SELinux labels to the PostgreSQL data directory.
#     SELinux denies file access when labels are wrong; restoring labels
#     fixes it WITHOUT weakening the security policy.
sudo restorecon -Rv /var/lib/pgsql

# T.3 Open the firewall for PostgreSQL -- only required for REMOTE clients.
#     Localhost connections (127.0.0.1) never traverse the firewall.
sudo firewall-cmd --permanent --add-service=postgresql
sudo firewall-cmd --reload

# T.4 Follow the server log live while you test the backend connection.
#     Failed logins appear here with the exact reason.
sudo journalctl -u postgresql -f
```

---

## 9. Optional: reset everything (destructive!)

```bash
# 9.1 Stop the service, delete the data directory, re-initialize.
#     WARNING: this erases ALL databases. Use only during local development.
sudo systemctl stop postgresql                    # stop the server first (files must be idle)
sudo rm -rf /var/lib/pgsql/data/*                 # delete every database file
sudo postgresql-setup --initdb --unit postgresql  # rebuild the empty cluster
sudo systemctl start postgresql                   # start again
# ...then re-run section 5 to recreate the role and database.
```


