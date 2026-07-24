import React from 'react';
import {
  ChevronLeft,
  Cpu,
  Cloud,
  FileText,
  MoreVertical,
  Zap,
  ArrowRight,
  Target,
} from 'lucide-react';

interface DashboardProps {
  onNavigateToTalentCheck: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onNavigateToTalentCheck }) => {
  const recentAnalyses = [
    {
      id: 1,
      filename: 'Jordan Smith.pdf',
      time: '2 hours ago',
      target: 'Senior Frontend Engineer',
      score: 94,
      status: 'QUALIFIED',
      badgeClass: 'qualified',
      barColor: '#10b981',
    },
    {
      id: 2,
      filename: 'Casey_Data_Sci.docx',
      time: 'Yesterday',
      target: 'ML Lead (Quant)',
      score: 78,
      status: 'PROCESSING',
      badgeClass: 'processing',
      barColor: '#6366f1',
    },
    {
      id: 3,
      filename: 'Dev_Ops_Lead.pdf',
      time: '2 days ago',
      target: 'Cloud Architect',
      score: 42,
      status: 'LOW MATCH',
      badgeClass: 'lowmatch',
      barColor: '#f43f5e',
    },
  ];

  return (
    <div className="content-body">
      {/* Sub-header status & Greeting */}
      <div className="welcome-header">
        <div className="system-status">
          <ChevronLeft size={14} />
          <span>SYSTEM STATUS: ACTIVE</span>
        </div>
        <h1>Welcome back, Alex</h1>
        <p>
          Your talent matching engine has processed 14 new resumes today. Profile completion is at
          its peak across the engineering vertical.
        </p>
      </div>

      {/* Top 4 Metrics Cards */}
      <div className="metrics-grid">
        {/* Card 1: Resume Strength */}
        <div className="card">
          <div className="card-label">
            <span>Resume Strength</span>
          </div>
          <div className="radial-gauge-container">
            <div className="radial-circle">
              <span className="radial-value">85%</span>
            </div>
            <span className="badge-growth">+5.2% from last month</span>
          </div>
        </div>

        {/* Card 2: AI Skills Found */}
        <div className="card">
          <div className="card-label">
            <span>AI Skills Found</span>
            <Cpu size={18} style={{ color: '#c084fc' }} />
          </div>
          <div style={{ fontFamily: "'Outfit', sans-serif", fontSize: '2.2rem', fontWeight: 800 }}>
            12
          </div>
          <div className="tags-wrapper">
            <span className="tag-pill">LLM Tuning</span>
            <span className="tag-pill">PyTorch</span>
            <span className="tag-pill">NLP</span>
            <span className="tag-pill" style={{ color: '#a78bfa', borderColor: 'rgba(167, 139, 250, 0.3)' }}>
              +9 more
            </span>
          </div>
        </div>

        {/* Card 3: Cloud Expertise */}
        <div className="card">
          <div className="card-label">
            <span>Cloud Expertise</span>
            <Cloud size={18} style={{ color: '#a78bfa' }} />
          </div>
          <div style={{ fontFamily: "'Outfit', sans-serif", fontSize: '2.2rem', fontWeight: 800 }}>
            8
          </div>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              fontSize: '0.75rem',
              color: '#94a3b8',
              marginTop: '0.5rem',
            }}
          >
            <span style={{ fontWeight: 600 }}>AWS (Advanced)</span>
            <span style={{ color: '#64748b' }}>4 items</span>
          </div>
          <div className="progress-bar-bg" style={{ marginTop: '0.5rem' }}>
            <div className="progress-bar-fill" style={{ width: '75%', background: 'linear-gradient(90deg, #7c3aed, #a855f7)' }}></div>
          </div>
        </div>

        {/* Card 4: Profile Completion */}
        <div className="card">
          <div className="card-label">
            <span>Profile Completion</span>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'baseline',
              gap: '0.5rem',
              marginTop: '1.25rem',
            }}
          >
            <span
              style={{ fontFamily: "'Outfit', sans-serif", fontSize: '2.2rem', fontWeight: 800 }}
            >
              92%
            </span>
            <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#10b981' }}>
              Excellent
            </span>
          </div>
          <div className="progress-bar-bg" style={{ marginTop: '1.25rem' }}>
            <div
              className="progress-bar-fill"
              style={{ width: '92%', background: 'linear-gradient(90deg, #6366f1, #10b981)' }}
            ></div>
          </div>
        </div>
      </div>

      {/* Two Column Layout: Recent Analyses + Skill Distribution */}
      <div className="dashboard-columns">
        {/* Left Column: Recent Analyses */}
        <div className="table-card">
          <div className="table-header-flex">
            <h2 className="table-title">Recent Analyses</h2>
            <button
              onClick={onNavigateToTalentCheck}
              className="view-history-link"
              style={{ background: 'none', border: 'none', cursor: 'pointer' }}
            >
              <span>View History</span>
              <ArrowRight size={14} />
            </button>
          </div>

          <table className="custom-table">
            <thead>
              <tr>
                <th>CANDIDATE / RESUME</th>
                <th>JOB TARGET</th>
                <th>MATCH SCORE</th>
                <th>STATUS</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {recentAnalyses.map((item) => (
                <tr key={item.id}>
                  <td>
                    <div className="candidate-cell">
                      <div className="file-icon-box">
                        <FileText size={18} />
                      </div>
                      <div>
                        <div className="file-name">{item.filename}</div>
                        <div className="file-time">{item.time}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ fontWeight: 600, color: '#e2e8f0' }}>{item.target}</td>
                  <td>
                    <div className="match-bar-cell">
                      <div className="mini-bar-bg">
                        <div
                          className="mini-bar-fill"
                          style={{ width: `${item.score}%`, backgroundColor: item.barColor }}
                        ></div>
                      </div>
                      <span style={{ fontWeight: 700, fontSize: '0.85rem', color: item.barColor }}>
                        {item.score}%
                      </span>
                    </div>
                  </td>
                  <td>
                    <span className={`status-badge ${item.badgeClass}`}>{item.status}</span>
                  </td>
                  <td>
                    <button
                      className="icon-btn"
                      style={{ padding: '0.25rem' }}
                      title="More options"
                    >
                      <MoreVertical size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Right Column: Skill Distribution & Quick Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Skill Distribution Card */}
          <div className="skill-chart-card">
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span
                style={{
                  fontFamily: "'Outfit', sans-serif",
                  fontSize: '1.1rem',
                  fontWeight: 700,
                }}
              >
                Skill Distribution
              </span>
              <Target size={16} style={{ color: '#a78bfa' }} />
            </div>

            {/* Radar Polygon Visualization */}
            <svg className="chart-placeholder-svg" viewBox="0 0 200 180">
              {/* Outer Spider Grid */}
              <polygon
                points="100,20 170,60 150,140 50,140 30,60"
                fill="none"
                stroke="rgba(255,255,255,0.08)"
                strokeWidth="1"
              />
              <polygon
                points="100,50 145,75 130,120 70,120 55,75"
                fill="none"
                stroke="rgba(255,255,255,0.12)"
                strokeWidth="1"
              />
              {/* Spider Grid Rays */}
              <line x1="100" y1="90" x2="100" y2="20" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
              <line x1="100" y1="90" x2="170" y2="60" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
              <line x1="100" y1="90" x2="150" y2="140" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
              <line x1="100" y1="90" x2="50" y2="140" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />
              <line x1="100" y1="90" x2="30" y2="60" stroke="rgba(255,255,255,0.06)" strokeWidth="1" />

              {/* Data Area Polygon */}
              <polygon
                points="100,30 160,65 140,135 65,125 40,70"
                fill="rgba(124, 58, 237, 0.28)"
                stroke="#8b5cf6"
                strokeWidth="2"
              />
              {/* Data Points */}
              <circle cx="100" cy="30" r="3" fill="#c084fc" />
              <circle cx="160" cy="65" r="3" fill="#c084fc" />
              <circle cx="140" cy="135" r="3" fill="#c084fc" />
              <circle cx="65" cy="125" r="3" fill="#c084fc" />
              <circle cx="40" cy="70" r="3" fill="#c084fc" />

              {/* Vertex Labels */}
              <text x="100" y="14" fill="#94a3b8" fontSize="8" textAnchor="middle">
                Frontend
              </text>
              <text x="178" y="62" fill="#94a3b8" fontSize="8" textAnchor="start">
                Backend
              </text>
              <text x="156" y="152" fill="#94a3b8" fontSize="8" textAnchor="start">
                Cloud
              </text>
              <text x="44" y="152" fill="#94a3b8" fontSize="8" textAnchor="end">
                Soft Skills
              </text>
              <text x="22" y="62" fill="#94a3b8" fontSize="8" textAnchor="end">
                AI / ML
              </text>
            </svg>

            <div className="chart-stats-row">
              <div className="chart-stat">
                <span className="chart-stat-label">STRONGEST</span>
                <span className="chart-stat-val" style={{ color: '#c084fc' }}>
                  AI / ML
                </span>
              </div>
              <div className="chart-stat">
                <span className="chart-stat-label">GROWING</span>
                <span className="chart-stat-val" style={{ color: '#818cf8' }}>
                  Cloud Infra
                </span>
              </div>
            </div>
          </div>

          {/* Quick Actions Card */}
          <div className="quick-actions-card">
            <span
              style={{
                fontFamily: "'Outfit', sans-serif",
                fontSize: '1.1rem',
                fontWeight: 700,
              }}
            >
              Quick Actions
            </span>

            <button className="btn-action-primary" onClick={onNavigateToTalentCheck}>
              <span>Analyze New JD</span>
              <Zap size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
