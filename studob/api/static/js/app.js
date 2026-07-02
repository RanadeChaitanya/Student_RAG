// ── STATE ──
const state = {
  student: null,
  currentView: 'dashboard',
  practiceQuestions: [],
  practiceSessionId: null,
  practiceStudentId: null,
  assessmentId: null,
  lastPracticeResult: null,
  lastAssessmentResult: null,
  _assessState: null,
};

// ── HELPERS ──
function fmtPct(v) { return Math.round(v || 0); }
function initials(name) { return (name || 'S').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase(); }
function scoreClass(v) { return v >= 70 ? 'success' : v >= 40 ? 'warning' : 'danger'; }
function fmtDate(d) {
  if (!d) return '';
  const date = new Date(d);
  const now = new Date();
  const diff = (now - date) / (1000 * 86400);
  if (diff < 1) return 'Today';
  if (diff < 2) return 'Yesterday';
  if (diff < 7) return `${Math.floor(diff)} days ago`;
  if (diff < 30) return `${Math.floor(diff / 7)} week${Math.floor(diff / 7) > 1 ? 's' : ''} ago`;
  return date.toLocaleDateString();
}

function scoreRing(pct, size, label) {
  const r2 = Math.round((size || 100) * 0.38);
  const circ2 = 2 * Math.PI * r2;
  const dash2 = Math.max(0, (pct / 100) * circ2);
  const cls = scoreClass(pct);
  const sz = size || 100;
  return `<div class="progress-circle" style="width:${sz}px;height:${sz}px">
    <svg width="${sz}" height="${sz}" viewBox="0 0 100 100">
      <circle class="bg" cx="50" cy="50" r="42"/>
      <circle class="fg ${cls}" cx="50" cy="50" r="42" stroke-dasharray="${dash2} ${circ2}"/>
    </svg>
    <span class="pv" style="font-size:${Math.round(sz*0.2)}px">${fmtPct(pct)}${label||'%'}</span>
  </div>`;
}

// ── NAVIGATION ──
function navigate(hash) {
  const page = hash.replace('#', '') || 'dashboard';
  state.currentView = page;
  renderPage(page);
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.dataset.nav === page.split('/')[0]);
  });
}

window.addEventListener('hashchange', () => navigate(window.location.hash));

// ── AUTH ──
async function handleLogin() {
  const name = document.getElementById('loginName').value.trim();
  const pin = document.getElementById('loginPin').value.trim() || '1234';
  const errEl = document.getElementById('loginError');
  if (!name) { errEl.textContent = 'Please enter your name'; errEl.style.display = 'block'; return; }
  errEl.style.display = 'none';
  try {
    const res = await API.login(name, pin);
    API.setToken(res.token);
    state.student = res.student;
    sessionStorage.setItem('studob_student', JSON.stringify(res.student));
    showApp();
  } catch (e) {
    errEl.textContent = e.message || 'Login failed';
    errEl.style.display = 'block';
  }
}

async function handleLogout() {
  try { await API.logout(); } catch {}
  API.setToken(null);
  state.student = null;
  sessionStorage.removeItem('studob_student');
  document.getElementById('app-shell').style.display = 'none';
  document.getElementById('login-page').style.display = 'flex';
  document.getElementById('loginName').value = '';
  document.getElementById('loginPin').value = '';
}

async function showApp() {
  document.getElementById('login-page').style.display = 'none';
  document.getElementById('app-shell').style.display = 'flex';
  if (state.student) {
    document.getElementById('profileAvatar').textContent = initials(state.student.name);
    document.getElementById('profileName').textContent = state.student.name;
    document.getElementById('profileGrade').textContent = `${state.student.grade} | ${state.student.exam_target || state.student.board}`;
  }
  navigate(window.location.hash || '#dashboard');
}

async function initApp() {
  const token = API.loadToken();
  if (token) {
    try {
      const res = await API.verifyToken();
      const stored = sessionStorage.getItem('studob_student');
      if (stored) state.student = JSON.parse(stored);
      showApp();
      return;
    } catch {
      API.setToken(null);
    }
  }
  document.getElementById('login-page').style.display = 'flex';
}

// ── PAGE ROUTER ──
async function renderPage(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const pageName = page.split('/')[0];
  const el = document.getElementById('page-' + pageName);
  if (!el) { renderDashboard(); return; }
  el.classList.add('active');
  el.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading...</p></div>';
  try {
    if (pageName === 'dashboard' || pageName === '') await renderDashboard();
    else if (pageName === 'practice') await renderPractice();
    else if (pageName === 'practice-session') await renderPracticeSession();
    else if (pageName === 'practice-results') await renderPracticeResults();
    else if (pageName === 'assessment') await renderAssessment();
    else if (pageName === 'concepts') await renderConcepts();
    else if (pageName === 'analytics') await renderAnalytics();
    else if (pageName === 'analytics-report') await renderAnalyticsReport(page.split('/')[1]);
    else renderDashboard();
  } catch (e) {
    el.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
  }
}

