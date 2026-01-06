
# 👨🏻‍🏫 통합 교육 플랫폼(LMS) 개발 프로젝트
<br>

---
<div align=center> 

### 🔗 <a href="https://my.ozcodingschool.site/" target="_blank"> 통합 교육 플랫폼(LMS) 사이트 바로가기</a>
</div>

---

<br>

## 📖 프로젝트 소개

>  본 프로젝트는 학습자, 강사, 관리자가 하나의 시스템에서 학습 전 과정을 관리할 수 있도록 설계된 __```통합 교육 플랫폼(LMS)```__ 입니다. 수업 운영, 평가, 학습 관리 기능을 하나의 서비스로 통합하여 __교육 운영의 효율성__ 과 __편의성__ 을 높이는 것을 목표로 합니다.

<br>

## 🗓️ 프로젝트 기간
- 2025년 12월 5일 - 2026년 1월 5일
<br>


## 🧰 사용 스택

### :wrench: System Architecture


<div align=center> 
  <img src="https://img.shields.io/badge/Amazon%20EC2-FF9900?style=for-the-badge&logo=Amazon%20EC2&logoColor=white">
  <img src="https://img.shields.io/badge/Amazon%20S3-569A31?style=for-the-badge&logo=Amazon%20S3&logoColor=white">
  <img src="https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white">
  <img src="https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white">
  <img src="https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white">
  <img src="https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white">
    <br>
  <img src="https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white">
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white">
  <img src="https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white">
  <img src="https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white">

  <br>
</div>
  <br>
  <br>



## 🪢 ERD

<a href="https://dbdiagram.io/d/Externship-6823ff4e5b2fc4582f7c2afa" target="_blanck"><img width="2677" height="1964" alt="Externship" src="https://github.com/user-attachments/assets/027087b9-bc01-4847-b3ea-712a9471bbe5" /></a>

---

<br> 

## 🖥️ 서비스 소개

### ` 🔐 회원 관리 기능 `

> 회원 인증, 계정 관리, 권한 관리 및 관리자의 회원 운영/통계 관리를 목적으로 합니다.

<details> <summary><strong>👩‍💻 회원 페이지 (User)</strong></summary><br>

**1. 회원가입**
- 이메일 회원가입
    - 이메일(인증 필수), 비밀번호
    - 이름, 닉네임, 성별
    - 휴대폰 번호(인증 필수)
    - 생년월일
- 이메일 인증
    - Gmail을 통한 인증코드 발송
    - Base62 인코딩 인증코드 사용
- 휴대폰 인증
    - SMS 인증 (6자리 난수)
    - Twilio Auth 서비스 사용
    <br>

**2. 소셜 로그인 회원가입**
- 카카오
    - OAuth2 인증
    - 기존 회원 존재 시 로그인 처리
    - 필수 수집 정보
        - 이메일, 닉네임(중복 방지용 랜덤값 처리), 이름
        - 휴대폰 번호, 생년월일, 프로필 이미지
- 네이버
    - OAuth2 인증
    - 기존 회원 존재 시 로그인 처리
    - 필수 수집 정보
        - 이메일, 닉네임(중복 방지), 이름
        - 휴대폰 번호, 생년월일, 성별, 프로필 이미지
 <br>

**3. 로그인**
- 이메일 로그인
    - 이메일, 비밀번호
- 소셜 로그인
    - 카카오 / 네이버 OAuth 로그인 지원
<br>

**4. 계정 찾기**
- 이메일 찾기
    - 이름, 휴대폰 번호 입력
    - 휴대폰 인증 후 이메일 일부 마스킹 노출
- 비밀번호 찾기
- 이메일 인증 후 비밀번호 재설정
    - 인증코드: Base62 인코딩
<br>

**5. 내 정보 관리**
- 내 정보 조회
    - 프로필 이미지
    - 이메일, 닉네임, 이름
    - 성별, 휴대폰 번호, 생년월일
    - 수강생인 경우: 과정 / 기수 정보
- 내 정보 수정
    - 프로필 이미지, 닉네임
- 휴대폰 번호 변경
    - SMS 인증 필수 (Twilio)
