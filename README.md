# 대한민국 지자체 공공일터

나라일터 OpenAPI의 지방자치단체 채용정보를 Firebase `job-region`에 저장하고 GitHub Pages로 제공하는 사이트입니다.

## 운영 구조

- GitHub Actions가 기존 `khoon77/job-portal`과 동일하게 5분마다 실행됩니다.
- 지자체(`g02`)의 공무원(`e01`)·공무직 등(`e04`) 목록을 확인합니다.
- Firestore `region_jobs`의 기존 ID는 상세 API 호출 전에 제외합니다.
- 신규 공고만 상세정보·직급·첨부파일을 수집해 Firestore에 저장합니다.
- 매일 KST 00:00에 등록 30일 경과 및 마감된 공고를 정리합니다.
- 웹페이지는 Firestore에서 직접 데이터를 읽고 GitHub Pages로 배포됩니다.

## GitHub Secrets

`Settings → Secrets and variables → Actions`에 아래 두 항목을 등록해야 합니다.

- `NARAITEO_API_KEY`: 나라일터 OpenAPI 일반 인증키(Decoding)
- `FIREBASE_CREDENTIALS_BASE64`: `job-region` Firebase 서비스 계정 JSON을 Base64로 인코딩한 값

## GitHub Pages

`Settings → Pages → Build and deployment → Source`를 **GitHub Actions**로 설정합니다.
