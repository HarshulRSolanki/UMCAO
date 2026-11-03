import React from 'react';
import { X, ShieldCheck, Cpu, Code2, BookOpen, Layers } from 'lucide-react';

export default function DocsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
      <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] shadow-2xl border border-[#E5E9E5] flex flex-col overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Modal Header */}
        <div className="bg-[#F3F5F2] text-[#202824] p-5 border-b border-[#E5E9E5] flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#174F4A] text-white flex items-center justify-center">
              <BookOpen className="w-4 h-4 text-white" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#202824]">UMCAO Documentation & Architecture</h3>
              <p className="text-xs text-[#68736D]">Universal Multi-Language Code Analyzer & Optimizer</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white hover:bg-[#E5E9E5] text-[#68736D] hover:text-[#202824] border border-[#E5E9E5] transition-all cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 text-xs text-[#202824] leading-relaxed">
          {/* Security & Zero Server Execution */}
          <section className="p-4 bg-[#F0FDF4] rounded-xl border border-[#BBF7D0] space-y-2">
            <div className="flex items-center space-x-2 text-[#21865A] font-bold text-sm">
              <ShieldCheck className="w-5 h-5 text-[#21865A]" />
              <span>Zero Server-Side Execution Guarantee</span>
            </div>
            <p className="text-[#202824]">
              UMCAO <strong className="text-[#174F4A]">never executes, evaluates, or imports</strong> user-submitted code. All checks are performed
              via Python's built-in <code className="bg-white px-1.5 py-0.5 rounded text-[#174F4A] border border-[#BBF7D0] font-mono">ast</code> (Abstract Syntax Tree) module. User code is safely transformed into
              an in-memory AST data structure, parsed, and discarded.
            </p>
          </section>

          {/* Complexity Estimation Heuristics */}
          <section className="space-y-2">
            <h4 className="text-sm font-bold text-[#202824] flex items-center space-x-1.5">
              <Cpu className="w-4 h-4 text-[#174F4A]" />
              <span>Algorithmic Complexity & Big-O Estimation</span>
            </h4>
            <p className="text-[#68736D]">
              Complexity estimation is derived statically from structural AST attributes:
            </p>
            <ul className="list-disc list-inside space-y-1 text-[#202824] pl-2">
              <li>
                <strong className="text-[#174F4A]">Loop Nesting Depth:</strong> Depth 1 = O(N), Depth 2 = O(N²), Depth 3+ = O(N³).
              </li>
              <li>
                <strong className="text-[#174F4A]">Logarithmic Decrement:</strong> While-loops with halving operators (<code className="bg-[#F3F5F2] px-1 rounded text-[#174F4A] border border-[#E5E9E5] font-mono">//= 2</code>,{' '}
                <code className="bg-[#F3F5F2] px-1 rounded text-[#174F4A] border border-[#E5E9E5] font-mono">&gt;&gt;= 1</code>) are flagged as O(log N).
              </li>
              <li>
                <strong className="text-[#174F4A]">Branching Recursion:</strong> Recursive functions calling themselves multiple times without memoization
                are classified as O(2^N) exponential time.
              </li>
              <li>
                <strong className="text-[#174F4A]">Uncertainty Indicators:</strong> Static analysis cannot determine dynamic collection sizes or early loop
                exits without profiling; uncertainty is explicitly reported in every response.
              </li>
            </ul>
          </section>

          {/* Modular Multi-Language Engine */}
          <section className="space-y-2">
            <h4 className="text-sm font-bold text-[#202824] flex items-center space-x-1.5">
              <Layers className="w-4 h-4 text-[#174F4A]" />
              <span>Modular Multi-Language Architecture</span>
            </h4>
            <p className="text-[#68736D]">
              UMCAO uses a pluggable registry pattern (<code className="bg-[#F3F5F2] px-1 rounded text-[#174F4A] border border-[#E5E9E5] font-mono">BaseAnalyzer</code> interface). While Python uses the standard
              library <code className="bg-[#F3F5F2] px-1 rounded text-[#174F4A] border border-[#E5E9E5] font-mono">ast</code> parser, language analyzers for C, C++, Java, and JavaScript provide static syntax analysis,
              complexity estimation, and optimization suggestions without server-side execution.
            </p>
          </section>

          {/* Supported Static Rules */}
          <section className="space-y-2">
            <h4 className="text-sm font-bold text-[#202824] flex items-center space-x-1.5">
              <Code2 className="w-4 h-4 text-[#174F4A]" />
              <span>Active Static Analysis Rules</span>
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-[11px]">
              <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5] text-[#202824]">
                <strong className="text-[#174F4A] block mb-0.5">String Concatenation:</strong>
                Detects <code className="text-[#174F4A] font-mono font-bold">str += ...</code> in loops causing O(N²) memory reallocation.
              </div>
              <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5] text-[#202824]">
                <strong className="text-[#174F4A] block mb-0.5">List Search in Loop:</strong>
                Detects <code className="text-[#174F4A] font-mono font-bold">in list</code> inside loops creating O(N²) bottlenecks.
              </div>
              <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5] text-[#202824]">
                <strong className="text-[#174F4A] block mb-0.5">Unidiomatic range(len()):</strong>
                Flags index iteration vs Pythonic <code className="text-[#174F4A] font-mono font-bold">enumerate()</code>.
              </div>
              <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5] text-[#202824]">
                <strong className="text-[#174F4A] block mb-0.5">Un-memoized Recursion:</strong>
                Flags O(2^N) branching trees and suggests dynamic programming or caching.
              </div>
              <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5] text-[#202824]">
                <strong className="text-[#174F4A] block mb-0.5">Resource Leaks:</strong>
                Flags <code className="text-[#174F4A] font-mono font-bold">open()</code> calls without <code className="text-[#174F4A] font-mono font-bold">with</code> context managers.
              </div>
              <div className="p-3 bg-[#F3F5F2] rounded-xl border border-[#E5E9E5] text-[#202824]">
                <strong className="text-[#174F4A] block mb-0.5">Multiple Print Statements:</strong>
                Flags repeated print calls and recommends loop consolidation or helper functions.
              </div>
            </div>
          </section>
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-[#F3F5F2] border-t border-[#E5E9E5] flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-[#174F4A] hover:bg-[#123E3A] text-white text-xs font-bold shadow-xs transition-all cursor-pointer"
          >
            Close Documentation
          </button>
        </div>
      </div>
    </div>
  );
}