- 비밀번호 변경
    - 구 비밀번호
    - 신규 비밀번호
    - 신규 비밀번호 확인
<br>

**6. 회원탈퇴 및 복구**

- 회원탈퇴
    - 마이페이지에서 탈퇴 가능
    - 탈퇴 후 2주 뒤 데이터 삭제
- 탈퇴 계정 복구
    - 이메일 인증 후 즉시 복구 가능

<br>
</details>

<details>
<summary><strong>🛠 회원 관리 페이지 (Admin)</strong></summary><br>

**1. 회원 정보 관리**
- 회원 목록 조회
    - 페이지네이션, 검색, 정렬, 필터링
    - 조회 항목
        - ID, 이메일, 닉네임, 이름
        - 생년월일, 권한, 상태, 가입일
- 회원 상세 조회
    - 공통 정보 + 권한별 추가 정보
        - 수강생: 수강 과정/기수
        - 조교: 담당 과정/기수
        - 운영매니저/러닝코치: 담당 과정
- 회원 정보 수정
    - 이름, 성별, 닉네임
    - 생년월일, 전화번호
    - 상태, 프로필 이미지
- 회원 정보 삭제
    - 관리자만 가능
    - 관련 데이터 즉시 삭제 (복구 불가)
<br>

**2. 회원 권한 관리**
- 관리자 권한으로 회원 권한 변경 가능
<br>

**3. 수강생 관리**
- 수강생 목록 조회
    - 과정-기수 기준 조회
    - 페이지네이션, 검색, 필터링
- 수강생 등록 신청 관리
    - 등록 신청 목록 조회
    - 일괄 승인 / 반려 처리
<br>

**4. 회원 탈퇴 관리**
- 탈퇴 내역 조회
    - 탈퇴 사유, 탈퇴 일시 조회
- 탈퇴 내역 상세 조회
    - 권한별 추가 정보 제공
    - 삭제 예정 일시 확인 가능
- 탈퇴 회원 복구
    - 탈퇴 요청 삭제 후 즉시 복구
<br>

**5. 대시보드**
- 회원가입 추세
    - 월별 / 년별 가입자 수 그래프
- 회원탈퇴 추세
    - 월별 / 년별 탈퇴자 수 그래프
- 탈퇴 사유 분석
    - 원형 차트
    - 월별 탈퇴 사유 추이 막대그래프
- 수강생 전환 추이
    - 월별 / 년별 수강생 전환 수 그래프

</details>

- 자세한 사항이 궁금하다면 <a href="https://www.miricanvas.com/v2/design/15bqgoy?location=design&type=copy_link&access=link&permission=viewer&viewMode=VklFV0VS" target="_blank"> BE_1팀 발표 자료 </a> 를 참고하세요.

<br>

<div align=center> 
  
| <a href=https://github.com/4vpr><img src="https://avatars.githubusercontent.com/u/108639830?v=4" width=100px/><br/><sub><b>@4vpr</b></sub></a><br/> |  <a href=https://github.com/choi8154><img src="https://avatars.githubusercontent.com/u/223584123?v=4" width=100px/><br/><sub><b>@choi8154</b></sub></a><br/> | <a href=https://github.com/urumuru><img src="https://avatars.githubusercontent.com/u/227329514?v=4" width=100px/><br/><sub><b>@urumuru</b></sub></a><br/> |  <a href=https://github.com/kbsj2018ng-byte><img src="https://avatars.githubusercontent.com/u/222920787?v=4" width=100px/><br/><sub><b>@kbsj2018ng-byte</b></sub></a><br/> |
|:-------:|:-------:|:-------:|:-------:|
| 이건우(팀장) | 최건희 | 김준호 | 정대기|

</div>


<br>


---

### ` 📝 쪽지시험 기능 `

> 수강생의 **학습 점검**과 어드민의 **시험 생성·배포·관리**를 목적으로 합니다.


   <details> <summary><strong>👩‍🎓 쪽지시험 (User)</strong></summary><br>

