import React from 'react';
import {
  LayoutDashboard,
  BarChart3,
  FileText,
  UserCheck,
  Award,
  Zap,
  Settings,
  Plus,
  HelpCircle,
  LogOut,
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'jd-analytics', label: 'JD Analytics', icon: BarChart3 },
    { id: 'resume-parser', label: 'Resume Parser', icon: FileText },
    { id: 'profile-builder', label: 'Profile Builder', icon: UserCheck },
    { id: 'talent-check', label: 'Talent Check', icon: Award },
    { id: 'skill-matching', label: 'Skill Matching', icon: Zap },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-title">RADIX</div>
        <div className="sidebar-logo-sub">AI TALENT MATCH</div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              className={`nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setActiveTab(item.id)}
            >
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="sidebar-bottom">
        <button className="btn-new-analysis" onClick={() => setActiveTab('talent-check')}>
          <Plus size={18} />
          <span>New Analysis</span>
        </button>

        <button className="nav-item" style={{ border: 'none', background: 'none' }}>
          <HelpCircle size={18} />
          <span>Support</span>
        </button>

        <button className="nav-item" style={{ border: 'none', background: 'none' }}>
          <LogOut size={18} />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
