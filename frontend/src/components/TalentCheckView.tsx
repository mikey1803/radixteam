import React, { useState } from 'react';
import axios from 'axios';
import {
  Award,
  FileText,
  Briefcase,
  Play,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Sparkles,
  Loader2,
} from 'lucide-react';

export const TalentCheckView: React.FC = () => {
  const [candidateName, setCandidateName] = useState('Jordan Smith');
  const [candidateEmail, setCandidateEmail] = useState('jordan.smith@example.com');
  const [resumeText, setResumeText] = useState(
    'Experienced Full Stack Engineer with 4 years building web apps using React, Python, FastAPI, TypeScript, PostgreSQL, and Docker. Strong background in microservices and UI/UX design.'
  );

  const [jdTitle, setJdTitle] = useState('Senior Full Stack Developer');
  const [jdCompany, setJdCompany] = useState('RadixTeam');
  const [jdDescription, setJdDescription] = useState(
    'We are seeking a Senior Full Stack Developer to lead core features. Must be proficient in Python, FastAPI, React, TypeScript, Docker, Kubernetes, and AWS.'
  );
  const [requiredSkillsStr, setRequiredSkillsStr] = useState(
    'Python, FastAPI, React, TypeScript, Docker, Kubernetes, AWS'
  );

  const [loading, setLoading] = useState(false);
  const [parsing, setParsing] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Handle Resume Parse
  const handleParseResume = async () => {
    if (!resumeText.trim()) return;
    setParsing(true);
    setError(null);
    try {
      const resp = await axios.post('/api/v1/talent-check/candidates/parse-resume', {
        resume_text: resumeText,
      });
      if (resp.data.name) setCandidateName(resp.data.name);
      if (resp.data.email) setCandidateEmail(resp.data.email);
    } catch (err: any) {
      console.error('Parse error', err);
    } finally {
      setParsing(false);
    }
  };

  // Handle Talent Check Evaluation
  const handleRunCheck = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // 1. Create Candidate
      const candidateResp = await axios.post('/api/v1/talent-check/candidates', {
        name: candidateName,
        email: candidateEmail,
        skills: resumeText.split(',').map((s) => s.trim()),
        experience_years: 4.0,
        resume_text: resumeText,
      });

      // 2. Create Job Description
      const jdResp = await axios.post('/api/v1/talent-check/job-descriptions', {
        title: jdTitle,
        company: jdCompany,
        description: jdDescription,
        required_skills: requiredSkillsStr.split(',').map((s) => s.trim()),
        min_experience: 3.0,
      });

      // 3. Run Talent Check Evaluation
      const checkResp = await axios.post('/api/v1/talent-check/check', {
        candidate_id: candidateResp.data.id,
        job_description_id: jdResp.data.id,
      });

      setResult(checkResp.data);
    } catch (err: any) {
      console.error('Check error', err);
      setError(err.response?.data?.detail || 'Failed to run talent check evaluation');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="content-body">
      <div className="welcome-header">
        <div className="system-status">
          <Award size={14} />
          <span>TALENT CHECK ENGINE</span>
        </div>
        <h1>Candidate Fit & Gap Analysis</h1>
        <p>
          Evaluate candidates against job requirements using AI. Calculates readiness score,
          identifies skillset gaps, and generates targeted interview questions.
        </p>
      </div>

      {/* Two Column Form & Evaluation Workspace */}
      <div className="dashboard-columns">
        {/* Left Column: Form Inputs */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Candidate Card */}
          <div className="card">
            <div className="card-label">
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <FileText size={18} style={{ color: '#a78bfa' }} />
                Candidate Resume Input
              </span>
              <button
                className="tag-pill"
                style={{ cursor: 'pointer', background: 'rgba(124,58,237,0.2)', color: '#c084fc' }}
                onClick={handleParseResume}
                disabled={parsing}
              >
                {parsing ? 'Parsing...' : 'AI Auto-Extract'}
              </button>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '1rem',
                marginBottom: '1rem',
              }}
            >
              <div>
                <label
                  style={{
                    fontSize: '0.75rem',
                    color: '#94a3b8',
                    display: 'block',
                    marginBottom: '0.25rem',
                  }}
                >
                  Candidate Name
                </label>
                <input
                  type="text"
                  value={candidateName}
                  onChange={(e) => setCandidateName(e.target.value)}
                  className="search-input"
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: '#100e1d',
                  }}
                />
              </div>

              <div>
                <label
                  style={{
                    fontSize: '0.75rem',
                    color: '#94a3b8',
                    display: 'block',
                    marginBottom: '0.25rem',
                  }}
                >
                  Candidate Email
                </label>
                <input
                  type="email"
                  value={candidateEmail}
                  onChange={(e) => setCandidateEmail(e.target.value)}
                  className="search-input"
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: '#100e1d',
                  }}
                />
              </div>
            </div>

            <div>
              <label
                style={{
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  display: 'block',
                  marginBottom: '0.25rem',
                }}
              >
                Raw Resume Text
              </label>
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                rows={4}
                style={{
                  width: '100%',
                  padding: '0.8rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: '#100e1d',
                  color: '#f1f1f7',
                  fontSize: '0.85rem',
                  fontFamily: 'inherit',
                  outline: 'none',
                  resize: 'vertical',
                }}
              />
            </div>
          </div>

          {/* Job Description Card */}
          <div className="card">
            <div className="card-label">
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Briefcase size={18} style={{ color: '#818cf8' }} />
                Job Target & Requirements
              </span>
            </div>

            <div
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '1rem',
                marginBottom: '1rem',
              }}
            >
              <div>
                <label
                  style={{
                    fontSize: '0.75rem',
                    color: '#94a3b8',
                    display: 'block',
                    marginBottom: '0.25rem',
                  }}
                >
                  Job Title
                </label>
                <input
                  type="text"
                  value={jdTitle}
                  onChange={(e) => setJdTitle(e.target.value)}
                  className="search-input"
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: '#100e1d',
                  }}
                />
              </div>

              <div>
                <label
                  style={{
                    fontSize: '0.75rem',
                    color: '#94a3b8',
                    display: 'block',
                    marginBottom: '0.25rem',
                  }}
                >
                  Company Name
                </label>
                <input
                  type="text"
                  value={jdCompany}
                  onChange={(e) => setJdCompany(e.target.value)}
                  className="search-input"
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.8rem',
                    borderRadius: '8px',
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: '#100e1d',
                  }}
                />
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label
                style={{
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  display: 'block',
                  marginBottom: '0.25rem',
                }}
              >
                Required Skills (comma separated)
              </label>
              <input
                type="text"
                value={requiredSkillsStr}
                onChange={(e) => setRequiredSkillsStr(e.target.value)}
                className="search-input"
                style={{
                  width: '100%',
                  padding: '0.6rem 0.8rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: '#100e1d',
                }}
              />
            </div>

            <div>
              <label
                style={{
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  display: 'block',
                  marginBottom: '0.25rem',
                }}
              >
                Job Description Details
              </label>
              <textarea
                value={jdDescription}
                onChange={(e) => setJdDescription(e.target.value)}
                rows={3}
                style={{
                  width: '100%',
                  padding: '0.8rem',
                  borderRadius: '8px',
                  border: '1px solid rgba(255,255,255,0.1)',
                  background: '#100e1d',
                  color: '#f1f1f7',
                  fontSize: '0.85rem',
                  fontFamily: 'inherit',
                  outline: 'none',
                  resize: 'vertical',
                }}
              />
            </div>
          </div>

          <button className="btn-action-primary" onClick={handleRunCheck} disabled={loading}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />}
              {loading ? 'Evaluating Candidate...' : 'Run Talent Check Analysis'}
            </span>
            <Play size={18} />
          </button>

          {error && (
            <div
              style={{
                color: '#f43f5e',
                fontSize: '0.85rem',
                background: 'rgba(244,63,94,0.1)',
                padding: '0.75rem',
                borderRadius: '8px',
              }}
            >
              ❌ {error}
            </div>
          )}
        </div>

        {/* Right Column: Live Results Display */}
        <div>
          {result ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Score & Recommendation Card */}
              <div className="card">
                <div className="card-label">EVALUATION SUMMARY</div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}
                >
                  <div>
                    <div
                      style={{
                        fontSize: '2.4rem',
                        fontFamily: "'Outfit', sans-serif",
                        fontWeight: 800,
                        color: '#f8fafc',
                      }}
                    >
                      {result.overall_score}%
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Overall Readiness</div>
                  </div>

                  <span
                    className={`status-badge ${
                      result.recommendation === 'PASS'
                        ? 'qualified'
                        : result.recommendation === 'REVIEW'
                        ? 'processing'
                        : 'lowmatch'
                    }`}
                    style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
                  >
                    {result.recommendation}
                  </span>
                </div>

                <div className="progress-bar-bg" style={{ marginTop: '1rem' }}>
                  <div
                    className="progress-bar-fill"
                    style={{
                      width: `${result.overall_score}%`,
                      background:
                        result.overall_score >= 70
                          ? 'linear-gradient(90deg, #7c3aed, #10b981)'
                          : 'linear-gradient(90deg, #7c3aed, #f43f5e)',
                    }}
                  ></div>
                </div>

                {result.reasoning && (
                  <p
                    style={{
                      fontSize: '0.85rem',
                      color: '#cbd5e1',
                      marginTop: '1rem',
                      lineHeight: 1.5,
                      background: 'rgba(255,255,255,0.03)',
                      padding: '0.75rem',
                      borderRadius: '8px',
                    }}
                  >
                    "{result.reasoning}"
                  </p>
                )}
              </div>

              {/* Matched vs Gap Breakdown */}
              <div className="card">
                <div className="card-label">SKILLSET BREAKDOWN</div>

                <div style={{ marginBottom: '1rem' }}>
                  <div
                    style={{
                      fontSize: '0.75rem',
                      color: '#34d399',
                      fontWeight: 700,
                      marginBottom: '0.4rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                    }}
                  >
                    <CheckCircle2 size={14} /> MATCHED SKILLS ({result.matched_skills?.length || 0})
                  </div>
                  <div className="tags-wrapper">
                    {result.matched_skills?.map((skill: string, idx: number) => (
                      <span
                        key={idx}
                        className="tag-pill"
                        style={{ background: 'rgba(16,185,129,0.15)', color: '#34d399' }}
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>

                <div>
                  <div
                    style={{
                      fontSize: '0.75rem',
                      color: '#fb7185',
                      fontWeight: 700,
                      marginBottom: '0.4rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.3rem',
                    }}
                  >
                    <AlertCircle size={14} /> IDENTIFIED SKILL GAPS (
                    {result.skill_gaps?.length || 0})
                  </div>
                  <div className="tags-wrapper">
                    {result.skill_gaps?.map((gap: string, idx: number) => (
                      <span
                        key={idx}
                        className="tag-pill"
                        style={{ background: 'rgba(244,63,94,0.15)', color: '#fb7185' }}
                      >
                        {gap}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Generated Interview Questions */}
              {result.interview_questions && result.interview_questions.length > 0 && (
                <div className="card">
                  <div className="card-label">
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                      <HelpCircle size={16} style={{ color: '#c084fc' }} />
                      GENERATED INTERVIEW QUESTIONS
                    </span>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                      marginTop: '0.5rem',
                    }}
                  >
                    {result.interview_questions.map((q: any, idx: number) => (
                      <div
                        key={idx}
                        style={{
                          background: 'rgba(255,255,255,0.03)',
                          padding: '0.75rem',
                          borderRadius: '8px',
                          borderLeft: '3px solid #7c3aed',
                        }}
                      >
                        <div
                          style={{
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            color: '#a78bfa',
                            textTransform: 'uppercase',
                          }}
                        >
                          Focus: {q.focus_area}
                        </div>
                        <div
                          style={{
                            fontSize: '0.85rem',
                            color: '#f1f1f7',
                            marginTop: '0.2rem',
                          }}
                        >
                          {q.question}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div
              className="card"
              style={{
                textAlign: 'center',
                padding: '3rem 1.5rem',
                color: '#64748b',
              }}
            >
              <Award size={48} style={{ margin: '0 auto 1rem', opacity: 0.4 }} />
              <h3 style={{ color: '#e2e8f0', marginBottom: '0.5rem' }}>No Analysis Selected</h3>
              <p style={{ fontSize: '0.85rem', maxWidth: '280px', margin: '0 auto' }}>
                Fill in candidate details and job requirements on the left, then click "Run Talent
                Check Analysis".
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