**1. 쪽지시험 목록 조회**
- 과정·기수 기준 배포된 시험 목록 조회
- 무한 스크롤, 상태별 필터링(전체 / 응시 완료 / 미응시)
- 제공 정보
    - 과목 로고, 시험명, 과목명
    - 문항 수, 총점
    - 응시 상태, 점수, 정답 수
<br>

**2. 쪽지시험 응시**
- 참가코드 입력 후 응시
- 제한 시간 내 시험 진행
<br>

**3. 문제 풀이**
- 문제 유형
    - 빈칸 채우기, 순서 정렬, 다지선다, 단답형, OX
- 경과 시간, 부정행위 횟수 표시
- 시간 초과 시 자동 제출
<br>

**4. 부정행위 및 상태 체크**
- 화면 이탈 시 부정행위 기록
- 3회 적발 시 즉시 종료
- 배포 상태 변경 시 시험 자동 종료
<br>

**5. 시험 제출 및 결과 확인**
- 자동 채점
- 점수, 응시 시간, 문항별 채점 결과 및 해설 제공
<br>

</details>

<details>
<summary><strong>🛠 쪽지시험 관리 (Admin)</strong></summary><br>

**1. 쪽지시험 관리**
- 시험 생성 / 조회 / 수정 / 삭제
- 시험 정보: 이름, 과목, 로고
<br>

**2. 문제 관리**
- 시험당 최대 20문항
- 총 배점 최대 100점
- 문제 추가 / 수정 / 삭제
- 문제 유형 변경 가능
<br>

**3. 배포 관리**
- 시험–배포 분리 구조
- 문제 스냅샷 저장
- Base62 참가코드 생성
- 배포 정보: 과정/기수, 시험 시간, 시작·종료 일시
<br>

**4. 배포 및 응시 내역 조회**
- 배포 목록 조회 (참여 인원, 평균 점수, 상태)
- 배포 on/off 제어
- 수강생 응시 내역 조회 / 상세 조회 / 삭제

</details>

- 자세한 사항이 궁금하다면 <a href="https://www.canva.com/design/DAG9PI29lpI/oI1oF0zA-_10pljt35ZGxQ/edit" target="_blank"> BE_2팀 발표 자료 </a> 를 참고하세요.

<br>

<div align=center> 

| <a href=https://github.com/ji-min0><img src="https://github.com/user-attachments/assets/898d2b29-5ced-40f8-9a76-07e8d360424f" width=100px/><br/><sub><b>@ji-min0</b></sub></a><br/> |  <a href=https://github.com/minju-kim-1901717/><img src="https://github.com/user-attachments/assets/a1e55caa-ca56-4edd-9cde-ee236cd56b72" width=100px/><br/><sub><b>@minju-kim-1901717</b></sub></a><br/> | <a href=https://github.com/JaMiLy-max><img src="https://avatars.githubusercontent.com/u/223883617?v=4" width=100px/><br/><sub><b>@JaMiLy-max</b></sub></a><br/> |  <a href=https://github.com/tjdgusf><img src="https://github.com/user-attachments/assets/01109264-96ba-4a9f-841e-df9dc51aaffc" width=100px/><br/><sub><b>@tjdgusf</b></sub></a><br/> |
|:-------:|:-------:|:-------:|:-------:|
| 강지민(팀장) | 김민주 | 이아진 | 이성현 |

</div>

<br>

---

### ` 🤖 QnA, AI챗봇 기능 `

> 수강생의 **학습 중 궁금증**을 해결하고, **AI와 운영진의 답변**을 통해 학습 효율을 높이기 위한 기능입니다.

<details>
<summary><strong>❓ 질의응답 (User)</strong></summary><br>

**1. 질문**
- 질문 등록 / 수정
    - 제목, 내용(Markdown), 이미지, 대·중·소 카테고리
- 질의응답 목록 조회
    - 답변 여부 탭, 카테고리 필터, 검색
    - 최신순 정렬, 페이지네이션, 카드 UI
- 질의응답 상세 조회
    - 질문 내용, 작성자 정보, 조회수
    - 답변 및 답변 댓글 목록
    
    <br>
    

**2. 답변**
- 답변 등록 / 수정
    - Markdown 작성, 이미지 첨부
