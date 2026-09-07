// Owner: Keshav
// Login & Officer Profile page matching docs/API_CONTRACT.md
// Styled in the luxury minimalist porcelain & stark-white design system.

import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { login, logout, getCurrentRole, getCurrentUsername } from "../api/client";

export default function Login({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();
  const currentRole = getCurrentRole();
  const currentUsername = getCurrentUsername();

  const handleLoginSubmit = async (e) => {
    e?.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const data = await login(username, password);
      onLoginSuccess?.(data.role, data.username);
      navigate("/");
    } catch (err) {
      setError(err.message || "Invalid credentials. Check username or password.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = async (demoUser, demoPass) => {
    setUsername(demoUser);
    setPassword(demoPass);
    setError(null);
    setLoading(true);
    try {
      const data = await login(demoUser, demoPass);
      onLoginSuccess?.(data.role, data.username);
      navigate("/");
    } catch (err) {
      setError(err.message || "Quick login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = () => {
    logout();
    onLoginSuccess?.(null, null);
    setUsername("");
    setPassword("");
  };

  // If already logged in, show Officer Profile & Access Level
  if (currentRole) {
    return (
      <div className="max-w-md mx-auto py-12">
        <div className="bg-white p-8 rounded-2xl border border-[#E5E7EB] shadow-sm space-y-6">
          <div className="text-center space-y-2">
            <div className="w-16 h-16 rounded-full bg-neutral-100 border border-[#E5E7EB] flex items-center justify-center text-2xl mx-auto shadow-inner">
              👮‍♂️
            </div>
            <h2 className="text-lg font-bold text-neutral-900 tracking-tight">Authenticated Officer</h2>
            <div className="inline-block px-3 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider bg-neutral-100 text-neutral-800 border border-neutral-200">
              Role: {currentRole}
            </div>
          </div>

          <div className="bg-neutral-50 rounded-xl p-4 border border-[#E5E7EB] space-y-2 text-xs">
            <div className="flex justify-between py-1 border-b border-neutral-200/70">
              <span className="text-neutral-500">Officer Username:</span>
              <span className="font-mono text-neutral-900 font-semibold">{currentUsername || "inspector1"}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-neutral-200/70">
              <span className="text-neutral-500">Session Status:</span>
              <span className="text-emerald-700 font-semibold font-mono">ACTIVE (TOKEN_VALID)</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-neutral-500">Scope Authority:</span>
              <span className="text-neutral-800 font-medium">
                {currentRole === "admin"
                  ? "Full System Admin & Rules Audit"
                  : "Field Inspection & Report Generation"}
              </span>
            </div>
          </div>

          <div className="space-y-2.5 pt-2">
            <button
              onClick={() => navigate("/")}
              className="w-full py-3 rounded-xl text-xs font-bold uppercase tracking-wider bg-black text-white hover:bg-neutral-900 transition-colors shadow-sm"
            >
              Go to Workspace →
            </button>
            <button
              onClick={handleSignOut}
              className="w-full py-2.5 rounded-xl text-xs font-semibold uppercase tracking-wider bg-white hover:bg-neutral-50 text-neutral-600 hover:text-black border border-[#E5E7EB] transition-colors"
            >
              Sign Out
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Not logged in: show Login Form with Quick-Login presets
  return (
    <div className="max-w-md mx-auto py-12 space-y-6">
      <div className="bg-white p-8 rounded-2xl border border-[#E5E7EB] shadow-sm space-y-6">
        <div className="text-center space-y-1.5 border-b border-[#F0F2F5] pb-4">
          <div className="w-12 h-12 rounded-xl bg-black text-white flex items-center justify-center text-lg mx-auto mb-2 font-serif font-bold shadow-sm">
            LM
          </div>
          <h2 className="text-xl font-bold tracking-tight text-neutral-900">
            Legal Metrology Officer Access
          </h2>
          <p className="text-xs text-neutral-500">
            Authenticate to record official packaged commodity compliance audits.
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleLoginSubmit} className="space-y-4">
          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-neutral-700 mb-1">
              Username:
            </label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. inspector1 or admin1"
              className="w-full px-3 py-2 text-xs rounded-lg bg-neutral-50 border border-[#D1D5DB] text-neutral-900 placeholder-neutral-400 focus:outline-none focus:border-black font-sans"
            />
          </div>

          <div>
            <label className="block text-[11px] font-bold uppercase tracking-wider text-neutral-700 mb-1">
              Password:
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3 py-2 text-xs rounded-lg bg-neutral-50 border border-[#D1D5DB] text-neutral-900 placeholder-neutral-400 focus:outline-none focus:border-black font-sans"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 rounded-xl bg-black text-white text-xs font-bold uppercase tracking-widest hover:bg-neutral-900 active:scale-[0.99] transition-all shadow-md disabled:opacity-60"
          >
            {loading ? "Authenticating..." : "Sign In to System"}
          </button>
        </form>

        {/* Quick Demo Login Presets */}
        <div className="pt-4 border-t border-[#F0F2F5] space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-widest text-neutral-400 text-center">
            One-Click Official Demo Profiles
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin("inspector", "inspector123")}
              className="p-2.5 rounded-xl bg-neutral-50 hover:bg-neutral-100 border border-[#E5E7EB] text-left transition-colors"
            >
              <div className="text-xs font-bold text-neutral-900">Field Officer</div>
              <div className="text-[10px] text-neutral-500 font-mono">inspector</div>
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin("admin", "admin123")}
              className="p-2.5 rounded-xl bg-neutral-50 hover:bg-neutral-100 border border-[#E5E7EB] text-left transition-colors"
            >
              <div className="text-xs font-bold text-neutral-900">Enforcement Dir.</div>
              <div className="text-[10px] text-neutral-500 font-mono">admin</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