// ── MODULE 1: DASHBOARD ──
async function renderDashboard() {
  const el = document.getElementById('page-dashboard');
  const sid = state.student?.id;
  if (!sid) { el.innerHTML = '<div class="alert alert-warning">Please log in first</div>'; return; }

  const [mastery, sessions] = await Promise.all([
    API.getMastery(sid).catch(() => null),
    API.getStudentSessions(sid).catch(() => []),
  ]);

  const overall_score = mastery ? mastery.overall_score : 0;
  const weakList = mastery ? mastery.weak_topics || [] : [];
  const strongList = mastery ? mastery.strengths || [] : [];

  const assessments = (sessions || []).filter(s => s.session_type === 'assessment' && s.ended_at).slice(0, 5);

  const recommendedTopic = weakList.length > 0 ? weakList[0] : null;

  const subjectCards = mastery && mastery.subject_breakdown
    ? Object.entries(mastery.subject_breakdown).map(([subj, score]) =>
        `<div class="stat-card"><div class="stat-value">${fmtPct(score)}%</div><div class="stat-label" style="text-transform:capitalize">${subj}</div></div>`).join('')
    : '';

  el.innerHTML = `
    <div class="dash-header">
      <div>
        <h2>Welcome back, ${state.student?.name || 'Student'}</h2>
        <p class="text-dim" style="font-size:0.84rem">${state.student?.grade || ''} | ${state.student?.exam_target || state.student?.board || 'JEE Aspirant'}</p>
      </div>
      <button class="btn btn-primary" onclick="navigate('#practice')">Start Practice</button>
    </div>

    <div class="row mb-3">
      <div class="col col-2">
        <div class="card" style="display:flex;align-items:center;gap:var(--space-md);flex-wrap:wrap">
          ${scoreRing(overall_score, 100)}
          <div>
            <h3 style="margin-bottom:2px">Overall Mastery</h3>
            <p class="text-dim" style="font-size:0.84rem">${weakList.length} weak topics · ${strongList.length} strengths</p>
          </div>
        </div>
      </div>
      <div class="col">
        <div class="card" style="display:flex;align-items:center;gap:var(--space-md);flex-wrap:wrap">
          <div class="score-ring ${recommendedTopic ? 'warning' : 'success'}" style="width:56px;height:56px;font-size:0.9rem">
            ${recommendedTopic ? '!' : '✓'}
          </div>
          <div>
            <h4 style="margin-bottom:2px">${recommendedTopic ? `Study: ${recommendedTopic.subtopic}` : 'All caught up!'}</h4>
            <p class="text-dim" style="font-size:0.78rem">${recommendedTopic ? `${recommendedTopic.subject} · ${fmtPct(recommendedTopic.score)}% mastery` : 'Great progress this week'}</p>
          </div>
        </div>
      </div>
    </div>

    ${subjectCards ? `<div class="card"><div class="card-header">Subject Progress</div><div class="stat-row">${subjectCards}</div></div>` : ''}

    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">Recent Tests</div>
          ${assessments.length ? assessments.map(s => {
            const pct = s.questions_count > 0 ? Math.round(s.correct_count / s.questions_count * 100) : 0;
            return `<div class="test-card" onclick="navigate('#analytics-report/${s.id}')">
              <div class="test-card-top">
                <span class="test-name">${s.subject || 'Test'} Assessment</span>
                <span class="badge ${pct >= 60 ? 'badge-success' : pct >= 35 ? 'badge-warning' : 'badge-danger'}">${pct}%</span>
              </div>
              <div class="test-card-meta">
                <span>${s.correct_count}/${s.questions_count}</span>
                <span class="text-dim">${fmtDate(s.ended_at)}</span>
              </div>
              <button class="btn btn-xs btn-ghost test-view-btn">View →</button>
            </div>`;
          }).join('') : '<p class="text-dim">No tests completed yet. Start an assessment to see results here.</p>'}
          ${assessments.length > 0 ? `<button class="btn btn-ghost btn-sm btn-block mt-2" onclick="navigate('#analytics')">View All Reports →</button>` : ''}
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Weak Topics</div>
          ${weakList.slice(0, 5).map(w => `
            <div class="flex items-center justify-between" style="padding:0.4rem 0;border-bottom:1px solid var(--border-light)">
              <span style="font-size:0.84rem">${w.subtopic}</span>
              <div class="flex items-center gap-2">
                <div class="progress" style="width:60px"><div class="progress-bar danger" style="width:${w.score}%"></div></div>
                <span style="font-weight:600;color:var(--danger);font-size:0.84rem">${fmtPct(w.score)}</span>
              </div>
            </div>`).join('') || '<p class="text-dim">No weak topics identified</p>'}
        </div>
        <div class="card">
          <div class="card-header">Strengths</div>
          ${strongList.slice(0, 5).map(s => `
            <div class="flex items-center justify-between" style="padding:0.4rem 0;border-bottom:1px solid var(--border-light)">
              <span style="font-size:0.84rem">${s.subtopic}</span>
              <div class="flex items-center gap-2">
                <div class="progress" style="width:60px"><div class="progress-bar success" style="width:${s.score}%"></div></div>
                <span style="font-weight:600;color:var(--secondary);font-size:0.84rem">${fmtPct(s.score)}</span>
              </div>
            </div>`).join('') || '<p class="text-dim">No strengths identified yet</p>'}
        </div>
      </div>
    </div>`;
}

