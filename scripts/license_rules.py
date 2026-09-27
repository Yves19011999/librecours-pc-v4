ALLOWED_FOR_REPUBLICATION = {"CC BY", "CC BY 4.0", "CC0", "Public Domain"}
NONCOMMERCIAL_ONLY = {"CC BY-NC", "CC BY-NC 4.0", "CC BY-NC-SA", "CC BY-NC-SA 4.0"}

def classify(license_text):
    t = (license_text or "").lower()
    if "cc0" in t or "public domain" in t:
        return "redistribution"
    if "cc by-nc" in t or "cc-by-nc" in t:
        return "noncommercial"
    if "cc by" in t or "cc-by" in t:
        return "redistribution"
    return "review"
