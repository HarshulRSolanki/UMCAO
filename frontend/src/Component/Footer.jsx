import React from 'react';
import { Terminal, ShieldCheck } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="mt-auto bg-white border-t border-[#E5E9E5] py-5 px-6">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between text-xs text-[#68736D] gap-3">
        <div className="flex items-center space-x-2">
          <div className="w-5 h-5 rounded-md bg-[#174F4A] text-white flex items-center justify-center">
            <Terminal className="w-3 h-3 text-white" />
          </div>
          <span className="font-bold text-[#202824] font-mono">UMCAO</span>
          <span>— Universal Multi-Language Code Analyzer and Optimizer</span>
        </div>

        <div className="flex items-center space-x-4 text-[11px]">
          <div className="flex items-center space-x-1 text-[#21865A]">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Zero Server-Side Code Execution</span>
          </div>
          <span className="text-[#8E9993]">•</span>
          <span>Python AST + Google Gemini AI</span>
        </div>
      </div>
    </footer>
  );
}