// ── MODULE 2: PRACTICE ──
async function renderPractice() {
  const el = document.getElementById('page-practice');
  const sid = state.student?.id;
  if (!sid) { el.innerHTML = '<div class="alert alert-warning">Please log in first</div>'; return; }

  const mastery = await API.getMastery(sid).catch(() => null);
  const weakTopics = mastery ? mastery.weak_topics || [] : [];

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>Practice</h2>
    </div>
    <div class="row">
      <div class="col col-2">
        <div class="card">
          <div class="card-header">Configure Session</div>
          <div class="form-group">
            <label class="form-label">Subject</label>
            <select class="form-control" id="pSubject">
              <option value="physics">Physics</option>
              <option value="chemistry">Chemistry</option>
              <option value="mathematics">Mathematics</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">Chapter</label>
            <select class="form-control" id="pTopic">
              <option value="">All Chapters</option>
              <option value="mechanics">Mechanics</option>
              <option value="electrostatics">Electrostatics</option>
              <option value="optics">Optics</option>
              <option value="calculus">Calculus</option>
              <option value="algebra">Algebra</option>
              <option value="coordinate_geometry">Coordinate Geometry</option>
              <option value="physical_chemistry">Physical Chemistry</option>
              <option value="organic_chemistry">Organic Chemistry</option>
              <option value="inorganic_chemistry">Inorganic Chemistry</option>
            </select>
          </div>
          <div class="row">
            <div class="col">
              <div class="form-group">
                <label class="form-label">Difficulty</label>
                <select class="form-control" id="pDifficulty">
                  <option value="0">All Levels</option>
                  <option value="1">Level 1 (Easy)</option>
                  <option value="2">Level 2</option>
                  <option value="3">Level 3 (Medium)</option>
                  <option value="4">Level 4</option>
                  <option value="5">Level 5 (Hard)</option>
                </select>
              </div>
            </div>
            <div class="col">
              <div class="form-group">
                <label class="form-label">Questions</label>
                <select class="form-control" id="pCount">
                  <option value="5">5</option>
                  <option value="10" selected>10</option>
                  <option value="20">20</option>
                  <option value="30">30</option>
                  <option value="50">50</option>
                </select>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Time Limit</label>
            <select class="form-control" id="pTime">
              <option value="0">Unlimited</option>
              <option value="15">15 Minutes</option>
              <option value="30" selected>30 Minutes</option>
              <option value="60">60 Minutes</option>
              <option value="90">90 Minutes</option>
            </select>
          </div>
          <div class="flex items-center justify-between" style="padding:0.5rem 0;border-bottom:1px solid var(--border-light);margin-bottom:0.75rem">
            <span style="font-size:0.84rem;font-weight:500">Personalized</span>
            <label class="toggle"><input type="checkbox" id="pPersonalized" checked><span class="toggle-slider"></span></label>
          </div>
          <div class="flex items-center justify-between" style="padding:0.5rem 0;border-bottom:1px solid var(--border-light);margin-bottom:0.75rem">
            <span style="font-size:0.84rem;font-weight:500">PYQ Only</span>
            <label class="toggle"><input type="checkbox" id="pPyqOnly"><span class="toggle-slider"></span></label>
          </div>
          <div class="flex items-center justify-between" style="padding:0.5rem 0;margin-bottom:0.75rem">
            <span style="font-size:0.84rem;font-weight:500">Challenge Mode</span>
            <label class="toggle"><input type="checkbox" id="pChallenge"><span class="toggle-slider"></span></label>
          </div>
          <button class="btn btn-primary btn-block" onclick="startPractice()">Start Practice</button>
        </div>
      </div>
      <div class="col">
        ${weakTopics.length > 0 ? `
        <div class="card">
          <div class="card-header">Recommended Focus</div>
          ${weakTopics.slice(0, 6).map(w => `
            <div class="flex items-center justify-between" style="padding:0.35rem 0;border-bottom:1px solid var(--border-light);font-size:0.84rem">
              <span>${w.subtopic} <span class="text-dim">(${w.subject})</span></span>
              <span class="badge badge-danger">${fmtPct(w.score)}%</span>
            </div>`).join('')}
          <p class="text-dim mt-2" style="font-size:0.78rem">Personalized mode uses your weak areas to select questions</p>
        </div>` : ''}
        <div class="card">
          <div class="card-header">How it works</div>
          <ul style="padding-left:1.2rem;color:var(--on-surface-variant);font-size:0.84rem;line-height:1.8">
            <li>Select subject, chapter, and difficulty level</li>
            <li>Toggle <strong>Personalized</strong> for adaptive questions</li>
            <li>Enable <strong>PYQ Only</strong> for past JEE questions</li>
            <li>Challenge Mode adds time pressure per question</li>
          </ul>
        </div>
      </div>
    </div>`;
}

async function startPractice() {
  const studentId = state.student.id;
  const subject = document.getElementById('pSubject').value;
  const topic = document.getElementById('pTopic').value;
  const difficulty = parseInt(document.getElementById('pDifficulty').value);
  const qCount = parseInt(document.getElementById('pCount').value);
  const personalized = document.getElementById('pPersonalized').checked;
  const pyqOnly = document.getElementById('pPyqOnly').checked;
  const challenge = document.getElementById('pChallenge').checked;

  state.practiceConfig = { subject, topic, difficulty, qCount, personalized, pyqOnly, challenge };

  try {
    const session = await API.startSession({ student_id: studentId, session_type: 'practice' });
    state.currentSessionId = session.id;

    const practice = await API.generatePractice({
      student_id: studentId,
      session_id: session.id,
      target_concept: topic || subject,
      question_count: qCount,
    });
    state.practiceQuestions = practice.questions || [];
    state.practiceSessionId = practice.practice_session_id || session.id;
    state.practiceStudentId = studentId;
    navigate('#practice-session');
  } catch (e) {
    alert('Error: ' + e.message);
  }
}

// ── PRACTICE SESSION ──
async function renderPracticeSession() {
  const el = document.getElementById('page-practice-session');
  const questions = state.practiceQuestions || [];
  if (!questions.length) { navigate('#practice'); return; }

  const config = state.practiceConfig || {};
  let currentIdx = 0;
  const answers = [];
  let startTime = Date.now();
  let timerInterval;
  const timeLimit = parseInt(config.time || '0');

  function renderQ() {
    const q = questions[currentIdx];
    const progress = (currentIdx / questions.length * 100);
    const opts = q.options ? Object.entries(q.options).map(([k, v]) =>
      `<button class="option-btn" data-opt="${k}" onclick="selectOpt(this, '${k}')"><span class="option-label">${k}.</span> ${v}</button>`).join('') : '';

    el.innerHTML = `
      <div class="flex items-center justify-between mb-2 flex-wrap gap-1">
        <div class="flex items-center gap-2">
          <button class="btn btn-ghost btn-sm" onclick="navigate('#practice')" style="padding:0.25rem 0.5rem">← Back</button>
          <h2 style="font-size:1.1rem">${config.subject || 'Practice'}</h2>
        </div>
        <div class="flex items-center gap-2">
          <span id="timerDisplay" class="assessment-timer"></span>
          <span class="badge badge-primary">Q${currentIdx + 1}/${questions.length}</span>
        </div>
      </div>
      <div class="progress mb-3"><div class="progress-bar primary" style="width:${progress}%"></div></div>
      <div class="card">
        <div class="q-meta" style="display:flex;gap:var(--space-sm);flex-wrap:wrap;margin-bottom:var(--space-sm)">
          <span class="badge badge-info">${q.topic || config.topic || config.subject || ''}</span>
          <span class="badge ${q.difficulty <= 2 ? 'badge-success' : q.difficulty <= 3 ? 'badge-warning' : 'badge-danger'}">Lvl ${q.difficulty}/5</span>
          ${q.year ? `<span class="badge badge-neutral">PYQ ${q.year}</span>` : ''}
        </div>
        <div class="q-text" style="font-size:1rem;margin-bottom:var(--space-md)">${q.question_text}</div>
        <div id="practiceOpts">${opts}</div>
        <div id="practiceFeedback" class="mt-2" style="display:none"></div>
        <div class="flex items-center justify-between mt-2">
          <button class="btn btn-ghost btn-sm" onclick="getPracticeHint(${q.id})">Hint</button>
          <div id="hintArea"></div>
          <button class="btn btn-primary" id="submitBtn" onclick="submitPracticeAnswer(${q.id})">${currentIdx === questions.length - 1 ? 'Finish' : 'Next'}</button>
        </div>
      </div>`;
    window._practiceState = { answers, currentIdx, questions, startTime, sessionId: state.currentSessionId };

    if (timeLimit > 0) {
      const endTime = Date.now() + timeLimit * 60000;
      if (!timerInterval) {
        timerInterval = setInterval(() => {
          const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
          const t = document.getElementById('timerDisplay');
          if (t) t.textContent = `${Math.floor(remaining/60)}:${(remaining%60).toString().padStart(2,'0')}`;
          if (remaining <= 0) { clearInterval(timerInterval); finishPractice(); }
        }, 1000);
      }
    }
  }
  renderQ();
}

window.selectOpt = function(el, opt) {
  document.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
  el.classList.add('selected');
  window._selectedOpt = opt;
};

async function getPracticeHint(qId) {
  try {
    const hint = await API.getHint(qId);
    document.getElementById('hintArea').innerHTML = `<div class="hint-box">${hint.hint || hint}</div>`;
  } catch {}
}

async function submitPracticeAnswer(qId) {
  const opt = window._selectedOpt || '';
  const ps = window._practiceState;
  if (!ps) return;
  const timeSec = (Date.now() - ps.startTime) / 1000;
  const q = ps.questions[ps.currentIdx];
  const isCorrect = opt === q.correct_answer;

  const submitBtn = document.getElementById('submitBtn');
  if (submitBtn) submitBtn.disabled = true;

  const correct = q.correct_answer;
  const optsHtml = q.options ? Object.entries(q.options).map(([k, v]) => {
    let cls = 'option-btn';
    if (k === correct) cls += ' correct';
    else if (k === opt && k !== correct) cls += ' wrong';
    if (k === opt) cls += ' selected';
    return `<div class="${cls}"><span class="option-label">${k}.</span> ${v}${k === correct ? ' <span style="float:right;font-size:0.7rem;color:var(--secondary)">Correct</span>' : ''}</div>`;
  }).join('') : '';
  document.getElementById('practiceOpts').innerHTML = optsHtml;

  document.getElementById('practiceFeedback').style.display = 'block';
  document.getElementById('practiceFeedback').innerHTML = `
    <div class="hint-box" style="margin-top:0.5rem">
      <div style="font-weight:600;font-size:0.9rem;margin-bottom:0.25rem;color:${isCorrect ? 'var(--secondary)' : 'var(--danger)'}">${isCorrect ? '✓ Correct!' : '✗ Incorrect'}</div>
      <div style="font-size:0.84rem;color:var(--on-surface-variant);line-height:1.6">${q.explanation || 'No explanation available.'}</div>
    </div>
    <div style="margin-top:0.75rem;display:flex;justify-content:flex-end">
      <button class="btn btn-primary" onclick="continuePractice()">${ps.currentIdx + 1 >= ps.questions.length ? 'View Results' : 'Next Question →'}</button>
    </div>`;

  ps.answers.push({
    question_id: qId,
    subtopic: q.subtopic || q.topic || '',
    subject: q.subject || '',
    topic: q.topic || '',
    is_correct: isCorrect,
    response_time_seconds: timeSec,
    hints_used: document.getElementById('hintArea').innerHTML ? 1 : 0,
    retry_count: 0,
    is_recurrence: false,
    difficulty: q.difficulty,
  });
}

window.continuePractice = function() {
  const ps = window._practiceState;
  if (!ps) return;
  ps.currentIdx++;
  window._practiceState.startTime = Date.now();
  window._selectedOpt = null;
  if (ps.currentIdx >= ps.questions.length) finishPractice();
  else renderPracticeSession();
};

async function finishPractice() {
  const ps = window._practiceState;
  if (!ps) return;
  try {
    await API.endSession(ps.sessionId);
    const r = await API.submitPracticeResult(ps.sessionId, {
      student_id: state.practiceStudentId || state.student.id,
      attempts: ps.answers,
    });
    state.lastPracticeResult = r;
    navigate('#practice-results');
  } catch (e) {
    alert('Error: ' + e.message);
    navigate('#practice');
  }
}

async function renderPracticeResults() {
  const el = document.getElementById('page-practice-results');
  const r = state.lastPracticeResult;
  if (!r) { navigate('#practice'); return; }

  const correct = r.attempts ? r.attempts.filter(a => a.is_correct).length : 0;
  const total = r.attempts ? r.attempts.length : 0;
  const pct = total ? Math.round(correct / total * 100) : 0;
  const avgTime = total && r.attempts ? r.attempts.reduce((a, b) => a + b.response_time_seconds, 0) / total : 0;

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>Practice Complete</h2>
      <button class="btn btn-ghost btn-sm" onclick="navigate('#practice')">Practice Again</button>
    </div>
    <div class="row">
      <div class="col col-2">
        <div class="card text-center" style="padding:var(--space-lg)">
          ${scoreRing(pct, 130)}
          <p class="mt-2" style="font-weight:600;font-size:1.05rem">${correct}/${total} Correct</p>
          <p class="text-dim">Avg Time: ${avgTime.toFixed(0)}s per question</p>
          <p class="text-dim">Mastery Change: <span style="color:${r.mastery_delta >= 0 ? 'var(--secondary)' : 'var(--danger)'}">${r.mastery_delta >= 0 ? '+' : ''}${r.mastery_delta.toFixed(1)}</span></p>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Question Summary</div>
          <div class="table-wrap">
            <table class="table table-condensed">
              <thead><tr><th>#</th><th>Result</th><th>Time</th><th>Difficulty</th></tr></thead>
              <tbody>${(r.attempts || []).map((a, i) => `<tr>
                <td>Q${i+1}</td>
                <td><span class="badge ${a.is_correct ? 'badge-success' : 'badge-danger'}">${a.is_correct ? 'Correct' : 'Wrong'}</span></td>
                <td class="text-dim">${a.response_time_seconds.toFixed(0)}s</td>
                <td><span class="badge badge-neutral">Lvl ${a.difficulty || '-'}</span></td>
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
  const sid = state.student?.id;
  if (!sid) { el.innerHTML = '<div class="alert alert-warning">Please log in first</div>'; return; }

  if (state._conceptAssessment) {
    renderConceptAssessment();
    return;
  }

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>Concept Assessment</h2>
    </div>
    <div class="card">
      <div class="card-header">Complete a Concept Assessment</div>
      <p class="text-dim mb-3">Assessments are launched from the Concepts page. Select a concept and click "Complete Concept" to start a 30-question assessment.</p>
      <button class="btn btn-primary" onclick="navigate('#concepts')">Go to Concepts</button>
    </div>`;
}

async function renderConceptAssessment() {
  const el = document.getElementById('page-assessment');
  const ca = state._conceptAssessment;
  if (!ca || !ca.questions || !ca.questions.length) {
    state._conceptAssessment = null;
    navigate('#concepts');
    return;
  }

  const questions = ca.questions;
  let currentIdx = ca.currentIdx || 0;
  const answers = ca.answers || [];
  let startTime = ca.startTime || Date.now();
  let timerInterval;

  function renderQ() {
    const q = questions[currentIdx];
    const progress = ((currentIdx + 1) / questions.length * 100);
    const opts = q.options ? Object.entries(q.options).map(([k, v]) =>
      `<button class="option-btn" data-opt="${k}" onclick="selectOpt(this, '${k}')"><span class="option-label">${k}.</span> ${v}</button>`).join('') : '';

    el.innerHTML = `
      <div class="flex items-center justify-between mb-2 flex-wrap gap-1">
        <div class="flex items-center gap-2">
          <button class="btn btn-ghost btn-sm" onclick="cancelConceptAssessment()" style="padding:0.25rem 0.5rem">← Exit</button>
          <h2 style="font-size:1.1rem">${ca.conceptName} Assessment</h2>
        </div>
        <div class="flex items-center gap-2">
          <span id="timerDisplay" class="assessment-timer">30:00</span>
          <span class="badge badge-primary">Q${currentIdx + 1}/${questions.length}</span>
          <span class="badge badge-success">${answers.filter(a=>a.is_correct).length} correct</span>
        </div>
      </div>
      <div class="progress mb-3"><div class="progress-bar primary" style="width:${progress}%"></div></div>
      <div class="card">
        <div class="q-meta" style="display:flex;gap:var(--space-sm);flex-wrap:wrap;margin-bottom:var(--space-sm)">
          <span class="badge badge-info">${q.topic || q.subtopic || ca.conceptName}</span>
          <span class="badge ${q.difficulty <= 2 ? 'badge-success' : q.difficulty <= 3 ? 'badge-warning' : 'badge-danger'}">Lvl ${q.difficulty}/5</span>
          <span class="badge badge-neutral">${q.question_type || 'mcq'}</span>
        </div>
        <div class="q-text" style="font-size:1rem;margin-bottom:var(--space-md)">${q.question_text}</div>
        <div id="assessOpts">${opts}</div>
        <div id="assessFeedback" class="mt-2" style="display:none"></div>
        <div class="flex justify-between mt-2">
          <button class="btn btn-primary" id="submitAssessBtn" onclick="submitConceptAnswer()">Submit Answer</button>
        </div>
      </div>`;
    window._conceptState = { currentIdx, answers, startTime, questions };

    const endTime = Date.now() + 30 * 60000;
    timerInterval = setInterval(() => {
      const remaining = Math.max(0, Math.floor((endTime - Date.now()) / 1000));
      const t = document.getElementById('timerDisplay');
      if (t) t.textContent = `${Math.floor(remaining/60)}:${(remaining%60).toString().padStart(2,'0')}`;
      if (remaining <= 0) { clearInterval(timerInterval); finishConceptAssessment(); }
    }, 1000);
    window._conceptTimer = timerInterval;
  }
  renderQ();
}

window.cancelConceptAssessment = function() {
  clearInterval(window._conceptTimer);
  state._conceptAssessment = null;
  navigate('#concepts');
};

window.submitConceptAnswer = function() {
  const selected = document.querySelector('.option-btn.selected');
  if (!selected) { document.getElementById('assessFeedback').innerHTML = '<div class="alert alert-warning">Please select an option first.</div>'; document.getElementById('assessFeedback').style.display = 'block'; return; }

  const cs = window._conceptState;
  const q = cs.questions[cs.currentIdx];
  const chosen = selected.dataset.opt;
  const isCorrect = chosen === q.correct_answer;
  const timeSec = (Date.now() - cs.startTime) / 1000;

  cs.answers.push({
    question_id: q.id,
    question_text: q.question_text,
    options: q.options,
    correct_answer: q.correct_answer,
    explanation: q.explanation || '',
    student_answer: chosen,
    is_correct: isCorrect,
    response_time_seconds: timeSec,
    difficulty: q.difficulty,
    topic: q.topic || '',
    subject: q.subject || '',
  });

  document.getElementById('submitAssessBtn').disabled = true;

  const optsHtml = q.options ? Object.entries(q.options).map(([k, v]) => {
    let cls = 'option-btn';
    if (k === q.correct_answer) cls += ' correct';
    else if (k === chosen && k !== q.correct_answer) cls += ' wrong';
    if (k === chosen) cls += ' selected';
    return `<div class="${cls}"><span class="option-label">${k}.</span> ${v}${k === q.correct_answer ? ' <span style="float:right;font-size:0.7rem;color:var(--secondary)">Correct</span>' : ''}</div>`;
  }).join('') : '';
  document.getElementById('assessOpts').innerHTML = optsHtml;

  document.getElementById('assessFeedback').style.display = 'block';
  document.getElementById('assessFeedback').innerHTML = `
    <div class="hint-box" style="margin-top:0.5rem">
      <div style="font-weight:600;font-size:0.9rem;margin-bottom:0.25rem;color:${isCorrect ? 'var(--secondary)' : 'var(--danger)'}">${isCorrect ? '✓ Correct!' : '✗ Incorrect'}</div>
      <div style="font-size:0.84rem;color:var(--on-surface-variant);line-height:1.6">${q.explanation || 'No explanation available.'}</div>
    </div>
    <div style="margin-top:0.75rem;display:flex;justify-content:flex-end">
      <button class="btn btn-primary" onclick="nextConceptQ()">${cs.currentIdx + 1 >= cs.questions.length ? 'View Results' : 'Next Question →'}</button>
    </div>`;
  window._conceptState = cs;
};

window.nextConceptQ = function() {
  const cs = window._conceptState;
  if (!cs) return;
  cs.currentIdx++;
  window._conceptState.startTime = Date.now();
  if (cs.currentIdx >= cs.questions.length) {
    clearInterval(window._conceptTimer);
    finishConceptAssessment();
  } else {
    state._conceptAssessment.currentIdx = cs.currentIdx;
    state._conceptAssessment.answers = cs.answers;
    state._conceptAssessment.startTime = cs.startTime;
    renderConceptAssessment();
  }
};

async function finishConceptAssessment() {
  const cs = window._conceptState;
  if (!cs) return;
  const correct = cs.answers.filter(a => a.is_correct).length;
  const total = cs.answers.length;
  const pct = total ? Math.round(correct / total * 100) : 0;
  const passed = pct >= 90;

  const el = document.getElementById('page-assessment');
  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>Assessment Complete</h2>
      <button class="btn btn-ghost btn-sm" onclick="navigate('#concepts')">← Concepts</button>
    </div>
    <div class="card text-center" style="padding:var(--space-lg)">
      <div style="font-size:3rem;margin-bottom:var(--space-sm)">${passed ? '🎉' : '💪'}</div>
      ${scoreRing(pct, 140)}
      <h3 class="mt-3">${passed ? 'Concept Understood!' : 'Keep Practicing'}</h3>
      <p class="text-dim">${correct}/${total} correct (${pct}%)${passed ? ' — You have demonstrated understanding of this concept.' : ' — Review the explanations below and try again.'}</p>
    </div>
    <div class="card">
      <div class="card-header">Question Analysis</div>
      ${cs.answers.map((a, i) => `
        <div class="test-card" onclick="this.querySelector('.qa-detail').classList.toggle('hidden')">
          <div class="test-card-top">
            <span style="font-size:0.84rem">Q${i+1}: ${a.question_text ? a.question_text.substring(0, 60) + '...' : ''}</span>
            <span class="badge ${a.is_correct ? 'badge-success' : 'badge-danger'}">${a.is_correct ? 'Correct' : 'Wrong'}</span>
          </div>
          <div class="qa-detail hidden" style="padding:0.5rem 0;font-size:0.82rem;color:var(--on-surface-variant)">
            <p><strong>Your answer:</strong> ${a.student_answer || '-'}</p>
            <p><strong>Correct answer:</strong> ${a.correct_answer || '-'}</p>
            <p class="mt-1">${a.explanation || 'No explanation'}</p>
            ${!a.is_correct ? `<div class="mt-1" style="padding:0.5rem;background:rgba(240,96,112,0.06);border-radius:var(--radius-sm)">
              <strong>Failure Analysis:</strong> ${getFailureAnalysis(a)}
            </div>` : ''}
          </div>
        </div>`).join('')}
    </div>
    <div class="flex justify-center gap-1 mt-2">
      <button class="btn btn-primary" onclick="navigate('#concepts')">Back to Concepts</button>
      ${!passed ? `<button class="btn btn-ghost" onclick="startConceptAssessment('${state._conceptAssessment.conceptId}', '${state._conceptAssessment.conceptName}')">Retry Assessment</button>` : ''}
    </div>`;
  state._conceptAssessment = null;
}

