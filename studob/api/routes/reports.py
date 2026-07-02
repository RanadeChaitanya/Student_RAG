import datetime
import uuid

from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class TestReportRequest(BaseModel):
    student_id: str
    session_id: str


def _score_ring_svg(percentage: float) -> str:
    r = 54
    cx, cy = 64, 64
    circ = 2 * 3.14159265 * r
    offset = circ * (1 - percentage / 100)
    color = "#4ec9a0" if percentage >= 70 else "#f0b34b" if percentage >= 40 else "#f06070"
    return f"""<svg width="128" height="128" viewBox="0 0 128 128">
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#1a2340" stroke-width="10"/>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{color}" stroke-width="10"
        stroke-dasharray="{circ}" stroke-dashoffset="{offset}"
        stroke-linecap="round" transform="rotate(-90, {cx}, {cy})"/>
    <text x="{cx}" y="{cy}" text-anchor="middle" dominant-baseline="central"
        font-size="28" font-weight="700" fill="#e8edf5">{percentage:.0f}%</text>
</svg>"""


def _build_html(
    student,
    session,
    attempts,
    session_analytics,
    mastery_summary,
    recommendations,
) -> str:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    report_id = str(uuid.uuid4())[:8]

    correct = session_analytics.get("correct_count", 0)
    total = session_analytics.get("questions_attempted", 0)
    accuracy = session_analytics.get("accuracy_percent", 0.0)
    time_spent = session_analytics.get("total_time_spent_seconds", 0)
    duration = session_analytics.get("duration_minutes", 0)
    mastery_delta = session_analytics.get("mastery_delta", 0)
    session_type = session_analytics.get("session_type", session.session_type)

    minutes = int(time_spent // 60) if time_spent else int(duration or 0)
    seconds = int(time_spent % 60) if time_spent else 0

    mastery_delta_str = f"+{mastery_delta:.1f}" if mastery_delta >= 0 else f"{mastery_delta:.1f}"
    mastery_color = "#4ec9a0" if mastery_delta >= 0 else "#f06070"

    subject_breakdown = getattr(mastery_summary, "subject_breakdown", {})
    weak_topics = getattr(mastery_summary, "weak_topics", [])
    strengths = getattr(mastery_summary, "strengths", [])
    overall_mastery = getattr(mastery_summary, "overall_score", 0)

    weak_rows = ""
    for w in weak_topics[:5]:
        weak_rows += f"""<tr><td style="padding:8px 12px;border-bottom:1px solid #1a2340">{w.subject}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{w.topic} / {w.subtopic}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{w.score:.1f}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340;color:#f06070">{w.gap:.1f}</td></tr>"""

    strong_rows = ""
    for s in strengths[:5]:
        strong_rows += f"""<tr><td style="padding:8px 12px;border-bottom:1px solid #1a2340">{s.subject}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{s.topic} / {s.subtopic}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{s.score:.1f}</td></tr>"""

    topic_rows = ""
    for subject, score in sorted(subject_breakdown.items()):
        topic_rows += f"""<tr><td style="padding:8px 12px;border-bottom:1px solid #1a2340">{subject}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340;text-align:right">{score:.1f}%</td></tr>"""

    attempt_rows = ""
    for idx, a in enumerate(attempts, 1):
        status = "Correct" if a.is_correct else "Wrong"
        status_color = "#4ec9a0" if a.is_correct else "#f06070"
        t = a.response_time_seconds
        tm = f"{int(t//60)}m {int(t%60)}s" if t >= 60 else f"{t:.1f}s"
        attempt_rows += f"""<tr>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{idx}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{a.question_id}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340;color:{status_color}">{status}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{tm}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{a.hints_used}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340">{a.retry_count}</td>
</tr>"""

    mistake_rows = """<tr><td colspan="4" style="padding:16px;text-align:center;color:#a0a8c0">No mistakes recorded</td></tr>"""

    diff_breakdown = session_analytics.get("difficulty_breakdown", None)
    diff_rows = ""
    if diff_breakdown:
        for diff, data in sorted(diff_breakdown.items()):
            diff_rows += f"""<tr><td style="padding:8px 12px;border-bottom:1px solid #1a2340">{diff}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340;text-align:right">{data.get("count", 0)}</td>
<td style="padding:8px 12px;border-bottom:1px solid #1a2340;text-align:right">{data.get("accuracy", 0):.1f}%</td></tr>"""

    rec_html = ""
    if recommendations:
        for r in recommendations:
            rec_html += f"""<li style="margin-bottom:8px;color:#a0a8c0;line-height:1.5">{r}</li>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Test Report - Studob</title>
<style>
  @page {{ margin: 20mm; size: A4; }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', -apple-system, Roboto, Helvetica, Arial, sans-serif; background: #0a0e1a; color: #e8edf5; line-height: 1.6; padding: 40px; }}
  .report {{ max-width: 900px; margin: 0 auto; background: #0f1525; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,0.5); }}
  .header {{ background: linear-gradient(135deg, #0f1525 0%, #1a2340 100%); padding: 32px 40px; border-bottom: 1px solid #1a2340; }}
  .header h1 {{ font-size: 24px; font-weight: 700; color: #e8edf5; margin-bottom: 4px; }}
  .header .subtitle {{ font-size: 13px; color: #6b8cff; text-transform: uppercase; letter-spacing: 2px; }}
  .header .brand {{ font-size: 18px; font-weight: 700; color: #6b8cff; margin-bottom: 8px; }}
  .body {{ padding: 32px 40px; }}
  .section {{ margin-bottom: 32px; }}
  .section-title {{ font-size: 16px; font-weight: 600; color: #6b8cff; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #1a2340; text-transform: uppercase; letter-spacing: 1px; }}
  .card {{ background: #121a30; border-radius: 8px; padding: 20px; margin-bottom: 16px; border: 1px solid #1a2340; }}
  .card-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .info-label {{ font-size: 11px; color: #7a82a0; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }}
  .info-value {{ font-size: 14px; color: #e8edf5; font-weight: 500; }}
  .score-summary {{ display: flex; align-items: center; gap: 32px; flex-wrap: wrap; }}
  .score-stats {{ flex: 1; min-width: 200px; }}
  .stat-row {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #1a2340; }}
  .stat-row:last-child {{ border-bottom: none; }}
  .stat-label {{ font-size: 13px; color: #a0a8c0; }}
  .stat-value {{ font-size: 14px; color: #e8edf5; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ padding: 10px 12px; text-align: left; font-weight: 600; color: #a0a8c0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #1a2340; }}
  td {{ padding: 10px 12px; border-bottom: 1px solid #1a2340; color: #e8edf5; }}
  .badge {{ display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }}
  .badge-weak {{ background: rgba(240,96,112,0.12); color: #f06070; }}
  .badge-strong {{ background: rgba(78,201,160,0.12); color: #4ec9a0; }}
  .recommendation-list {{ list-style: none; padding: 0; }}
  .recommendation-list li {{ padding: 12px 16px; background: rgba(107,140,255,0.04); border-left: 3px solid #6b8cff; margin-bottom: 8px; border-radius: 0 6px 6px 0; color: #a0a8c0; line-height: 1.5; }}
  .footer {{ text-align: center; padding: 24px 40px; border-top: 1px solid #1a2340; font-size: 11px; color: #7a82a0; }}
  .footer span {{ margin: 0 12px; }}
  @media print {{ body {{ background: #0a0e1a; -webkit-print-color-adjust: exact; print-color-adjust: exact; }} }}
</style>
</head>
<body>
<div class="report">
  <div class="header">
    <div class="brand">Studob</div>
    <h1>Test Performance Report</h1>
    <div class="subtitle">{session_type.upper()} SESSION &mdash; {session.id[:8]}</div>
  </div>
  <div class="body">
    <div class="section">
      <div class="section-title">Student Information</div>
      <div class="card">
        <div class="card-grid">
          <div>
            <div class="info-label">Name</div>
            <div class="info-value">{student.name}</div>
          </div>
          <div>
            <div class="info-label">Grade</div>
            <div class="info-value">{student.grade}</div>
          </div>
          <div>
            <div class="info-label">Board</div>
            <div class="info-value">{student.board}</div>
          </div>
          <div>
            <div class="info-label">Exam Target</div>
            <div class="info-value">{student.exam_target or "N/A"}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Score Summary</div>
      <div class="card">
        <div class="score-summary">
          <div style="flex-shrink:0">{_score_ring_svg(accuracy)}</div>
          <div class="score-stats">
            <div class="stat-row"><span class="stat-label">Correct Answers</span><span class="stat-value">{correct} / {total}</span></div>
            <div class="stat-row"><span class="stat-label">Accuracy</span><span class="stat-value">{accuracy:.1f}%</span></div>
            <div class="stat-row"><span class="stat-label">Time Taken</span><span class="stat-value">{minutes}m {seconds}s</span></div>
            <div class="stat-row"><span class="stat-label">Mastery Change</span><span class="stat-value" style="color:{mastery_color}">{mastery_delta_str}</span></div>
            <div class="stat-row"><span class="stat-label">Overall Mastery</span><span class="stat-value">{overall_mastery:.1f}%</span></div>
          </div>
        </div>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Topic Analysis</div>
      <div class="card">
        <table>
          <thead><tr><th>Subject</th><th style="text-align:right">Mastery Score</th></tr></thead>
          <tbody>{topic_rows if topic_rows else '<tr><td colspan="2" style="padding:16px;text-align:center;color:#a0a8c0">No topic data available</td></tr>'}</tbody>
        </table>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Weak Topics</div>
      <div class="card">
        <table>
          <thead><tr><th>Subject</th><th>Topic</th><th>Score</th><th>Gap</th></tr></thead>
          <tbody>{weak_rows if weak_rows else '<tr><td colspan="4" style="padding:16px;text-align:center;color:#a0a8c0">No weak topics identified</td></tr>'}</tbody>
        </table>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Strong Topics</div>
      <div class="card">
        <table>
          <thead><tr><th>Subject</th><th>Topic</th><th>Score</th></tr></thead>
          <tbody>{strong_rows if strong_rows else '<tr><td colspan="3" style="padding:16px;text-align:center;color:#a0a8c0">No strong topics identified</td></tr>'}</tbody>
        </table>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Question-wise Performance</div>
      <div class="card">
        <table>
          <thead><tr><th>#</th><th>Question ID</th><th>Result</th><th>Time</th><th>Hints</th><th>Retries</th></tr></thead>
          <tbody>{attempt_rows if attempt_rows else '<tr><td colspan="6" style="padding:16px;text-align:center;color:#a0a8c0">No attempts recorded</td></tr>'}</tbody>
        </table>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Difficulty Breakdown</div>
      <div class="card">
        <table>
          <thead><tr><th>Level</th><th style="text-align:right">Questions</th><th style="text-align:right">Accuracy</th></tr></thead>
          <tbody>{diff_rows if diff_rows else '<tr><td colspan="3" style="padding:16px;text-align:center;color:#a0a8c0">No difficulty breakdown available</td></tr>'}</tbody>
        </table>
      </div>
    </div>

    <div class="section">
      <div class="section-title">Recommendations</div>
      <div class="card">
        {f'<ul class="recommendation-list">{rec_html}</ul>' if rec_html else '<p style="color:#a0a8c0;font-size:13px">Continue with your current study plan. Focus on maintaining consistency.</p>'}
      </div>
    </div>
  </div>
  <div class="footer">
    <span>Report ID: {report_id}</span>
    <span>Generated: {now}</span>
    <span>Studob &mdash; AI-Powered Adaptive Learning</span>
  </div>
</div>
</body>
</html>"""


@router.post("/test-report")
async def generate_test_report(request: Request, body: TestReportRequest):
    try:
        student = await request.app.state.context.student_profile.get_student(body.student_id)
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"detail": f"Student not found: {e}"},
        )

    try:
        session = await request.app.state.context.session_memory.get_session(body.session_id)
    except Exception as e:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=404,
            content={"detail": f"Session not found: {e}"},
        )

    try:
        attempts = await request.app.state.context.session_memory.get_session_attempts(
            body.session_id
        )
    except Exception:
        attempts = []

    try:
        session_analytics = await request.app.state.context.analytics.get_session_analytics(
            body.session_id
        )
    except Exception:
        session_analytics = {}

    try:
        mastery_summary = await request.app.state.context.mastery.get_mastery_summary(
            body.student_id
        )
    except Exception:
        from studob.schemas.student import MasterySummaryResponse

        mastery_summary = MasterySummaryResponse(
            student_id=body.student_id,
            overall_score=0.0,
            subject_breakdown={},
            weak_topics=[],
            strengths=[],
        )

    recommendations = []
    try:
        student_analytics = await request.app.state.context.analytics.get_student_analytics(
            body.student_id
        )
        recommendations_text = student_analytics.practice_recommendation
        if recommendations_text:
            recommendations = [r.strip() for r in recommendations_text.split(".") if r.strip()]
    except Exception:
        pass

    html = _build_html(
        student, session, attempts, session_analytics,
        mastery_summary, recommendations,
    )

    return {"html": html}
