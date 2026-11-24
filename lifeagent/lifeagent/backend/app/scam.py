import re, difflib
from urllib.parse import urlparse

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"']+|\b[\w-]+(?:\.[\w-]+)*\.(?:com|net|org|in|co|xyz|top|click|info|link|icu|gov|uk|us|ly|io|me)\b(?:/[^\s]*)?", re.I)
TRUSTED = (".gov", ".gov.in", ".gov.uk", ".nic.in")
BRANDS = {"sbi": "sbi.co.in", "hdfc": "hdfcbank.com", "paypal": "paypal.com", "amazon": "amazon.com", "irs": "irs.gov",
          "hmrc": "hmrc.gov.uk", "microsoft": "microsoft.com", "google": "google.com", "npci": "npci.org.in", "usps": "usps.com"}
BAD_TLD = (".xyz", ".top", ".click", ".link", ".icu", ".shop", ".buzz")
SHORT = ("bit.ly", "tinyurl.com", "t.co", "cutt.ly", "is.gd", "rb.gy")
URGENT = ("urgent", "immediately", "within 24", "last chance", "expires today", "account will be blocked", "suspended", "final notice")
CRED = ("otp", "pin", "password", "cvv", "card number", "aadhaar number", "social security")
MONEY = ("gift card", "processing fee", "pay a fee", "lottery", "prize", "you have won", "claim your", "wire transfer", "crypto")
AUTH = ("bank", "police", "arrest", "customs", "tax", "government", "kyc")

def _host(u):
    return (urlparse(u if "://" in u else "http://" + u).hostname or "").lower()

def analyze(text: str) -> dict:
    t, score, reasons = text.lower(), 0, []
    urls = [m.group(0).rstrip(".,)") for m in URL_RE.finditer(text)]
    for u in urls:
        h = _host(u)
        if any(h.endswith(s) for s in TRUSTED):
            reasons.append(f"{h}: official government domain (trusted)")
            continue
        parts, label = h.split("."), (h.split(".")[-2] if h.count(".") else h)
        if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", h): score += 30; reasons.append(f"{h}: raw IP address instead of a name")
        if "xn--" in h: score += 25; reasons.append(f"{h}: punycode lookalike characters")
        if h.endswith(BAD_TLD): score += 20; reasons.append(f"{h}: high-abuse domain ending")
        if h in SHORT: score += 15; reasons.append(f"{h}: link shortener hides the real destination")
        if u.lower().startswith("http://"): score += 10; reasons.append("Link is not encrypted (http)")
        if len(parts) > 3 or h.count("-") >= 2: score += 10; reasons.append(f"{h}: unusually long or hyphenated domain")
        flat = h.replace("-", "").replace(".", "")
        for brand, dom in BRANDS.items():
            official = h == dom or h.endswith("." + dom)
            fuzzy = label != brand and difflib.SequenceMatcher(None, label, brand).ratio() >= 0.8
            if not official and ((len(brand) >= 4 and brand in flat) or fuzzy):
                score += 40; reasons.append(f"{h}: imitates {brand.upper()} (official site is {dom})"); break
    for words, pts, msg in ((URGENT, 15, "Creates false urgency"), (CRED, 25, "Asks for secret codes or credentials"),
                            (MONEY, 25, "Promises money or demands a fee"), (AUTH, 10, "Claims to be a bank or authority")):
        hit = [w for w in words if w in t]
        if hit: score += pts; reasons.append(f"{msg} ({', '.join(hit[:3])})")
    score = min(score, 100)
    verdict = "dangerous" if score >= 70 else "suspicious" if score >= 40 else "likely safe"
    advice = {"dangerous": ["Do NOT click or reply.", "Never share OTP, PIN or passwords.", "Report it and block the sender."],
              "suspicious": ["Do not click. Open the official app or site by typing the address yourself.", "Ask a family member to double-check."],
              "likely safe": ["No red flags found, but stay careful with unexpected requests."]}[verdict]
    return {"risk_score": score, "verdict": verdict, "reasons": reasons, "urls": urls, "advice": advice}