function getFailureAnalysis(a) {
  const time = a.response_time_seconds || 0;
  const diff = a.difficulty || 3;

  if (time < 15 && diff <= 3) {
    return `<span style="color:var(--warning)">Possible Cause: Careless Error</span> — <span class="text-dim">Review the solution carefully and practice similar questions.</span>
    <div class="mt-1" style="font-size:0.78rem;color:var(--on-surface-variant)">Recommendation: Timed accuracy practice set.</div>`;
  }
  if (time >= 60 && diff >= 3) {
    return `<span style="color:var(--danger)">Possible Cause: Concept Gap</span> — <span class="text-dim">The concept was not fully understood.</span>
    <div class="mt-1" style="font-size:0.78rem;color:var(--on-surface-variant)">Recommendation: Revise fundamental concepts and try easier questions first.</div>`;
  }
  if (time < 10 && diff >= 4) {
    return `<span style="color:var(--warning)">Possible Cause: Guessing</span> — <span class="text-dim">Answered too quickly for difficulty level.</span>
    <div class="mt-1" style="font-size:0.78rem;color:var(--on-surface-variant)">Recommendation: Practice with no time pressure to build understanding.</div>`;
  }
  if (time >= 120) {
    return `<span style="color:var(--primary)">Possible Cause: Time Pressure</span> — <span class="text-dim">Too much time spent, may have rushed the final calculation.</span>
    <div class="mt-1" style="font-size:0.78rem;color:var(--on-surface-variant)">Recommendation: Timed practice sessions with easier questions.</div>`;
  }
  return `<span style="color:var(--danger)">Possible Cause: Application Error</span> — <span class="text-dim">The concept may be understood but not correctly applied.</span>
  <div class="mt-1" style="font-size:0.78rem;color:var(--on-surface-variant)">Recommendation: Practice application-based questions.</div>`;
}

