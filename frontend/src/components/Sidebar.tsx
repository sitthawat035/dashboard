// components/Sidebar.tsx — Now uses Zustand store (zero props needed from parent)
import React from 'react';
import { Rocket, LayoutDashboard, Bot, Terminal, Cpu, Shield, LogOut, Zap, Menu, X, Gamepad2 } from 'lucide-react';
import type { TabId } from '../types';
import { useAppStore } from '../stores/useAppStore';

const Sidebar: React.FC = () => {
  const activeTab = useAppStore(s => s.activeTab);
  const setActiveTab = useAppStore(s => s.setActiveTab);
  const sidebarOpen = useAppStore(s => s.sidebarOpen);
  const setSidebarOpen = useAppStore(s => s.setSidebarOpen);
  const killAll = useAppStore(s => s.killAll);
  const setIsLoggedIn = useAppStore(s => s.setIsLoggedIn);

  const menuItems = [
    { id: 'dashboard' as TabId, label: 'Dashboard', icon: LayoutDashboard },
    { id: 'mission' as TabId, label: 'Mission Control', icon: Gamepad2 },
    { id: 'agents' as TabId, label: 'Agents', icon: Bot },
    { id: 'terminal' as TabId, label: 'PowerShell', icon: Terminal },
    { id: 'multi' as TabId, label: 'Engine Hub', icon: Cpu },
    { id: 'settings' as TabId, label: 'CLI Auth', icon: Shield },
  ];

  const handleNavClick = (id: TabId) => {
    setActiveTab(id);
    if (window.innerWidth < 768) setSidebarOpen(false);
  };

  return (
    <>
      {/* Mobile hamburger button */}
      <button 
        className="mobile-menu-btn"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle menu"
      >
        {sidebarOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={`sidebar ${sidebarOpen ? 'open' : 'collapsed'}`}>
        <div className="sidebar-logo">
          <div className="logo-box">
            <Rocket size={22} color="#fff" />
          </div>
          <div>
            <div className="logo-title">JOEPV</div>
            <div className="logo-sub">v4 (Clean Slate)</div>
          </div>
        </div>

        <nav className="nav">
          {menuItems.map((item) => {
            const Icon = item.icon;
            return (
              <div
                key={item.id}
                className={`nav-item ${activeTab === item.id ? 'active' : ''}`}
                onClick={() => handleNavClick(item.id)}
              >
                <Icon size={18} className="nav-icon" />
                <span>{item.label}</span>
              </div>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div
            className="nav-item sidebar-kill"
            onClick={() => {
              if (window.confirm('EMERGENCY: KILL ALL AGENTS?')) killAll();
            }}
          >
            <Zap size={18} />
            <span>Kill All System</span>
          </div>
          <div className="nav-item sidebar-logout" onClick={() => setIsLoggedIn(false)}>
            <LogOut size={18} />
            <span>Logout</span>
          </div>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
