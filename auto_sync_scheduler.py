"""기존 job-portal과 동일하게 5분마다 신규 지자체 공고만 저장한다."""
import os, sys, time
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from naraiteo_api import RegionJobAPI

COLLECTION = "region_jobs"
JOB_TYPES = (("e01", "공무원"), ("e04", "공무직 등"))
MAX_PAGES = 2

def firebase_db():
    if not firebase_admin._apps:
        firebase_admin.initialize_app(credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_FILE", "firebase-service-account.json")))
    return firestore.client()

def parse_date(value):
    try: return datetime.strptime((value or "").replace("-", "").replace(".", "")[:8], "%Y%m%d")
    except ValueError: return None

def position_summary(rows):
    labels, count = [], 0
    for row in rows:
        name, value = row.get("name") or "", row.get("cnt") or ""
        if name: labels.append(f"{name} {value}명".strip())
        if str(value).isdigit(): count += int(value)
    return ", ".join(labels), count

def sync():
    db, api = firebase_db(), RegionJobAPI()
    known = {doc.id for doc in db.collection(COLLECTION).select([]).stream()}
    today, cutoff = datetime.now(), datetime.now() - timedelta(days=30)
    saved = list_calls = detail_calls = 0
    print(f"[CACHE] 기존 {len(known)}건")
    for code, label in JOB_TYPES:
        for page in range(1, MAX_PAGES + 1):
            jobs = api.get_job_list(page, 100, code); list_calls += 1
            if not jobs: break
            skipped = 0
            for basic in jobs:
                idx = str(basic.get("idx") or "")
                if not idx or idx in known: skipped += 1; continue
                basic_registered, basic_deadline = parse_date(basic.get("regdate")), parse_date(basic.get("enddate"))
                if not ((basic_registered and basic_registered >= cutoff) or (basic_deadline and basic_deadline >= today)):
                    continue
                detail = api.get_job_detail(idx); detail_calls += 1
                registered, deadline = parse_date(detail.get("regdate")), parse_date(detail.get("enddate"))
                if not ((registered and registered >= cutoff) or (deadline and deadline >= today)): continue
                files, positions = api.get_job_files(idx), api.get_job_positions(idx); detail_calls += 2
                grade, recruit_count = position_summary(positions)
                data = {**basic, **detail, "idx": idx,
                    "dept_name": detail.get("deptName") or "지방자치단체",
                    "work_region": detail.get("areaNm") or "공고문 확인",
                    "employment_type": label, "employment_category": label,
                    "employment_category_code": code,
                    "recruit_type": grade or label,
                    "recruit_num": str(recruit_count) if recruit_count else "공고문 확인",
                    "grade": grade or "채용직급 정보 없음", "contents": detail.get("contents") or "",
                    "files": files, "positions": positions, "job_type": "region", "source": "naraiteo",
                    "created_at": firestore.SERVER_TIMESTAMP, "updated_at": firestore.SERVER_TIMESTAMP,
                    "data_completeness": "full_4api"}
                db.collection(COLLECTION).document(idx).set(data); known.add(idx); saved += 1
                print(f"[NEW] {idx} {data.get('title', '')[:60]}"); time.sleep(0.3)
            if skipped > 80: print(f"[EARLY EXIT] {label} 중복 {skipped}건"); break
            time.sleep(0.5)
    print(f"[DONE] 신규 {saved}건 / 목록 {list_calls}회 / 상세 {detail_calls}회")

if __name__ == "__main__":
    try: sync()
    except Exception as exc: print(f"[FATAL] {exc}"); sys.exit(1)