// ── MODULE 3: CONCEPTS ──
async function renderConcepts() {
  const el = document.getElementById('page-concepts');
  const sid = state.student?.id;
  if (!sid) { el.innerHTML = '<div class="alert alert-warning">Please log in first</div>'; return; }

  const [graphData, mastery, sessions] = await Promise.all([
    API.getFullGraph().catch(() => ({ nodes: [], edges: [] })),
    API.getMastery(sid).catch(() => null),
    API.getStudentSessions(sid).catch(() => []),
  ]);

  const nodes = graphData.nodes || [];
  const subjects = [...new Set(nodes.map(n => n.subject))];
  const masteryScores = mastery?.subject_breakdown || {};
  const weakTopics = mastery?.weak_topics || [];
  const weakSubtopicNames = new Set(weakTopics.map(w => w.subtopic?.toLowerCase()));

  let allHtml = '';
  for (const subject of subjects) {
    const subjectMastery = masteryScores[subject] || 0;
    const subjectNodes = nodes.filter(n => n.subject === subject);
    const topics = [...new Set(subjectNodes.map(n => n.topic))];

    // Chapter breakdown for this subject
    let chapterData = {};
    for (const topic of topics) {
      const topicSessions = (sessions || []).filter(s => s.topic === topic);
      const total = topicSessions.length;
      const correct = topicSessions.reduce((sum, s) => sum + (s.correct_count || 0), 0);
      const attempted = topicSessions.reduce((sum, s) => sum + (s.questions_count || 0), 0);
      chapterData[topic] = attempted > 0 ? Math.round(correct / attempted * 100) : null;
    }

    let topicHtml = '';
    for (const topic of topics) {
      const topicNodes = subjectNodes.filter(n => n.topic === topic);
      const chapterPct = chapterData[topic];
      let conceptHtml = topicNodes.map(n => {
        const conceptName = n.display_name || n.subtopic || '';
        const isWeak = weakSubtopicNames.has(conceptName.toLowerCase()) || weakSubtopicNames.has(n.subtopic?.toLowerCase());
        let statusClass = 'status-not-started';
        let statusLabel = 'Not Started';
        let progressPct = 0;
        if (isWeak) {
          statusClass = 'status-needs-revision';
          statusLabel = 'Needs Revision';
          const weak = weakTopics.find(w => w.subtopic?.toLowerCase() === conceptName.toLowerCase() || w.subtopic?.toLowerCase() === n.subtopic?.toLowerCase());
          progressPct = weak ? weak.score : 30;
        }

        return `<div class="concept-card" onclick="startConceptAssessment('${n.subtopic || conceptName}', '${conceptName.replace(/'/g, "\\'")}')">
          <div class="concept-card-top">
            <span class="concept-name">${conceptName}</span>
            <span class="concept-status ${statusClass}">${statusLabel}</span>
          </div>
          <div class="progress mt-1"><div class="progress-bar ${isWeak ? 'danger' : 'primary'}" style="width:${progressPct}%"></div></div>
          <div class="concept-card-meta">
            <span class="text-dim">${isWeak ? `${fmtPct(progressPct)}% mastery` : 'Not practiced'}</span>
            <span class="badge badge-neutral">Lvl ${n.difficulty || '-'}</span>
          </div>
        </div>`;
      }).join('');

      topicHtml += `
        <div class="topic-section">
          <h4 class="topic-header">${topic}</h4>
          <div class="concept-grid">${conceptHtml}</div>
        </div>`;
    }

    allHtml += `
      <div class="subject-section">
        <div class="subject-header">
          <h3>${subject.charAt(0).toUpperCase() + subject.slice(1)}</h3>
          <span class="badge badge-primary">${fmtPct(subjectMastery)}%</span>
        </div>
        ${topicHtml}
      </div>`;
  }

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>Concepts</h2>
      <span class="text-dim" style="font-size:0.84rem">${nodes.length} concepts</span>
    </div>
    ${allHtml || '<div class="alert alert-info">No concepts loaded yet.</div>'}`;
}

window.startConceptAssessment = async function(conceptId, conceptName) {
  const sid = state.student?.id;
  if (!sid) return;

  // Fetch questions for this concept
  const [appQs, testQs] = await Promise.all([
    API.listAppQuestions({ subtopic: conceptId }).catch(() => []),
    API.listTestQuestions({ subtopic: conceptId }).catch(() => []),
  ]);

  const allQs = [...(appQs || []), ...(testQs || [])];
  if (allQs.length < 10) {
    // Try fetching by topic
    const [appByTopic, testByTopic] = await Promise.all([
      API.listAppQuestions({ topic: conceptId }).catch(() => []),
      API.listTestQuestions({ topic: conceptId }).catch(() => []),
    ]);
    allQs.push(...(appByTopic || []), ...(testByTopic || []));
  }

  // Shuffle and pick up to 30
  const shuffled = allQs.sort(() => Math.random() - 0.5).slice(0, 30);

  state._conceptAssessment = {
    conceptId,
    conceptName,
    questions: shuffled,
    currentIdx: 0,
    answers: [],
    startTime: Date.now(),
  };
  navigate('#assessment');
};

// ── MODULE 4: ANALYTICS ──
async function renderAnalytics() {
  const el = document.getElementById('page-analytics');
  const sid = state.student?.id;
  if (!sid) { el.innerHTML = '<div class="alert alert-warning">Please log in first</div>'; return; }

  const [analytics, mastery, sessions] = await Promise.all([
    API.getStudentAnalytics(sid).catch(() => null),
    API.getMastery(sid).catch(() => null),
    API.getStudentSessions(sid).catch(() => []),
  ]);

  const sortedSessions = (sessions || []).filter(s => s.ended_at).sort((a, b) => new Date(b.started_at) - new Date(a.started_at));
  const assessments = sortedSessions.filter(s => s.session_type === 'assessment');
  const practice_sessions = sortedSessions.filter(s => s.session_type === 'practice');

  const recentTests = assessments.slice(0, 5);

  const trendSessions = [...sortedSessions].reverse().slice(-30);

  const weakStr = Array.isArray(analytics?.weak_topics) ? analytics.weak_topics.join(', ') : 'None identified';
  const strongStr = Array.isArray(analytics?.strengths) ? analytics.strengths.join(', ') : 'None identified';

  const subjBreakdown = mastery?.subject_breakdown || {};

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <h2>Analytics</h2>
      <span class="text-dim" style="font-size:0.82rem">${assessments.length} tests · ${practice_sessions.length} practice sessions</span>
    </div>

    <div class="row">
      <div class="col col-2">
        <div class="card">
          <div class="card-header">Recent Tests</div>
          ${recentTests.length ? recentTests.map(s => {
            const pct = s.questions_count > 0 ? Math.round(s.correct_count / s.questions_count * 100) : 0;
            return `<div class="test-card" onclick="navigate('#analytics-report/${s.id}')">
              <div class="test-card-top">
                <span class="test-name">${s.subject || 'Test'}</span>
                <span class="badge ${pct >= 60 ? 'badge-success' : pct >= 35 ? 'badge-warning' : 'badge-danger'}">${pct}%</span>
              </div>
              <div class="test-card-meta">
                <span>${s.correct_count}/${s.questions_count} · ${fmtDate(s.ended_at)}</span>
                <span class="text-dim">${s.mastery_delta >= 0 ? '+' : ''}${(s.mastery_delta || 0).toFixed(1)} mastery</span>
              </div>
            </div>`;
          }).join('') : '<p class="text-dim">No tests completed yet</p>'}
          ${assessments.length > 5 ? `<p class="text-dim mt-1" style="font-size:0.78rem">+ ${assessments.length - 5} more tests</p>` : ''}
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Overall Mastery</div>
          ${scoreRing(analytics?.overall_mastery || 0, 100)}
          <p class="text-center text-dim mt-1" style="font-size:0.82rem">${sortedSessions.length} total sessions</p>
        </div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">Subject Breakdown</div>
      <div class="stat-row">
        ${Object.entries(subjBreakdown).length ? Object.entries(subjBreakdown).map(([subj, score]) =>
          `<div class="stat-card"><div class="stat-value">${fmtPct(score)}%</div><div class="stat-label" style="text-transform:capitalize">${subj}</div></div>`
        ).join('') : '<p class="text-dim">No data</p>'}
      </div>
    </div>

    <div class="card">
      <div class="card-header">Chapter Breakdown</div>
      ${sortedSessions.length ? (() => {
        const chapters = {};
        sortedSessions.filter(s => s.topic || s.subject).forEach(s => {
          const key = s.topic || s.subject || 'general';
          if (!chapters[key]) chapters[key] = { correct: 0, total: 0 };
          chapters[key].correct += s.correct_count || 0;
          chapters[key].total += s.questions_count || 0;
        });
        return Object.entries(chapters).length ? Object.entries(chapters).map(([ch, d]) => {
          const chPct = d.total > 0 ? Math.round(d.correct / d.total * 100) : 0;
          return `<div class="chart-bar-group">
            <div class="chart-bar-label"><span style="text-transform:capitalize">${ch}</span><span>${fmtPct(chPct)}%</span></div>
            <div class="chart-bar"><div class="chart-bar-fill ${scoreClass(chPct)}" style="width:${chPct}%"></div></div>
          </div>`;
        }).join('') : '<p class="text-dim">No chapter data</p>';
      })() : '<p class="text-dim">No sessions yet</p>'}
    </div>

    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">Weak Areas</div>
          <p class="text-dim">${weakStr}</p>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Strengths</div>
          <p class="text-dim">${strongStr}</p>
        </div>
      </div>
    </div>

    <div class="row">
      <div class="col">
        <div class="card">
          <div class="card-header">Score Trend</div>
          <div style="max-height:300px;overflow-y:auto">
            ${trendSessions.slice(-20).map(s => {
              const pct = s.questions_count > 0 ? Math.round(s.correct_count / s.questions_count * 100) : 0;
              return `<div class="flex items-center justify-between" style="font-size:0.78rem;padding:0.25rem 0;border-bottom:1px solid var(--border-light)">
                <span class="text-dim">${fmtDate(s.started_at)}</span>
                <span><span class="badge ${pct >= 60 ? 'badge-success' : pct >= 35 ? 'badge-warning' : 'badge-danger'}">${pct}%</span></span>
              </div>`;
            }).join('') || '<p class="text-dim">Not enough data</p>'}
          </div>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Recommendations</div>
          <p class="text-dim">${analytics?.practice_recommendation || 'Complete more practice to receive AI-powered recommendations.'}</p>
        </div>
        <div class="card">
          <div class="card-header">Best Test</div>
          ${assessments.length ? (() => {
            const best = assessments.reduce((a, b) => Math.max(a, b.questions_count > 0 ? b.correct_count/b.questions_count : 0), 0);
            const bestSession = assessments.find(s => (s.questions_count > 0 ? s.correct_count/s.questions_count : 0) === best);
            if (bestSession) {
              const pct = Math.round(best * 100);
              return `<p class="text-dim">${fmtPct(pct)}% · ${bestSession.subject || 'Test'} · ${fmtDate(bestSession.ended_at)}</p>`;
            }
            return '<p class="text-dim">No tests yet</p>';
          })() : '<p class="text-dim">No tests yet</p>'}
        </div>
      </div>
    </div>`;
}

