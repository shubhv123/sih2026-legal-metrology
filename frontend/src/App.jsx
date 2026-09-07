import React, { useState, useEffect } from "react";
import { Routes, Route, NavLink, useNavigate, useLocation } from "react-router-dom";
import Upload from "./pages/Upload";
import Results from "./pages/Results";
import Dashboard from "./pages/Dashboard";
import History from "./pages/History";
import Login from "./pages/Login";
import { getCurrentRole, getCurrentUsername, logout, checkBackendHealth } from "./api/client";

export default function App() {
  const [role, setRole] = useState(getCurrentRole());
  const [username, setUsername] = useState(getCurrentUsername());
  const [backendOnline, setBackendOnline] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    let isMounted = true;
    const probe = async () => {
      const isUp = await checkBackendHealth();
      if (isMounted) setBackendOnline(isUp);
    };
    probe();
    const interval = setInterval(probe, 8000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleLogout = () => {
    logout();
    setRole(null);
    setUsername(null);
    navigate("/login");
  };

  // Sidebar navigation link style (tracking-widest uppercase as in the mockup)
  const navLinkClass = ({ isActive }) =>
    `relative flex items-center px-6 py-4 text-[11px] font-semibold tracking-[0.2em] uppercase transition-all duration-150 ${
      isActive
        ? "text-black bg-neutral-100/70 border-l-2 border-black font-bold"
        : "text-neutral-400 hover:text-neutral-800 hover:bg-neutral-50/60 border-l-2 border-transparent"
    }`;

  // Get current page label for header
  const getPageTitle = () => {
    if (location.pathname.startsWith("/results")) return "Results";
    if (location.pathname === "/dashboard") return "Dashboard";
    if (location.pathname === "/history") return "History / Search";
    if (location.pathname === "/login") return "Login";
    return "Upload";
  };

  return (
    <div className="min-h-screen flex bg-[#F8F9FA] text-[#18181B] font-sans antialiased selection:bg-neutral-900 selection:text-white relative overflow-x-hidden">
      {/* SOFT AMBIENT DIFFUSED AURA CORNER GLOWS (As depicted in mockup) */}
      <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
        {/* Top-Right warm ivory aura glow */}
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full bg-[#FEF3C7]/40 blur-[140px] animate-ambient-pulse" />
        {/* Bottom-Left pale mist-green aura glow */}
        <div className="absolute -bottom-40 -left-40 w-[650px] h-[650px] rounded-full bg-[#D1FAE5]/45 blur-[150px] animate-ambient-pulse" style={{ animationDelay: "4s" }} />
      </div>

      {/* LEFT SIDEBAR — Permanent stark-white vertical navigation menu */}
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-[#E5E7EB] shrink-0 z-30 shadow-[1px_0_10px_rgba(0,0,0,0.02)]">
        {/* Brand Header */}
        <div className="h-20 flex items-center px-6 border-b border-[#F0F2F5]">
          <NavLink to="/" className="flex items-center space-x-3 group">
            <div className="w-8 h-8 rounded-lg bg-black text-white flex items-center justify-center font-serif text-sm font-bold shadow-sm">
              LM
            </div>
            <div>
              <span className="font-bold text-[15px] tracking-tight text-black block leading-none">
                Legal Metrology AI
              </span>
              <span className="text-[9px] text-neutral-400 font-mono tracking-wider block mt-1">
                LMPC RULES 2011 • v1.1
              </span>
            </div>
          </NavLink>
        </div>

        {/* Typographic Navigation Links */}
        <nav className="flex-1 py-6 space-y-1">
          <NavLink to="/" className={navLinkClass} end>
            UPLOAD
          </NavLink>
          <NavLink to="/results" className={navLinkClass}>
            RESULTS
          </NavLink>
          <NavLink to="/history" className={navLinkClass}>
            HISTORY / SEARCH
          </NavLink>
          <NavLink to="/dashboard" className={navLinkClass}>
            DASHBOARD
          </NavLink>
          <NavLink to="/login" className={navLinkClass}>
            LOGIN
          </NavLink>
        </nav>

        {/* Sidebar Footer: System Status & User Profile */}
        <div className="p-5 border-t border-[#F0F2F5] space-y-3 bg-[#FAFAFA]">
          {/* Telemetry Status Indicator */}
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-neutral-500 font-mono tracking-wider uppercase text-[10px]">Backend:</span>
            <div className="flex items-center space-x-1.5 px-2 py-0.5 rounded-md bg-white border border-[#E5E7EB] text-[10px] font-mono">
              <span className={`w-2 h-2 rounded-full ${backendOnline ? "bg-emerald-500" : "bg-amber-500"}`} />
              <span className={backendOnline ? "text-emerald-700 font-semibold" : "text-amber-700 font-semibold"}>
                {backendOnline ? "API Online" : "Demo Mock"}
              </span>
            </div>
          </div>

          {/* Officer session */}
          {role ? (
            <div className="pt-2 border-t border-[#E5E7EB] flex items-center justify-between">
              <div className="truncate">
                <p className="text-xs font-bold text-neutral-900 leading-tight truncate">{username || role}</p>
                <p className="text-[10px] uppercase font-mono tracking-wider text-neutral-500">{role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 hover:text-black hover:underline"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <NavLink
              to="/login"
              className="block w-full py-2 text-center text-xs font-semibold rounded-lg bg-black text-white hover:bg-neutral-800 transition-colors shadow-sm"
            >
              Sign In
            </NavLink>
          )}
        </div>
      </aside>

      {/* RIGHT MAIN LAYOUT */}
      <div className="flex-1 flex flex-col min-w-0 z-10 relative">
        {/* TOP BAR */}
        <header className="h-16 bg-white/80 backdrop-blur-md border-b border-[#E5E7EB] flex items-center justify-between px-6 sticky top-0 z-20">
          <div className="flex items-center space-x-3">
            {/* Mobile menu logo indicator */}
            <div className="lg:hidden flex items-center space-x-2">
              <div className="w-7 h-7 rounded-md bg-black text-white flex items-center justify-center font-serif text-xs font-bold">
                LM
              </div>
            </div>
            <h1 className="text-sm font-bold tracking-tight text-neutral-900 font-mono uppercase">
              {getPageTitle()}
            </h1>
          </div>

          {/* Right Header Navigation & Actions */}
          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center space-x-2 text-xs text-neutral-500 font-mono">
              <span>Framework:</span>
              <span className="font-semibold text-neutral-900 bg-neutral-100 px-2 py-0.5 rounded border border-neutral-200">
                LMPC-2011-v1.1
              </span>
            </div>

            {/* Profile / Role Dropdown trigger */}
            <NavLink
              to="/login"
              className="flex items-center space-x-1.5 text-xs text-neutral-700 hover:text-black font-medium transition-colors"
            >
              <span>{role ? `${role.toUpperCase()} // ${username || "ACTIVE"}` : "Login"}</span>
              <span className="text-[10px] text-neutral-400">⌵</span>
            </NavLink>
          </div>
        </header>

        {/* MOBILE NAVIGATION BAR (Shown on small screens) */}
        <div className="lg:hidden flex items-center justify-around bg-white border-b border-[#E5E7EB] py-2 px-3 text-[10px] font-semibold tracking-wider uppercase overflow-x-auto gap-2">
          <NavLink to="/" className={({ isActive }) => isActive ? "text-black font-bold shrink-0" : "text-neutral-400 shrink-0"}>
            Upload
          </NavLink>
          <NavLink to="/results" className={({ isActive }) => isActive ? "text-black font-bold shrink-0" : "text-neutral-400 shrink-0"}>
            Results
          </NavLink>
          <NavLink to="/history" className={({ isActive }) => isActive ? "text-black font-bold shrink-0" : "text-neutral-400 shrink-0"}>
            History/Search
          </NavLink>
          <NavLink to="/dashboard" className={({ isActive }) => isActive ? "text-black font-bold shrink-0" : "text-neutral-400 shrink-0"}>
            Dashboard
          </NavLink>
          <NavLink to="/login" className={({ isActive }) => isActive ? "text-black font-bold shrink-0" : "text-neutral-400 shrink-0"}>
            Login
          </NavLink>
        </div>

        {/* CONTENT VIEWPORT */}
        <main className="flex-1 p-6 md:p-8 max-w-[1600px] w-full mx-auto">
          <Routes>
            <Route path="/" element={<Upload />} />
            <Route path="/upload" element={<Upload />} />
            <Route path="/results" element={<Results />} />
            <Route path="/results/:scanId" element={<Results />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/history" element={<History />} />
            <Route
              path="/login"
              element={
                <Login
                  onLoginSuccess={(newRole, newUsername) => {
                    setRole(newRole);
                    setUsername(newUsername);
                  }}
                />
              }
            />
          </Routes>
        </main>
      </div>
    </div>
  );
}
