import React from 'react';
import {
  Code2,
  Sparkles,
  BarChart3,
  History,
  Settings,
  BookOpen,
  Terminal,
  Shield,
  CheckCircle2,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react';

export default function Sidebar({
  activeTab,
  setActiveTab,
  isBackendOnline,
  onOpenDocs,
  isCollapsed,
  setIsCollapsed,
  isMobileOpen,
  setIsMobileOpen,
}) {
  const navItems = [
    {
      id: 'dashboard',
      label: 'Code Analyzer',
      description: 'AST diagnosis & editor',
      icon: Code2,
    },
    {
      id: 'ai-explainer',
      label: 'AI Explainer',
      description: 'Gemini step-by-step',
      icon: Sparkles,
      badge: 'Gemini',
    },
    {
      id: 'performance',
      label: 'Charts & Metrics',
      description: 'Theoretical scaling',
      icon: BarChart3,
    },
    {
      id: 'history',
      label: 'Analysis History',
      description: 'Saved past runs',
      icon: History,
    },
    {
      id: 'settings',
      label: 'Settings',
      description: 'Preferences & engine',
      icon: Settings,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 backdrop-blur-xs lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed lg:sticky top-0 left-0 z-40 h-screen bg-white border-r border-[#E5E9E5] flex flex-col justify-between transition-all duration-300 shadow-xs shrink-0 select-none ${
          isMobileOpen ? 'translate-x-0 w-64' : '-translate-x-full lg:translate-x-0'
        } ${isCollapsed ? 'lg:w-20' : 'lg:w-64'}`}
      >
        {/* Top Header */}
        <div className={`border-b border-[#E5E9E5] ${isCollapsed ? 'p-3 flex flex-col items-center' : 'p-4 flex items-center justify-between'}`}>
          <div className={`flex items-center ${isCollapsed ? 'flex-col space-y-2' : 'space-x-3 overflow-hidden'}`}>
            <div
              onClick={() => {
                setActiveTab('dashboard');
                setIsMobileOpen(false);
              }}
              className="w-10 h-10 rounded-xl bg-[#174F4A] text-white flex items-center justify-center shrink-0 shadow-xs cursor-pointer hover:bg-[#123E3A] transition-all"
              title="UMCAO Home"
            >
              <Terminal className="w-5 h-5 text-white" />
            </div>

            {!isCollapsed && (
              <div className="truncate">
                <div className="flex items-center space-x-1.5">
                  <span className="font-bold text-base text-[#202824] tracking-tight font-mono">UMCAO</span>
                  <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded-full bg-[#174F4A]/10 text-[#174F4A] border border-[#174F4A]/20">
                    AST+AI
                  </span>
                </div>
                <p className="text-[10px] text-[#68736D] truncate">Universal Code Analyzer</p>
              </div>
            )}
          </div>

          {/* Mobile close button */}
          <button
            onClick={() => setIsMobileOpen(false)}
            className="p-1 rounded-lg text-[#68736D] hover:text-[#202824] hover:bg-[#F3F5F2] lg:hidden"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Desktop collapse toggle */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={`hidden lg:flex p-1.5 rounded-lg text-[#68736D] hover:text-[#202824] hover:bg-[#F3F5F2] transition-all cursor-pointer ${
              isCollapsed ? 'mt-2' : ''
            }`}
            title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            {isCollapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
          </button>
        </div>

        {/* Navigation List */}
        <div className="flex-1 py-4 px-3 space-y-1.5 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setIsMobileOpen(false);
                }}
                className={`w-full flex items-center rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                  isCollapsed ? 'justify-center p-3' : 'space-x-3 px-3 py-2.5'
                } ${
                  isActive
                    ? 'bg-[#174F4A] text-white shadow-xs'
                    : 'text-[#68736D] hover:text-[#202824] hover:bg-[#F3F5F2]'
                }`}
                title={isCollapsed ? item.label : undefined}
              >
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? 'text-white' : item.id === 'ai-explainer' ? 'text-[#174F4A]' : 'text-[#68736D]'
                  }`}
                />
                {!isCollapsed && (
                  <div className="flex-1 text-left flex items-center justify-between">
                    <div>
                      <span className="block leading-tight">{item.label}</span>
                      <span
                        className={`text-[10px] block mt-0.5 leading-tight ${
                          isActive ? 'text-emerald-100/80' : 'text-[#8E9993]'
                        }`}
                      >
                        {item.description}
                      </span>
                    </div>
                    {item.badge && (
                      <span
                        className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider ${
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-emerald-50 text-[#174F4A] border border-emerald-200'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>

        {/* Bottom Actions & Status */}
        <div className={`border-t border-[#E5E9E5] ${isCollapsed ? 'p-2 flex flex-col items-center space-y-2' : 'p-3 space-y-2'}`}>
          {/* Docs Modal Button */}
          <button
            onClick={onOpenDocs}
            className={`w-full flex items-center rounded-xl text-xs font-medium text-[#202824] bg-[#F3F5F2] hover:bg-[#E5E9E5] transition-all cursor-pointer ${
              isCollapsed ? 'justify-center p-2.5' : 'space-x-2.5 px-3 py-2'
            }`}
            title="Documentation & Rules"
          >
            <BookOpen className="w-4 h-4 text-[#174F4A] shrink-0" />
            {!isCollapsed && <span>Docs & Rules</span>}
          </button>

          {/* Backend Status Badge */}
          <div
            className={`flex items-center rounded-xl text-[11px] font-medium border ${
              isCollapsed ? 'justify-center p-2.5 w-full' : 'space-x-2 px-3 py-2'
            } ${
              isBackendOnline
                ? 'bg-[#F0FDF4] text-[#21865A] border-[#BBF7D0]'
                : 'bg-[#FEFCE8] text-[#D99A28] border-[#FEF08A]'
            }`}
            title={isBackendOnline ? 'FastAPI Backend Online (localhost:8000)' : 'Connecting to backend...'}
          >
            {isBackendOnline ? (
              <>
                <span className="relative flex h-2 w-2 shrink-0">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-[#21865A]"></span>
                </span>
                {!isCollapsed && <span className="truncate">API Online</span>}
              </>
            ) : (
              <>
                <AlertCircle className="w-3.5 h-3.5 text-[#D99A28] shrink-0" />
                {!isCollapsed && <span className="truncate">Connecting...</span>}
              </>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}
