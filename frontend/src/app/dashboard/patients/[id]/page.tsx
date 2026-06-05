'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/api';
import { 
  ArrowLeft, 
  Phone, 
  ShieldAlert, 
  Sparkles, 
  Check, 
  Plus, 
  ChevronRight, 
  Calendar, 
  FileText, 
  ClipboardCheck, 
  Activity, 
  AlertTriangle,
  Heart,
  Clock,
  BriefcaseMedical
} from 'lucide-react';

interface PatientDetailData {
  id: string;
  telegram_id: number | null;
  phone: string | null;
  full_name: string;
  age: number | null;
  gender: string | null;
  village: string | null;
  sub_center: string | null;
  preferred_language: string;
  medical_history: Record<string, any>;
  is_active: boolean;
  risk_score: number;
  risk_level: string;
  risk_factors: string[];
  created_at: string;
  assigned_hcw: { id: string; name: string } | null;
  assigned_doctor: { id: string; name: string } | null;
  prescriptions_count: number;
  prescriptions: Array<{
    id: string;
    raw_image_url: string;
    raw_ocr_text: string | null;
    structured_data: Array<{
      name: string;
      dosage?: string;
      frequency?: string;
      duration?: string;
    }>;
    issue_date: string | null;
    telegram_id: number | null;
    diagnosis: string | null;
    created_at: string;
  }>;
  active_reminders: Array<{
    id: string;
    medicine_name: string;
    dosage: string | null;
    schedule_time: string;
    frequency: string;
    start_date: string;
  }>;
  lab_reports: Array<{
    id: string;
    report_type: string;
    extracted_metrics: Record<string, any>;
    summary: string;
    ai_explanation: string | null;
    file_url: string;
    uploaded_at: string;
  }>;
  active_alerts: Array<{
    id: string;
    risk_level: string;
    source: string;
    alert_message: string;
    reason?: string | null;
    recommendation?: string | null;
    created_at: string;
  }>;
  recent_symptoms: Array<{
    id: string;
    answers: Record<string, string>;
    severity_score: number;
    symptoms: string | null;
    severity: string | null;
    recommendation: string | null;
    created_at: string;
  }>;
  timeline: Array<{
    type: string;
    date: string | null;
    title: string;
    description: string;
  }>;
  ai_health_summary: string;
}

interface ComplianceStats {
  compliance_rate: number;
  total_events: number;
  taken: number;
  missed: number;
  pending: number;
}

interface CopilotData {
  recommendations: string[];
  suggested_diagnosis: string;
  suggested_follow_up: string;
  suggested_lab_tests: string[];
  medication_review: string;
  compliance_assessment: string;
}

function AiHealthSummaryCard({ summary }: { summary: string }) {
  if (!summary) return null;
  
  const lines = summary.split('\n');
  
  return (
    <div className="p-6 rounded-3xl bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-100 shadow-sm relative overflow-hidden group">
      <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-emerald-500/5 rounded-full blur-xl transition-all group-hover:scale-110" />
      
      <div className="flex items-center gap-2 mb-4 border-b border-emerald-100/50 pb-3">
        <span className="text-xl">🤖</span>
        <h4 className="text-xs font-bold text-emerald-700 uppercase tracking-widest block font-outfit">AI Clinical Summary</h4>
      </div>
      
      <div className="space-y-2 text-xs text-slate-700 leading-relaxed font-semibold">
        {lines.map((line, idx) => {
          const cleanLine = line.trim();
          if (!cleanLine) return <div key={idx} className="h-1" />;
          
          if (cleanLine.startsWith('•') || cleanLine.startsWith('-')) {
            return (
              <div key={idx} className="flex items-start gap-2 py-0.5">
                <span className="text-emerald-500 select-none font-bold">•</span>
                <span className="text-slate-600">{cleanLine.replace(/^[•-]\s*/, '')}</span>
              </div>
            );
          }
          
          if (cleanLine.toLowerCase().includes('overall condition:')) {
            const parts = cleanLine.split(':');
            const condition = parts[1]?.trim() || '';
            let colorClass = 'text-emerald-700 border-emerald-200 bg-emerald-50';
            if (condition.toLowerCase().includes('critical')) {
              colorClass = 'text-rose-700 border-rose-200 bg-rose-50 animate-pulse font-bold';
            } else if (condition.toLowerCase().includes('guard')) {
              colorClass = 'text-amber-700 border-amber-200 bg-amber-50 font-bold';
            }
            
            return (
              <div key={idx} className="mt-4 pt-3 border-t border-emerald-100/50 flex justify-between items-center">
                <span className="font-bold text-slate-500 uppercase tracking-wider text-[10px]">{parts[0]}:</span>
                <span className={`px-2.5 py-1 text-xs font-bold rounded-xl border ${colorClass}`}>
                  {condition}
                </span>
              </div>
            );
          }
          
          return <p key={idx} className="text-slate-700 font-semibold">{cleanLine}</p>;
        })}
      </div>
    </div>
  );
}

