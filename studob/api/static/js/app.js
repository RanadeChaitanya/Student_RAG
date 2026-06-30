const state = {
  students: [], selectedStudentId: null, currentView: 'dashboard',
  currentSessionId: null, practiceQuestions: [], assessmentQuestions: [],
  assessmentId: null,
  _assessState: null,
};

const COLORS = ['#6b8cff','#4ec9a0','#f0b34b','#f06070','#a078f0','#58c4e8','#f09060','#78d0a0'];

function navigate(hash) {
  const page = hash.replace('#', '') || 'dashboard';
  state.currentView = page;
  renderPage(page);
  updateNav(page);
  document.querySelector('.navbar-nav')?.classList.remove('open');
}

function toggleNav() { document.querySelector('.navbar-nav').classList.toggle('open'); }

function updateNav(page) {
  document.querySelectorAll('.nav-link').forEach(el => {
    const href = el.getAttribute('href').replace('#', '');
    el.classList.toggle('active',
      href === page || page.startsWith(href) ||
      (href.endsWith('/') && page.startsWith(href)));
  });
}

window.addEventListener('hashchange', () => navigate(window.location.hash));
window.addEventListener('load', () => navigate(window.location.hash || '#dashboard'));

async function renderPage(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const el = document.getElementById('page-' + page.split('/')[0]);
  if (!el) { renderDashboard(); return; }
  el.classList.add('active');
  el.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';
  try {
    if (page === 'dashboard' || page === '') await renderDashboard();
    else if (page === 'students') await renderStudents();
    else if (page.startsWith('student/')) await renderStudentDetail(page.split('/')[1]);
    else if (page === 'questions') await renderQuestions();
    else if (page === 'practice') await renderPractice();
    else if (page.startsWith('practice/')) await renderPracticeSession(page.split('/')[1]);
    else if (page.startsWith('practice-results/')) await renderPracticeResults(page.split('/')[1]);
    else if (page === 'assessment') await renderAssessment();
    else if (page.startsWith('assessment/')) await renderAssessmentDetail(page.split('/')[1]);
    else if (page.startsWith('diagnosis/')) await renderDiagnosis(page.split('/')[1]);
    else if (page.startsWith('analytics/')) await renderAnalytics(page.split('/')[1]);
    else if (page === 'concepts') await renderConcepts();
    else renderDashboard();
  } catch (e) {
    el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

function fmtPct(v) { return Math.round(v); }
function initials(name) { return name.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase(); }
function scoreClass(v) { return v >= 70 ? 'success' : v >= 40 ? 'warning' : 'danger'; }

function scoreRing(pct, size, label) {
  const r = 38; const circ = 2 * Math.PI * r;
  const dash = Math.max(0, (pct / 100) * circ);
  const cls = scoreClass(pct);
  size = size || 100;
  const r2 = Math.round(size * 0.38);
  const circ2 = 2 * Math.PI * r2;
  const dash2 = Math.max(0, (pct / 100) * circ2);
  return `<div class="progress-circle" style="width:${size}px;height:${size}px">
    <svg width="${size}" height="${size}" viewBox="0 0 100 100">
      <circle class="bg" cx="50" cy="50" r="42"/>
      <circle class="fg ${cls}" cx="50" cy="50" r="42" stroke-dasharray="${dash2} ${circ2}"/>
    </svg>
    <span class="pv" style="font-size:${Math.round(size*0.2)}px">${fmtPct(pct)}${label||'%'}</span>
  </div>`;
}

// ── DASHBOARD ──
async function renderDashboard() {
  const el = document.getElementById('page-dashboard');
  let students;
  try { students = await API.listStudents(); } catch { students = []; }
  state.students = students;

  if (students.length === 0) {
    el.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">+</div>
        <h2 class="mt-3">Welcome to Studob</h2>
        <p class="text-muted mb-3">Adaptive JEE Preparation Platform</p>
        <button class="btn btn-primary" onclick="showCreateStudent()">Add Student</button>
      </div>`;
    return;
  }

  const selectedId = state.selectedStudentId || students[0].id;
  state.selectedStudentId = selectedId;
  let mastery, analytics, weakTopics;
  try { mastery = await API.getMastery(selectedId); } catch { mastery = null; }
  try { analytics = await API.getStudentAnalytics(selectedId); } catch { analytics = null; }
  try { weakTopics = await API.getWeakTopics(selectedId); } catch { weakTopics = []; }

  const student = students.find(s => s.id === selectedId) || students[0];
  const overallScore = mastery ? mastery.overall_score : 0;

  const sidebarList = students.map(s => `
    <div class="student-item ${s.id === selectedId ? 'active' : ''}" onclick="switchStudent('${s.id}')">
      <div class="student-avatar" onclick="event.stopPropagation();navigate('#student/${s.id}')" style="cursor:pointer">${initials(s.name)}</div>
      <div>
        <div style="font-weight:600;font-size:0.84rem;cursor:pointer" onclick="event.stopPropagation();navigate('#student/${s.id}')">${s.name}</div>
        <div style="font-size:0.7rem;color:var(--on-surface-variant)">${s.grade} | ${s.exam_target || s.board}</div>
      </div>
    </div>`).join('');

  const subjectCards = mastery && mastery.subject_breakdown
    ? Object.entries(mastery.subject_breakdown).map(([subj, score]) =>
        `<div class="stat-card"><div class="stat-value">${fmtPct(score)}%</div><div class="stat-label" style="text-transform:capitalize">${subj}</div></div>`).join('')
    : '';

  const weakList = mastery ? mastery.weak_topics || [] : [];
  const strongList = mastery ? mastery.strengths || [] : [];

  const patterns = analytics && analytics.mistake_patterns ? analytics.mistake_patterns.slice(0, 4) : [];
  const sessions = analytics && analytics.recent_sessions ? analytics.recent_sessions.slice(0, 5) : [];

  el.innerHTML = `
    <div class="split">
      <div>
        <div class="card" style="padding:0.65rem">
          <div class="label-sm mb-2" style="padding:0 0.5rem">Students</div>
          ${sidebarList}
        </div>
        <div class="card" style="padding:0.65rem">
          <button class="btn btn-primary btn-sm btn-block" onclick="showCreateStudent()">+ Add Student</button>
        </div>
      </div>
      <div>
        <div class="flex items-center justify-between mb-3 flex-wrap gap-1">
          <h2>Dashboard</h2>
          <div class="flex gap-1 flex-wrap">
            <button class="btn btn-primary btn-sm" onclick="navigate('#practice')">Practice</button>
            <button class="btn btn-success btn-sm" onclick="navigate('#assessment')">Assess</button>
            <button class="btn btn-ghost btn-sm" onclick="navigate('#analytics/${selectedId}')">Analytics</button>
          </div>
        </div>

        <div class="card">
          <div class="flex items-center gap-3" style="flex-wrap:wrap">
            ${scoreRing(overallScore, 100)}
            <div class="flex-1">
              <h3 style="margin-bottom:2px">${student.name}</h3>
              <p class="text-dim" style="font-size:0.84rem">${student.grade} | ${student.board} | ${student.exam_target || 'No target'}</p>
              <div class="flex gap-1 mt-1 flex-wrap">
                <span class="badge badge-primary">${weakList.length} weak</span>
                <span class="badge badge-success">${strongList.length} strong</span>
                <span class="badge badge-info">${sessions.length} recent</span>
              </div>
            </div>
          </div>
          ${subjectCards ? `<div class="stat-row mt-2">${subjectCards}</div>` : ''}
        </div>

        <div class="row">
          <div class="col">
            <div class="card">
              <div class="card-header">Weak Topics</div>
              ${weakList.slice(0, 5).map(w => `
                <div class="flex items-center justify-between" style="padding:0.4rem 0;border-bottom:1px solid var(--border-light)">
                  <span style="font-size:0.84rem">${w.subtopic} (${w.subject})</span>
                  <div class="flex items-center gap-2">
                    <div class="progress" style="width:60px"><div class="progress-bar danger" style="width:${w.score}%"></div></div>
                    <span style="font-weight:600;color:var(--danger);font-size:0.84rem">${fmtPct(w.score)}</span>
                  </div>
                </div>`).join('') || '<p class="text-dim">No weak topics identified</p>'}
              ${weakList.length > 5 ? `<a href="#" onclick="navigate('#diagnosis/${selectedId}')" class="text-primary" style="font-size:0.82rem">View all ${weakList.length}</a>` : ''}
            </div>
            <div class="card">
              <div class="card-header">Strong Topics</div>
              ${strongList.slice(0, 5).map(s => `
                <div class="flex items-center justify-between" style="padding:0.4rem 0;border-bottom:1px solid var(--border-light)">
                  <span style="font-size:0.84rem">${s.subtopic} (${s.subject})</span>
                  <div class="flex items-center gap-2">
                    <div class="progress" style="width:60px"><div class="progress-bar success" style="width:${s.score}%"></div></div>
                    <span style="font-weight:600;color:var(--secondary);font-size:0.84rem">${fmtPct(s.score)}</span>
                  </div>
                </div>`).join('') || '<p class="text-dim">No strengths identified</p>'}
            </div>
          </div>
          <div class="col">
            <div class="card">
              <div class="card-header">Mistake Patterns</div>
              ${patterns.length ? patterns.map(p => `
                <div class="flex items-center justify-between" style="padding:0.35rem 0;border-bottom:1px solid var(--border-light)">
                  <span style="text-transform:capitalize;font-size:0.84rem">${p.error_category.replace(/_/g,' ')}</span>
                  <span><span class="badge badge-warning">${p.count}x</span> <span class="text-dim" style="font-size:0.74rem">(${fmtPct(p.frequency_percent)}%)</span></span>
                </div>`).join('') : '<p class="text-dim">No data yet</p>'}
            </div>
            <div class="card">
              <div class="card-header">Recent Sessions</div>
              ${sessions.length ? sessions.map(s => `
                <div class="session-item">
                  <div class="flex justify-between">
                    <span class="session-type" style="text-transform:capitalize">${s.session_type || 'practice'}</span>
                    <span class="badge ${s.avg_score >= 60 ? 'badge-success' : 'badge-warning'}">${fmtPct(s.avg_score)}%</span>
                  </div>
                  <div class="session-meta">${s.subject || ''}${s.topic ? ' / ' + s.topic : ''}${s.created_at ? ' - ' + new Date(s.created_at).toLocaleDateString() : ''}</div>
                </div>`).join('') : '<p class="text-dim" style="padding:0.5rem 0">No sessions yet</p>'}
            </div>
          </div>
        </div>
      </div>
    </div>`;
}

function switchStudent(id) {
  state.selectedStudentId = id;
  renderDashboard();
}

// ── STUDENTS ──
async function renderStudents() {
  const el = document.getElementById('page-students');
  const students = await API.listStudents();
  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>All Students</h2>
      <button class="btn btn-primary" onclick="showCreateStudent()">+ Add Student</button>
    </div>
    <div class="card" style="padding:0">
      <div class="table-wrap">
      <table class="table">
        <thead><tr><th>Name</th><th>Grade</th><th>Board</th><th>Target</th><th>Lang</th><th></th></tr></thead>
        <tbody>${students.map(s => `<tr>
          <td><strong>${s.name}</strong></td>
          <td>${s.grade}</td><td>${s.board}</td><td>${s.exam_target || '-'}</td><td>${s.language}</td>
          <td>
            <button class="btn btn-xs btn-ghost" onclick="navigate('#diagnosis/${s.id}')">Diagnose</button>
            <button class="btn btn-xs btn-ghost" onclick="navigate('#analytics/${s.id}')">Analytics</button>
            <button class="btn btn-xs btn-danger" onclick="deleteStudent('${s.id}')">Del</button>
          </td>
        </tr>`).join('')}</tbody>
      </table>
      </div>
    </div>`;
}

async function renderStudentDetail(id) {
  const el = document.getElementById('page-student');
  const [student, mastery, sessions] = await Promise.all([
    API.getStudent(id), API.getMastery(id),
    API.getStudentSessions(id).catch(() => []),
  ]);
  const overallScore = mastery ? mastery.overall_score : 0;
  const assessments = (sessions || []).filter(s => s.session_type === 'assessment');
  const practice_sessions = (sessions || []).filter(s => s.session_type === 'practice');
  const avgScore = assessments.length ? assessments.reduce((a,s) => a + (s.questions_count > 0 ? s.correct_count/s.questions_count*100 : 0), 0) / assessments.length : 0;

  const assessHtml = assessments.length ? `
    <div class="card">
      <div class="card-header">Test Results <span class="badge badge-info">${assessments.length} tests</span></div>
      <div class="table-wrap">
        <table class="table table-condensed">
          <thead><tr><th>Date</th><th>Score</th><th>Percentage</th><th>Mastery Δ</th><th></th></tr></thead>
          <tbody>${assessments.map(s => {
            const pct = s.questions_count > 0 ? Math.round(s.correct_count/s.questions_count*100) : 0;
            return `<tr>
              <td>${new Date(s.started_at).toLocaleDateString()}</td>
              <td>${s.correct_count}/${s.questions_count}</td>
              <td><span class="badge ${pct >= 60 ? 'badge-success' : pct >= 35 ? 'badge-warning' : 'badge-danger'}">${pct}%</span></td>
              <td class="${s.mastery_delta >= 0 ? 'text-success' : 'text-danger'}" style="font-weight:600">${s.mastery_delta >= 0 ? '+' : ''}${s.mastery_delta.toFixed(1)}</td>
              <td><button class="btn btn-xs btn-ghost" onclick="generateTestReport('${id}', '${s.id}')">Report</button></td>
            </tr>`;
          }).join('')}</tbody>
        </table>
      </div>
    </div>` : '';

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3 flex-wrap gap-1">
      <h2>${student.name}</h2>
      <div class="flex gap-1">
        <button class="btn btn-primary btn-sm" onclick="navigate('#practice')">Practice</button>
        <button class="btn btn-success btn-sm" onclick="navigate('#assessment')">Assess</button>
        <button class="btn btn-ghost btn-sm" onclick="navigate('#diagnosis/${id}')">Diagnosis</button>
        <button class="btn btn-ghost btn-sm" onclick="navigate('#analytics/${id}')">Analytics</button>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card text-center">
          ${scoreRing(overallScore, 120)}
          <p class="mt-2 text-dim" style="font-size:0.84rem">${student.grade} | ${student.board} | ${student.exam_target || 'No target'}</p>
          <p class="text-dim" style="font-size:0.78rem">${student.language} | ${student.id.slice(0,8)}</p>
        </div>
        <div class="card">
          <div class="card-header">Mastery by Subject</div>
          ${mastery && mastery.subject_breakdown ? Object.entries(mastery.subject_breakdown).map(([subj, score]) => {
            const c = scoreClass(score);
            return `<div class="mb-2">
              <div class="flex justify-between" style="font-size:0.82rem;margin-bottom:0.2rem"><span style="text-transform:capitalize">${subj}</span><span>${fmtPct(score)}%</span></div>
              <div class="progress"><div class="progress-bar ${c}" style="width:${score}%"></div></div>
            </div>`;
          }).join('') : '<p class="text-dim">No data</p>'}
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Weak Topics</div>
          ${mastery ? mastery.weak_topics.slice(0, 8).map(w =>
            `<div class="flex items-center justify-between" style="padding:0.3rem 0;border-bottom:1px solid var(--border-light);font-size:0.84rem">
              <span>${w.subtopic} (${w.subject})</span>
              <div class="flex items-center gap-2"><div class="progress" style="width:50px"><div class="progress-bar danger" style="width:${w.score}%"></div></div><span style="font-weight:600;color:var(--danger)">${fmtPct(w.score)}</span></div>
            </div>`).join('') : '<p class="text-dim">No weak topics identified</p>'}
        </div>
        <div class="card">
          <div class="card-header">Recent Sessions (${sessions.length})</div>
          <div style="max-height:200px;overflow-y:auto">
            ${sessions.length ? sessions.slice(0, 8).map(s =>
              `<div class="session-item">
                <div class="flex justify-between">
                  <span class="session-type" style="text-transform:capitalize">${s.session_type}</span>
                  <span class="badge ${(s.questions_count ? Math.round(s.correct_count / s.questions_count * 100) : 0) >= 60 ? 'badge-success' : 'badge-warning'}">${s.questions_count ? Math.round(s.correct_count / s.questions_count * 100) : 0}%</span>
                </div>
                <div class="session-meta">${s.started_at ? new Date(s.started_at).toLocaleDateString() : ''}${s.ended_at ? ' - completed' : ' - active'}</div>
              </div>`
            ).join('') : '<p class="text-dim">No sessions yet</p>'}
          </div>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col">
        ${assessHtml}
      </div>
      ${practice_sessions.length ? `
      <div class="col">
        <div class="card">
          <div class="card-header">Practice Sessions <span class="badge badge-info">${practice_sessions.length}</span></div>
          <div class="table-wrap">
            <table class="table table-condensed">
              <thead><tr><th>Date</th><th>Score</th><th>Mastery Δ</th></tr></thead>
              <tbody>${practice_sessions.slice(0, 8).map(s => {
                const pct = s.questions_count > 0 ? Math.round(s.correct_count/s.questions_count*100) : 0;
                return `<tr><td>${new Date(s.started_at).toLocaleDateString()}</td><td>${s.correct_count}/${s.questions_count} (${pct}%)</td><td class="${s.mastery_delta >= 0 ? 'text-success' : 'text-danger'}">${s.mastery_delta >= 0 ? '+' : ''}${s.mastery_delta.toFixed(1)}</td></tr>`;
              }).join('')}</tbody>
            </table>
          </div>
        </div>
      </div>` : ''}
    </div>`;
}

async function generateTestReport(studentId, sessionId) {
  if (!sessionId) { alert('No assessment sessions available to generate report.'); return; }
  try {
    const response = await API.generateReport(studentId, sessionId);
    if (response.html) {
      const w = window.open('', '_blank');
      w.document.write(response.html);
      w.document.close();
    }
  } catch(e) {
    alert('Failed to generate report: ' + e.message);
  }
}

// ── QUESTIONS ──
async function renderQuestions() {
  const el = document.getElementById('page-questions');
  const [appQs, testQs] = await Promise.all([API.listAppQuestions(), API.listTestQuestions()]);
  el.innerHTML = `<h2 class="mb-3">Question Bank</h2>
    <div class="tabs" id="qTabs">
      <div class="tab active" onclick="switchQTab('app', this)">Practice (${appQs.length})</div>
      <div class="tab" onclick="switchQTab('test', this)">Test (${testQs.length})</div>
    </div>
    <div id="qList">${renderQList(appQs, 'app')}</div>`;
  window._appQs = appQs; window._testQs = testQs;
}

function switchQTab(type, tabEl) {
  document.querySelectorAll('#qTabs .tab').forEach(t => t.classList.remove('active'));
  tabEl.classList.add('active');
  document.getElementById('qList').innerHTML = renderQList(type === 'app' ? window._appQs : window._testQs, type);
}

function renderQList(questions, type) {
  if (!questions || !questions.length) return '<div class="alert alert-info">No questions found</div>';
  return questions.map((q, i) => `<div class="question-card">
    <div class="q-text">${i+1}. ${q.question_text}</div>
    <div class="q-meta">
      <span class="badge badge-primary">${q.subject}</span>
      <span class="badge badge-info">${q.topic}</span>
      <span class="badge badge-warning">${q.subtopic}</span>
      <span class="badge ${q.difficulty <= 2 ? 'badge-success' : q.difficulty <= 3 ? 'badge-warning' : 'badge-danger'}">Lvl ${q.difficulty}</span>
      ${type === 'test' ? `<span class="badge badge-neutral">${q.year || ''} ${q.exam_type || ''}</span>` : ''}
    </div>
    ${q.options ? `<details style="margin-top:8px"><summary style="cursor:pointer;font-size:0.8rem;color:var(--on-surface-variant)">View Options</summary><div style="margin-top:6px;padding:8px;background:var(--surface-container);border-radius:6px;font-size:0.82rem">${Object.entries(q.options).map(([k,v]) => `<div><strong>${k}.</strong> ${v}</div>`).join('')}</div></details>` : ''}
  </div>`).join('');
}

// ── PRACTICE ──
async function renderPractice() {
  const el = document.getElementById('page-practice');
  const students = state.students.length ? state.students : await API.listStudents();
  state.students = students;
  const sid = state.selectedStudentId || (students[0] && students[0].id) || '';
  const mastery = sid ? await API.getMastery(sid) : null;
  const weakTopics = mastery ? mastery.weak_topics || [] : [];
  const studentOpts = students.map(s => `<option value="${s.id}" ${s.id === sid ? 'selected' : ''}>${s.name}</option>`).join('');
  const weakOpts = weakTopics.map(w => `<option value="${w.subtopic}">${w.subtopic} (${w.subject}) — ${fmtPct(w.score)}%</option>`).join('');

  el.innerHTML = `<h2 class="mb-3">Practice Session</h2>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">Configure Practice</div>
          <div class="form-group"><label class="form-label">Student</label><select class="form-control" id="pStudent" onchange="updatePracticeTopics()">${studentOpts}</select></div>
          <div class="form-group"><label class="form-label">Focus Concept</label><select class="form-control" id="pConcept">${weakOpts || '<option value="">Select a concept</option>'}<option value="kinematics">Kinematics</option><option value="newtons-laws">Newton\'s Laws</option><option value="electrostatics">Electrostatics</option><option value="differentiation">Differentiation</option><option value="integration">Integration</option><option value="chemical-bonding">Chemical Bonding</option><option value="organic-chemistry">Organic Chemistry</option></select></div>
          <div class="form-group"><label class="form-label">Error Category</label><select class="form-control" id="pError"><option value="concept_misunderstood">Concept Misunderstood</option><option value="formula_recall_failure">Formula Recall Failure</option><option value="calculation_error">Calculation Error</option><option value="misread_question">Misread Question</option><option value="guessing">Guessing</option></select></div>
          <div class="form-group"><label class="form-label">Questions</label><select class="form-control" id="pCount"><option value="3">3</option><option value="5" selected>5</option><option value="8">8</option><option value="10">10</option></select></div>
          <button class="btn btn-primary btn-block" onclick="startPractice()">Start Practice</button>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">How it works</div>
          <ul style="padding-left:1.2rem;color:var(--on-surface-variant);font-size:0.84rem;line-height:1.8">
            <li>Adaptive questions target your identified weak areas</li>
            <li>AI diagnosis classifies mistakes into 7 categories</li>
            <li>Real-time mastery updates after each session</li>
            <li>Focus on one concept at a time for best results</li>
          </ul>
        </div>
      </div>
    </div>`;
}

async function updatePracticeTopics() {
  const sid = document.getElementById('pStudent').value;
  state.selectedStudentId = sid;
  try {
    const mastery = await API.getMastery(sid);
    const weakTopics = mastery.weak_topics || [];
    const sel = document.getElementById('pConcept');
    const html = weakTopics.map(w => `<option value="${w.subtopic}">${w.subtopic} (${w.subject}) — ${fmtPct(w.score)}%</option>`).join('');
    if (html) sel.innerHTML = html + '<option value="">Other concept...</option>';
  } catch {}
}

async function startPractice() {
  const studentId = document.getElementById('pStudent').value;
  const concept = document.getElementById('pConcept').value;
  const errorCategory = document.getElementById('pError').value;
  const qCount = parseInt(document.getElementById('pCount').value);
  try {
    const session = await API.startSession({ student_id: studentId, session_type: 'practice' });
    state.currentSessionId = session.id;
    const practice = await API.generatePractice({ student_id: studentId, session_id: session.id, target_concept: concept, error_category: errorCategory, question_count: qCount });
    state.practiceQuestions = practice.questions;
    state.practiceSessionId = practice.practice_session_id;
    state.practiceStudentId = studentId;
    state.practiceConcept = concept;
    navigate(`#practice/${practice.practice_session_id}`);
  } catch (e) { alert('Error: ' + e.message); }
}

async function renderPracticeSession(sessionId) {
  const el = document.getElementById('page-practice');
  const questions = state.practiceQuestions || [];
  if (!questions.length) { navigate('#practice'); return; }

  let currentIdx = 0;
  const answers = [];
  let startTime = Date.now();

  function renderQ() {
    const q = questions[currentIdx];
    const progress = (currentIdx / questions.length * 100);
    const opts = q.options ? Object.entries(q.options).map(([k, v]) =>
      `<button class="option-btn" data-opt="${k}" onclick="selectPracticeOpt(this, '${k}')"><span class="option-label">${k}.</span> ${v}</button>`).join('') : '';

    el.innerHTML = `
      <div class="flex items-center justify-between mb-2 flex-wrap gap-1">
        <h2 style="font-size:1.15rem">Practice: ${state.practiceConcept || ''}</h2>
        <span class="badge badge-primary">${currentIdx + 1} / ${questions.length}</span>
      </div>
      <div class="progress mb-3"><div class="progress-bar primary" style="width:${progress}%"></div></div>
      <div class="card">
        <div class="q-text">${q.question_text}</div>
        <div class="q-meta"><span class="badge badge-info">Lvl ${q.difficulty}/5</span><span class="badge badge-primary">${q.concept_reference || ''}</span></div>
        <div id="practiceOpts">${opts}</div>
        <div class="flex items-center justify-between mt-2">
          <button class="btn btn-ghost btn-sm" onclick="getPracticeHint(${q.id})">Hint</button>
          <div id="hintArea"></div>
          <button class="btn btn-primary" id="nextBtn" onclick="submitPracticeAnswer(${q.id}, '${q.concept_reference || ''}', ${q.difficulty})">${currentIdx === questions.length - 1 ? 'Finish' : 'Next'}</button>
        </div>
      </div>`;
    window._practiceState = { answers, currentIdx, questions, startTime, sessionId };
  }
  renderQ();
}

function selectPracticeOpt(el, opt) {
  document.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
  window._selectedOpt = opt;
}

async function getPracticeHint(qId) {
  try {
    const hint = await API.getHint(qId);
    document.getElementById('hintArea').innerHTML = `<div class="hint-box">${hint.hint || hint}</div>`;
  } catch {}
}

async function submitPracticeAnswer(qId, conceptRef, difficulty) {
  const opt = window._selectedOpt || '';
  const ps = window._practiceState;
  if (!ps) return;
  const timeSec = (Date.now() - ps.startTime) / 1000;
  const q = ps.questions[ps.currentIdx];
  const isCorrect = opt === q.correct_answer;
  ps.answers.push({ question_id: qId, subtopic: conceptRef || state.practiceConcept || '', subject: '', topic: '', is_correct: isCorrect, response_time_seconds: timeSec, hints_used: document.getElementById('hintArea').innerHTML ? 1 : 0, retry_count: 0, is_recurrence: false });
  window._selectedOpt = null;

  const correct = q.correct_answer;
  const opts = q.options ? Object.entries(q.options).map(([k, v]) => {
    let cls = 'option-btn';
    if (k === correct) cls += ' correct';
    else if (k === opt && k !== correct) cls += ' wrong';
    if (k === opt) cls += ' selected';
    return `<div class="${cls}"><span class="option-label">${k}.</span> ${v}${k === correct ? ' <span style="float:right;font-size:0.7rem;color:var(--secondary)">Correct</span>' : ''}</div>`;
  }).join('') : '';

  el.innerHTML = `
    <div class="flex items-center justify-between mb-2">
      <h2 style="font-size:1.15rem">Practice: ${state.practiceConcept || ''}</h2>
      <span class="badge ${isCorrect ? 'badge-success' : 'badge-danger'}">${isCorrect ? 'Correct' : 'Incorrect'}</span>
    </div>
    <div class="card">
      <div class="q-text">${q.question_text}</div>
      <div style="margin-bottom:0.75rem">${opts}</div>
      <div class="hint-box" style="margin-top:0">
        <div style="font-weight:600;font-size:0.84rem;margin-bottom:0.25rem">Explanation</div>
        <div style="font-size:0.84rem;color:var(--on-surface-variant);line-height:1.6">${q.explanation || 'No explanation available.'}</div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:0.75rem">
        <button class="btn btn-primary" onclick="continuePractice()">${ps.currentIdx + 1 >= ps.questions.length ? 'View Results' : 'Next Question'}</button>
      </div>
    </div>`;
}

window.continuePractice = function() {
  const ps = window._practiceState;
  if (!ps) return;
  ps.currentIdx++;
  window._practiceState.startTime = Date.now();
  if (ps.currentIdx >= ps.questions.length) finishPractice(ps.answers, ps.sessionId);
  else renderPracticeSession(ps.sessionId);
};

async function finishPractice(answers, sessionId) {
  try {
    await API.endSession(sessionId);
    const r = await API.submitPracticeResult(sessionId, { student_id: state.practiceStudentId, attempts: answers });
    state.lastPracticeResult = r;
    navigate(`#practice-results/${sessionId}`);
  } catch (e) { alert('Error: ' + e.message); }
}

async function renderPracticeResults(sessionId) {
  const el = document.getElementById('page-practice');
  const r = state.lastPracticeResult;
  if (!r) { navigate('#practice'); return; }
  const correct = r.attempts.filter(a => a.is_correct).length;
  const total = r.attempts.length;
  const pct = total ? Math.round(correct / total * 100) : 0;
  const avgTime = total ? r.attempts.reduce((a, b) => a + b.response_time_seconds, 0) / total : 0;

  el.innerHTML = `
    <h2 class="mb-3">Practice Complete</h2>
    <div class="row">
      <div class="col col-2">
        <div class="card text-center">
          ${scoreRing(pct, 120)}
          <p class="mt-2" style="font-weight:600">${correct}/${total} Correct</p>
          <p class="text-dim">Avg Time: ${avgTime.toFixed(0)}s/question</p>
          <p class="text-dim">Mastery Change: <span style="color:${r.mastery_delta >= 0 ? 'var(--secondary)' : 'var(--danger)'}">${r.mastery_delta >= 0 ? '+' : ''}${r.mastery_delta.toFixed(1)}</span></p>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Attempts</div>
          <div class="table-wrap">
            <table class="table table-condensed">
              <thead><tr><th>#</th><th>Result</th><th>Time</th><th>Hints</th></tr></thead>
              <tbody>${r.attempts.map((a, i) => `<tr>
                <td>Q${i+1}</td>
                <td><span class="badge ${a.is_correct ? 'badge-success' : 'badge-danger'}">${a.is_correct ? 'Correct' : 'Wrong'}</span></td>
                <td class="text-dim">${a.response_time_seconds.toFixed(0)}s</td>
                <td class="text-dim">${a.hints_used || 0}</td>
              </tr>`).join('')}</tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    <div class="flex justify-center gap-1 mt-2">
      <button class="btn btn-primary" onclick="navigate('#practice')">Practice Again</button>
      <button class="btn btn-ghost" onclick="navigate('#dashboard')">Dashboard</button>
    </div>`;
}

// ── ASSESSMENT ──
async function renderAssessment() {
  const el = document.getElementById('page-assessment');
  const students = state.students.length ? state.students : await API.listStudents();
  state.students = students;
  const sid = state.selectedStudentId || (students[0] && students[0].id) || '';
  const studentOpts = students.map(s => `<option value="${s.id}" ${s.id === sid ? 'selected' : ''}>${s.name}</option>`).join('');

  el.innerHTML = `<h2 class="mb-3">Assessment</h2>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">Create Assessment</div>
          <div class="form-group"><label class="form-label">Student</label><select class="form-control" id="aStudent">${studentOpts}</select></div>
          <div class="form-group"><label class="form-label">Subject</label><select class="form-control" id="aSubject"><option value="physics">Physics</option><option value="chemistry">Chemistry</option><option value="mathematics">Mathematics</option></select></div>
          <div class="form-group"><label class="form-label">Topic <span class="text-dim" style="font-weight:400">(optional)</span></label><select class="form-control" id="aTopic"><option value="">All topics</option><option value="mechanics">Mechanics</option><option value="electrostatics">Electrostatics</option><option value="optics">Optics</option><option value="calculus">Calculus</option><option value="algebra">Algebra</option><option value="coordinate_geometry">Coordinate Geometry</option><option value="physical_chemistry">Physical Chemistry</option><option value="organic_chemistry">Organic Chemistry</option><option value="inorganic_chemistry">Inorganic Chemistry</option></select></div>
          <button class="btn btn-success btn-block" onclick="startAssessment()">Start Assessment</button>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Guidelines</div>
          <ul style="padding-left:1.2rem;color:var(--on-surface-variant);font-size:0.84rem;line-height:1.8">
            <li>JEE-level questions from the test bank</li>
            <li>Auto-selected by subject and topic</li>
            <li>60-minute timer, topic-wise results</li>
            <li>Mistakes diagnosed automatically</li>
          </ul>
        </div>
      </div>
    </div>`;
}

async function startAssessment() {
  const studentId = document.getElementById('aStudent').value;
  const subject = document.getElementById('aSubject').value;
  const topic = document.getElementById('aTopic').value;
  try {
    const body = { student_id: studentId, subject };
    if (topic) body.topic = topic;
    const assessment = await API.createAssessment(body);
    state.assessmentId = assessment.id;
    state.assessmentQuestions = assessment.questions || [];
    navigate(`#assessment/${assessment.id}`);
  } catch (e) { alert('Error: ' + e.message); }
}

async function renderAssessmentDetail(id) {
  const el = document.getElementById('page-assessment');
  const assessment = await API.getAssessment(id);
  const questions = state.assessmentQuestions || assessment.questions || [];

  if (assessment.status === 'completed') { renderAssessmentResults(id, assessment); return; }

  let queue = questions.map((q, i) => ({ ...q, _idx: i }));
  let correctCount = 0;
  let totalAttempted = 0;
  let currentIdx = 0;
  const startTime = Date.now();
  const timeLimit = 60;
  let timerInterval;
  let answered = false;

  function renderQ() {
    const q = queue[currentIdx];
    if (!q) { finishAssessment(); return; }
    const opts = q.options ? Object.entries(q.options).map(([k, v]) =>
      `<button class="option-btn" data-opt="${k}" onclick="selectAssessOpt(this)"><span class="option-label">${k}.</span> ${v}</button>`).join('') : '';

    let timerDisplay = '';
    if (currentIdx === 0 && !timerInterval) {
      const endTime = startTime + timeLimit * 60000;
      timerDisplay = `<span class="assessment-timer" id="timerDisplay">${timeLimit}:00</span>`;
      timerInterval = setInterval(() => {
        const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
        const t = document.getElementById('timerDisplay');
        if (t) t.textContent = `${Math.floor(remaining/60)}:${(remaining%60).toString().padStart(2,'0')}`;
        if (remaining <= 0) { clearInterval(timerInterval); finishAssessment(); }
      }, 1000);
    }

    answered = false;
    el.innerHTML = `
      <div class="flex items-center justify-between mb-2 flex-wrap gap-1">
        <h2 style="font-size:1.15rem">Assessment: ${assessment.subject}</h2>
        ${timerDisplay}
        <div class="flex gap-1">
          <span class="badge badge-success">${correctCount} correct</span>
          <span class="badge badge-primary">${queue.length} remaining</span>
        </div>
      </div>
      <div class="card">
        <div class="q-text">${q.question_text}</div>
        <div class="q-meta"><span class="badge badge-info">Lvl ${q.difficulty}/5</span><span class="badge badge-primary">${q.subject} / ${q.topic}</span></div>
        <div id="assessOpts">${opts}</div>
        <div id="assessFeedback" class="mt-2"></div>
        <div class="flex justify-between mt-2">
          <button class="btn btn-primary" id="submitAnsBtn" onclick="submitAssessmentAnswer('${id}')">Submit Answer</button>
        </div>
      </div>`;
    window._assessState = { queue, currentIdx, correctCount, totalAttempted, startTime, id, assessment, timerInterval };
  }

  window.selectAssessOpt = function(el) {
    document.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
    el.classList.add('selected');
  };

  window.submitAssessmentAnswer = async function(aid) {
    const selected = document.querySelector('.option-btn.selected');
    if (!selected) { document.getElementById('assessFeedback').innerHTML = '<div class="alert alert-warning">Please select an option first.</div>'; return; }
    if (answered) return;
    answered = true;

    const as = window._assessState;
    const q = as.queue[as.currentIdx];
    const chosen = selected.dataset.opt;
    const isCorrect = chosen === q.correct_answer;
    as.totalAttempted++;

    // Submit to backend
    try { await API.submitAnswer(aid, { question_id: q.id, student_answer: chosen || '' }); } catch {}

    // Show feedback with correct answer highlighted
    const opts = q.options ? Object.entries(q.options).map(([k, v]) => {
      let cls = 'option-btn';
      if (k === q.correct_answer) cls += ' correct';
      else if (k === chosen && k !== q.correct_answer) cls += ' wrong';
      if (k === chosen) cls += ' selected';
      return `<div class="${cls}"><span class="option-label">${k}.</span> ${v}${k === q.correct_answer ? ' <span style="float:right;font-size:0.7rem;color:var(--secondary)">Correct</span>' : ''}</div>`;
    }).join('') : '';

    if (isCorrect) {
      as.correctCount++;
      as.queue.splice(as.currentIdx, 1);
    } else {
      const reQueue = as.queue.splice(as.currentIdx, 1)[0];
      as.queue.push(reQueue);
    }

    document.getElementById('assessOpts').innerHTML = opts;
    document.getElementById('submitAnsBtn').remove();
    document.getElementById('assessFeedback').innerHTML = `
      <div class="hint-box" style="margin-top:0.5rem">
        <div style="font-weight:600;font-size:0.84rem;margin-bottom:0.25rem;color:${isCorrect ? 'var(--secondary)' : 'var(--danger)'}">${isCorrect ? 'Correct!' : 'Incorrect'}</div>
        <div style="font-size:0.84rem;color:var(--on-surface-variant);line-height:1.6">${q.explanation || 'No explanation available.'}</div>
      </div>
      <div style="margin-top:0.75rem;display:flex;justify-content:flex-end">
        <button class="btn btn-primary" onclick="nextAssessmentQ()">${as.queue.length === 0 ? 'View Results' : 'Next Question ->'}</button>
      </div>`;

    window._assessState = as;
  };

  window.nextAssessmentQ = function() {
    const as = window._assessState;
    if (!as) return;
    if (as.queue.length === 0) { finishAssessment(); return; }
    if (as.currentIdx >= as.queue.length) as.currentIdx = 0;
    renderQ();
  };

  async function finishAssessment() {
    clearInterval(window._assessState?.timerInterval);
    const as = window._assessState;
    if (!as) return;
    try { await API.completeAssessment(as.id); } catch {}
    const result = { total_questions: as.totalAttempted, correct: as.correctCount, incorrect: as.totalAttempted - as.correctCount, score_percentage: as.totalAttempted ? Math.round(as.correctCount / as.totalAttempted * 100) : 0, topic_breakdown: {} };
    state.lastAssessmentResult = result;
    renderAssessmentResults(as.id, result);
  }

  renderQ();
}

async function renderAssessmentResults(id, data) {
  const el = document.getElementById('page-assessment');
  const r = data.results || data;
  const total = r.total_questions || data.total_questions || 0;
  const correct = r.correct || data.correct || 0;
  const score = r.score_percentage || data.score_percentage || 0;
  const topicBreakdown = r.topic_breakdown || data.topic_breakdown || {};

  clearInterval(window._assessState?.timerInterval);

  const topicHtml = typeof topicBreakdown === 'object' && !Array.isArray(topicBreakdown)
    ? Object.entries(topicBreakdown).map(([topic, info]) => {
        const pct = typeof info === 'number' ? info : (info.correct / info.total * 100);
        return `<div class="mb-2">
          <div class="flex justify-between" style="font-size:0.82rem;margin-bottom:0.25rem"><span>${topic}</span><span>${fmtPct(pct)}%</span></div>
          <div class="progress"><div class="progress-bar ${scoreClass(pct)}" style="width:${pct}%"></div></div>
        </div>`;
      }).join('') : '<p class="text-dim">No breakdown available</p>';

  el.innerHTML = `
    <h2 class="mb-3">Assessment Complete</h2>
    <div class="row">
      <div class="col col-2">
        <div class="card text-center">
          ${scoreRing(score, 120)}
          <p class="mt-2" style="font-weight:600">${correct} / ${total} correct</p>
          <p class="text-dim">${total - correct} incorrect</p>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Topic Breakdown</div>
          ${topicHtml}
        </div>
      </div>
    </div>
    <div class="flex justify-center gap-1 mt-2">
      <button class="btn btn-success" onclick="navigate('#assessment')">New Assessment</button>
      <button class="btn btn-ghost" onclick="navigate('#dashboard')">Dashboard</button>
    </div>`;
}


// ── DIAGNOSIS ──
async function renderDiagnosis(studentId) {
  const el = document.getElementById('page-diagnosis');
  const sid = studentId || state.selectedStudentId || '';
  if (!sid) { el.innerHTML = '<div class="alert alert-warning">Select a student first</div>'; return; }

  const [history, patterns, mastery] = await Promise.all([
    API.getMistakeHistory(sid, 50).catch(() => []),
    API.getRecurringPatterns(sid).catch(() => []),
    API.getMastery(sid).catch(() => null),
  ]);
  const weakTopics = mastery ? mastery.weak_topics || [] : [];

  // Count by error category
  const catCount = {};
  history.forEach(h => { const c = h.error_category || 'unknown'; catCount[c] = (catCount[c] || 0) + 1; });
  const catHtml = Object.entries(catCount).sort((a,b) => b[1]-a[1]).slice(0, 5).map(([cat, count]) => {
    const pct = history.length ? Math.round(count/history.length*100) : 0;
    return `<div class="mb-2">
      <div class="flex justify-between" style="font-size:0.82rem;margin-bottom:0.25rem"><span style="text-transform:capitalize">${cat.replace(/_/g,' ')}</span><span>${count} (${pct}%)</span></div>
      <div class="progress"><div class="progress-bar danger" style="width:${pct}%"></div></div>
    </div>`;
  }).join('');

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>Mistake Diagnosis</h2>
      <div class="flex gap-1">
        <select class="form-control student-selector" onchange="navigate('#diagnosis/'+this.value)">
          <option value="">Switch Student</option>
          ${state.students.map(s => `<option value="${s.id}" ${s.id===sid?'selected':''}>${s.name}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">Error Distribution</div>
          ${catHtml || '<p class="text-dim">No mistakes recorded</p>'}
        </div>
        <div class="card">
          <div class="card-header">Recurring Patterns</div>
          ${patterns.length ? patterns.map(p => `
            <div class="flex items-center justify-between" style="padding:0.5rem 0;border-bottom:1px solid var(--border-light)">
              <div><span class="badge badge-danger">${p.error_category || p.error_type || 'unknown'}</span><span class="text-dim" style="font-size:0.8rem"> ${(p.common_concepts || []).join(', ')}</span></div>
              <span class="badge badge-warning">${p.count || 0}x</span>
            </div>`).join('') : '<p class="text-dim">No recurring patterns found</p>'}
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Weak Topics</div>
          ${weakTopics.slice(0, 10).map(w => `
            <div class="flex items-center justify-between" style="padding:0.35rem 0;border-bottom:1px solid var(--border-light)">
              <span style="font-size:0.84rem">${w.subtopic} (${w.subject})</span>
              <div class="flex items-center gap-2"><div class="progress" style="width:50px"><div class="progress-bar danger" style="width:${w.score}%"></div></div><span style="font-weight:600;color:var(--danger)">${fmtPct(w.score)}</span></div>
            </div>`).join('') || '<p class="text-dim">No weak topics</p>'}
          ${weakTopics.length > 10 ? `<p class="text-dim mt-1">+ ${weakTopics.length - 10} more</p>` : ''}
        </div>
        <div class="card">
          <div class="card-header">Mistake History</div>
          <div style="max-height:350px;overflow-y:auto">
            ${history.length ? history.slice(0, 30).map(h => `
              <div class="flex items-center justify-between" style="padding:0.35rem 0;border-bottom:1px solid var(--border-light);font-size:0.82rem">
                <div><span class="badge badge-danger" style="font-size:0.66rem">${h.error_category}</span><span class="text-dim"> ${h.concept_tag || ''}</span></div>
                <span class="text-dim" style="font-size:0.7rem">${h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}</span>
              </div>`).join('') : '<p class="text-dim">No mistake history yet. Complete some practice sessions.</p>'}
          </div>
        </div>
      </div>
    </div>`;
}

// ── ANALYTICS ──
async function renderAnalytics(studentId) {
  const el = document.getElementById('page-analytics');
  const sid = studentId || state.selectedStudentId || '';
  if (!sid) { el.innerHTML = '<div class="alert alert-warning">Select a student first</div>'; return; }

  const [analytics, mastery, sessions] = await Promise.all([
    API.getStudentAnalytics(sid).catch(() => null),
    API.getMastery(sid).catch(() => null),
    API.getStudentSessions(sid).catch(() => []),
  ]);

  if (!analytics) {
    el.innerHTML = `<div class="alert alert-warning">No analytics data available yet. Complete some sessions first.</div>`;
    return;
  }

  // Trend data from sessions
  const sortedSessions = (sessions || []).filter(s => s.ended_at).sort((a,b) => new Date(a.started_at) - new Date(b.started_at));
  const trendPoints = sortedSessions.slice(-20).map(s => {
    const pct = s.questions_count > 0 ? Math.round(s.correct_count/s.questions_count*100) : 0;
    return { date: new Date(s.started_at).toLocaleDateString(), score: pct, mastery: s.mastery_delta || 0 };
  });
  const trendHtml = trendPoints.length ? trendPoints.map((p, i) =>
    `<div class="flex items-center justify-between" style="font-size:0.78rem;padding:0.2rem 0;border-bottom:1px solid var(--border-light)">
      <span class="text-dim">${p.date}</span>
      <span><span class="badge ${p.score >= 60 ? 'badge-success' : 'badge-warning'}">${p.score}%</span> <span class="${p.mastery >= 0 ? 'text-success' : 'text-danger'}">${p.mastery >= 0 ? '+' : ''}${p.mastery.toFixed(1)}</span></span>
    </div>`).join('') : '<p class="text-dim">Not enough data</p>';

  const weakStr = Array.isArray(analytics.weak_topics) ? analytics.weak_topics.join(', ') : 'None identified';
  const strongStr = Array.isArray(analytics.strengths) ? analytics.strengths.join(', ') : 'None identified';

  // Mastery by subject trend
  const subjTrend = mastery && mastery.subject_breakdown ? Object.entries(mastery.subject_breakdown).map(([subj, score]) =>
    `<div class="stat-card"><div class="stat-value">${fmtPct(score)}%</div><div class="stat-label" style="text-transform:capitalize">${subj}</div></div>`
  ).join('') : '';

  // Compute consistency
  const today = new Date();
  const weeklySessions = sortedSessions.filter(s => (today - new Date(s.started_at)) < 7*24*60*60*1000).length;

  // Compute practice frequency
  const dailyCounts = {};
  sortedSessions.forEach(s => {
    const d = new Date(s.started_at).toLocaleDateString();
    dailyCounts[d] = (dailyCounts[d] || 0) + 1;
  });

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3 flex-wrap gap-1">
      <h2>Analytics</h2>
      <select class="form-control student-selector" onchange="navigate('#analytics/'+this.value)">
        ${state.students.map(s => `<option value="${s.id}" ${s.id===sid?'selected':''}>${s.name}</option>`).join('')}
      </select>
    </div>

    <div class="row">
      <div class="col col-2">
        <div class="card">
          ${scoreRing(analytics.overall_mastery || 0, 100)}
          <div class="text-center mt-2">
            <p style="font-weight:600">Overall Mastery</p>
            <p class="text-dim" style="font-size:0.82rem">${weeklySessions} sessions this week</p>
          </div>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Weak Areas</div>
          <p class="text-dim">${weakStr}</p>
        </div>
        <div class="card">
          <div class="card-header">Strengths</div>
          <p class="text-dim">${strongStr}</p>
        </div>
      </div>
    </div>

    ${subjTrend ? `
    <div class="card">
      <div class="card-header">Mastery by Subject</div>
      <div class="stat-row">${subjTrend}</div>
    </div>` : ''}

    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">Score Trend</div>
          <div style="max-height:300px;overflow-y:auto">${trendHtml}</div>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Mistake Patterns</div>
          ${analytics.mistake_patterns && analytics.mistake_patterns.length
            ? analytics.mistake_patterns.map(p => `
              <div class="flex items-center justify-between" style="padding:0.5rem 0;border-bottom:1px solid var(--border-light)">
                <div><span class="badge badge-warning">${p.error_category.replace(/_/g,' ')}</span><span class="text-dim" style="font-size:0.8rem"> ${(p.common_concepts || []).join(', ')}</span></div>
                <span style="font-weight:600">${p.count}x <span class="text-dim">(${fmtPct(p.frequency_percent)}%)</span></span>
              </div>`).join('')
            : '<p class="text-dim">No mistake patterns yet</p>'}
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">Recommendation</div>
      <p class="text-dim">${analytics.practice_recommendation || 'Complete more practice to receive AI-powered recommendations.'}</p>
    </div>`;
}

// ── CONCEPT MAP ──
async function renderConcepts() {
  const el = document.getElementById('page-concepts');
  let graphData;
  try { graphData = await API.getFullGraph(); } catch {
    el.innerHTML = '<div class="alert alert-danger">Failed to load concept graph</div>'; return;
  }
  const nodes = graphData.nodes || [];
  const edges = graphData.edges || [];
  const subjects = [...new Set(nodes.map(n => n.subject))];
  const subjectTabs = subjects.map((s, i) => `<div class="tab ${i === 0 ? 'active' : ''}" onclick="filterConcepts(this, '${s}')">${s}</div>`).join('');

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>Concept Map</h2>
      <span class="text-dim" style="font-size:0.82rem">${nodes.length} concepts · ${edges.length} prerequisite links</span>
    </div>
    <div class="card" style="padding:0.75rem">
      <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-bottom:0.75rem">
        <input class="form-control" id="conceptSearch" placeholder="Search concepts..." oninput="filterConceptsByName(this.value)" style="max-width:300px">
      </div>
      <div class="tabs" id="conceptTabs">${subjectTabs}</div>
      <div id="conceptList" class="grid-auto"></div>
    </div>`;
  window._graphNodes = nodes;
  window._graphEdges = edges;
  filterConcepts(document.querySelector('#conceptTabs .tab'), subjects[0]);
}

function filterConcepts(tabEl, subject) {
  document.querySelectorAll('#conceptTabs .tab').forEach(t => t.classList.remove('active'));
  tabEl.classList.add('active');
  const nodes = window._graphNodes.filter(n => n.subject === subject);
  document.getElementById('conceptList').innerHTML = nodes.length
    ? nodes.map(n => `<div class="card" style="padding:0.75rem;margin:0">
        <div style="font-weight:600;font-size:0.85rem">${n.display_name || n.id}</div>
        <div class="text-dim" style="font-size:0.72rem;margin-top:2px">${n.topic} / ${n.subtopic}</div>
        <div style="margin-top:4px"><span class="badge badge-neutral">${n.difficulty ? 'Lvl '+n.difficulty : ''}</span></div>
      </div>`).join('')
    : '<p class="text-dim" style="padding:1rem;text-align:center">No concepts found in this subject</p>';
}

function filterConceptsByName(query) {
  const q = query.toLowerCase();
  const nodes = window._graphNodes.filter(n => (n.display_name || n.id).toLowerCase().includes(q) || (n.subtopic || '').toLowerCase().includes(q));
  const activeSubject = document.querySelector('#conceptTabs .tab.active');
  if (activeSubject) activeSubject.classList.remove('active');
  document.getElementById('conceptList').innerHTML = nodes.length
    ? nodes.map(n => `<div class="card" style="padding:0.75rem;margin:0">
        <div style="font-weight:600;font-size:0.85rem">${n.display_name || n.id}</div>
        <div class="text-dim" style="font-size:0.72rem;margin-top:2px">${n.subject} / ${n.topic}</div>
        <div style="margin-top:4px"><span class="badge badge-neutral">${n.difficulty ? 'Lvl '+n.difficulty : ''}</span></div>
      </div>`).join('')
    : '<p class="text-dim" style="padding:1rem;text-align:center">No concepts match your search</p>';
}

// ── MODAL / CREATE STUDENT ──
function showCreateStudent() {
  const overlay = document.getElementById('modalOverlay');
  overlay.innerHTML = `
    <div class="modal">
      <h3>Create Student</h3>
      <div class="form-group"><label class="form-label">Name</label><input class="form-control" id="sName" placeholder="Full name"></div>
      <div class="form-group"><label class="form-label">Grade</label><select class="form-control" id="sGrade"><option value="11">11</option><option value="12">12</option></select></div>
      <div class="form-group"><label class="form-label">Board</label><select class="form-control" id="sBoard"><option value="CBSE">CBSE</option><option value="ICSE">ICSE</option><option value="State Board">State Board</option></select></div>
      <div class="form-group"><label class="form-label">Exam Target</label><select class="form-control" id="sTarget"><option value="JEE_Main">JEE Main</option><option value="JEE_Advanced">JEE Advanced</option></select></div>
      <div class="form-group"><label class="form-label">Language</label><select class="form-control" id="sLang"><option value="English">English</option><option value="Hindi">Hindi</option></select></div>
      <div class="flex justify-between mt-3">
        <button class="btn btn-ghost" onclick="closeModal()">Cancel</button>
        <button class="btn btn-primary" onclick="createStudent()">Create</button>
      </div>
    </div>`;
  overlay.classList.add('open');
}

function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

async function createStudent() {
  const name = document.getElementById('sName').value.trim();
  if (!name) { alert('Name is required'); return; }
  try {
    await API.createStudent({ name, grade: document.getElementById('sGrade').value, board: document.getElementById('sBoard').value, exam_target: document.getElementById('sTarget').value, language: document.getElementById('sLang').value });
    closeModal();
    navigate('#students');
  } catch (e) { alert('Error: ' + e.message); }
}

async function deleteStudent(id) {
  if (!confirm('Delete this student and all associated data?')) return;
  try {
    await API.deleteStudent(id);
    navigate('#students');
  } catch (e) { alert('Error: ' + e.message); }
}
