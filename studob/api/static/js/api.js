const API = {
  BASE: '/api/v1',

  _token: null,

  setToken(token) {
    this._token = token;
    if (token) localStorage.setItem('studob_token', token);
    else localStorage.removeItem('studob_token');
  },

  loadToken() {
    this._token = localStorage.getItem('studob_token');
    return this._token;
  },

  async request(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (this._token) opts.headers['Authorization'] = 'Bearer ' + this._token;
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(this.BASE + path, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  },

  // Auth
  login(name, pin) { return this.request('POST', '/auth/login', { name, pin }); },
  verifyToken() { return this.request('POST', '/auth/verify'); },
  logout() { return this.request('POST', '/auth/logout'); },

  // Mastery
  getMastery(studentId) { return this.request('GET', `/students/${studentId}/mastery`); },
  getWeakTopics(studentId) { return this.request('GET', `/students/${studentId}/weak-topics`); },

  // Questions
  listAppQuestions(params) {
    const q = new URLSearchParams(params || {}).toString();
    return this.request('GET', `/questions/app${q ? '?' + q : ''}`);
  },
  listTestQuestions(params) {
    const q = new URLSearchParams(params || {}).toString();
    return this.request('GET', `/questions/test${q ? '?' + q : ''}`);
  },

  // Sessions
  startSession(data) { return this.request('POST', '/sessions/', data); },
  getSession(id) { return this.request('GET', `/sessions/${id}`); },
  endSession(id) { return this.request('PUT', `/sessions/${id}/end`); },
  recordAttempt(sessionId, data) { return this.request('POST', `/sessions/${sessionId}/attempts`, data); },
  getStudentSessions(studentId) { return this.request('GET', `/sessions/student/${studentId}/all`); },

  // Practice
  generatePractice(data) { return this.request('POST', '/practice/generate', data); },
  submitPracticeResult(sessionId, data) { return this.request('POST', `/practice/${sessionId}/result`, data); },
  getHint(questionId) { return this.request('GET', `/practice/hint/${questionId}`); },

  // Assessment
  createAssessment(data) { return this.request('POST', '/assessment/', data); },
  getAssessment(id) { return this.request('GET', `/assessment/${id}`); },
  submitAnswer(assessmentId, data) { return this.request('POST', `/assessment/${assessmentId}/answer`, data); },
  completeAssessment(id) { return this.request('POST', `/assessment/${id}/complete`); },

  // Analytics
  getStudentAnalytics(studentId) { return this.request('GET', `/analytics/student/${studentId}`); },
  getSessionAnalytics(sessionId) { return this.request('GET', `/analytics/session/${sessionId}`); },

  // Reports
  generateReport(studentId, sessionId) {
    return this.request('POST', '/reports/test-report', { student_id: studentId, session_id: sessionId });
  },

  // Concept Graph
  getFullGraph() { return this.request('GET', '/graph/full-graph'); },
  listConcepts() { return this.request('GET', '/graph/concepts'); },
  getConcept(id) { return this.request('GET', `/graph/concepts/${id}`); },
  getConceptChain(id) { return this.request('GET', `/graph/concepts/${id}/chain`); },
};
