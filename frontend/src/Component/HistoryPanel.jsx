import React from 'react';
import { History, Play, Trash2, Clock, Code2, Zap, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function HistoryPanel({ history, onLoadHistoryItem, onClearHistory, onRemoveHistoryItem }) {
  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-xs border border-[#E5E9E5] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2.5">
            <span className="p-2 rounded-xl bg-[#174F4A]/10 text-[#174F4A]">
              <History className="w-5 h-5 text-[#174F4A]" />
            </span>
            <h2 className="text-xl font-bold text-[#202824]">Analysis History</h2>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-[#F3F5F2] text-[#68736D] border border-[#E5E9E5]">
              {history.length} Saved {history.length === 1 ? 'Run' : 'Runs'}
            </span>
          </div>
          <p className="text-xs text-[#68736D] mt-1 max-w-xl">
            Review past static analysis and optimization runs. Click "Load into Editor" to inspect or re-analyze any previous snippet.
          </p>
        </div>

        {history.length > 0 && (
          <button
            onClick={onClearHistory}
            className="self-start sm:self-auto px-3.5 py-2 rounded-xl text-xs font-semibold text-[#D64545] bg-[#FEF2F2] hover:bg-red-100 border border-[#FECACA] transition-all flex items-center space-x-1.5 cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* History List */}
      {history.length === 0 ? (
        <div className="bg-white rounded-2xl p-12 text-center border border-[#E5E9E5] shadow-xs flex flex-col items-center justify-center min-h-[360px]">
          <div className="w-14 h-14 rounded-2xl bg-[#F3F5F2] text-[#68736D] flex items-center justify-center mb-3 border border-[#E5E9E5]">
            <History className="w-7 h-7 text-[#174F4A]" />
          </div>
          <h3 className="text-base font-bold text-[#202824]">No Analysis History Yet</h3>
          <p className="text-xs text-[#68736D] mt-1 max-w-sm">
            Whenever you run code analysis in the Code Analyzer, a snapshot will be automatically recorded here for instant replay.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {history.map((item, idx) => (
            <div
              key={item.id ? `${item.id}-${idx}` : idx}
              className="bg-white rounded-xl border border-[#E5E9E5] p-5 shadow-xs hover:border-[#174F4A]/40 transition-all flex flex-col justify-between"
            >
              <div>
                {/* Card Top */}
                <div className="flex items-center justify-between text-xs mb-3">
                  <div className="flex items-center space-x-2">
                    <span className="font-bold text-xs uppercase px-2 py-0.5 rounded-md bg-[#174F4A] text-white">
                      {item.language}
                    </span>
                    <span className="text-[11px] font-semibold text-[#68736D] flex items-center space-x-1">
                      <Clock className="w-3 h-3 text-[#68736D]" />
                      <span>{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </span>
                  </div>

                  <button
                    onClick={() => onRemoveHistoryItem(item.id)}
                    className="text-[#68736D] hover:text-[#D64545] p-1 transition-all cursor-pointer"
                    title="Delete item"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Code Preview */}
                <div className="p-3 bg-[#F3F5F2] rounded-lg border border-[#E5E9E5] font-mono text-xs text-[#202824] line-clamp-3 mb-3">
                  {item.code}
                </div>

                {/* Metrics Highlights */}
                <div className="grid grid-cols-3 gap-2 text-[11px] mb-4">
                  <div className="p-2 bg-[#FDFAF5] rounded border border-[#E5E9E5]">
                    <span className="text-[#68736D] block">Complexity</span>
                    <strong className="text-[#174F4A]">{item.complexity || 'O(?)'}</strong>
                  </div>
                  <div className="p-2 bg-[#FDFAF5] rounded border border-[#E5E9E5]">
                    <span className="text-[#68736D] block">Lines</span>
                    <strong className="text-[#202824]">{item.lines || 1}</strong>
                  </div>
                  <div className="p-2 bg-[#FDFAF5] rounded border border-[#E5E9E5]">
                    <span className="text-[#68736D] block">Optimizations</span>
                    <strong className="text-[#21865A]">{item.optimizationsCount || 0}</strong>
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <button
                onClick={() => onLoadHistoryItem(item)}
                className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg bg-[#174F4A] hover:bg-[#123E3A] text-white text-xs font-bold shadow-xs transition-all cursor-pointer"
              >
                <span>Load into Editor</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

