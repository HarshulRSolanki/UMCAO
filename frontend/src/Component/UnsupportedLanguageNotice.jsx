import React from 'react';
import { Construction, Sparkles, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function UnsupportedLanguageNotice({ result, onSwitchToPython }) {
  const roadmap = result.roadmap_info;
  const langDisplay = roadmap?.display_name || result.language?.toUpperCase() || 'Language';

  return (
    <div className="bg-white rounded-2xl shadow-xs border border-[#E5E9E5] overflow-hidden">
      {/* Header Banner */}
      <div className="bg-[#F3F5F2] p-6 border-b border-[#E5E9E5]">
        <div className="flex items-start space-x-4">
          <div className="w-12 h-12 rounded-xl bg-white text-[#174F4A] border border-[#E5E9E5] flex items-center justify-center shrink-0 shadow-xs">
            <Construction className="w-6 h-6 text-[#174F4A]" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-[#FEFCE8] text-[#D99A28] border border-[#FEF08A]">
                Phase 2 Roadmap Engine
              </span>
              <span className="text-xs font-mono text-[#68736D] font-semibold">
                Status: In Development
              </span>
            </div>
            <h3 className="text-xl font-bold text-[#202824] mt-1.5">
              {langDisplay} Static Analyzer Roadmap
            </h3>
            <p className="text-xs text-[#68736D] mt-1.5 leading-relaxed max-w-xl">
              {result.message}
            </p>
          </div>
        </div>
      </div>

      {/* Body Details */}
      <div className="p-6 space-y-6">
        {/* Planned Engine Info */}
        {roadmap && (
          <div className="bg-[#FDFAF5] p-4 rounded-xl border border-[#E5E9E5] space-y-2">
            <div className="text-xs font-bold text-[#68736D] uppercase tracking-wider">
              Architecture & Engine Specification
            </div>
            <div className="text-xs font-semibold text-[#202824]">
              Planned Engine: <span className="font-mono text-[#174F4A] bg-white px-2 py-0.5 rounded border border-[#E5E9E5] font-bold">{roadmap.planned_engine}</span>
            </div>
            <p className="text-xs text-[#68736D] leading-relaxed">
              {roadmap.description}
            </p>
          </div>
        )}

        {/* Features In Progress */}
        {roadmap?.features_in_progress && (
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#68736D]">
              Modular Capabilities Under Active Development:
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {roadmap.features_in_progress.map((feature, idx) => (
                <div
                  key={idx}
                  className="flex items-center space-x-2 text-xs text-[#202824] p-3 rounded-xl bg-[#F3F5F2] border border-[#E5E9E5]"
                >
                  <CheckCircle2 className="w-4 h-4 text-[#21865A] shrink-0" />
                  <span>{feature}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Action Button to switch to Python */}
        <div className="pt-3 flex flex-wrap items-center justify-between gap-4 border-t border-[#E5E9E5]">
          <div className="flex items-center space-x-2 text-xs text-[#68736D]">
            <ShieldCheck className="w-4 h-4 text-[#21865A]" />
            <span>Full AST static analysis is active for Python.</span>
          </div>

          <button
            onClick={onSwitchToPython}
            className="flex items-center space-x-2 px-4 py-2.5 rounded-xl bg-[#174F4A] hover:bg-[#123E3A] text-white text-xs font-bold shadow-xs transition-all cursor-pointer"
          >
            <span>Switch to Python & Test Presets</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
