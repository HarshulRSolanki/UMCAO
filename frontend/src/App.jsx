import React, { useState, useEffect } from 'react';
import Navbar from './Component/Navbar';
import Sidebar from './Component/Sidebar';
import CodeEditorPanel from './Component/CodeEditorPanel';
import OutputConsole from './Component/OutputConsole';
import ResultsPanel from './Component/ResultsPanel';
import PerformanceDashboard from './Component/PerformanceDashboard';
import AIExplainerPanel from './Component/AIExplainerPanel';
import HistoryPanel from './Component/HistoryPanel';
import SettingsPanel from './Component/SettingsPanel';
import DocsModal from './Component/DocsModal';
import Footer from './Component/Footer';
import {
  API_BASE_URL,
  analyzeCode,
  analyzeAndRunCode,
  getLanguages,
  getSamplePresets,
  checkBackendHealth,
} from './services/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

const DEFAULT_PYTHON_CODE = `def find_duplicate_pairs(list_a, list_b):
    # Inefficient pairwise comparison with O(N^2) complexity
    duplicates = []
    for a in list_a:
        for b in list_b:
            if a == b:
                duplicates.append((a, b))
    return duplicates

# Run example
data_a = [1, 2, 3, 4]
data_b = [3, 4, 5, 6]
print("Duplicate pairs found:", find_duplicate_pairs(data_a, data_b))
`;

