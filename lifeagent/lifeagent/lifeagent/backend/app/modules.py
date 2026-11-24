LIVE = [
  {"id": "benefits", "name": "Government & Benefits", "status": "live"},
  {"id": "scam", "name": "Safety & Scam Shield", "status": "live"},
]
PLANNED = [
  {"id": "money", "name": "Money & Bills", "status": "planned", "keywords": ("bill", "subscription", "charge", "overcharge", "payment"),
   "plan": "Read bills, explain them, flag overcharges, cancel unused subscriptions, remind before due dates."},
  {"id": "health", "name": "Health", "status": "planned", "keywords": ("doctor", "medicine", "appointment", "report", "prescription"),
   "plan": "Book doctors around your calendar, medicine reminders, explain reports in simple language."},
  {"id": "shopping", "name": "Shopping", "status": "planned", "keywords": ("buy", "price", "compare", "shopping", "review"),
   "plan": "Compare prices and reviews against your budget; purchase only after your approval."},
  {"id": "travel", "name": "Travel", "status": "planned", "keywords": ("trip", "flight", "hotel", "travel", "visa"),
   "plan": "Plan trips, compare fares and stays, prepare visa paperwork from your vault."},
  {"id": "career", "name": "Education & Career", "status": "planned", "keywords": ("job", "course", "resume", "career", "interview"),
   "plan": "Match jobs and courses, draft applications, track deadlines."},
  {"id": "family", "name": "Family Care", "status": "planned", "keywords": ("parent", "mother", "father", "child", "family"),
   "plan": "Caregiver mode: manage a parent's tasks with their explicit consent (guardian alerts already live in Scam Shield)."},
]
def match_module(text: str):
    t = text.lower()
    return next((m for m in PLANNED if any(k in t for k in m["keywords"])), None)