- 답변 채택
    - 질문자 본인만 가능
    - 질문당 1개 답변 채택
- 답변 댓글 작성
    - 최대 500자
    
    <br>
    

**3. AI 답변**
- 질문 등록 시 AI 최초 답변 자동 생성
- AI 답변은 모든 사용자에게 동일하게 노출
- AI 답변 기반 추가 질문 채팅 제공
- SSE 기반 실시간 타이핑 효과
- 로그인 사용자만 채팅 가능

<br></details>

<details>
<summary><strong>🛠 질의응답 관리 (Admin)</strong></summary><br>

**1. 질의응답 관리**
- 질의응답 목록 / 상세 조회
- 질의응답 삭제
    - 질문, 답변, 댓글 일괄 삭제
- 답변 삭제
    - 답변 댓글 포함 삭제

<br>

**2. 카테고리 관리**
- 대·중·소 카테고리 등록 / 조회 / 삭제
- 카테고리 검색 및 필터
- 카테고리 삭제 시
    - 하위 카테고리 함께 삭제
    - 기존 질문은 일반 질문 카테고리로 전환

<br></details>

<details>
<summary><strong>🤖 AI 챗봇</strong></summary><br>
  
- 플로팅 버튼 기반 채팅 인터페이스
- 질의응답과 연계된 채팅 세션 생성
- 이전 채팅 세션 불러오기 / 신규 세션 생성
- AI 요약 기반 자동 세션 제목 생성 (30자 이내)
- SSE 기반 응답 스트리밍
- 채팅 종료 시 세션 및 SSE 연결 종료

</details>

- 자세한 사항이 궁금하다면 <a href="https://www.canva.com/design/DAG9f9Z3d5M/7KPKlHf2agyCHCJw7HLycA/edit" target="_blank"> BE_3팀 발표 자료 </a> 를 참고하세요.

<br>

<div align=center> 

|  <a href=https://github.com/partofship><img src="https://avatars.githubusercontent.com/u/146055630?v=4" width=100px/><br/><sub><b>@partofship</b></sub></a><br/> | <a href=https://github.com/KIHOON-KOR><img src="https://avatars.githubusercontent.com/u/221495533?v=4" width=100px/><br/><sub><b>@KIHOON-KOR</b></sub></a><br/> |  <a href=https://github.com/Lukascruise><img src="https://avatars.githubusercontent.com/u/227330858?v=4" width=100px/><br/><sub><b>@Lukascruise</b></sub></a><br/> |
|:-------:|:-------:|:-------:|
| 송호창(팀장) | 김기훈 | 최재흥 | 

</div>

<br>

---


### ` 📖 과정·기수·과목 관리 / 💬 커뮤니티 기능 `

> 교육 과정 운영을 위한 **학사 관리**와, 수강생 간 학습 소통을 지원하기 위한 **커뮤니티 기능**을 제공합니다.

<details>
<summary><strong>🛠 과정 · 기수 관리 (Admin)</strong></summary><br>

**1. 과정 관리**
- 과정 등록
    - 과정명, 과정 태그, 과정 소개, 썸네일 이미지
- 과정 목록 조회
    - 운영 기수 수, 총 수강 인원, 등록/수정 일시
- 과정 상세 조회
- 과정 정보 수정
- 과정 삭제
    - 기수 및 수강생 존재 시 삭제 제한

<br>

**2. 기수 관리**
- 기수 등록
    - 기수 번호, 최대 인원, 수강 기간
- 기수 목록 조회
    - 과정별 필터링, 상태(준비/시작/종료)
- 기수 상세 조회
- 기수 정보 수정
    - 수강 시작일 / 종료일
- 기수 삭제
    - 수강생 존재 시 삭제 불가

<br>

**3. 대시보드**
- 과정별 기수 등록 인원 추세
- 과정별 월별 등록 인원 추세

<br></details>

<details>
<summary><strong>🛠 수강 과목 관리 (Admin)</strong></summary><br>

- 과목 등록
    - 과목명, 과정, 수강일수, 시수, 상태, 썸네일
