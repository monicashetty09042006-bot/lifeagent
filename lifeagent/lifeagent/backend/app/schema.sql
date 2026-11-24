PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL, language TEXT DEFAULT 'en',
  age INT, gender TEXT, occupation TEXT, annual_income REAL, currency TEXT, household_size INT,
  guardian_user_id INT REFERENCES users(id));
CREATE TABLE IF NOT EXISTS vault_docs(
  id INTEGER PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id), doc_type TEXT, title TEXT,
  content_json TEXT DEFAULT '{}', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS consents(
  id INTEGER PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id), scope TEXT NOT NULL,
  granted INT DEFAULT 1, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id, scope));
CREATE TABLE IF NOT EXISTS approvals(
  id INTEGER PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id), kind TEXT NOT NULL, summary TEXT,
  payload_json TEXT NOT NULL, status TEXT DEFAULT 'pending', created_at TEXT DEFAULT CURRENT_TIMESTAMP, decided_at TEXT);
CREATE TABLE IF NOT EXISTS applications(
  id INTEGER PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id), scheme_id TEXT, scheme_name TEXT,
  status TEXT DEFAULT 'draft', reference TEXT, form_json TEXT, screenshot TEXT, mode TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS deadlines(
  id INTEGER PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id), title TEXT, due_date TEXT,
  source TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS scam_checks(
  id INTEGER PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id), input_text TEXT, risk_score INT,
  verdict TEXT, reasons_json TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS activity_log(
  id INTEGER PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id), agent TEXT, action TEXT, detail TEXT,
  status TEXT DEFAULT 'done', undoable INT DEFAULT 0, ref_table TEXT, ref_id INT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS notifications(
  id INTEGER PRIMARY KEY, user_id INT NOT NULL REFERENCES users(id), channel TEXT, title TEXT, body TEXT,
  is_read INT DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS ix_act_user ON activity_log(user_id, id DESC);
CREATE INDEX IF NOT EXISTS ix_dead_due ON deadlines(due_date);
