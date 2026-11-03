import React, { useState } from 'react';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  HardDrive,
  Zap,
  Code2,
  FileJson,
  Copy,
  Download,
  Check,
  Info,
  TrendingDown,
  Layers,
  HelpCircle,
  Sparkles,
} from 'lucide-react';
import UnsupportedLanguageNotice from './UnsupportedLanguageNotice';

export default function ResultsPanel({ result, isAnalyzing, onSwitchToPython }) {
  const [activeTab, setActiveTab] = useState('optimizations');
  const [copiedJson, setCopiedJson] = useState(false);

  if (isAnalyzing) {
    return (
      <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] p-12 flex flex-col items-center justify-center min-h-[460px] text-center">
        <div className="w-12 h-12 rounded-full border-4 border-[#E5E9E5] border-t-[#174F4A] animate-spin mb-4" />
        <h3 className="text-lg font-bold text-[#202824]">Parsing Abstract Syntax Tree...</h3>
        <p className="text-xs text-[#68736D] mt-1 max-w-sm">
          Extracting AST nodes, inspecting loop depths, tracking recursion, and evaluating algorithmic patterns.
        </p>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] p-10 flex flex-col items-center justify-center min-h-[460px] text-center">
        <div className="w-14 h-14 rounded-2xl bg-[#F3F5F2] text-[#174F4A] flex items-center justify-center mb-4 border border-[#E5E9E5] shadow-xs">
          <Code2 className="w-7 h-7 text-[#174F4A]" />
        </div>
        <h3 className="text-xl font-bold text-[#202824]">Ready for Static Code Analysis</h3>
        <p className="text-xs text-[#68736D] mt-2 max-w-md leading-relaxed">
          Paste your code on the left or select a preset snippet, then click{' '}
          <strong className="text-[#174F4A]">"Analyze Code"</strong> to run structural AST diagnosis, algorithmic complexity
          estimation, and optimization suggestions.
        </p>
        <div className="mt-6 flex flex-wrap gap-2 justify-center text-xs text-[#68736D]">
          <span className="px-3 py-1 bg-[#F3F5F2] rounded-full border border-[#E5E9E5] text-[#202824] font-medium">✓ Zero code execution</span>
          <span className="px-3 py-1 bg-[#F3F5F2] rounded-full border border-[#E5E9E5] text-[#202824] font-medium">✓ Python AST Engine</span>
          <span className="px-3 py-1 bg-[#F3F5F2] rounded-full border border-[#E5E9E5] text-[#202824] font-medium">✓ Complexity Big-O</span>
        </div>
      </div>
    );
  }

  // Handle Unsupported Languages (C, C++, Java, JavaScript)
  if (result.status === 'unsupported_language' || !result.supported) {
    return <UnsupportedLanguageNotice result={result} onSwitchToPython={onSwitchToPython} />;
  }

  // Handle Syntax Errors
  if (result.status === 'syntax_error' && result.syntax_error?.has_error) {
    const err = result.syntax_error;
    return (
      <div className="bg-white rounded-2xl shadow-xs border border-[#FECACA] overflow-hidden">
        <div className="bg-[#FEF2F2] p-6 border-b border-[#FECACA]">
          <div className="flex items-start space-x-3">
            <div className="p-2 rounded-xl bg-white text-[#D64545] border border-[#FECACA] shrink-0 shadow-xs">
              <AlertTriangle className="w-6 h-6 text-[#D64545]" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-white text-[#D64545] border border-[#FECACA]">
                  Syntax Error Detected
                </span>
                <span className="text-xs font-mono text-[#D64545] font-semibold">
                  Line {err.line}, Column {err.column}
                </span>
              </div>
              <h3 className="text-base font-bold text-[#D64545] mt-1.5">{err.message}</h3>
              <p className="text-xs text-[#202824] mt-2 leading-relaxed bg-white/90 p-3 rounded-xl border border-[#FECACA]">
                💡 <strong className="text-[#21865A]">How to fix:</strong> {err.friendly_explanation}
              </p>
            </div>
          </div>
        </div>

        {err.text && (
          <div className="p-6 bg-white text-[#202824] font-mono text-xs">
            <div className="text-[11px] text-[#68736D] mb-1.5">// Erroneous Line {err.line}:</div>
            <div className="p-3 bg-[#FEF2F2] rounded-xl border border-[#FECACA] text-[#D64545]">
              {err.text}
            </div>
            {err.column && (
              <div className="text-[#D64545] text-[11px] pl-3 mt-1 select-none font-mono">
                {' '.repeat(Math.max(err.column - 1, 0))}^ [Syntax error starts here]
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  // Successful Analysis View
  const complexity = result.complexity;
  const patterns = result.patterns || [];
  const optimizations = result.optimizations || [];
  const astMetrics = result.ast_metrics;

  const handleCopyJson = () => {
    navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  const handleDownloadJson = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `umcao-analysis-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      {/* Top Metrics Cards Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {/* Time Complexity */}
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-[#E5E9E5] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-[#68736D] font-bold">
            <span>Time Complexity</span>
            <Clock className="w-4 h-4 text-[#174F4A]" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold font-mono text-[#174F4A]">
              {complexity?.time_complexity || 'O(?)'}
            </div>
            <div className="mt-1 flex items-center space-x-1.5">
              <span
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                  complexity?.confidence === 'high'
                    ? 'bg-[#F0FDF4] text-[#21865A] border-[#BBF7D0]'
                    : complexity?.confidence === 'medium'
                    ? 'bg-[#FEFCE8] text-[#D99A28] border-[#FEF08A]'
                    : 'bg-[#F3F5F2] text-[#68736D] border-[#E5E9E5]'
                }`}
              >
                {complexity?.confidence?.toUpperCase()} CONFIDENCE
              </span>
            </div>
          </div>
        </div>

        {/* Space Complexity */}
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-[#E5E9E5] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-[#68736D] font-bold">
            <span>Space Complexity</span>
            <HardDrive className="w-4 h-4 text-[#174F4A]" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold font-mono text-[#202824]">
              {complexity?.space_complexity || 'O(?)'}
            </div>
            <div className="mt-1 text-[11px] text-[#68736D] truncate">
              Auxiliary RAM Allocation
            </div>
          </div>
        </div>

        {/* Inefficient Patterns */}
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-[#E5E9E5] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-[#68736D] font-bold">
            <span>Detected Patterns</span>
            <AlertTriangle className="w-4 h-4 text-[#D99A28]" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold font-mono text-[#D99A28]">
              {patterns.length}
            </div>
            <div className="mt-1 text-[11px] text-[#68736D]">
              {patterns.filter((p) => p.severity === 'high').length} High Severity
            </div>
          </div>
        </div>

        {/* Optimizations */}
        <div className="bg-white p-4 rounded-2xl shadow-xs border border-[#E5E9E5] flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-[#68736D] font-bold">
            <span>Optimizations</span>
            <Zap className="w-4 h-4 text-[#21865A]" />
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold font-mono text-[#21865A]">
              {optimizations.length}
            </div>
            <div className="mt-1 text-[11px] text-[#68736D]">
              Refactoring Opportunities
            </div>
          </div>
        </div>
      </div>

      {/* Main Results Container with Tabs */}
      <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] overflow-hidden">
        {/* Navigation Tabs Header */}
        <div className="bg-[#F3F5F2] px-4 border-b border-[#E5E9E5] flex flex-wrap items-center justify-between gap-2">
          <div className="flex space-x-1 sm:space-x-2 overflow-x-auto py-2">
            <button
              onClick={() => setActiveTab('optimizations')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 cursor-pointer ${
                activeTab === 'optimizations'
                  ? 'bg-[#174F4A] text-white shadow-xs font-bold'
                  : 'text-[#68736D] hover:text-[#202824] hover:bg-white'
              }`}
            >
              <Zap className={`w-3.5 h-3.5 ${activeTab === 'optimizations' ? 'text-white' : 'text-[#21865A]'}`} />
              <span>Optimizations ({optimizations.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('patterns')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 cursor-pointer ${
                activeTab === 'patterns'
                  ? 'bg-[#174F4A] text-white shadow-xs font-bold'
                  : 'text-[#68736D] hover:text-[#202824] hover:bg-white'
              }`}
            >
              <AlertTriangle className={`w-3.5 h-3.5 ${activeTab === 'patterns' ? 'text-white' : 'text-[#D99A28]'}`} />
              <span>Inefficiencies ({patterns.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('complexity')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 cursor-pointer ${
                activeTab === 'complexity'
                  ? 'bg-[#174F4A] text-white shadow-xs font-bold'
                  : 'text-[#68736D] hover:text-[#202824] hover:bg-white'
              }`}
            >
              <Layers className={`w-3.5 h-3.5 ${activeTab === 'complexity' ? 'text-white' : 'text-[#68736D]'}`} />
              <span>Complexity & AST</span>
            </button>

            <button
              onClick={() => setActiveTab('json')}
              className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center space-x-1.5 cursor-pointer ${
                activeTab === 'json'
                  ? 'bg-[#174F4A] text-white shadow-xs font-bold'
                  : 'text-[#68736D] hover:text-[#202824] hover:bg-white'
              }`}
            >
              <FileJson className={`w-3.5 h-3.5 ${activeTab === 'json' ? 'text-white' : 'text-[#68736D]'}`} />
              <span>Structured JSON</span>
            </button>
          </div>
        </div>

        {/* Tab Content Body */}
        <div className="p-5">
          {/* TAB 1: OPTIMIZATIONS */}
          {activeTab === 'optimizations' && (
            <div className="space-y-4">
              {optimizations.length === 0 ? (
                <div className="p-8 text-center bg-[#F3F5F2] rounded-2xl border border-[#E5E9E5]">
                  <CheckCircle className="w-8 h-8 text-[#21865A] mx-auto mb-2" />
                  <h4 className="font-bold text-[#202824]">No Major Optimizations Flagged</h4>
                  <p className="text-xs text-[#68736D] mt-1 max-w-sm mx-auto">
                    The analyzed code conforms to standard idiomatic patterns and does not exhibit known static bottlenecks.
                  </p>
                </div>
              ) : (
                optimizations.map((opt) => (
                  <div
                    key={opt.id}
                    className="border border-[#E5E9E5] hover:border-[#174F4A]/30 rounded-2xl overflow-hidden bg-white shadow-xs transition-all"
                  >
                    <div className="p-4 bg-[#F3F5F2] border-b border-[#E5E9E5] flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center space-x-2">
                        <span className="p-1.5 rounded-lg bg-[#F0FDF4] text-[#21865A] border border-[#BBF7D0]">
                          <Zap className="w-4 h-4 text-[#21865A]" />
                        </span>
                        <h4 className="font-bold text-sm text-[#202824]">{opt.title}</h4>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-white text-[#202824] border border-[#E5E9E5] font-bold uppercase">
                          {opt.impact} Impact
                        </span>
                        <span className="text-[11px] px-2.5 py-0.5 rounded-full bg-white text-[#68736D] border border-[#E5E9E5]">
                          {opt.category}
                        </span>
                      </div>
                    </div>

                    <div className="p-4 space-y-3">
                      <p className="text-xs text-[#202824] leading-relaxed">{opt.explanation}</p>

                      {/* Before vs After Code Comparison */}
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 pt-1">
                        {/* Original */}
                        <div className="rounded-xl overflow-hidden border border-[#FECACA]">
                          <div className="bg-[#FEF2F2] px-3 py-1.5 text-[11px] font-bold text-[#D64545] border-b border-[#FECACA] flex items-center justify-between">
                            <span>Original Inefficient Pattern</span>
                            <span className="text-[#D64545] font-mono text-[10px]">CURRENT</span>
                          </div>
                          <pre className="p-3 bg-[#FFF5F5] text-[#D64545] font-mono text-xs overflow-x-auto leading-relaxed">
                            {opt.original_code}
                          </pre>
                        </div>

                        {/* Optimized */}
                        <div className="rounded-xl overflow-hidden border border-[#BBF7D0]">
                          <div className="bg-[#F0FDF4] px-3 py-1.5 text-[11px] font-bold text-[#21865A] border-b border-[#BBF7D0] flex items-center justify-between">
                            <span>Recommended Optimization</span>
                            <span className="text-[#21865A] font-mono text-[10px]">OPTIMIZED</span>
                          </div>
                          <pre className="p-3 bg-[#F6FEF9] text-[#21865A] font-mono text-xs overflow-x-auto leading-relaxed">
                            {opt.optimized_code}
                          </pre>
                        </div>
                      </div>

                      {/* Theoretical Benefit */}
                      <div className="flex items-center space-x-2 text-[11px] text-[#202824] bg-[#F3F5F2] p-2.5 rounded-xl border border-[#E5E9E5]">
                        <TrendingDown className="w-4 h-4 text-[#21865A] shrink-0" />
                        <span>
                          <strong className="text-[#174F4A]">Theoretical Benefit:</strong> {opt.theoretical_benefit}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* TAB 2: INEFFICIENT PATTERNS */}
          {activeTab === 'patterns' && (
            <div className="space-y-3">
              {patterns.length === 0 ? (
                <div className="p-8 text-center bg-[#F3F5F2] rounded-2xl border border-[#E5E9E5]">
                  <CheckCircle className="w-8 h-8 text-[#21865A] mx-auto mb-2" />
                  <h4 className="font-bold text-[#202824]">Clean Code</h4>
                  <p className="text-xs text-[#68736D] mt-1">
                    No anti-patterns or inefficiencies were triggered during static analysis.
                  </p>
                </div>
              ) : (
                patterns.map((pat) => (
                  <div
                    key={pat.id}
                    className="p-4 rounded-2xl border border-[#E5E9E5] hover:border-[#174F4A]/30 bg-white shadow-xs space-y-2.5 transition-all"
                  >
                    <div className="flex items-center justify-between flex-wrap gap-2">
                      <div className="flex items-center space-x-2">
                        <span
                          className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase border ${
                            pat.severity === 'high'
                              ? 'bg-[#FEF2F2] text-[#D64545] border-[#FECACA]'
                              : pat.severity === 'medium'
                              ? 'bg-[#FEFCE8] text-[#D99A28] border-[#FEF08A]'
                              : 'bg-[#F3F5F2] text-[#68736D] border-[#E5E9E5]'
                          }`}
                        >
                          {pat.severity}
                        </span>
                        <h4 className="font-bold text-sm text-[#202824]">{pat.title}</h4>
                      </div>
                      {pat.line && (
                        <span className="text-xs font-mono text-[#68736D] bg-[#F3F5F2] px-2 py-0.5 rounded border border-[#E5E9E5]">
                          Line {pat.line}
                        </span>
                      )}
                    </div>

                    {pat.snippet && (
                      <div className="p-2.5 bg-[#F3F5F2] rounded-xl font-mono text-xs text-[#202824] border border-[#E5E9E5] overflow-x-auto">
                        {pat.snippet}
                      </div>
                    )}

                    <p className="text-xs text-[#202824] leading-relaxed">{pat.explanation}</p>

                    <div className="text-xs font-medium text-[#202824] bg-[#F0FDF4] p-2.5 rounded-xl border border-[#BBF7D0] flex items-start space-x-1.5">
                      <span className="font-bold text-[#21865A]">💡 Suggestion:</span>
                      <span>{pat.suggestion}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* TAB 3: COMPLEXITY & AST DETAILS */}
          {activeTab === 'complexity' && (
            <div className="space-y-5">
              {/* Complexity Rationale Box */}
              <div className="p-5 bg-white rounded-2xl border border-[#E5E9E5] space-y-3 shadow-xs">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-[#202824] flex items-center space-x-1.5">
                    <Clock className="w-4 h-4 text-[#174F4A]" />
                    <span>Complexity Structural Reasoning</span>
                  </h4>
                  <span className="text-xs font-mono font-bold text-[#174F4A] bg-[#F0FDF4] px-2.5 py-1 rounded-full border border-[#BBF7D0]">
                    {complexity?.time_complexity} Time / {complexity?.space_complexity} Space
                  </span>
                </div>

                <ul className="text-xs text-[#202824] space-y-1.5 list-disc list-inside">
                  {complexity?.reasons?.map((reason, i) => (
                    <li key={i} className="leading-relaxed">
                      {reason}
                    </li>
                  ))}
                </ul>

                {/* Uncertainty Factors */}
                {complexity?.uncertainty_factors && complexity.uncertainty_factors.length > 0 && (
                  <div className="pt-2 border-t border-[#E5E9E5]">
                    <div className="text-xs font-semibold text-[#D99A28] flex items-center space-x-1 mb-1.5">
                      <HelpCircle className="w-3.5 h-3.5 text-[#D99A28]" />
                      <span>Uncertainty & Runtime Factors:</span>
                    </div>
                    <ul className="text-xs text-[#202824] space-y-1 list-disc list-inside bg-[#FEFCE8] p-2.5 rounded-xl border border-[#FEF08A]">
                      {complexity.uncertainty_factors.map((factor, i) => (
                        <li key={i}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <p className="text-[11px] text-[#68736D] italic pt-1">
                  * {complexity?.disclaimer}
                </p>
              </div>

              {/* AST Metrics Breakdown */}
              {astMetrics && (
                <div>
                  <h4 className="font-bold text-xs uppercase tracking-wider text-[#68736D] mb-3">
                    Abstract Syntax Tree Node Distribution
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-center">
                    <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5]">
                      <div className="text-xl font-bold font-mono text-[#174F4A]">
                        {astMetrics.total_nodes}
                      </div>
                      <div className="text-[11px] text-[#68736D]">Total AST Nodes</div>
                    </div>
                    <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5]">
                      <div className="text-xl font-bold font-mono text-[#174F4A]">
                        {astMetrics.max_nesting_depth}
                      </div>
                      <div className="text-[11px] text-[#68736D]">Max Nesting Depth</div>
                    </div>
                    <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5]">
                      <div className="text-xl font-bold font-mono text-[#174F4A]">
                        {astMetrics.loops_count}
                      </div>
                      <div className="text-[11px] text-[#68736D]">Loop Blocks</div>
                    </div>
                    <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5]">
                      <div className="text-xl font-bold font-mono text-[#174F4A]">
                        {astMetrics.branches_count}
                      </div>
                      <div className="text-[11px] text-[#68736D]">Branches / Conditions</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 4: STRUCTURED JSON */}
          {activeTab === 'json' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs text-[#68736D]">
                <span>Complete API Response Payload in Valid Structured JSON:</span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={handleCopyJson}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-white hover:bg-[#F3F5F2] text-[#202824] border border-[#E5E9E5] transition-all font-semibold cursor-pointer shadow-xs"
                  >
                    {copiedJson ? <Check className="w-3.5 h-3.5 text-[#21865A]" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedJson ? 'Copied' : 'Copy JSON'}</span>
                  </button>
                  <button
                    onClick={handleDownloadJson}
                    className="flex items-center space-x-1 px-3 py-1.5 rounded-xl bg-[#174F4A] hover:bg-[#123E3A] text-white transition-all font-bold cursor-pointer shadow-xs"
                  >
                    <Download className="w-3.5 h-3.5 text-white" />
                    <span>Download .json</span>
                  </button>
                </div>
              </div>

              <div className="rounded-2xl overflow-hidden border border-[#E5E9E5]">
                <pre className="p-4 bg-[#F3F5F2] text-[#202824] font-mono text-xs leading-relaxed max-h-[460px] overflow-auto">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