- 과목 목록 조회
- 과목 상세 조회
- 과목 정보 수정
- 과목 삭제
    - 관련 과제, 쪽지시험 데이터 함께 삭제

<br></details>

<details>
<summary><strong>💬 커뮤니티 (User)</strong></summary><br>

**1. 게시글**
- 게시글 작성
    - 제목, 내용(Markdown), 이미지, 카테고리
- 게시글 목록 조회
    - 카테고리별 조회, 검색, 정렬, 페이지네이션
- 게시글 상세 조회
- 게시글 수정 / 삭제 (본인)
- 게시글 좋아요 / 취소

<br>

**2. 댓글**
- 댓글 작성 (최대 500자)
- 유저 태그 기능 (`@닉네임`)
- 댓글 목록 조회 (무한 스크롤)
- 댓글 삭제 (본인)

<br></details>

<details>
<summary><strong>🛠 커뮤니티 관리 (Admin)</strong></summary><br>

**1. 게시판 카테고리 관리**
- 카테고리 등록 / 조회 / 수정 / 삭제
- 카테고리 활성화 on/off

<br>

**2. 게시글 관리**
- 게시글 목록 조회 (검색, 필터, 정렬)
- 게시글 상세 조회
- 게시글 수정 / 삭제
- 게시글 노출 on/off
- 공지사항 등록

<br>

**3. 댓글 관리**
- 게시글 내 댓글 삭제

</details>



- 자세한 사항이 궁금하다면 <a href="https://www.miricanvas.com/v2/design/15bp82t?location=design&type=copy_link&access=link&permission=viewer&viewMode=VklFV0VS" target="_blank"> BE_4팀 발표 자료 </a> 를 참고하세요.

<br>

<div align=center> 

|  <a href=https://github.com/minseokgyang><img src="https://avatars.githubusercontent.com/u/227292159?v=4" width=100px/><br/><sub><b>@minseokgyang</b></sub></a><br/> | <a href=https://github.com/dddops><img src="https://avatars.githubusercontent.com/u/217551827?v=4" width=100px/><br/><sub><b>@dddops</b></sub></a><br/> |  <a href=https://github.com/sowon-bak><img src="https://avatars.githubusercontent.com/u/227330858?v=4" width=100px/><br/><sub><b>@sowon-bak</b></sub></a><br/> |
|:-------:|:-------:|:-------:|
| 양민석(팀장) | 김재진 | 박성우 | 

</div>

<br>




---

## 🗂 프로젝트 구조

