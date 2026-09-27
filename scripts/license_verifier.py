"""Vérification locale, explicable et prudente des mentions de licence."""
import re

PERMISSIVE = {
    "CC BY": 92,
    "CC BY-SA": 88,
    "CC0": 95,
    "PUBLIC DOMAIN": 95,
    "DOMAINE PUBLIC": 95,
}
RESTRICTED = {
    "CC BY-NC": 62,
    "CC BY-NC-SA": 58,
    "CC BY-ND": 55,
    "CC BY-NC-ND": 45,
}

def verify_license(title, license_text, source_url="", page_text=""):
    raw = " ".join(str(x or "") for x in (title, license_text, source_url, page_text)).strip()
    text = re.sub(r"\s+", " ", raw).upper()
    license_value = str(license_text or "").strip()
    if not license_value:
        return {"score": 0, "decision": "review", "reason": "Aucune licence explicite détectée."}
    for label, score in RESTRICTED.items():
        if label in text:
            return {"score": score, "decision": "review", "reason": f"Licence {label} détectée : conditions particulières à vérifier avant publication."}
    for label, score in PERMISSIVE.items():
        if label in text:
            return {"score": score, "decision": "likely_ok", "reason": f"Licence {label} détectée avec une autorisation de réutilisation identifiable ; attribution à conserver."}
    if "CREATIVE COMMONS" in text or "LICENCE" in text or "LICENSE" in text:
        return {"score": 35, "decision": "review", "reason": "Une licence est mentionnée, mais son autorisation précise n’est pas reconnue automatiquement."}
    return {"score": 10, "decision": "reject", "reason": "La source ne fournit pas de licence identifiable permettant de conclure automatiquement."}
