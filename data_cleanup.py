import os, sys
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore

def parse_date(value):
    try: return datetime.strptime((value or "").replace("-", "").replace(".", "")[:8], "%Y%m%d")
    except ValueError: return None

def cleanup():
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_FILE", "firebase-service-account.json")))
    db, today, cutoff = firestore.client(), datetime.now(), datetime.now() - timedelta(days=30)
    batch, pending, deleted, kept = db.batch(), 0, 0, 0
    for doc in db.collection("region_jobs").stream():
        data = doc.to_dict(); reg = parse_date(data.get("regdate") or data.get("reg_date")); end = parse_date(data.get("enddate") or data.get("end_date"))
        if reg and reg < cutoff and (not end or end < today):
            batch.delete(doc.reference); pending += 1; deleted += 1
            if pending == 400: batch.commit(); batch, pending = db.batch(), 0
        else: kept += 1
    if pending: batch.commit()
    print(f"[CLEANUP] 삭제 {deleted}건 / 보존 {kept}건")

if __name__ == "__main__":
    try: cleanup()
    except Exception as exc: print(f"[FATAL] {exc}"); sys.exit(1)