// ── ANALYTICS REPORT (per test session) ──
async function renderAnalyticsReport(sessionId) {
  const el = document.getElementById('page-analytics-report');
  if (!sessionId) { navigate('#analytics'); return; }

  const [session, analytics] = await Promise.all([
    API.getSession(sessionId).catch(() => null),
    API.getSessionAnalytics(sessionId).catch(() => null),
  ]);
  if (!session) {
    el.innerHTML = '<div class="alert alert-danger">Session not found</div>';
    return;
  }

  const pct = session.questions_count > 0 ? Math.round(session.correct_count / session.questions_count * 100) : 0;
  const incorrect = (session.questions_count || 0) - (session.correct_count || 0);
  const diffData = analytics?.difficulty_distribution || {};
  const topicData = analytics?.topic_breakdown || {};

  // Build failure analysis categories
  const failureCauses = [
    {
      cause: 'Calculation Error',
      icon: '🔢',
      desc: 'Mistakes in arithmetic or algebraic manipulation',
      rec: 'Solve arithmetic-intensive practice set with focus on accuracy.',
    },
    {
      cause: 'Concept Gap',
      icon: '📚',
      desc: 'Underlying concept not fully understood',
      rec: 'Revise fundamentals through concept notes and video explanations.',
    },
    {
      cause: 'Application Error',
      icon: '⚡',
      desc: 'Concept understood but incorrectly applied',
      rec: 'Practice application-based and numerical problems.',
    },
    {
      cause: 'Time Pressure',
      icon: '⏱',
      desc: 'Rushed decision due to time constraints',
      rec: 'Take timed practice sessions to improve speed.',
    },
    {
      cause: 'Formula Recall Issue',
      icon: '📝',
      desc: 'Could not recall the correct formula',
      rec: 'Create a formula revision sheet and review daily.',
    },
  ];

  el.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <button class="btn btn-ghost btn-sm" onclick="navigate('#analytics')">← Back</button>
        <h2 style="font-size:1.1rem">${session.subject || 'Test'} Report</h2>
      </div>
      <span class="badge badge-info">${fmtDate(session.ended_at)}</span>
    </div>

    <div class="row">
      <div class="col col-2">
        <div class="card text-center" style="padding:var(--space-lg)">
          ${scoreRing(pct, 130)}
          <p class="mt-2" style="font-weight:600;font-size:1.05rem">${session.correct_count}/${session.questions_count}</p>
          <p class="text-dim">Mastery Change: <span style="color:${(session.mastery_delta || 0) >= 0 ? 'var(--secondary)' : 'var(--danger)'}">${(session.mastery_delta || 0) >= 0 ? '+' : ''}${(session.mastery_delta || 0).toFixed(1)}</span></p>
        </div>
      </div>
      <div class="col">
        <div class="card">
          <div class="card-header">Summary</div>
          <div class="info-grid">
            <div class="info-item"><div class="info-label">Total Questions</div><div class="info-value">${session.questions_count || 0}</div></div>
            <div class="info-item"><div class="info-label">Correct</div><div class="info-value" style="color:var(--secondary)">${session.correct_count || 0}</div></div>
            <div class="info-item"><div class="info-label">Incorrect</div><div class="info-value" style="color:var(--danger)">${incorrect}</div></div>
            <div class="info-item"><div class="info-label">Accuracy</div><div class="info-value">${pct}%</div></div>
          </div>
        </div>
      </div>
    </div>

    ${Object.keys(topicData).length ? `
    <div class="card">
      <div class="card-header">Chapter Breakdown</div>
      ${Object.entries(topicData).map(([topic, info]) => {
        const tpct = typeof info === 'number' ? info : (info.correct / info.total * 100);
        return `<div class="chart-bar-group">
          <div class="chart-bar-label"><span>${topic}</span><span>${fmtPct(tpct)}%</span></div>
          <div class="chart-bar"><div class="chart-bar-fill ${scoreClass(tpct)}" style="width:${tpct}%"></div></div>
        </div>`;
      }).join('')}
    </div>` : ''}

    ${incorrect > 0 ? `
    <div class="card">
      <div class="card-header">Failure Analysis</div>
      <p class="text-dim mb-2">Based on your performance, here are possible causes and recommendations:</p>
      ${failureCauses.map(fc => `
        <div class="test-card" style="border-left:3px solid var(--border-light);margin-bottom:var(--space-xs)">
          <div style="display:flex;align-items:flex-start;gap:var(--space-sm)">
            <span style="font-size:1.2rem">${fc.icon}</span>
            <div>
              <div style="font-weight:600;font-size:0.84rem;color:var(--on-surface)">${fc.cause}</div>
              <div style="font-size:0.78rem;color:var(--on-surface-variant);margin:2px 0">${fc.desc}</div>
              <div style="font-size:0.8rem;color:var(--primary-fixed)">→ ${fc.rec}</div>
            </div>
          </div>
        </div>`).join('')}
    </div>` : ''}

    <div class="card">
      <div class="card-header">Recommendations</div>
      <ul style="padding-left:1.2rem;color:var(--on-surface-variant);font-size:0.84rem;line-height:1.8">
        <li>Review incorrect answers and understand the solutions</li>
        <li>Focus practice on chapters where accuracy was below 60%</li>
        <li>Take shorter, focused practice sessions on weak topics</li>
        ${pct < 60 ? '<li>Consider revisiting fundamental concepts before attempting advanced questions</li>' : ''}
      </ul>
    </div>`;
}

// ── INIT ──
document.addEventListener('DOMContentLoaded', () => {
  initApp();
});