export default function App() {
  const [code, setCode] = useState(DEFAULT_PYTHON_CODE);
  const [language, setLanguage] = useState('python');
  const [languagesList, setLanguagesList] = useState([
    { id: 'python', name: 'Python', supported: true, engine: 'Python AST' },
    { id: 'c', name: 'C', supported: true, engine: 'Python AST' },
    { id: 'cpp', name: 'C++', supported: true, engine: 'Python AST' },
    { id: 'java', name: 'Java', supported: true, engine: 'Python AST' },
    { id: 'javascript', name: 'JavaScript', supported: false, engine: 'Babel / Acorn' },
  ]);
  const [samplePresets, setSamplePresets] = useState([]);
  const [result, setResult] = useState(null);
  const [executionResult, setExecutionResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [stdinInput, setStdinInput] = useState('');
  const [isBackendOnline, setIsBackendOnline] = useState(true);
  const [apiError, setApiError] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isDocsOpen, setIsDocsOpen] = useState(false);

  // Layout states for Sidebar
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  // Analysis History & Settings in LocalStorage
  const [history, setHistory] = useState(() => {
    try {
      const saved = localStorage.getItem('umcao_history');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [settings, setSettings] = useState(() => {
    try {
      const saved = localStorage.getItem('umcao_settings');
      return saved ? JSON.parse(saved) : { tabSize: '4', fontSize: '13px', defaultLang: 'english' };
    } catch {
      return { tabSize: '4', fontSize: '13px', defaultLang: 'english' };
    }
  });

  // Save history on change
  useEffect(() => {
    try {
      localStorage.setItem('umcao_history', JSON.stringify(history));
    } catch (e) {
      console.warn('Could not save history to localStorage:', e);
    }
  }, [history]);

  // Save settings on change
  useEffect(() => {
    try {
      localStorage.setItem('umcao_settings', JSON.stringify(settings));
    } catch (e) {
      console.warn('Could not save settings to localStorage:', e);
    }
  }, [settings]);

  // Initialize and check backend connection
  useEffect(() => {
    let mounted = true;

    async function init() {
      const health = await checkBackendHealth();
      if (mounted) {
        setIsBackendOnline(health.healthy);
      }

      try {
        const langData = await getLanguages();
        if (mounted && langData.languages) {
          setLanguagesList(langData.languages);
        }
      } catch (err) {
        console.warn('Could not fetch language registry:', err);
      }

      try {
        const samplesData = await getSamplePresets('python');
        if (mounted && samplesData.samples) {
          setSamplePresets(samplesData.samples);
        }
      } catch (err) {
        console.warn('Could not fetch sample presets:', err);
      }
    }

    init();

    // Heartbeat check every 15s
    const timer = setInterval(async () => {
      const health = await checkBackendHealth();
      if (mounted) {
        setIsBackendOnline(health.healthy);
      }
    }, 15000);

    return () => {
      mounted = false;
      clearInterval(timer);
    };
  }, []);

  // Update sample presets whenever language changes
  useEffect(() => {
    async function loadPresets() {
      try {
        const data = await getSamplePresets(language);
        setSamplePresets(data.samples || []);
      } catch (err) {
        console.warn(`Could not load presets for ${language}:`, err);
      }
    }
    loadPresets();
  }, [language]);

  // Load a chosen preset into editor
  const handleLoadPreset = (presetId) => {
    const found = samplePresets.find((p) => p.id === presetId);
    if (found) {
      setCode(found.code);
      setExecutionResult(null);
      setApiError(null);
    }
  };

  // Perform Complete Analyze & Run Workflow (Validation -> Compilation -> Execution -> AST)
  const handleAnalyzeAndRun = async () => {
    if (!code.trim()) {
      setApiError('Please enter some code to analyze and run.');
      return;
    }

    setIsRunning(true);
    setIsAnalyzing(true);
    setApiError(null);

    try {
      const data = await analyzeAndRunCode({
        code,
        language,
        stdinInput,
        includeAst: true,
      });

      setExecutionResult(data);
      if (data.ast_analysis) {
        setResult(data.ast_analysis);
      }
      setIsBackendOnline(true);

      // Record in History if execution was successful or has AST info
      if (data && data.success) {
        const historyItem = {
          id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
          timestamp: new Date().toISOString(),
          language,
          code,
          complexity: data.ast_analysis?.complexity?.time_complexity || 'O(1)',
          lines: code.split('\n').length,
          optimizationsCount: data.ast_analysis?.optimizations?.length || 0,
        };
        setHistory((prev) => [historyItem, ...prev.slice(0, 19)]);
      }
    } catch (err) {
      console.error('Analyze & Run failed:', err);
      setApiError(
        `Unable to reach UMCAO Backend API at (${API_BASE_URL}). ${
          err.message === 'Failed to fetch'
            ? 'The Render backend may still be waking up (cold start takes ~30s), or CORS / VITE_API_BASE_URL is misconfigured.'
            : err.message
        }`
      );
      setIsBackendOnline(false);
    } finally {
      setIsRunning(false);
      setIsAnalyzing(false);
    }
  };

  // Perform Static AST Analysis Only
  const handleAnalyze = async () => {
    if (!code.trim()) {
      setApiError('Please enter some code to analyze.');
      return;
    }

    setIsAnalyzing(true);
    setApiError(null);

    try {
      const data = await analyzeCode(code, language);
      setResult(data);
      setIsBackendOnline(true);
    } catch (err) {
      console.error('AST Analysis failed:', err);
      setApiError(
        `Unable to reach UMCAO Backend API at (${API_BASE_URL}). ${
          err.message === 'Failed to fetch'
            ? 'The Render backend may still be waking up, or CORS / VITE_API_BASE_URL needs to be checked.'
            : err.message
        }`
      );
      setIsBackendOnline(false);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Apply Corrected Code from Gemini Error Diagnosis
  const handleApplyFix = (correctedCode) => {
    if (correctedCode) {
      setCode(correctedCode);
      setExecutionResult(null);
    }
  };

  // Trigger initial analyze & run on startup once ready
  useEffect(() => {
    handleAnalyzeAndRun();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSwitchToPython = () => {
    setLanguage('python');
    setCode(DEFAULT_PYTHON_CODE);
    setResult(null);
    setExecutionResult(null);
    setApiError(null);
    setTimeout(() => {
      handleAnalyzeAndRun();
    }, 100);
  };

  const handleLoadHistoryItem = (item) => {
    setCode(item.code);
    setLanguage(item.language);
    setExecutionResult(null);
    setActiveTab('dashboard');
    setTimeout(() => {
      handleAnalyzeAndRun();
    }, 100);
  };

  const handleClearHistory = () => {
    setHistory([]);
  };

  const handleRemoveHistoryItem = (id) => {
    setHistory((prev) => prev.filter((item) => item.id !== id));
  };

  return (
    <div className="h-screen flex overflow-hidden bg-[#FDFAF5] text-[#202824]">
      {/* Clean Modern Bright Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        isBackendOnline={isBackendOnline}
        onOpenDocs={() => setIsDocsOpen(true)}
        isCollapsed={isSidebarCollapsed}
        setIsCollapsed={setIsSidebarCollapsed}
        isMobileOpen={isMobileSidebarOpen}
        setIsMobileOpen={setIsMobileSidebarOpen}
      />

      {/* Main Column with smooth scroll container */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {/* Top Navbar */}
        <Navbar
          isBackendOnline={isBackendOnline}
          activeLanguage={language}
          onOpenDocs={() => setIsDocsOpen(true)}
          activeTab={activeTab}
          onToggleMobileSidebar={() => setIsMobileSidebarOpen(true)}
        />

        {/* Content Body */}
        <main className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8 space-y-6">
          {/* API / Backend Connection Warning Banner */}
          {apiError && (
            <div className="p-4 rounded-2xl bg-[#FEF2F2] border border-[#FECACA] text-[#D64545] flex items-start space-x-3 shadow-xs">
              <AlertCircle className="w-5 h-5 text-[#D64545] shrink-0 mt-0.5" />
              <div className="flex-1 text-xs">
                <span className="font-bold text-[#D64545]">Backend Connection Notice: </span>
                <span className="text-[#202824]">{apiError}</span>
              </div>
              <button
                onClick={() => handleAnalyze()}
                className="px-3 py-1 bg-[#D64545] hover:bg-[#B93838] rounded-xl text-xs font-semibold text-white transition-all flex items-center space-x-1 cursor-pointer shadow-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Retry</span>
              </button>
            </div>
          )}

          {/* View Tab 1: Dashboard / Code Analyzer */}
          {activeTab === 'dashboard' && (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
              {/* Left Column: Code Editor + Output Console (6 cols) */}
              <div className="lg:col-span-6 space-y-5">
                <CodeEditorPanel
                  code={code}
                  setCode={setCode}
                  language={language}
                  setLanguage={setLanguage}
                  languagesList={languagesList}
                  samplePresets={samplePresets}
                  onLoadPreset={handleLoadPreset}
                  onAnalyzeAndRun={handleAnalyzeAndRun}
                  onAnalyzeAST={handleAnalyze}
                  isRunning={isRunning}
                  errorLine={executionResult?.line || result?.syntax_error?.line}
                  stdinInput={stdinInput}
                  setStdinInput={setStdinInput}
                />

                {/* Output Console Component */}
                <OutputConsole
                  executionResult={executionResult}
                  result={result}
                  isRunning={isRunning}
                  code={code}
                  language={language}
                  onApplyFix={handleApplyFix}
                />
              </div>

              {/* Right Column: Results & Optimizations Panel (6 cols) */}
              <div className="lg:col-span-6 h-full">
                <ResultsPanel
                  result={result}
                  isAnalyzing={isAnalyzing}
                  onSwitchToPython={handleSwitchToPython}
                />
              </div>
            </div>
          )}

          {/* View Tab 2: Gemini AI Code Explainer */}
          {activeTab === 'ai-explainer' && (
            <AIExplainerPanel />
          )}

          {/* View Tab 3: Performance Dashboard (Dedicated Charts & Metrics) */}
          {activeTab === 'performance' && (
            <div className="space-y-6">
              <div className="bg-white rounded-2xl p-6 shadow-xs border border-[#E5E9E5] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-xl font-bold text-[#202824]">
                    Performance & Algorithmic Scaling Dashboard
                  </h2>
                  <p className="text-xs text-[#68736D] mt-0.5">
                    Visualizing theoretical computational scaling, issue distributions, and AST structural metrics.
                  </p>
                </div>
                <button
                  onClick={() => setActiveTab('dashboard')}
                  className="px-3 py-1.5 rounded-xl bg-[#F3F5F2] hover:bg-[#E5E9E5] text-xs font-semibold text-[#174F4A] transition-all cursor-pointer self-start sm:self-auto border border-[#E5E9E5]"
                >
                  ← Back to Code Analyzer
                </button>
              </div>

              <PerformanceDashboard result={result} />
            </div>
          )}

          {/* View Tab 4: Analysis History */}
          {activeTab === 'history' && (
            <HistoryPanel
              history={history}
              onLoadHistoryItem={handleLoadHistoryItem}
              onClearHistory={handleClearHistory}
              onRemoveHistoryItem={handleRemoveHistoryItem}
            />
          )}

          {/* View Tab 5: Settings */}
          {activeTab === 'settings' && (
            <SettingsPanel
              settings={settings}
              setSettings={setSettings}
              isBackendOnline={isBackendOnline}
              setIsBackendOnline={setIsBackendOnline}
            />
          )}
        </main>

        {/* Footer */}
        <Footer />
      </div>

      {/* Documentation Modal */}
      <DocsModal isOpen={isDocsOpen} onClose={() => setIsDocsOpen(false)} />
    </div>
  );
}
