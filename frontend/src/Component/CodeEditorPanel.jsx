import React, { useRef, useState } from 'react';
import {
  Play,
  Copy,
  Trash2,
  Check,
  ShieldCheck,
  AlertCircle,
  Terminal,
  ChevronDown,
  ChevronUp,
  Sparkles,
} from 'lucide-react';

export default function CodeEditorPanel({
  code,
  setCode,
  language,
  setLanguage,
  languagesList,
  samplePresets,
  onLoadPreset,
  onAnalyzeAndRun,
  onAnalyzeAST,
  isRunning = false,
  errorLine = null,
  stdinInput = '',
  setStdinInput,
}) {
  const [copied, setCopied] = useState(false);
  const [showStdin, setShowStdin] = useState(false);
  const textareaRef = useRef(null);
  const lineNumbersRef = useRef(null);

  // Sync scroll between textarea and line numbers
  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Support Ctrl+Enter for quick Analyze & Run, and Tab for 4 spaces
  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (onAnalyzeAndRun) onAnalyzeAndRun();
      return;
    }

    if (e.key === 'Tab') {
      e.preventDefault();
      const start = e.target.selectionStart;
      const end = e.target.selectionEnd;
      const newCode = code.substring(0, start) + '    ' + code.substring(end);
      setCode(newCode);
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.selectionStart = textareaRef.current.selectionEnd = start + 4;
        }
      }, 0);
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lineCount = Math.max(code.split('\n').length, 1);
  const linesArray = Array.from({ length: lineCount }, (_, i) => i + 1);

  // Format placeholder per language
  const getPlaceholder = () => {
    switch (language) {
      case 'c':
        return '// Enter C source code here...\n#include <stdio.h>\n\nint main() {\n    printf("Hello UMCAO\\n");\n    return 0;\n}';
      case 'cpp':
        return '// Enter C++ source code here...\n#include <iostream>\n\nint main() {\n    std::cout << "Hello UMCAO" << std::endl;\n    return 0;\n}';
      case 'java':
        return '// Enter Java source code here...\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello UMCAO");\n    }\n}';
      case 'javascript':
        return '// Enter JavaScript (Node.js) code here...\nconsole.log("Hello UMCAO");\nconsole.log(10 + 20);';
      default:
        return '# Enter Python code here...\nprint("Hello UMCAO")\nprint(10 + 20)';
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] overflow-hidden flex flex-col h-full transition-all">
      {/* Editor Header Bar */}
      <div className="bg-[#F3F5F2] px-4 py-3 border-b border-[#E5E9E5] flex flex-wrap items-center justify-between gap-3">
        {/* Language Selector */}
        <div className="flex items-center space-x-2">
          <label htmlFor="language-select" className="text-xs font-bold text-[#68736D] uppercase tracking-wider">
            Language:
          </label>
          <div className="relative">
            <select
              id="language-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="text-xs font-bold bg-white border border-[#E5E9E5] text-[#202824] rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#174F4A] transition-all cursor-pointer shadow-xs"
            >
              {languagesList.map((lang) => (
                <option key={lang.id} value={lang.id} className="bg-white text-[#202824]">
                  {lang.name}
                </option>
              ))}
            </select>
          </div>
          {['python', 'javascript'].includes(language) ? (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#F0FDF4] text-[#21865A] font-bold border border-[#BBF7D0]">
              Runtime Ready
            </span>
          ) : (
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#FEFCE8] text-[#D99A28] font-bold border border-[#FEF08A]">
              Compiler Support
            </span>
          )}
        </div>

        {/* Presets & Utility Controls */}
        <div className="flex items-center flex-wrap gap-2">
          {samplePresets && samplePresets.length > 0 && (
            <div className="relative">
              <select
                onChange={(e) => {
                  if (e.target.value) {
                    onLoadPreset(e.target.value);
                    e.target.value = '';
                  }
                }}
                defaultValue=""
                className="text-xs bg-white border border-[#E5E9E5] text-[#202824] hover:bg-[#F3F5F2] rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-2 focus:ring-[#174F4A] transition-all cursor-pointer font-medium shadow-xs"
              >
                <option value="" disabled className="text-[#68736D]">
                  ⚡ Load Preset Snippet...
                </option>
                {samplePresets.map((preset) => (
                  <option key={preset.id} value={preset.id} className="text-[#202824]">
                    {preset.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Stdin Toggle */}
          {setStdinInput && (
            <button
              onClick={() => setShowStdin(!showStdin)}
              className={`p-1.5 px-2.5 text-xs rounded-lg border transition-all flex items-center space-x-1 cursor-pointer shadow-xs ${showStdin || (stdinInput && stdinInput.trim())
                ? 'bg-[#174F4A]/10 text-[#174F4A] border-[#174F4A]/30 font-bold'
                : 'bg-white text-[#68736D] hover:text-[#202824] hover:bg-[#F3F5F2] border-[#E5E9E5]'
                }`}
              title="Toggle Standard Input (stdin)"
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>stdin</span>
              {showStdin ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>
          )}

          <button
            onClick={handleCopy}
            className="p-1.5 px-2 text-xs text-[#68736D] hover:text-[#202824] bg-white hover:bg-[#F3F5F2] rounded-lg border border-[#E5E9E5] transition-all flex items-center space-x-1 cursor-pointer shadow-xs"
            title="Copy Code"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-[#21865A]" /> : <Copy className="w-3.5 h-3.5" />}
            <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
          </button>

          <button
            onClick={() => setCode('')}
            className="p-1.5 px-2 text-xs text-[#68736D] hover:text-[#D64545] bg-white hover:bg-[#FEF2F2] rounded-lg border border-[#E5E9E5] hover:border-[#FECACA] transition-all flex items-center space-x-1 cursor-pointer shadow-xs"
            title="Clear Code"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Clear</span>
          </button>
        </div>
      </div>

      {/* Optional Stdin Input Drawer */}
      {showStdin && setStdinInput && (
        <div className="bg-[#F8FAF8] border-b border-[#E5E9E5] p-3 text-xs">
          <div className="flex items-center justify-between mb-1.5">
            <span className="font-bold text-[#174F4A] flex items-center space-x-1">
              <Terminal className="w-3.5 h-3.5" />
              <span>Standard Input (stdin)</span>
            </span>
            <span className="text-[11px] text-[#68736D]">Supplied to input() / scanf / cin</span>
          </div>
          <textarea
            value={stdinInput}
            onChange={(e) => setStdinInput(e.target.value)}
            rows={2}
            placeholder="Type standard input lines here (e.g. for user input prompts)..."
            className="w-full p-2 bg-white border border-[#E5E9E5] rounded-lg font-mono text-xs text-[#202824] focus:outline-none focus:ring-1 focus:ring-[#174F4A] resize-y"
          />
        </div>
      )}

      {/* Editor Body with Line Numbers and Code Textarea */}
      <div className="relative h-[420px] lg:h-[460px] bg-white flex text-[#111816] overflow-hidden">
        {/* Line Numbers Gutter */}
        <div
          ref={lineNumbersRef}
          className="w-12 h-full py-3 bg-[#F3F5F2] text-[#68736D] text-right pr-3 select-none overflow-hidden border-r border-[#E5E9E5] font-mono shrink-0"
          style={{
            fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', Consolas, 'Courier New', monospace",
            fontSize: '13px',
            lineHeight: '24px',
          }}
        >
          {linesArray.map((num) => {
            const isErrorLine = errorLine === num;
            return (
              <div
                key={num}
                className={`h-[24px] leading-[24px] text-[12px] transition-colors ${isErrorLine
                  ? 'bg-[#FEF2F2] text-[#D64545] font-bold -mr-3 pr-3 border-r-2 border-[#D64545]'
                  : 'text-[#68736D]'
                  }`}
                title={isErrorLine ? `Error on line ${num}` : undefined}
              >
                {num}
              </div>
            );
          })}
        </div>

        {/* Code Textarea Wrapper with absolute positioning to guarantee 100% full height */}
        <div className="flex-1 relative h-full min-w-0">
          <textarea
            ref={textareaRef}
            value={code}
            onChange={(e) => setCode(e.target.value)}
            onScroll={handleScroll}
            onKeyDown={handleKeyDown}
            placeholder={getPlaceholder()}
            spellCheck={false}
            autoCapitalize="off"
            autoComplete="off"
            autoCorrect="soft"
            wrap="off"
            style={{
              fontFamily: "'Cascadia Code', 'Fira Code', 'JetBrains Mono', Consolas, 'Courier New', monospace",
              fontSize: '13px',
              lineHeight: '24px',
              tabSize: 4,
              MozTabSize: 4,
            }}
            className="absolute inset-0 w-full h-full p-3 bg-white text-[#111816] font-medium selection:bg-[#174F4A]/20 selection:text-[#174F4A] resize-none outline-none overflow-auto focus:ring-0 focus:outline-none placeholder:text-[#8E9993] border-0 m-0 whitespace-pre-wrap break-words"
          />
        </div>
      </div>

      {/* Editor Footer & Actions */}
      <div className="bg-[#F3F5F2] px-4 py-3 border-t border-[#E5E9E5] flex flex-wrap items-center justify-between gap-3">
        {/* Metrics & Sandbox Safety Notice */}
        <div className="flex items-center space-x-4 text-xs text-[#68736D]">
          <div className="flex items-center space-x-1 font-mono">
            <span className="font-bold text-[#202824]">{lineCount}</span>
            <span>lines</span>
            <span className="text-[#8E9993]">•</span>
            <span className="font-bold text-[#202824]">{code.length}</span>
            <span>chars</span>
          </div>

          <div className="hidden sm:flex items-center space-x-1 text-[#202824] bg-white px-2.5 py-1 rounded-md border border-[#E5E9E5] shadow-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-[#21865A]" />
            <span className="text-[11px] font-medium">Safe Subprocess Sandbox (5s Timeout)</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          {onAnalyzeAST && (
            <button
              onClick={onAnalyzeAST}
              disabled={isRunning}
              className="hidden md:inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-[#174F4A] bg-white hover:bg-[#E5E9E5] border border-[#E5E9E5] transition-all cursor-pointer shadow-xs disabled:opacity-50"
              title="Run Static AST Complexity Analysis without executing"
            >
              <span>AST Only</span>
            </button>
          )}

          <span className="hidden md:inline text-[11px] text-[#68736D] font-mono">
            Ctrl + Enter
          </span>

          <button
            onClick={onAnalyzeAndRun}
            disabled={isRunning}
            className={`flex items-center space-x-2 px-5 py-2.5 rounded-xl text-xs font-bold shadow-xs transition-all ${isRunning
              ? 'bg-zinc-200 text-zinc-500 cursor-not-allowed border border-zinc-300'
              : 'bg-[#174F4A] hover:bg-[#123E3A] text-white active:scale-98 cursor-pointer'
              }`}
          >
            {isRunning ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                </svg>
                <span>Compiling & Running...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Analyze & Run</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
