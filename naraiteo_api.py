import os, time, requests, xml.etree.ElementTree as ET

class RegionJobAPI:
    BASE_URL = "http://openapi.mpm.go.kr/openapi/service/RetrievePblinsttEmpmnInfoService"
    def __init__(self):
        self.key = os.getenv("NARAITEO_API_KEY", "").strip()
        if not self.key: raise RuntimeError("NARAITEO_API_KEY 환경변수가 필요합니다.")
        self.session = requests.Session()
    def _request(self, endpoint, params):
        last = None
        for attempt in range(3):
            try:
                response = self.session.get(f"{self.BASE_URL}/{endpoint}", params={"serviceKey": self.key, **params}, timeout=40)
                response.raise_for_status(); root = ET.fromstring(response.text)
                if root.findtext(".//resultCode") != "00": raise RuntimeError(root.findtext(".//resultMsg") or "API 오류")
                return [{child.tag: child.text for child in item} for item in root.findall(".//item")]
            except Exception as exc:
                last = exc
                if attempt < 2: time.sleep(2 ** attempt)
        raise RuntimeError(f"{endpoint} 호출 실패: {last}")
    def get_job_list(self, page_no=1, num_of_rows=100, job_type="e01"):
        return self._request("getList", {"pageNo": page_no, "numOfRows": num_of_rows, "Instt_se": "g02", "Pblanc_ty": job_type})
    def get_job_detail(self, idx):
        rows = self._request("getItem", {"idx": idx}); return rows[0] if rows else {}
    def get_job_files(self, idx): return self._request("getItemFile", {"idx": idx})
    def get_job_positions(self, idx): return self._request("getItemPosition", {"idx": idx})