function RiskScoreGauge({ score, level }: { score: number, level: string }) {
  let strokeColor = 'stroke-emerald-500';
  let bgColor = 'bg-emerald-50';
  let textColor = 'text-emerald-700';
  
  if (score > 80) {
    strokeColor = 'stroke-rose-500';
    bgColor = 'bg-rose-50';
    textColor = 'text-rose-700';
  } else if (score > 60) {
    strokeColor = 'stroke-orange-500';
    bgColor = 'bg-orange-50';
    textColor = 'text-orange-700';
  } else if (score > 30) {
    strokeColor = 'stroke-amber-500';
    bgColor = 'bg-amber-50';
    textColor = 'text-amber-700';
  }

  const radius = 30;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (score / 100) * circumference;

  return (
    <div className="flex items-center gap-4 p-5 rounded-3xl bg-white border border-slate-100 shadow-sm flex-1">
      <div className="relative h-20 w-20 flex items-center justify-center flex-shrink-0">
        <svg className="w-20 h-20 transform -rotate-90">
          <circle cx="40" cy="40" r={radius} className="stroke-slate-100 fill-none" strokeWidth="6" />
          <circle 
            cx="40" 
            cy="40" 
            r={radius} 
            className={`fill-none ${strokeColor} transition-all duration-500`} 
            strokeWidth="6" 
            strokeDasharray={circumference} 
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
          />
        </svg>
        <span className="absolute text-xl font-extrabold text-slate-800">{score}</span>
      </div>
      <div>
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Predictive Risk Level</span>
        <span className={`inline-block px-2.5 py-0.5 text-xs font-bold rounded-full border mt-1.5 ${bgColor} ${textColor} border-current`}>
          {level} Risk
        </span>
      </div>
    </div>
  );
}

