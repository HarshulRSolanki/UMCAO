import React, { useState } from 'react';
import { Settings, ShieldCheck, Sparkles, Terminal, Sliders, CheckCircle2, RefreshCw } from 'lucide-react';
import { API_BASE_URL, checkBackendHealth } from '../services/api';

export default function SettingsPanel({
  settings,
  setSettings,
  isBackendOnline,
  setIsBackendOnline,
}) {
  const [testingHealth, setTestingHealth] = useState(false);
  const [healthStatus, setHealthStatus] = useState(null);

  const handleTestConnection = async () => {
    setTestingHealth(true);
    setHealthStatus(null);
    try {
      const res = await checkBackendHealth();
      setIsBackendOnline(res.healthy);
      setHealthStatus({
        ok: res.healthy,
        message: res.healthy
          ? `Backend API connected cleanly (${API_BASE_URL})`
          : res.error || `Could not reach backend at ${API_BASE_URL}`,
      });
    } catch {
      setIsBackendOnline(false);
      setHealthStatus({ ok: false, message: `Backend unreachable at ${API_BASE_URL}.` });
    } finally {
      setTestingHealth(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl">
      {/* Top Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-xs border border-[#E5E9E5]">
        <div className="flex items-center space-x-2.5">
          <span className="p-2 rounded-xl bg-[#174F4A]/10 text-[#174F4A]">
            <Settings className="w-5 h-5 text-[#174F4A]" />
          </span>
          <div>
            <h2 className="text-xl font-bold text-[#202824]">UMCAO System Settings</h2>
            <p className="text-xs text-[#68736D] mt-0.5">
              Configure editor preferences, default languages, Gemini AI settings, and backend connection.
            </p>
          </div>
        </div>
      </div>

      {/* Setting Section 1: Editor Preferences */}
      <div className="bg-white rounded-2xl p-6 shadow-xs border border-[#E5E9E5] space-y-4">
        <div className="flex items-center space-x-2 pb-3 border-b border-[#E5E9E5]">
          <Sliders className="w-4 h-4 text-[#174F4A]" />
          <h3 className="text-sm font-bold text-[#202824] uppercase tracking-wider">Editor Preferences</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-[#202824] block mb-1">Tab Indentation</label>
            <select
              value={settings.tabSize || '4'}
              onChange={(e) => setSettings({ ...settings, tabSize: e.target.value })}
              className="w-full text-xs bg-[#F3F5F2] border border-[#E5E9E5] text-[#202824] rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-[#174F4A] cursor-pointer"
            >
              <option value="2">2 Spaces</option>
              <option value="4">4 Spaces (Standard)</option>
            </select>
          </div>

          <div>
            <label className="text-xs font-semibold text-[#202824] block mb-1">Editor Font Size</label>
            <select
              value={settings.fontSize || '13px'}
              onChange={(e) => setSettings({ ...settings, fontSize: e.target.value })}
              className="w-full text-xs bg-[#F3F5F2] border border-[#E5E9E5] text-[#202824] rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-[#174F4A] cursor-pointer"
            >
              <option value="12px">12px (Compact)</option>
              <option value="13px">13px (Default)</option>
              <option value="14px">14px (Comfortable)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Setting Section 2: Gemini AI Settings */}
      <div className="bg-white rounded-2xl p-6 shadow-xs border border-[#E5E9E5] space-y-4">
        <div className="flex items-center space-x-2 pb-3 border-b border-[#E5E9E5]">
          <Sparkles className="w-4 h-4 text-[#174F4A]" />
          <h3 className="text-sm font-bold text-[#202824] uppercase tracking-wider">Gemini AI Engine Configuration</h3>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-semibold text-[#202824] block mb-1">Active AI Model</label>
            <div className="p-2.5 rounded-lg bg-[#F0FDF4] border border-[#BBF7D0] text-[#21865A] text-xs font-mono font-semibold flex items-center justify-between">
              <span>gemini-3.5-flash-lite</span>
              <span className="text-[10px] bg-white px-2 py-0.5 rounded border border-[#BBF7D0]">Active SDK</span>
            </div>
          </div>

          <div>
            <label className="text-xs font-semibold text-[#202824] block mb-1">Default Explanation Language</label>
            <select
              value={settings.defaultLang || 'english'}
              onChange={(e) => setSettings({ ...settings, defaultLang: e.target.value })}
              className="w-full text-xs bg-[#F3F5F2] border border-[#E5E9E5] text-[#202824] rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-[#174F4A] cursor-pointer"
            >
              <option value="english">English</option>
              <option value="gujarati">Gujarati (ગુજરાતી)</option>
              <option value="hindi">Hindi (हिन्दी)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Setting Section 3: Backend API Health */}
      <div className="bg-white rounded-2xl p-6 shadow-xs border border-[#E5E9E5] space-y-4">
        <div className="flex items-center space-x-2 pb-3 border-b border-[#E5E9E5]">
          <Terminal className="w-4 h-4 text-[#174F4A]" />
          <h3 className="text-sm font-bold text-[#202824] uppercase tracking-wider">Backend API Connection</h3>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold text-[#202824] block">Endpoint Target</span>
            <span className="font-mono text-xs text-[#68736D] break-all">{API_BASE_URL}</span>
          </div>

          <button
            onClick={handleTestConnection}
            disabled={testingHealth}
            className="flex items-center space-x-2 px-4 py-2 rounded-xl bg-[#174F4A] hover:bg-[#123E3A] text-white text-xs font-bold shadow-xs transition-all cursor-pointer self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${testingHealth ? 'animate-spin' : ''}`} />
            <span>{testingHealth ? 'Testing...' : 'Test Connection'}</span>
          </button>
        </div>

        {healthStatus && (
          <div
            className={`p-3 rounded-lg border text-xs flex items-center space-x-2 ${
              healthStatus.ok
                ? 'bg-[#F0FDF4] border-[#BBF7D0] text-[#21865A]'
                : 'bg-[#FEF2F2] border-[#FECACA] text-[#D64545]'
            }`}
          >
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{healthStatus.message}</span>
          </div>
        )}
      </div>

      {/* Safety Info Card */}
      <div className="p-4 rounded-xl bg-[#FDFAF5] border border-[#E5E9E5] flex items-start space-x-3 text-xs text-[#68736D]">
        <ShieldCheck className="w-5 h-5 text-[#21865A] shrink-0 mt-0.5" />
        <div>
          <strong className="text-[#202824] block">Zero Server-Side Execution Guarantee</strong>
          <span>
            UMCAO enforces a strict static-only execution architecture. Your source code is never executed, evaluated,
            or executed on the host server.
          </span>
        </div>
      </div>
    </div>
  );
}