```

oz_externship_be_05/                       
├── .dockerignore                          
├── .github/                              # GitHub 레포 관리 설정
│   ├── CODEOWNERS                        # 경로별 코드 리뷰 담당자 지정
│   ├── ISSUE_TEMPLATE/                   # GitHub 이슈 템플릿
│   │   ├── bug_report.md                 # 버그 리포트용 이슈 템플릿
│   │   └── feature_request.md            # 기능 요청용 이슈 템플릿
│   ├── PULL_REQUEST_TEMPLATE.md          # PR 작성 시 기본 템플릿
│   ├── commit_template.txt               # 커밋 메시지 컨벤션 템플릿
│   └── workflows/                        # GitHub Actions CI/CD 파이프라인
│       ├── checks.yml                    # PR 시 테스트/린트 등 기본 체크
│       ├── dev_deploy.yml                # 개발 환경 배포 워크플로우
│       ├── pr_review_request.yml         # PR 생성 시 리뷰어 자동 요청
│       └── prod_deploy.yml               # 운영 환경 배포 워크플로우
├── .gitignore                            
├── config/                               # Django 프로젝트 전역 설정
│   ├── __init__.py
│   ├── asgi.py                           # ASGI 서버 엔트리포인트
│   ├── settings/                         # 환경별 Django 설정
│   │   ├── base.py                       # 공통 설정
│   │   ├── dev.py                        # 개발 서버 설정
│   │   ├── local.py                      # 로컬 개발 환경 설정
│   │   └── prod.py                       # 운영 환경 설정
│   ├── urls.py                           # 프로젝트 루트 URL 라우팅
│   └── wsgi.py                           # WSGI 서버 엔트리포인트
├── apps/                                 # 도메인별 Django 앱 모음
│   ├── core/                             # 공통 유틸, 예외, 상수 모듈
│   │   ├── constants.py                  # 프로젝트 전역 상수 정의
│   │   ├── exceptions/                   # 커스텀 예외 및 핸들러
│   │   ├── management/commands/          # Django 커스텀 커맨드
│   │   ├── response/                     # 공통 응답 메시지 포맷
│   │   ├── utils/                        # 공통 유틸 함수
│   │   └── tests/                        # core 모듈 테스트
│   ├── chatbot/                          # 챗봇 도메인
│   │   ├── models/                       # 모델
│   │   ├── serializers/                  # API 입출력 직렬화
│   │   ├── services/                     # 비즈니스 로직 계층
│   │   ├── views/                        # API 엔드포인트
│   │   └── tests/                        # 도메인 테스트
│   ├── community/                        # 커뮤니티(게시글/댓글) 도메인
│   │   ├── models/                       .
│   │   ├── admin/                        .
│   │   ├── serializers/                  .
│   │   ├── views/                        .
│   │   └── tests/                        .
│   ├── courses/                          # 코스/기수/과목 관리 도메인
│   │   ├── models/                       .
│   │   ├── admin/                        .
│   │   ├── serializers/                  .
│   │   └── tests/                        .
│   ├── exams/                            # 쪽지시험 도메인
│   │   ├── models/                       .
│   │   ├── serializers/                  .
│   │   ├── services/                     .
│   │   ├── views/                        .
│   │   └── tests/                        .
│   ├── qna/                              # 질의응답(Q&A) 도메인
│   │   ├── models/                       .
│   │   ├── services/                     .
│   │   ├── serializers/                  .
│   │   ├── views/                        .
│   │   └── tests/                        .
│   └── user/                             # 사용자/인증 도메인
│       ├── models/                       .
│       ├── serializers/                  .
│       ├── services/                     .
│       ├── views/                        .
│       └── tests/                        .
├── envs/
│   └── .local.env                        # 로컬 개발용 환경 변수
├── docker-compose.local.yml              # 로컬 개발용 Docker Compose 설정
├── manage.py                             # Django 관리 커맨드 엔트리
├── pyproject.toml                        # Poetry 의존성 및 프로젝트 설정
├── poetry.lock                           # 의존성 버전 고정 파일
└── resources/                            # 인프라 및 보조 스크립트
    ├── nginx/                            # Nginx 설정 및 Dockerfile
    └── scripts/                          # 로컬/운영 보조 스크립트


```
  


  <br>
  <br>



# 📘 프로젝트 규칙 (Project Rules)

## 🌿 Git Workflow & Convention

### 1.⏳ Git Flow

기본적으로 다음과 같은 브랜치들을 사용합니다.
```
- main/: 제품의 배포 가능한 최종 상태를 저장하는 브랜치
- develop/: 개발 중인 기능을 통합하는 브랜치
- feature/: 새로운 기능 개발을 위한 브랜치
- fix/: 버그를 수정하는 브랜치
- refactor: 리팩토링을 위한 브랜치
- hotfix/: 운영 중인 서비스의 긴급 수정 사항을 처리하는 브랜치
```    
- 기본 브랜치: `main`, `develop`
- `main`, `develop` 직접 push **금지**
- 모든 PR은 최소 **1인 이상 승인 필수**

<br>

### 2. ✏️ Git Commit Convention

 - **🧱 기본 구조** : ` <type>(#이슈번호): <작업 요약> `
 - **✅ 예시** :
   - `✨feat(#10): 시험 모델 추가`
   - `🐛fix(#32): 마이그레이션 오류 수정`
   - `♻️refactor(#78): 시험 조회 로직 리팩터링`
   - `📝docs(#51): README 구조 업데이트`
     
<details>
<summary><strong> 📐 Commit Template </strong></summary><br>

