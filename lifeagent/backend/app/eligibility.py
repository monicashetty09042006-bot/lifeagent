import json, pathlib, datetime as dt

SCHEMES = json.loads((pathlib.Path(__file__).parent / "data" / "schemes.json").read_text())

def match(p: dict) -> dict:
    """Explainable rules engine: returns eligible and not-eligible schemes WITH reasons."""
    eligible, not_eligible = [], []
    age, inc = p.get("age") or 0, p.get("annual_income") or 0
    occ = (p.get("occupation") or "").lower()
    for s in SCHEMES:
        if s["country"] != p["country"]:
            continue
        r, why, fail = s["rules"], [], []
        def chk(ok, yes, no):
            (why if ok else fail).append(yes if ok else no)
        if "min_age" in r: chk(age >= r["min_age"], f"Age {age} meets minimum {r['min_age']}", f"Age {age} is below {r['min_age']}")
        if "max_income" in r: chk(inc <= r["max_income"], f"Income {inc:,.0f} is within limit {r['max_income']:,}", f"Income {inc:,.0f} is above limit {r['max_income']:,}")
        if "occupations" in r: chk(occ in r["occupations"], f"Occupation '{occ}' qualifies", f"Scheme is for {', '.join(r['occupations'])}")
        item = {k: v for k, v in s.items() if k != "rules"}
        item["deadline"] = (dt.date.today() + dt.timedelta(days=s["deadline_days"])).isoformat()
        item["reasons"], item["failed"] = why, fail
        (not_eligible if fail else eligible).append(item)
    eligible.sort(key=lambda e: e["deadline"])
    return {"eligible": eligible, "not_eligible": not_eligible}
