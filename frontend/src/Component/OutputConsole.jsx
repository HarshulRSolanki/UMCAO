import React, { useState } from 'react';
import {
  Terminal,
  AlertTriangle,
  Info,
  CheckCircle2,
  Copy,
  Check,
  ChevronDown,
  ChevronUp,
  Cpu,
  ShieldCheck,
  Clock,
  Sparkles,
  ArrowRight,
  RotateCcw,
  AlertCircle,
  FileCode,
  Wand2,
} from 'lucide-react';
import { explainErrorWithGemini } from '../services/api';

export default function OutputConsole({
  executionResult,
  result, // AST result
  isRunning = false,
  code = '',
  language = 'python',
  onApplyFix,
}) {
  const [activeTab, setActiveTab] = useState('output');
  const [copied, setCopied] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Gemini Error Explanation state
  const [isDiagnosing, setIsDiagnosing] = useState(false);
  const [diagnosisResult, setDiagnosisResult] = useState(null);
  const [diagnosisError, setDiagnosisError] = useState(null);
  const [explanationLanguage, setExplanationLanguage] = useState('english');
  const [appliedFix, setAppliedFix] = useState(false);

  // Determine error state from execution result or AST result
  const execStatus = executionResult?.status;
  const isExecutionSuccess = executionResult?.success === true;
  const hasExecError =
    executionResult &&
    !executionResult.success &&
    ['syntax_error', 'compilation_failed', 'runtime_error', 'execution_timeout', 'tool_not_installed'].includes(
      execStatus
    );

  const stdout = executionResult?.stdout || '';
  const stderr = executionResult?.stderr || '';
  const errorMsg = executionResult?.error_message || stderr || '';
  const errorType = executionResult?.error_type || (execStatus === 'compilation_failed' ? 'CompilationError' : 'Error');
  const errorLine = executionResult?.line;
  const errorCol = executionResult?.column;
  const execTime = executionResult?.execution_time ?? 0.0;
  const exitCode = executionResult?.exit_code ?? (isExecutionSuccess ? 0 : 1);

  // Switch to errors tab automatically when an error is detected
  React.useEffect(() => {
    if (hasExecError) {
      setActiveTab('errors');
      setDiagnosisResult(null);
      setDiagnosisError(null);
      setAppliedFix(false);
    } else if (isExecutionSuccess && stdout) {
      setActiveTab('output');
    }
  }, [executionResult]);

  // Request error diagnosis from Gemini
  const handleDiagnoseError = async () => {
    if (!code || !hasExecError) return;
    setIsDiagnosing(true);
    setDiagnosisError(null);
    setDiagnosisResult(null);
    setAppliedFix(false);

    try {
      const data = await explainErrorWithGemini({
        code,
        language,
        errorMessage: errorMsg,
        errorType,
        line: errorLine,
        explanationLanguage,
      });
      setDiagnosisResult(data);
    } catch (err) {
      console.error('Gemini error diagnosis failed:', err);
      setDiagnosisError(err.message || 'Failed to explain error with Gemini. Please check API key in backend/.env.');
    } finally {
      setIsDiagnosing(false);
    }
  };

  const handleApplyFix = () => {
    if (diagnosisResult?.corrected_code && onApplyFix) {
      onApplyFix(diagnosisResult.corrected_code);
      setAppliedFix(true);
      setTimeout(() => setAppliedFix(false), 3000);
    }
  };

  const handleCopy = () => {
    let textToCopy = '';
    if (activeTab === 'output') {
      textToCopy = stdout || '[UMCAO Output Console: Program produced no standard output]';
    } else if (activeTab === 'errors') {
      textToCopy = hasExecError
        ? `Status: ${execStatus}\nType: ${errorType}\nLine: ${errorLine || 'N/A'}\nMessage: ${errorMsg}\n\nDetails:\n${stderr}`
        : 'No errors detected in current execution.';
    } else {
      textToCopy = `Language: ${language}\nStatus: ${execStatus || 'Ready'}\nExecution Time: ${execTime}s\nExit Code: ${exitCode}`;
    }
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Helper for human-readable status badge
  const renderStatusBadge = () => {
    if (isRunning) {
      return (
        <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#E0F2FE] text-[#0369A1] border border-[#BAE6FD] flex items-center space-x-1 animate-pulse">
          <span className="w-1.5 h-1.5 rounded-full bg-[#0369A1]" />
          <span>Executing...</span>
        </span>
      );
    }

    if (!executionResult) {
      return (
        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#F3F5F2] text-[#68736D] border border-[#E5E9E5]">
          Ready to Run
        </span>
      );
    }

    switch (execStatus) {
      case 'execution_successful':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#F0FDF4] text-[#21865A] border border-[#BBF7D0] flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3 text-[#21865A]" />
            <span>Execution Successful</span>
          </span>
        );
      case 'compilation_successful':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#F0FDF4] text-[#21865A] border border-[#BBF7D0]">
            Compilation Successful
          </span>
        );
      case 'syntax_error':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#FEF2F2] text-[#D64545] border border-[#FECACA] flex items-center space-x-1">
            <AlertTriangle className="w-3 h-3 text-[#D64545]" />
            <span>Syntax Error</span>
          </span>
        );
      case 'compilation_failed':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#FEF2F2] text-[#D64545] border border-[#FECACA] flex items-center space-x-1">
            <AlertTriangle className="w-3 h-3 text-[#D64545]" />
            <span>Compilation Failed</span>
          </span>
        );
      case 'runtime_error':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#FEF2F2] text-[#D64545] border border-[#FECACA] flex items-center space-x-1">
            <AlertCircle className="w-3 h-3 text-[#D64545]" />
            <span>Runtime Error</span>
          </span>
        );
      case 'execution_timeout':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#FEFCE8] text-[#D99A28] border border-[#FEF08A] flex items-center space-x-1">
            <Clock className="w-3 h-3 text-[#D99A28]" />
            <span>Execution Timeout</span>
          </span>
        );
      case 'tool_not_installed':
        return (
          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#FEFCE8] text-[#D99A28] border border-[#FEF08A] flex items-center space-x-1">
            <AlertTriangle className="w-3 h-3 text-[#D99A28]" />
            <span>Compiler Missing</span>
          </span>
        );
      default:
        return (
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#F3F5F2] text-[#68736D] border border-[#E5E9E5]">
            {execStatus || 'Complete'}
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] overflow-hidden flex flex-col transition-all">
      {/* Console Header Bar */}
      <div className="bg-[#F3F5F2] px-4 py-2.5 border-b border-[#E5E9E5] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-[#174F4A]" />
          <span className="text-xs font-bold text-[#202824] uppercase tracking-wider">Output Console</span>
          {renderStatusBadge()}
        </div>

        {/* Tabs: Output, Errors, Execution Info */}
        <div className="flex items-center space-x-2">
          <div className="flex items-center bg-white p-1 rounded-lg border border-[#E5E9E5]">
            {/* Output Tab */}
            <button
              onClick={() => {
                setActiveTab('output');
                setIsCollapsed(false);
              }}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'output' && !isCollapsed
                  ? 'bg-[#174F4A] text-white shadow-xs'
                  : 'text-[#68736D] hover:text-[#202824] hover:bg-[#F3F5F2]'
              }`}
            >
              <CheckCircle2
                className={`w-3.5 h-3.5 ${
                  activeTab === 'output' && !isCollapsed ? 'text-white' : 'text-[#21865A]'
                }`}
              />
              <span>Output</span>
            </button>

            {/* Errors Tab */}
            <button
              onClick={() => {
                setActiveTab('errors');
                setIsCollapsed(false);
              }}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'errors' && !isCollapsed
                  ? 'bg-[#174F4A] text-white shadow-xs'
                  : 'text-[#68736D] hover:text-[#202824] hover:bg-[#F3F5F2]'
              }`}
            >
              <AlertTriangle
                className={`w-3.5 h-3.5 ${
                  hasExecError
                    ? 'text-[#D64545]'
                    : activeTab === 'errors' && !isCollapsed
                    ? 'text-white'
                    : 'text-[#68736D]'
                }`}
              />
              <span>Errors</span>
              {hasExecError && (
                <span className="w-2 h-2 rounded-full bg-[#D64545] animate-pulse" />
              )}
            </button>

            {/* Execution Info Tab */}
            <button
              onClick={() => {
                setActiveTab('info');
                setIsCollapsed(false);
              }}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer flex items-center space-x-1.5 ${
                activeTab === 'info' && !isCollapsed
                  ? 'bg-[#174F4A] text-white shadow-xs'
                  : 'text-[#68736D] hover:text-[#202824] hover:bg-[#F3F5F2]'
              }`}
            >
              <Info
                className={`w-3.5 h-3.5 ${
                  activeTab === 'info' && !isCollapsed ? 'text-white' : 'text-[#3979B9]'
                }`}
              />
              <span>Execution Info</span>
            </button>
          </div>

          {/* Copy Button */}
          {!isCollapsed && (
            <button
              onClick={handleCopy}
              className="p-1 px-2 text-xs text-[#68736D] hover:text-[#202824] bg-white rounded-md border border-[#E5E9E5] transition-all flex items-center space-x-1 cursor-pointer shadow-xs"
              title="Copy Console Output"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-[#21865A]" /> : <Copy className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
            </button>
          )}

          {/* Collapse/Expand Toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1.5 rounded-lg text-[#68736D] hover:text-[#202824] bg-white border border-[#E5E9E5] transition-all cursor-pointer shadow-xs"
            title={isCollapsed ? 'Expand console' : 'Collapse console'}
          >
            {isCollapsed ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Console Body Area (Collapsible) */}
      {!isCollapsed && (
        <div className="p-4 bg-white font-mono text-xs min-h-[160px] max-h-[320px] overflow-y-auto leading-relaxed select-text">
          {isRunning && (
            <div className="flex items-center space-x-2 text-[#68736D] py-4">
              <div className="w-4 h-4 border-2 border-[#174F4A] border-t-transparent rounded-full animate-spin" />
              <span>Compiling and executing code in isolated sandbox...</span>
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 1: OUTPUT (Actual standard output)                   */}
          {/* ======================================================== */}
          {!isRunning && activeTab === 'output' && (
            <div>
              {!executionResult && (
                <div className="text-[#68736D] italic py-2">
                  // Program output will appear here. Click "Analyze & Run" to execute code.
                </div>
              )}

              {executionResult && isExecutionSuccess && (
                <div className="space-y-2">
                  {stdout ? (
                    <div className="p-3 bg-[#F8FAF8] rounded-xl border border-[#E5E9E5] text-[#202824] font-mono text-[12px] whitespace-pre-wrap leading-relaxed">
                      {stdout}
                    </div>
                  ) : (
                    <div className="p-3 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] text-[#21865A] text-xs font-mono">
                      // Process finished with exit code 0 (no output to stdout).
                    </div>
                  )}

                  <div className="flex items-center justify-between text-[11px] text-[#68736D] pt-1">
                    <span>
                      Language: <strong className="text-[#174F4A]">{language.toUpperCase()}</strong>
                    </span>
                    <span>
                      Duration: <strong>{(execTime * 1000).toFixed(1)} ms</strong>
                    </span>
                  </div>
                </div>
              )}

              {executionResult && !isExecutionSuccess && (
                <div className="p-3 bg-[#FEF2F2] border border-[#FECACA] rounded-xl text-[#D64545] space-y-1">
                  <div className="font-bold flex items-center space-x-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Execution halted due to an error.</span>
                  </div>
                  <div className="text-xs text-[#202824]">
                    Switch to the <strong>Errors</strong> tab to see full compiler/runtime diagnostics and get Gemini AI suggested fixes.
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 2: ERRORS (Syntax, Compilation, Runtime errors)     */}
          {/* ======================================================== */}
          {!isRunning && activeTab === 'errors' && (
            <div className="space-y-3">
              {hasExecError ? (
                <>
                  {/* Error Card */}
                  <div className="p-3.5 rounded-xl bg-[#FEF2F2] border border-[#FECACA] text-[#D64545] space-y-2">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center space-x-2 font-bold text-xs">
                        <AlertCircle className="w-4 h-4 text-[#D64545]" />
                        <span>
                          {errorType}: {errorMsg}
                        </span>
                      </div>
                      {errorLine && (
                        <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-white border border-[#FECACA] text-[#D64545]">
                          Line {errorLine} {errorCol ? `(col ${errorCol})` : ''}
                        </span>
                      )}
                    </div>

                    {/* Stderr Traceback / Diagnostics */}
                    {stderr && (
                      <div className="p-2.5 bg-white/80 rounded-lg border border-[#FECACA] text-[#202824] font-mono text-[11px] whitespace-pre-wrap max-h-40 overflow-y-auto">
                        {stderr}
                      </div>
                    )}
                  </div>

                  {/* Explain Error with Gemini AI Action Bar */}
                  <div className="p-3 bg-[#F0FDF4] rounded-xl border border-[#BBF7D0] flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-[#21865A]" />
                      <span className="text-xs font-bold text-[#174F4A]">
                        Explain Error with Gemini AI
                      </span>
                    </div>

                    <div className="flex items-center space-x-2">
                      {/* Language Selection */}
                      <select
                        value={explanationLanguage}
                        onChange={(e) => setExplanationLanguage(e.target.value)}
                        className="text-xs bg-white border border-[#BBF7D0] text-[#174F4A] rounded-lg px-2 py-1 focus:outline-none font-semibold cursor-pointer"
                      >
                        <option value="english">English</option>
                        <option value="gujarati">Gujarati</option>
                        <option value="hindi">Hindi</option>
                      </select>

                      <button
                        onClick={handleDiagnoseError}
                        disabled={isDiagnosing}
                        className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-bold text-white bg-[#174F4A] hover:bg-[#123E3A] transition-all cursor-pointer shadow-xs disabled:opacity-50"
                      >
                        {isDiagnosing ? (
                          <>
                            <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            <span>Diagnosing...</span>
                          </>
                        ) : (
                          <>
                            <Wand2 className="w-3 h-3" />
                            <span>Get AI Diagnosis</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Diagnosis Failure */}
                  {diagnosisError && (
                    <div className="p-3 bg-[#FEF2F2] border border-[#FECACA] rounded-xl text-xs text-[#D64545]">
                      <strong>AI Diagnosis Notice:</strong> {diagnosisError}
                    </div>
                  )}

                  {/* Gemini Error Diagnosis Display */}
                  {diagnosisResult && diagnosisResult.success && (
                    <div className="p-3.5 bg-white rounded-xl border border-[#BBF7D0] shadow-xs space-y-3">
                      <div className="flex items-center justify-between border-b border-[#E5E9E5] pb-2">
                        <span className="text-xs font-bold text-[#174F4A] flex items-center space-x-1">
                          <Sparkles className="w-3.5 h-3.5 text-[#21865A]" />
                          <span>Gemini Error Diagnosis & Fix ({explanationLanguage.toUpperCase()})</span>
                        </span>
                        {diagnosisResult.model_used && (
                          <span className="text-[10px] text-[#68736D] font-mono bg-[#F3F5F2] px-2 py-0.5 rounded">
                            {diagnosisResult.model_used}
                          </span>
                        )}
                      </div>

                      {/* Explanation Body */}
                      <div className="text-xs text-[#202824] leading-relaxed whitespace-pre-wrap font-sans">
                        {diagnosisResult.explanation}
                      </div>

                      {/* Corrected Code Preview & Apply Button */}
                      {diagnosisResult.corrected_code && (
                        <div className="pt-2 border-t border-[#E5E9E5] space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-[#21865A] flex items-center space-x-1">
                              <FileCode className="w-3.5 h-3.5" />
                              <span>Corrected Code Solution:</span>
                            </span>
                            {onApplyFix && (
                              <button
                                onClick={handleApplyFix}
                                className="px-3 py-1 bg-[#21865A] hover:bg-[#1A6C48] text-white text-xs font-bold rounded-lg transition-all flex items-center space-x-1 cursor-pointer shadow-xs"
                              >
                                {appliedFix ? (
                                  <>
                                    <Check className="w-3.5 h-3.5" />
                                    <span>Applied to Editor!</span>
                                  </>
                                ) : (
                                  <>
                                    <ArrowRight className="w-3.5 h-3.5" />
                                    <span>Apply Fix to Editor</span>
                                  </>
                                )}
                              </button>
                            )}
                          </div>
                          <pre className="p-2.5 bg-[#F3F5F2] rounded-lg text-[11px] font-mono text-[#202824] overflow-x-auto border border-[#E5E9E5]">
                            <code>{diagnosisResult.corrected_code}</code>
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </>
              ) : (
                <div className="p-3.5 rounded-xl bg-[#F0FDF4] border border-[#BBF7D0] text-[#21865A] flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-[#21865A]" />
                  <span className="font-semibold text-xs">
                    Clean compile and execution. No syntax errors, compiler diagnostics, or runtime exceptions found.
                  </span>
                </div>
              )}
            </div>
          )}

          {/* ======================================================== */}
          {/* TAB 3: EXECUTION INFO (Runtimes, Timings, Security)      */}
          {/* ======================================================== */}
          {!isRunning && activeTab === 'info' && (
            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-[#F3F5F2] border border-[#E5E9E5] text-[#202824] flex items-start space-x-2.5">
                <ShieldCheck className="w-4 h-4 text-[#21865A] shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold text-[#174F4A] block text-xs">
                    Isolated Subprocess Security Sandbox
                  </span>
                  <span className="text-[11px] text-[#68736D]">
                    Execution occurs in a strict isolated child process with a 5.0-second CPU timeout, sanitized environment (stripping API keys), and temporary file cleanup.
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
                <div className="p-2.5 rounded-xl bg-[#F3F5F2] border border-[#E5E9E5]">
                  <span className="text-[#68736D] block">Selected Language</span>
                  <span className="font-bold text-[#202824] uppercase">{language}</span>
                </div>

                <div className="p-2.5 rounded-xl bg-[#F3F5F2] border border-[#E5E9E5]">
                  <span className="text-[#68736D] block">Execution Status</span>
                  <span className="font-bold text-[#174F4A]">{execStatus || 'Idle / Not Run'}</span>
                </div>

                <div className="p-2.5 rounded-xl bg-[#F3F5F2] border border-[#E5E9E5]">
                  <span className="text-[#68736D] block">Process Duration</span>
                  <span className="font-bold text-[#202824]">
                    {execTime > 0 ? `${(execTime * 1000).toFixed(1)} ms (${execTime} s)` : 'N/A'}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-[#F3F5F2] border border-[#E5E9E5]">
                  <span className="text-[#68736D] block">Process Exit Code</span>
                  <span className={`font-mono font-bold ${exitCode === 0 ? 'text-[#21865A]' : 'text-[#D64545]'}`}>
                    {exitCode}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-[#F3F5F2] border border-[#E5E9E5]">
                  <span className="text-[#68736D] block">AST Static Complexity</span>
                  <span className="font-bold text-[#174F4A]">
                    {result?.complexity?.time_complexity || 'O(1)'}
                  </span>
                </div>

                <div className="p-2.5 rounded-xl bg-[#F3F5F2] border border-[#E5E9E5]">
                  <span className="text-[#68736D] block">AST Nodes</span>
                  <span className="font-bold text-[#202824]">
                    {result?.ast_metrics?.total_nodes || 0}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
