/**
 * UMCAO API Service
 * Handles communication between React frontend and FastAPI backend.
 */

function resolveApiBaseUrl() {
  const raw = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || '').trim();

  if (!raw) {
    return import.meta.env.DEV ? 'http://127.0.0.1:8000/api' : '/api';
  }

  let normalized = raw.replace(/\/+$/, '');

  // If a bare hostname is provided (e.g. from Render host property), add https://
  if (!normalized.startsWith('http://') && !normalized.startsWith('https://') && !normalized.startsWith('/')) {
    normalized = `https://${normalized}`;
  }

  // Ensure /api prefix is present so endpoints like /health, /analyze, /code/* always match FastAPI routers
  if (normalized !== '/api' && !normalized.endsWith('/api')) {
    normalized = `${normalized}/api`;
  }

  return normalized;
}

export const API_BASE_URL = resolveApiBaseUrl();

function createTimeoutSignal(ms) {
  if (typeof AbortSignal !== 'undefined' && typeof AbortSignal.timeout === 'function') {
    return AbortSignal.timeout(ms);
  }
  const controller = new AbortController();
  setTimeout(() => controller.abort(), ms);
  return controller.signal;
}

export async function analyzeCode(code, language = 'python', options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code,
        language,
        options,
      }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server responded with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API analyzeCode error:', error);
    throw error;
  }
}

export async function getLanguages() {
  try {
    const response = await fetch(`${API_BASE_URL}/languages`);
    if (!response.ok) {
      throw new Error(`Failed to fetch languages (status ${response.status})`);
    }
    return await response.json();
  } catch (error) {
    console.warn('API getLanguages error, falling back to static list:', error);
    return {
      status: 'fallback',
      languages: [
        { id: 'python', name: 'Python', supported: true, engine: 'Python AST' },
        { id: 'c', name: 'C', supported: false, engine: 'Clang AST' },
        { id: 'cpp', name: 'C++', supported: false, engine: 'Clang LibTooling' },
        { id: 'java', name: 'Java', supported: false, engine: 'Javaparser' },
        { id: 'javascript', name: 'JavaScript', supported: false, engine: 'Babel / Acorn' },
      ],
    };
  }
}

export async function getSamplePresets(language = 'python') {
  try {
    const response = await fetch(`${API_BASE_URL}/samples?language=${encodeURIComponent(language)}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch samples (status ${response.status})`);
    }
    return await response.json();
  } catch (error) {
    console.warn('API getSamplePresets error:', error);
    return { language, samples: [] };
  }
}

export async function checkBackendHealth() {
  const timeoutMs = import.meta.env.DEV ? 5000 : 45000;
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: createTimeoutSignal(timeoutMs),
    });
    if (!response.ok) {
      return { healthy: false, status: response.status, url: `${API_BASE_URL}/health` };
    }
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      return {
        healthy: false,
        status: response.status,
        error: 'Backend returned HTML instead of JSON. Verify VITE_API_BASE_URL points to the FastAPI backend.',
        url: `${API_BASE_URL}/health`,
      };
    }
    const data = await response.json();
    return { healthy: data.status === 'healthy', data, url: `${API_BASE_URL}/health` };
  } catch (err) {
    return {
      healthy: false,
      error: err?.message || 'Unable to reach backend server',
      url: `${API_BASE_URL}/health`,
    };
  }
}

/**
 * Gemini AI Code Explanation API
 */
export async function explainCodeWithAI({
  code,
  language = 'python',
  mode = 'detailed',
  explanationLanguage = 'english',
}) {
  try {
    let endpoint = `${API_BASE_URL}/ai/explain`;
    if (mode === 'line_by_line') endpoint = `${API_BASE_URL}/ai/explain-line-by-line`;
    else if (mode === 'algorithm') endpoint = `${API_BASE_URL}/ai/explain-algorithm`;
    else if (mode === 'interview') endpoint = `${API_BASE_URL}/ai/explain-interview`;
    else if (mode === 'optimization') endpoint = `${API_BASE_URL}/ai/explain-optimization`;

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code,
        language,
        mode,
        explanation_language: explanationLanguage,
      }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Gemini AI explanation failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API explainCodeWithAI error:', error);
    throw error;
  }
}

/**
 * Gemini AI Follow-Up Chat API
 */
export async function sendAIChat({
  code,
  message,
  language = 'python',
  explanationLanguage = 'english',
  history = [],
}) {
  try {
    const response = await fetch(`${API_BASE_URL}/ai/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code,
        message,
        language,
        explanation_language: explanationLanguage,
        history,
      }),
    });

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Gemini AI chat failed with status ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API sendAIChat error:', error);
    throw error;
  }
}

/**
 * Sandboxed Code Execution & Compilation APIs
 */

export async function validateCode({ code, language = 'python' }) {
  try {
    const response = await fetch(`${API_BASE_URL}/code/validate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Validation failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API validateCode error:', error);
    throw error;
  }
}

export async function compileCode({ code, language }) {
  try {
    const response = await fetch(`${API_BASE_URL}/code/compile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Compilation failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API compileCode error:', error);
    throw error;
  }
}

export async function executeCode({ code, language = 'python', stdinInput = '' }) {
  try {
    const response = await fetch(`${API_BASE_URL}/code/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, language, stdin_input: stdinInput }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Execution failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API executeCode error:', error);
    throw error;
  }
}

export async function analyzeAndRunCode({ code, language = 'python', stdinInput = '', includeAst = true }) {
  try {
    const response = await fetch(`${API_BASE_URL}/code/analyze-run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code,
        language,
        stdin_input: stdinInput,
        include_ast: includeAst,
      }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Analyze & Run failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API analyzeAndRunCode error:', error);
    throw error;
  }
}

export async function explainErrorWithGemini({
  code,
  language = 'python',
  errorMessage = '',
  errorType = null,
  line = null,
  explanationLanguage = 'english',
}) {
  try {
    const response = await fetch(`${API_BASE_URL}/code/explain-error`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code,
        language,
        error_message: errorMessage,
        error_type: errorType,
        line,
        explanation_language: explanationLanguage,
      }),
    });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Gemini error explanation failed with status ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API explainErrorWithGemini error:', error);
    throw error;
  }
}

