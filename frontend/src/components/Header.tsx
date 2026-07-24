import React from 'react';
import { Search, Bell, Moon } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header className="top-header">
      <div className="search-box">
        <Search size={16} />
        <input
          type="text"
          className="search-input"
          placeholder="Search talent, skills, or resumes..."
        />
      </div>

      <div className="header-right">
        <button className="icon-btn" title="Notifications">
          <Bell size={18} />
        </button>

        <button className="icon-btn" title="Toggle Theme">
          <Moon size={18} />
        </button>

        <div className="user-profile">
          <div className="avatar">AR</div>
          <div className="user-info">
            <span className="user-name">Alex Rivera</span>
            <span className="user-role">Talent Lead</span>
          </div>
        </div>
      </div>
    </header>
  );
};