export default function PatientDetail({ params }: { params: { id: string } }) {
  const [patientData, setPatientData] = useState<PatientDetailData | null>(null);
  const [complianceStats, setComplianceStats] = useState<ComplianceStats | null>(null);
  const [copilotData, setCopilotData] = useState<CopilotData | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [loadingCopilot, setLoadingCopilot] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [activeTab, setActiveTab] = useState<'prescriptions' | 'lab_reports' | 'symptoms' | 'compliance' | 'timeline'>('prescriptions');

  const fetchPatientData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [data, stats] = await Promise.all([
        api.getPatientDetail(params.id),
        api.getComplianceStats(params.id),
      ]);
      setPatientData(data);
      setComplianceStats(stats);
    } catch (err) {
      console.error(err);
      if (err instanceof ApiError) {
        setError(`Failed to retrieve records for patient (Status ${err.status}).`);
      } else {
        setError('Network connection error to AAROGYA client gateway.');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchCopilotData = async () => {
    setLoadingCopilot(true);
    try {
      const data = await api.getPatientCopilot(params.id);
      setCopilotData(data);
    } catch (err) {
      console.error('Failed to load copilot recommendations:', err);
    } finally {
      setLoadingCopilot(false);
    }
  };

  useEffect(() => {
    fetchPatientData();
    fetchCopilotData();
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <span className="text-4xl animate-spin text-emerald-500">🔄</span>
        <h3 className="font-semibold text-lg text-slate-600">Retrieving patient medical record dossier...</h3>
      </div>
    );
  }

  if (error || !patientData) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 max-w-md mx-auto text-center">
        <span className="text-5xl">📁</span>
        <h3 className="font-bold text-xl text-rose-500">Failed to Load Profile</h3>
        <p className="text-sm text-slate-500">{error || 'Patient files missing'}</p>
        <div className="flex gap-4">
          <Link href="/dashboard" className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-xl transition text-sm font-semibold border border-slate-200">
            Back to Dashboard
          </Link>
          <button 
            onClick={fetchPatientData}
            className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-md transition text-sm"
          >
            Retry Fetch
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Patient Profile Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <Link href="/dashboard" className="text-xs font-semibold text-emerald-600 hover:underline flex items-center gap-1">
            <ArrowLeft className="w-3.5 h-3.5" /> Return to Dashboard
          </Link>
          <h2 className="text-3xl font-bold font-outfit mt-2 text-slate-800 flex items-center gap-3">
            {patientData.full_name}
          </h2>
          <p className="text-slate-400 text-xs mt-1">Patient UUID: {patientData.id} • Telegram ID: {patientData.telegram_id || 'N/A'}</p>
        </div>
        
        <div className="flex gap-2">
          {patientData.phone && (
            <a href={`tel:${patientData.phone}`} className="inline-flex items-center gap-2 px-5 py-2.5 text-sm bg-emerald-500 hover:bg-emerald-600 text-white rounded-xl shadow-md transition font-semibold">
              <Phone className="w-4 h-4" /> Call Patient ({patientData.phone})
            </a>
          )}
        </div>
      </div>

      {/* Demographics Summary Card */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm">
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Demographics</span>
          <span className="text-slate-800 font-bold text-sm mt-1 block">
            {patientData.age ? `${patientData.age} yrs` : 'N/A'} • {patientData.gender || 'N/A'}
          </span>
        </div>
        
        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Location Details</span>
          <span className="text-slate-800 font-bold text-sm mt-1 block">
            {patientData.village || 'N/A'} ({patientData.sub_center || 'N/A'})
          </span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Assigned HCW Coordinator</span>
          <span className="text-emerald-600 font-bold text-sm mt-1 block">
            {patientData.assigned_hcw?.name || 'Unassigned'}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Preferred Language</span>
          <span className="text-slate-800 font-bold text-sm mt-1 block capitalize">
            {patientData.preferred_language}
          </span>
        </div>
      </div>

      {/* Risk Gauges and Contributors Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <RiskScoreGauge score={patientData.risk_score} level={patientData.risk_level} />

        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-3">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Clinical Risk Contributors</span>
          {patientData.risk_factors && patientData.risk_factors.length > 0 ? (
            <div className="space-y-1.5 max-h-24 overflow-y-auto pr-2">
              {patientData.risk_factors.map((factor: string, idx: number) => (
                <div key={idx} className="flex items-center gap-2 text-xs font-semibold text-rose-600 bg-rose-50 py-1.5 px-3 rounded-lg border border-rose-100/50">
                  <span className="w-1.5 h-1.5 rounded-full bg-rose-500 flex-shrink-0" />
                  <span>{factor}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No risk contributors flagged.</p>
          )}
        </div>
      </div>

      {/* Doctor Copilot Section */}
      <section className="space-y-4">
        <h3 className="text-lg font-bold font-outfit text-slate-800 flex items-center gap-2">
          <span className="p-2 bg-blue-50 text-blue-600 rounded-xl"><Sparkles className="w-4 h-4" /></span>
          AI Doctor Copilot Recommendations
        </h3>
        
        {loadingCopilot ? (
          <div className="p-12 text-center bg-white border border-slate-100 rounded-3xl text-slate-500 italic shadow-sm">
            <span className="animate-spin text-blue-500 inline-block mr-2">🔄</span> Synthesizing medical-history copilot diagnosis and guidelines...
          </div>
        ) : copilotData ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            
            {/* Suggested Diagnosis */}
            <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Suggested Diagnosis</span>
              <p className="text-sm font-bold text-slate-800 bg-blue-50/50 p-3.5 rounded-xl border border-blue-100">
                {copilotData.suggested_diagnosis}
              </p>
            </div>

            {/* AI Recommendations */}
            <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">AI Clinical Recommendations</span>
              <ul className="space-y-1.5 max-h-28 overflow-y-auto pr-2">
                {copilotData.recommendations.map((rec: string, i: number) => (
                  <li key={i} className="text-xs font-semibold text-slate-600 flex items-start gap-1.5">
                    <span className="text-emerald-500 font-bold">•</span>
                    <span>{rec}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Follow up */}
            <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Suggested Follow-Up</span>
              <p className="text-sm font-bold text-slate-850 bg-amber-50/50 p-3.5 rounded-xl border border-amber-100 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-amber-600" />
                {copilotData.suggested_follow_up}
              </p>
            </div>

            {/* Lab tests */}
            <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Suggested Lab Tests</span>
              <div className="flex flex-wrap gap-2 max-h-28 overflow-y-auto pr-2">
                {copilotData.suggested_lab_tests.map((test: string, i: number) => (
                  <span key={i} className="px-2.5 py-1 bg-slate-50 border border-slate-200 text-slate-600 text-xs font-bold rounded-lg shadow-sm">
                    {test}
                  </span>
                ))}
              </div>
            </div>

            {/* Med review */}
            <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Medication Review</span>
              <p className="text-xs font-medium text-slate-600 bg-slate-50 p-3.5 rounded-xl border border-slate-100 max-h-28 overflow-y-auto">
                {copilotData.medication_review}
              </p>
            </div>

            {/* Compliance risk */}
            <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block">Compliance Assessment</span>
              <div className="pt-2">
                <span className={`inline-block px-3 py-1.5 text-xs font-bold rounded-xl border ${
                  copilotData.compliance_assessment.toLowerCase().includes('risk') 
                    ? 'bg-rose-50 text-rose-600 border-rose-100 animate-pulse' 
                    : 'bg-emerald-50 text-emerald-600 border-emerald-100'
                }`}>
                  {copilotData.compliance_assessment}
                </span>
              </div>
            </div>

          </div>
        ) : (
          <div className="p-8 text-center bg-white border border-slate-100 rounded-3xl text-slate-400 shadow-sm">
            AI Clinical recommendations not available.
          </div>
        )}
      </section>

      {/* Main Tabs Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <section className="lg:col-span-2 space-y-6">
          <div className="flex border-b border-slate-200 overflow-x-auto whitespace-nowrap gap-1">
            {(['prescriptions', 'lab_reports', 'symptoms', 'compliance', 'timeline'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-6 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition ${
                  activeTab === tab 
                    ? 'border-emerald-500 text-emerald-600' 
                    : 'border-transparent text-slate-400 hover:text-slate-600'
                }`}
              >
                {tab.replace('_', ' ')}
              </button>
            ))}
          </div>

          {activeTab === 'prescriptions' && (
            <div className="space-y-8 animate-fade-in">
              {/* Active Reminders */}
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-bold font-outfit text-slate-800">Active Scheduled Reminders</h3>
                  <span className="text-xs text-slate-400 font-semibold">{patientData.active_reminders.length} reminders</span>
                </div>
                {patientData.active_reminders.length === 0 ? (
                  <div className="p-6 text-center rounded-2xl bg-white border border-slate-150 text-slate-400 text-xs font-semibold">
                    No active medicine reminders generated. Upload a prescription through Telegram to schedule.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {patientData.active_reminders.map((rem) => (
                      <div key={rem.id} className="p-4 rounded-2xl bg-white border border-slate-100 shadow-sm flex justify-between items-center">
                        <div>
                          <h4 className="font-bold text-slate-800 text-sm">{rem.medicine_name}</h4>
                          <p className="text-xs text-slate-400 font-semibold mt-0.5">{rem.dosage || '1 unit'} • {rem.frequency}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-xs font-bold text-slate-500 bg-slate-50 px-2 py-1 rounded border border-slate-100 flex items-center gap-1"><Clock className="w-3.5 h-3.5 text-slate-400" /> {rem.schedule_time}</span>
                          <span className="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-emerald-50 text-emerald-600 border border-emerald-100">
                            Active
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Prescription History */}
              <div className="space-y-4">
                <h3 className="text-lg font-bold font-outfit text-slate-800">Prescription Records History</h3>
                {!patientData.prescriptions || patientData.prescriptions.length === 0 ? (
                  <div className="p-6 text-center rounded-2xl bg-white border border-slate-150 text-slate-400 text-xs font-semibold">
                    No prescription uploads logged for this patient.
                  </div>
                ) : (
                  <div className="space-y-6">
                    {patientData.prescriptions.map((rx) => {
                      const imgUrl = rx.raw_image_url
                        ? (rx.raw_image_url.startsWith('http') 
                          ? rx.raw_image_url 
                          : `${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace('/api/v1', '')}${rx.raw_image_url}`)
                        : '';
                      return (
                        <div key={rx.id} className="p-5 rounded-3xl bg-white border border-slate-100 flex flex-col md:flex-row gap-6 shadow-sm">
                          {imgUrl && (
                            <div className="w-full md:w-32 h-32 relative rounded-2xl overflow-hidden border border-slate-150 flex-shrink-0 group bg-slate-100">
                              <img 
                                src={imgUrl} 
                                alt={`Prescription ${rx.diagnosis || rx.id}`} 
                                className="w-full h-full object-cover transition duration-300 group-hover:scale-105"
                              />
                              <a 
                                href={imgUrl} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="absolute inset-0 bg-slate-900/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition text-xs font-bold text-white"
                              >
                                View File 🔍
                              </a>
                            </div>
                          )}
                          <div className="flex-1 space-y-3">
                            <div className="flex justify-between items-start">
                              <div>
                                <span className="px-2.5 py-0.5 text-[9px] font-bold uppercase rounded-full bg-emerald-50 text-emerald-600 border border-emerald-100">
                                  Diagnosis Focus
                                </span>
                                <h4 className="text-base font-bold text-slate-800 mt-1">{rx.diagnosis || 'Unknown Diagnosis'}</h4>
                              </div>
                              <span className="text-xs font-bold text-slate-400 font-mono">
                                {rx.issue_date ? new Date(rx.issue_date).toLocaleDateString() : 'N/A'}
                              </span>
                            </div>
                            
                            <div className="space-y-1">
                              <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Structured Medicines</span>
                              {!rx.structured_data || rx.structured_data.length === 0 ? (
                                <p className="text-xs text-slate-400 italic">No medicines extracted.</p>
                              ) : (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-1">
                                  {rx.structured_data.map((med, idx) => (
                                    <div key={idx} className="p-2.5 rounded-xl bg-slate-50 border border-slate-150 text-xs">
                                      <span className="font-bold text-slate-700 block">{med.name}</span>
                                      <span className="text-slate-400 text-[10px] font-medium block mt-0.5">{med.dosage || 'As prescribed'} • {med.frequency || 'once daily'}</span>
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          )}

          {activeTab === 'lab_reports' && (
            <div className="space-y-6">
              <h3 className="text-lg font-bold font-outfit text-slate-800">Biochemical Lab Reports</h3>
              {patientData.lab_reports.length === 0 ? (
                <div className="p-8 text-center rounded-2xl bg-white border border-slate-150 text-slate-400 font-semibold">
                  No blood diagnostic tests processed. Upload a lab report through Telegram.
                </div>
              ) : (
                patientData.lab_reports.map((rep) => {
                  const fileUrl = rep.file_url
                    ? (rep.file_url.startsWith('http') 
                      ? rep.file_url 
                      : `${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace('/api/v1', '')}${rep.file_url}`)
                    : '';
                  return (
                    <div key={rep.id} className="space-y-6 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm">
                      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                        <div>
                          <h4 className="font-bold text-slate-800 text-sm">{rep.report_type || 'Lab Report'}</h4>
                          {fileUrl && (
                            <a 
                              href={fileUrl} 
                              target="_blank" 
                              rel="noopener noreferrer" 
                              className="text-[10px] text-emerald-600 hover:underline font-semibold mt-1 block"
                            >
                              📄 View Original Lab File
                            </a>
                          )}
                        </div>
                        <span className="text-xs text-slate-400 font-semibold">Uploaded {new Date(rep.uploaded_at).toLocaleDateString()}</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {Object.entries(rep.extracted_metrics).map(([key, details]: [string, any]) => {
                          const isHigh = details?.status === 'high';
                          const isLow = details?.status === 'low';
                          return (
                            <div key={key} className="p-4 rounded-2xl bg-slate-50 border border-slate-150">
                              <span className="text-xs text-slate-500 font-semibold block">{key}</span>
                              <div className="flex justify-between items-baseline mt-2">
                                <span className={`text-xl font-extrabold ${isHigh ? 'text-rose-600' : isLow ? 'text-amber-600' : 'text-slate-800'}`}>
                                  {details?.value} {details?.unit}
                                </span>
                                {details?.reference_range && (
                                  <span className="text-[10px] text-slate-400 font-mono font-bold">Ref: {details.reference_range}</span>
                                )}
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      {rep.ai_explanation && (
                        <div className="space-y-2">
                          <span className="text-xs text-emerald-600 font-bold uppercase tracking-wider block flex items-center gap-1">
                            <Sparkles className="w-3.5 h-3.5" /> AI Biomarker Insights
                          </span>
                          <p className="text-xs font-semibold text-slate-600 leading-relaxed bg-emerald-50/50 p-4 rounded-2xl border border-emerald-100/50">
                            {rep.ai_explanation}
                          </p>
                        </div>
                      )}

                      <div className="space-y-2">
                        <span className="text-xs text-slate-400 font-bold uppercase tracking-wider block">Raw OCR Summary</span>
                        <p className="text-[11px] text-slate-400 leading-relaxed bg-slate-50 p-4 rounded-2xl border border-slate-150 max-h-32 overflow-y-auto font-mono">
                          {rep.summary}
                        </p>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}

          {activeTab === 'symptoms' && (
            <div className="space-y-6">
              <h3 className="text-lg font-bold font-outfit text-slate-800">Symptom Log History</h3>
              {patientData.recent_symptoms.length === 0 ? (
                <div className="p-8 text-center rounded-2xl bg-white border border-slate-150 text-slate-400 font-semibold">
                  No symptom log records submitted by patient check-ins yet.
                </div>
              ) : (
                <div className="space-y-6">
                  {patientData.recent_symptoms.map((log) => {
                    const severity = log.severity || (log.severity_score >= 8 ? 'High' : log.severity_score >= 5 ? 'Medium' : 'Low');
                    const sevColor = severity.toLowerCase() === 'high' 
                      ? 'bg-rose-55 text-rose-600 border-rose-100' 
                      : severity.toLowerCase() === 'medium'
                      ? 'bg-amber-50 text-amber-600 border-amber-100'
                      : 'bg-emerald-50 text-emerald-600 border-emerald-100';

                    return (
                      <div key={log.id} className="p-5 rounded-3xl bg-white border border-slate-100 flex flex-col gap-4 shadow-sm">
                        <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                          <span className="text-xs text-slate-400 font-semibold">
                            Logged: {new Date(log.created_at).toLocaleString()}
                          </span>
                          <span className={`px-2.5 py-0.5 text-xs font-bold uppercase rounded-full border ${sevColor}`}>
                            {severity} Severity (Score: {log.severity_score}/10)
                          </span>
                        </div>
                        
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1.5">Check-in Responses</span>
                            <ul className="text-xs text-slate-600 space-y-1 bg-slate-50 p-3.5 rounded-2xl border border-slate-150 font-semibold">
                              {Object.entries(log.answers).map(([symp, ans]) => (
                                <li key={symp} className="capitalize flex justify-between">
                                  <span className="text-slate-400">{symp.replace('_', ' ')}:</span>
                                  <span className="font-bold text-slate-700">{ans}</span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          <div>
                            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-1.5">Classified Symptoms</span>
                            <div className="p-3.5 rounded-2xl bg-slate-50 border border-slate-150 text-xs text-slate-700 font-semibold min-h-[72px]">
                              {log.symptoms || 'No specific clinical symptoms identified.'}
                            </div>
                          </div>
                        </div>

                        {log.recommendation && (
                          <div className="p-3.5 rounded-2xl bg-emerald-50/50 border border-emerald-100/50 text-xs">
                            <span className="text-[10px] text-emerald-700 font-bold uppercase tracking-wider block mb-1">📋 AI Treatment Care Guidance</span>
                            <p className="text-slate-600 font-semibold leading-relaxed mt-1">{log.recommendation}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {activeTab === 'compliance' && (
            <div className="space-y-6">
              <h3 className="text-lg font-bold font-outfit text-slate-800">Medicine Adherence Analytics</h3>
              
              {complianceStats ? (
                <div className="space-y-6 animate-fade-in">
                  <div className="p-6 rounded-3xl bg-white border border-slate-100 text-center shadow-sm">
                    <span className="text-xs text-slate-400 font-bold uppercase tracking-widest block mb-2">Overall Compliance Rate</span>
                    <h3 className={`text-5xl font-extrabold font-outfit ${
                      complianceStats.compliance_rate >= 90 ? 'text-emerald-500' 
                      : complianceStats.compliance_rate >= 75 ? 'text-amber-500' 
                      : 'text-rose-500'
                    }`}>
                      {complianceStats.compliance_rate}%
                    </h3>
                    <div className="w-full max-w-xs mx-auto bg-slate-100 h-2 rounded-full mt-4 overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-700 ${
                          complianceStats.compliance_rate >= 90 ? 'bg-emerald-500'
                          : complianceStats.compliance_rate >= 75 ? 'bg-amber-500'
                          : 'bg-rose-500'
                        }`}
                        style={{ width: `${complianceStats.compliance_rate}%` }}
                      />
                    </div>
                  </div>

                  {(() => {
                    const rate = complianceStats.compliance_rate;
                    let title = "Excellent Adherence";
                    let emoji = "🟢";
                    let desc = "Patient is consistently taking medications on schedule. Lower risk of therapeutic failure.";
                    let borderClass = "border-emerald-100 bg-emerald-50/50";
                    let textClass = "text-emerald-700";
                    
                    if (rate >= 90) {
                      title = "Excellent Adherence";
                      emoji = "🟢";
                      desc = "Patient is consistently taking medications on schedule. Lower risk of therapeutic failure.";
                      borderClass = "border-emerald-100 bg-emerald-50/50";
                      textClass = "text-emerald-750";
                    } else if (rate >= 75) {
                      title = "Good Adherence";
                      emoji = "🟡";
                      desc = "Patient is mostly compliant. Review minor missed doses during next coordination call.";
                      borderClass = "border-amber-100 bg-amber-50/50";
                      textClass = "text-amber-700";
                    } else {
                      title = "Poor Adherence - Action Required";
                      emoji = "🚨";
                      desc = "CRITICAL ALERT: Patient is missing medication schedule frequently. High risk of decompensation.";
                      borderClass = "border-rose-100 bg-rose-50/50";
                      textClass = "text-rose-700";
                    }
                    
                    let complianceInsight = "";
                    if (complianceStats.missed > 0) {
                      complianceInsight += `Patient missed ${complianceStats.missed} doses this week. `;
                    } else {
                      complianceInsight += "Patient did not miss any doses this week. ";
                    }
                    
                    if (rate < 75) {
                      complianceInsight += "High probability of non-compliance.";
                    } else if (rate < 90) {
                      complianceInsight += "Medium probability of non-compliance.";
                    } else {
                      complianceInsight += "Low probability of non-compliance.";
                    }
                    
                    return (
                      <div className={`p-5 rounded-3xl border ${borderClass} flex items-start gap-4`}>
                        <span className="text-2xl">{emoji}</span>
                        <div className="space-y-2">
                          <h4 className={`font-bold ${textClass}`}>{title} ({rate}%)</h4>
                          <p className="text-xs font-semibold text-slate-600 leading-relaxed">{desc}</p>
                          <div className="pt-2 border-t border-slate-250 text-[11px] text-slate-400">
                            <strong>Compliance Insight:</strong> {complianceInsight}
                          </div>
                        </div>
                      </div>
                    );
                  })()}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 rounded-2xl bg-white border border-slate-100 text-center shadow-sm">
                      <span className="text-xs text-slate-400 font-semibold block">Total Events</span>
                      <span className="text-2xl font-extrabold text-slate-700 mt-1 block">{complianceStats.total_events}</span>
                    </div>
                    <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-100 text-emerald-700 text-center shadow-sm">
                      <span className="text-xs font-semibold block">Taken ✅</span>
                      <span className="text-2xl font-extrabold mt-1 block">{complianceStats.taken}</span>
                    </div>
                    <div className="p-4 rounded-2xl bg-rose-55 border border-rose-100 text-rose-700 text-center shadow-sm">
                      <span className="text-xs font-semibold block">Missed ❌</span>
                      <span className="text-2xl font-extrabold mt-1 block">{complianceStats.missed}</span>
                    </div>
                    <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100 text-amber-700 text-center shadow-sm">
                      <span className="text-xs font-semibold block">Pending ⏳</span>
                      <span className="text-2xl font-extrabold mt-1 block">{complianceStats.pending}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center rounded-3xl bg-white border border-slate-150 text-slate-400 font-semibold">
                  No compliance tracking data available for this patient.
                </div>
              )}
            </div>
          )}

          {activeTab === 'timeline' && (
            <div className="space-y-6">
              <h3 className="text-lg font-bold font-outfit text-slate-800">Patient Chronological History</h3>
              {!patientData.timeline || patientData.timeline.length === 0 ? (
                <div className="p-8 text-center rounded-2xl bg-white border border-slate-150 text-slate-400 font-semibold">
                  No chronological medical events recorded.
                </div>
              ) : (
                <div className="relative pl-6 border-l border-slate-200 space-y-8 ml-3 py-2">
                  {patientData.timeline.map((event, idx) => {
                    let icon = '📋';
                    let dotColor = 'bg-slate-50 border-slate-200 text-slate-600';
                    
                    switch (event.type) {
                      case 'registration':
                        icon = '👤';
                        dotColor = 'bg-emerald-50 border-emerald-200 text-emerald-600';
                        break;
                      case 'prescription':
                        icon = '💊';
                        dotColor = 'bg-blue-50 border-blue-200 text-blue-600';
                        break;
                      case 'lab_report':
                        icon = '🔬';
                        dotColor = 'bg-indigo-50 border-indigo-200 text-indigo-600';
                        break;
                      case 'checkin':
                        icon = '🌡';
                        dotColor = 'bg-amber-50 border-amber-200 text-amber-600';
                        break;
                      case 'alert':
                        icon = '🚨';
                        dotColor = 'bg-rose-50 border-rose-200 text-rose-600';
                        break;
                    }
                    
                    return (
                      <div key={idx} className="relative group">
                        <div className={`absolute -left-[35px] top-1.5 w-6 h-6 rounded-full border flex items-center justify-center text-xs ${dotColor} z-10 shadow-sm font-bold`}>
                          {icon}
                        </div>
                        
                        <div className="p-4 rounded-2xl bg-white border border-slate-100 hover:border-slate-200 transition space-y-1.5 shadow-sm">
                          <div className="flex justify-between items-start gap-4">
                            <h4 className="font-bold text-slate-800 text-sm">{event.title}</h4>
                            <span className="text-[9px] text-slate-400 font-bold whitespace-nowrap bg-slate-50 px-2 py-0.5 rounded-lg border border-slate-150">
                              {event.date ? new Date(event.date).toLocaleString() : 'N/A'}
                            </span>
                          </div>
                          <p className="text-xs text-slate-500 font-semibold leading-relaxed">{event.description}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </section>

        {/* Sidebar Cards */}
        <section className="space-y-6">
          <AiHealthSummaryCard summary={patientData.ai_health_summary} />

          {/* Active Risk Banner */}
          {patientData.active_alerts.length > 0 ? (
            <div className="p-6 rounded-3xl bg-rose-50 border border-rose-100 space-y-3 shadow-sm">
              <h4 className="text-[10px] font-bold text-rose-500 uppercase tracking-widest block font-outfit">Active Risk State</h4>
              <div className="flex items-center gap-2 mt-1">
                <span className="h-3 w-3 rounded-full bg-rose-500 animate-ping" />
                <span className="text-md font-extrabold text-rose-600">CRITICAL ATTENTION</span>
              </div>
              <ul className="space-y-3 mt-3">
                {patientData.active_alerts.map((alert) => (
                  <li key={alert.id} className="text-xs text-rose-600/90 font-semibold leading-relaxed border-t border-rose-100 pt-2 first:border-0 first:pt-0">
                    <span className="font-bold block">• {alert.reason || alert.alert_message}</span>
                    {alert.recommendation && (
                      <div className="text-[10px] text-slate-500 mt-1.5 pl-3 bg-white p-2 rounded-xl border border-rose-100">
                        <strong>Advice:</strong> {alert.recommendation}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="p-6 rounded-3xl bg-emerald-50 border border-emerald-100 space-y-2 shadow-sm">
              <h4 className="text-[10px] font-bold text-emerald-500 uppercase tracking-widest block font-outfit">Active Risk State</h4>
              <div className="flex items-center gap-2 mt-1">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-55" />
                <span className="text-md font-bold text-emerald-600">STABLE & SAFE</span>
              </div>
              <p className="text-xs font-semibold text-slate-450 mt-2">No pending risk alerts flagged.</p>
            </div>
          )}

          {/* Medical History */}
          <div className="p-6 rounded-3xl bg-white border border-slate-100 space-y-4 shadow-sm">
            <h4 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
              <BriefcaseMedical className="w-4 h-4 text-emerald-55" /> Chronic Medical History
            </h4>
            {Object.keys(patientData.medical_history).length === 0 ? (
              <p className="text-xs text-slate-400 italic">No chronic history logged.</p>
            ) : (
              <ul className="space-y-2">
                {Object.entries(patientData.medical_history).map(([key, val]: [string, any]) => (
                  <li key={key} className="text-xs text-slate-600 font-semibold flex items-start gap-2">
                    <span className="text-emerald-500 mt-0.5">•</span>
                    <span className="capitalize">
                      <strong>{key.replace('_', ' ')}:</strong> {String(val)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Coordination Details */}
          <div className="p-6 rounded-3xl bg-white border border-slate-100 space-y-3 shadow-sm">
            <h4 className="text-sm font-bold text-slate-800 flex items-center gap-1.5">
              <Heart className="w-4 h-4 text-emerald-55" /> Care Coordination
            </h4>
            <div className="space-y-2 mt-2">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-bold w-20">Doctor:</span>
                <span className="text-xs text-emerald-600 font-bold">{patientData.assigned_doctor?.name || 'Unassigned'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-bold w-20">HCW:</span>
                <span className="text-xs text-emerald-600 font-bold">{patientData.assigned_hcw?.name || 'Unassigned'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400 font-bold w-20">Registered:</span>
                <span className="text-xs text-slate-650 font-semibold">{new Date(patientData.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
