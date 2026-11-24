import json, datetime as dt
from . import db

def seed():
    U = [  # id, name, country, lang, age, gender, occupation, income, currency, household, guardian
        (1, "Ravi Kumar", "IN", "kn", 52, "male", "farmer", 120000, "INR", 5, 4),
        (2, "Maria Lopez", "US", "es", 20, "female", "student", 9000, "USD", 1, None),
        (3, "Margaret Hill", "GB", "en", 71, "female", "retired", 9500, "GBP", 1, None),
        (4, "Arjun Kumar", "IN", "en", 28, "male", "engineer", 900000, "INR", 3, None),
    ]
    for u in U:
        db.x("INSERT INTO users VALUES(?,?,?,?,?,?,?,?,?,?,NULL)", u[:10])
        db.x("INSERT INTO consents(user_id,scope,granted) VALUES(?,?,1)", (u[0], "vault:read"))
    for u in U:
        if u[10]: db.x("UPDATE users SET guardian_user_id=? WHERE id=?", (u[10], u[0]))
    docs = [
        (1, "id_proof", "National ID", {"number": "XXXX-XXXX-4821"}),
        (1, "land_record", "Land record (2.1 acres)", {"survey_no": "114/3"}),
        (2, "id_proof", "State ID", {"number": "D-5529-1180"}),
        (2, "enrollment", "University enrollment letter", {"school": "State University"}),
        (3, "id_proof", "National Insurance card", {"number": "QQ 12 34 56 C"}),
        (4, "id_proof", "National ID", {"number": "XXXX-XXXX-7710"}),
    ]
    for d in docs:
        db.x("INSERT INTO vault_docs(user_id,doc_type,title,content_json) VALUES(?,?,?,?)", (d[0], d[1], d[2], json.dumps(d[3])))
    soon = (dt.date.today() + dt.timedelta(days=3)).isoformat()
    db.x("INSERT INTO deadlines(user_id,title,due_date,source) VALUES(1,'Renew crop insurance',?,'seed')", (soon,))
