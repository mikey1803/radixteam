import { useState } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { Dashboard } from './components/Dashboard';
import { TalentCheckView } from './components/TalentCheckView';
import './index.css';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard onNavigateToTalentCheck={() => setActiveTab('talent-check')} />;
      case 'talent-check':
        return <TalentCheckView />;
      case 'jd-analytics':
      case 'resume-parser':
      case 'profile-builder':
      case 'skill-matching':
      case 'settings':
        return (
          <div className="content-body" style={{ textAlign: 'center', paddingTop: '5rem' }}>
            <h2 style={{ fontSize: '1.8rem', color: '#f1f1f7', textTransform: 'capitalize' }}>
              {activeTab.replace('-', ' ')}
            </h2>
            <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>
              Module initialized on <code style={{ color: '#c084fc' }}>feature/talent-check</code> branch.
            </p>
            <button
              className="btn-new-analysis"
              style={{ width: 'auto', display: 'inline-flex', marginTop: '1.5rem' }}
              onClick={() => setActiveTab('talent-check')}
            >
              Switch to Talent Check Module
            </button>
          </div>
        );
      default:
        return <Dashboard onNavigateToTalentCheck={() => setActiveTab('talent-check')} />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main-layout">
        <Header />
        {renderContent()}
      </div>
    </div>
  );
}
