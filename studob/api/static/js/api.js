const API = {
  BASE: '/api/v1',

  async request(method, path, body) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(this.BASE + path, opts);
    if (res.status === 204) return null;
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    return data;
  },

  // Students
  listStudents() { return this.request('GET', '/students/'); },
  getStudent(id) { return this.request('GET', `/students/${id}`); },
  getStudentByName(name) { return this.request('GET', `/students/by-name/${encodeURIComponent(name)}`); },
  createStudent(data) { return this.request('POST', '/students/', data); },
  deleteStudent(id) { return this.request('DELETE', `/students/${id}`); },

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
  getActiveSessions(studentId) { return this.request('GET', `/sessions/student/${studentId}/active`); },
  getStudentSessions(studentId) { return this.request('GET', `/sessions/student/${studentId}/all`); },

  // Diagnosis
  diagnose(data) { return this.request('POST', '/diagnosis/diagnose', data); },
  getMistakeHistory(studentId, limit) {
    return this.request('GET', `/diagnosis/student/${studentId}/history?limit=${limit || 20}`);
  },
  getRecurringPatterns(studentId) { return this.request('GET', `/diagnosis/student/${studentId}/patterns`); },

  // Retrieval
  retrieve(data) { return this.request('POST', '/retrieval/retrieve', data); },

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
  generateReport(studentId, sessionId) { return this.request('POST', '/reports/test-report', { student_id: studentId, session_id: sessionId }); },

  // Concept Graph
  getFullGraph() { return this.request('GET', '/graph/full-graph'); },
  listConcepts() { return this.request('GET', '/graph/concepts'); },
  getConcept(id) { return this.request('GET', `/graph/concepts/${id}`); },
  getConceptChain(id) { return this.request('GET', `/graph/concepts/${id}/chain`); },
};
