import React from 'react';
import {
  Code2,
  Sparkles,
  BarChart3,
  History,
  Settings,
  BookOpen,
  Terminal,
  AlertCircle,
  Menu,
} from 'lucide-react';
import { API_BASE_URL } from '../services/api';

export default function Navbar({
  isBackendOnline,
  activeLanguage,
  onOpenDocs,
  activeTab,
  onToggleMobileSidebar,
}) {
  const getTabInfo = () => {
    switch (activeTab) {
      case 'dashboard':
        return {
          title: 'Code Analyzer',
          subtitle: 'Static AST Inspection & Optimization',
          icon: Code2,
        };
      case 'ai-explainer':
        return {
          title: 'Gemini AI Explainer',
          subtitle: 'Multi-lingual Code Breakdown & Chat',
          icon: Sparkles,
        };
      case 'performance':
        return {
          title: 'Charts & Metrics',
          subtitle: 'Theoretical Computational Scaling',
          icon: BarChart3,
        };
      case 'history':
        return {
          title: 'Analysis History',
          subtitle: 'Saved Execution Snapshots',
          icon: History,
        };
      case 'settings':
        return {
          title: 'System Settings',
          subtitle: 'Preferences & AI Engine',
          icon: Settings,
        };
      default:
        return {
          title: 'UMCAO Dashboard',
          subtitle: 'Universal Multi-Language Code Analyzer',
          icon: Terminal,
        };
    }
  };

  const currentTab = getTabInfo();
  const TabIcon = currentTab.icon;

  return (
    <header className="sticky top-0 z-30 bg-white text-[#202824] shadow-xs border-b border-[#E5E9E5] shrink-0">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Left: Mobile Toggle & Desktop Breadcrumb */}
          <div className="flex items-center space-x-3">
            {/* Mobile hamburger menu toggle */}
            <button
              onClick={onToggleMobileSidebar}
              className="p-2 rounded-xl text-[#68736D] hover:text-[#202824] hover:bg-[#F3F5F2] lg:hidden cursor-pointer"
              aria-label="Open Navigation Menu"
            >
              <Menu className="w-5 h-5" />
            </button>

            {/* Mobile compact logo */}
            <div className="flex items-center space-x-2 lg:hidden">
              <div className="w-8 h-8 rounded-lg bg-[#174F4A] text-white flex items-center justify-center">
                <Terminal className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-base text-[#202824] font-mono">UMCAO</span>
            </div>

            {/* Desktop Section Breadcrumb / Header */}
            <div className="hidden lg:flex items-center space-x-3">
              <div className="p-2 rounded-xl bg-[#F3F5F2] text-[#174F4A] border border-[#E5E9E5]">
                <TabIcon className="w-4 h-4 text-[#174F4A]" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h1 className="text-sm font-bold text-[#202824] tracking-tight">{currentTab.title}</h1>
                  {activeTab === 'dashboard' && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#174F4A]/10 text-[#174F4A] border border-[#174F4A]/20 uppercase">
                      {activeLanguage}
                    </span>
                  )}
                  {activeTab === 'ai-explainer' && (
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-[#174F4A] border border-emerald-200">
                      Google GenAI SDK
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-[#68736D] -mt-0.5">{currentTab.subtitle}</p>
              </div>
            </div>
          </div>

          {/* Right Controls */}
          <div className="flex items-center space-x-2 sm:space-x-3">
            {/* Backend Health Status Badge */}
            <div
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border ${
                isBackendOnline
                  ? 'bg-[#F0FDF4] text-[#21865A] border-[#BBF7D0]'
                  : 'bg-[#FEFCE8] text-[#D99A28] border-[#FEF08A]'
              }`}
              title={isBackendOnline ? `FastAPI Backend Online (${API_BASE_URL})` : `Connecting to API server (${API_BASE_URL})...`}
            >
              {isBackendOnline ? (
                <>
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#21865A]"></span>
                  </span>
                  <span className="hidden sm:inline">API Online</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5 text-[#D99A28]" />
                  <span>Connecting...</span>
                </>
              )}
            </div>

            {/* Documentation Modal Button */}
            <button
              onClick={onOpenDocs}
              className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#F3F5F2] hover:bg-[#E5E9E5] text-[#202824] border border-[#E5E9E5] transition-all shadow-xs cursor-pointer"
              title="Documentation and Architecture Guide"
            >
              <BookOpen className="w-3.5 h-3.5 text-[#174F4A]" />
              <span className="hidden sm:inline">Docs & Rules</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