```

### 아래 1번 문항부터 주석 문구가 빈줄에 주석을 지우고 문항에 대한 내용을 작성하고 커밋을 완료해주세요.

# 1. 아래 형식에 맞춰 커밋 메시지 타이틀을 작성하세요:
# <이모지> <타입>: <간결한 커밋 메시지 요약>
#
# 예시:
# ✨ feat: 사용자 로그인 기능 추가
# 🐛 fix: 댓글 생성 시 발생하는 NullPointerException 수정
# 💡 chore: 불필요한 로그 제거 및 변수명 수정
# 🎨 style: black, isort 코드 포매터 실행
# 📝 docs: README에 프로젝트 설명 추가
# 🚚 build: Dockerfile 수정하여 실행 오류 해결
# ✅ test: 게시글 API 단위 테스트 추가
# ♻️ refactor: 중복 코드 제거 및 함수 분리
# 🚑 hotfix: 프로덕션 장애 수정 - 잘못된 URL 패턴 수정

# 2. 변경 또는 추가사항을 아래에 간략하게 작성하세요 ( 필수 )
#
# 본문 내용은 어떻게 변경했는지 보다 무엇을 변경했는지 또는 왜 변경했는지를 설명합니다.

# 3. 이슈가 있다면 아래에 연결하세요 ( 선택 )
#
# 예시
# 관련 이슈: #123

```
</details>

 -   **🔖 Commit Type 정의 → gitmoji**
   
<div align=center> 
  
| 깃모지 |    타입    | 설명                           |
| :-: | :------: | :--------------------------- |
|  ✨  |   feat   | 새로운 기능 추가                    |
|  🐛 |    fix   | 버그 수정                        |
|  💡 |   chore  | 기능 추가 없이 코드 수정 (오타, 주석 등)    |
|  🎨 |   style  | 코드 포매팅 수정                    |
|  📝 |   docs   | 문서 수정 (README 등)             |
|  🚚 |   build  | 빌드 관련 파일 수정                  |
|  ✅  |   test   | 테스트 코드 추가/변경 (프로덕션 코드 변경 없음) |
|  ♻️ | refactor | 리팩터링 (기능 변화 없음)              |
|  🚑 |  hotfix  | 긴급 수정                        |

</div>
  
  
## 🧑🏻‍💻 Code Convention

**1. 🧠 네이밍 규칙**
- **파일명**:  snake_case
- **클래스명**:  PascalCase
- **함수명**:  snake_case
-  **상수**:  UPPER_SNAKE_CASE

<br>

**2. 📍 URL 매핑 규칙**
- `Trailing Slash`는 추가하지 않는다

<br>

**3. ✨ Code Formatting**
- mypy
- isort
- black
- 위 세 가지를 사용하여 코드 포매팅과 타입 어노테이션을 준수한다.
<br>

**4. 🧪 Test Code**
- Django 내부에 포함된 `TestClient`를 활용하여 테스트코드를 작성한다.
- Coverage 80% 이상을 유지한다.
<br>

**5. 🏷️ Swagger 문서**
- Swagger 문서 자동화를 위한 라이브러리로 `drf-spectacular`를 사용한다.
- `extend_schema` 데코레이터를 사용하여 스키마를 구성하고 각 API 별 태깅, API 요약, 구체적인 설명, 파라미터 등을 지정한다.
  - Tag는 해당 API가 해당되는 요구사항 정의서의 카테고리 명을 사용
  - Summary에 해당 API의 요약 설명을 기재
  - Description에 해당 API의 구체적인 동작 설명

<br>

---


## :clipboard: Documents

> [ 🧚 요구사항 정의서 ](https://docs.google.com/spreadsheets/d/1xh37kqLOCXluecUXcNhFOMQnIhjjHsVNhvJnOx3gZEQ/edit?gid=0#gid=0)
> 
> [ 🪄 API 명세서 ](https://docs.google.com/spreadsheets/d/1JdQcyU0pfKxXxRBBy0xXr_kDt9bC29LJun_gNQLP-DQ/edit?gid=0#gid=0)
>
> [ 🔦 테이블 명세서 ](https://docs.google.com/spreadsheets/d/17r_O8EUqZDt9MoFmFTKgpXHLAKRh2Bsvx4cvIXjWmpM/edit?gid=684962824#gid=684962824)
>

