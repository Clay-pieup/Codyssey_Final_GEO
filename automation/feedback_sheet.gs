/**
 * 우리가게 AI 점검 — 사장님 의견을 이 스프레드시트의 '피드백' 시트에 한 줄씩 기록한다 (10/31, 팀장)
 *
 * 흐름: 결과 리포트 의견 팝업 → 서버 POST /api/feedback → (이 웹 앱 주소) doPost → '피드백' 시트에 한 줄 추가
 * - 서버가 보내는 칸: docs/ARCHITECTURE.md 5장 (이름·이메일은 오지 않음. 리포트 메일은 Make가 따로 보냄)
 * - 웹 앱 주소는 비밀값 → Vercel 환경 변수 FEEDBACK_WEBHOOK_URL 에만 넣고, 저장소·채팅에 올리지 않는다
 * - 설치 방법: 스프레드시트 → 확장 프로그램 → Apps Script → 이 코드 붙여 넣기 → 배포 → 새 배포 → 웹 앱
 */

const SHEET_NAME = '피드백';
const HEADERS = ['접수 시각', '결과 이해도(1~5)', 'AI가 소개한 말', '함께 나온 가게', '해 볼 개선 제안', '자유 의견',
                 '가게', '지역', '대표 메뉴', '언급률(%)', '추가 진단 실행'];

function doPost(e) {
  const data = JSON.parse(e.postData.contents);
  if (data.event !== 'feedback') {
    return ContentService.createTextOutput('ignored');   // 의견이 아닌 요청은 기록하지 않음
  }

  // 의견 두 개가 동시에 들어와도 줄이 섞이지 않게 잠깐 잠금
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const book = SpreadsheetApp.getActiveSpreadsheet();
    const sheet = book.getSheetByName(SHEET_NAME) || book.insertSheet(SHEET_NAME);
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(HEADERS);                           // 처음 한 번만 제목 줄
    }
    sheet.appendRow([
      data.submitted_at, data.clarity, data.accuracy, data.competitors, data.useful, data.comment,
      data.store, data.region, data.menus, data.mention_rate, data.agent_ran ? '예' : '아니요',
    ]);
  } finally {
    lock.releaseLock();
  }
  return ContentService.createTextOutput('ok');
}
