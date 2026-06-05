'use client';

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Users, 
  FileText, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  TrendingUp, 
  Mic, 
  Square, 
  Sparkles, 
  RefreshCw, 
  Database,
  ArrowRight,
  ClipboardCheck,
  Calendar,
  AlertCircle
} from 'lucide-react';
import { api, ApiError } from '@/lib/api';
import { useDataFilter } from '@/lib/dataFilter';
import { useToast } from '@/components/Toast';

interface DashboardSummary {
  total_patients: number;
  active_patients: number;
  prescriptions_uploaded: number;
  lab_reports_uploaded: number;
  risk_alerts: number;
  overall_compliance: number;
  village_health_score: number;
  new_prescriptions: number;
  new_reports: number;
  village_analytics: Array<{
    village: string;
    patient_count: number;
    compliance_rate: number;
  }>;
  village_insights: {
    top_diseases: Array<{ name: string; count: number }>;
    top_risk_villages: Array<{ village: string; alert_count: number }>;
    most_active_patients: Array<{ name: string; check_ins: number }>;
    most_missed_medicines: Array<{ medicine: string; missed_count: number }>;
    patients_requiring_attention: Array<{
      id: string; name: string; village: string | null;
      risk_score: number; risk_level: string;
    }>;
    village_summary?: string | null;
  };
}

interface Patient {
  id: string;
  telegram_id: number | null;
  phone: string | null;
  full_name: string;
  age: number | null;
  gender: string | null;
  village: string | null;
  sub_center: string | null;
  preferred_language: string;
  is_active: boolean;
  created_at: string;
}

interface Alert {
  id: string;
  patient_id: string;
  patient_name: string;
  village: string;
  sub_center: string;
  risk_level: string;
  source: string;
  alert_message: string;
  created_at: string;
}

interface ActivityLogItem {
  id: string;
  patient_id: string;
  patient_name: string;
  activity_type: string;
  message: string;
  created_at: string;
}

interface UserProfile {
  full_name: string;
  role: string;
}

export default function DashboardOverview() {
  const { dataFilter } = useDataFilter();
  const { showToast } = useToast();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [activities, setActivities] = useState<ActivityLogItem[]>([]);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // One-Click Demo Mode State
  const [isSeeding, setIsSeeding] = useState(false);
  const [isCleaning, setIsCleaning] = useState(false);

  // Voice Assistant States
  const [voiceLanguage, setVoiceLanguage] = useState('english');
  const [recording, setRecording] = useState(false);
  const [loadingVoice, setLoadingVoice] = useState(false);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const [voiceAiResponse, setVoiceAiResponse] = useState('');
  const [voiceAudioUrl, setVoiceAudioUrl] = useState('');
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const fetchDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, patientsRes, alertsRes, userRes, activitiesRes] = await Promise.all([
        api.getDashboardSummary(dataFilter),
        api.getPatients(dataFilter),
        api.getActiveAlerts(dataFilter),
        api.getMe(),
        api.getActivityFeed(dataFilter),
      ]);

      setSummary(summaryRes);
      setPatients(patientsRes);
      setAlerts(alertsRes);
      setUser({ full_name: userRes.full_name, role: userRes.role });
      setActivities(activitiesRes);
    } catch (err) {
      console.error(err);
      if (err instanceof ApiError) {
        setError(`API connection failed (Status ${err.status}). Please check if your FastAPI container is running.`);
      } else {
        setError('Failed to establish connection to the AAROGYA clinical servers.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [dataFilter]);

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      await api.acknowledgeAlert(alertId);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      const updatedSummary = await api.getDashboardSummary(dataFilter);
      setSummary(updatedSummary);
    } catch (err) {
      showToast('Failed to acknowledge alert. Please try again.', 'error');
    }
  };

  // Seeder call
  const handleLoadDemo = async () => {
    setIsSeeding(true);
    try {
      const res = await api.seedDemo();
      showToast(res.message || 'Demo dataset loaded successfully!');
      await fetchDashboardData();
    } catch (err) {
      console.error(err);
      showToast('Failed to load demo data. Ensure backend is running.', 'error');
    } finally {
      setIsSeeding(false);
    }
  };

  const handleCleanDemo = async () => {
    if (!confirm('Delete all demo records? Real patient data will be preserved.')) return;
    setIsCleaning(true);
    try {
      const res = await api.cleanDemo();
      showToast(res.message || 'Demo data cleaned.');
      await fetchDashboardData();
    } catch (err) {
      showToast('Failed to clean demo data.', 'error');
    } finally {
      setIsCleaning(false);
    }
  };

  // Voice recording handlers
  const startRecording = async () => {
    audioChunksRef.current = [];
    setVoiceTranscript('');
    setVoiceAiResponse('');
    setVoiceAudioUrl('');
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };
      recorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/ogg' });
        await sendVoiceAssistantRequest(audioBlob);
      };
      mediaRecorderRef.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (err) {
      showToast('Could not access microphone. Ensure permissions are granted.', 'error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && recording) {
      mediaRecorderRef.current.stop();
      // Stop all tracks on the stream
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
      setRecording(false);
    }
  };

  const sendVoiceAssistantRequest = async (blob: Blob) => {
    setLoadingVoice(true);
    try {
      const formData = new FormData();
      formData.append('file', blob, 'assistant_recording.ogg');
      formData.append('language', voiceLanguage);
      
      const res = await api.processVoiceAssistant(formData);
      setVoiceTranscript(res.transcript);
      setVoiceAiResponse(res.response_text);
      if (res.audio_base64) {
        const audioUrl = `data:audio/mp3;base64,${res.audio_base64}`;
        setVoiceAudioUrl(audioUrl);
        const audio = new Audio(audioUrl);
        audio.play();
      }
    } catch (err) {
      console.error(err);
      showToast('AI voice processing failed. Please try speaking again.', 'error');
    } finally {
      setLoadingVoice(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="flex justify-between items-center">
          <div className="h-10 bg-slate-200 rounded-xl w-64" />
          <div className="h-10 bg-slate-200 rounded-xl w-32" />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-32 bg-white border border-slate-200 rounded-3xl p-5" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 h-96 bg-white border border-slate-200 rounded-3xl" />
          <div className="h-96 bg-white border border-slate-200 rounded-3xl" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 max-w-md mx-auto text-center">
        <span className="text-5xl">📡</span>
        <h3 className="font-bold text-xl text-rose-500">Connection Error</h3>
        <p className="text-sm text-slate-500">{error}</p>
        <button 
          onClick={fetchDashboardData}
          className="px-6 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-md transition-all"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const firstName = user?.full_name?.split(' ')[0] || 'Doctor';
  const greeting = user?.role === 'doctor' ? `Welcome Back, Dr. ${firstName}` : `Welcome Back, ${user?.full_name || 'Worker'}`;

  return (
    <div className="space-y-8">
      {/* Welcome Header & Seeder Actions */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold font-outfit text-slate-800 flex items-center gap-2">
            {greeting}
          </h2>
          <p className="text-slate-500 text-sm mt-1">Real-time patient diagnostics and compliance metrics.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          {user?.role === 'admin' && (
            <>
              <button
                onClick={handleLoadDemo}
                disabled={isSeeding}
                className="px-4 py-2.5 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-sm transition flex items-center gap-2 disabled:opacity-50"
              >
                <Database className="w-4 h-4" />
                {isSeeding ? 'Loading Demo...' : '🚀 Load Hackathon Demo'}
              </button>
              <button
                onClick={handleCleanDemo}
                disabled={isCleaning}
                className="px-4 py-2.5 text-sm font-semibold bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 rounded-xl transition flex items-center gap-2 disabled:opacity-50"
              >
                {isCleaning ? 'Cleaning...' : '🗑 Clean Demo Data'}
              </button>
            </>
          )}
          <button 
            onClick={fetchDashboardData}
            className="px-4 py-2.5 text-sm font-semibold bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 shadow-sm transition flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>

      {/* Analytics Summary Panels */}
      <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-6">
        {/* Card 1: Total Patients */}
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Patients</span>
            <span className="p-2 rounded-xl bg-emerald-50 text-emerald-600"><Users className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-slate-800">{summary?.total_patients ?? 0}</h3>
          <p className="text-[10px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
            <span>●</span> Live records
          </p>
        </div>

        {/* Card 2: Active Patients */}
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Active Monitoring</span>
            <span className="p-2 rounded-xl bg-emerald-50 text-emerald-600"><CheckCircle className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-emerald-600">{summary?.active_patients ?? 0}</h3>
          <p className="text-[10px] text-slate-400 mt-1">Directly tracking</p>
        </div>

        {/* Card 3: Prescriptions */}
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Prescriptions</span>
            <span className="p-2 rounded-xl bg-blue-50 text-blue-600"><FileText className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-blue-600">{summary?.prescriptions_uploaded ?? 0}</h3>
          <p className="text-[10px] text-slate-400 mt-1">AI OCR extracted</p>
        </div>

        {/* Card 4: Lab Reports */}
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Lab Reports</span>
            <span className="p-2 rounded-xl bg-blue-50 text-blue-600"><Activity className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-blue-600">{summary?.lab_reports_uploaded ?? 0}</h3>
          <p className="text-[10px] text-slate-400 mt-1">Biomarker parsed</p>
        </div>

        {/* Card 5: Risk Alerts */}
        <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-rose-500 uppercase tracking-wider">Risk Alerts</span>
            <span className="p-2 rounded-xl bg-rose-50 text-rose-600"><AlertTriangle className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-rose-600">{summary?.risk_alerts ?? 0}</h3>
          <p className="text-[10px] text-rose-500/80 font-medium mt-1">Active alerts</p>
        </div>

        {/* Card 6: Compliance */}
        <motion.div whileHover={{ scale: 1.02 }} className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">💊 Compliance</span>
            <span className="p-2 rounded-xl bg-amber-50 text-amber-600"><ClipboardCheck className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-amber-600">
            {summary && summary.total_patients > 0 ? `${summary.overall_compliance}%` : '—'}
          </h3>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden">
            <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${summary?.overall_compliance ?? 0}%` }} />
          </div>
        </motion.div>
      </section>

      {/* Village Health Score */}
      {summary && summary.total_patients > 0 && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className="p-5 rounded-3xl bg-gradient-to-r from-emerald-50 to-blue-50 border border-emerald-100 flex items-center justify-between">
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">📈 Village Health Score</span>
            <h3 className="text-4xl font-bold text-emerald-600 mt-1">{summary.village_health_score}%</h3>
            <p className="text-xs text-slate-500 mt-1">Aggregated compliance across all villages</p>
          </div>
          <TrendingUp className="w-12 h-12 text-emerald-300" />
        </motion.div>
      )}

      {/* Dynamic Voice Assistant Widget & Executive AI Clinical Card */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Voice Assistant Widget */}
        <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm space-y-6">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h3 className="font-bold font-outfit text-slate-800 flex items-center gap-2">
              <span className="p-2 bg-emerald-50 text-emerald-600 rounded-xl"><Mic className="w-4 h-4" /></span>
              Rural Voice Assistant
            </h3>
            
            <select 
              value={voiceLanguage}
              onChange={(e) => setVoiceLanguage(e.target.value)}
              className="text-xs font-semibold bg-slate-50 border border-slate-200 text-slate-700 py-1.5 px-3 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-500"
            >
              <option value="english">English</option>
              <option value="tamil">Tamil (தமிழ்)</option>
              <option value="hindi">Hindi (हिंदी)</option>
              <option value="telugu">Telugu (తెలుగు)</option>
              <option value="kannada">Kannada (ಕನ್ನಡ)</option>
              <option value="malayalam">Malayalam (മലയാളம்)</option>
            </select>
          </div>

          <div className="flex flex-col items-center justify-center py-6 border border-dashed border-slate-200 rounded-2xl bg-slate-50/50 space-y-4">
            {!recording ? (
              <button 
                onClick={startRecording}
                className="h-16 w-16 rounded-full bg-emerald-500 hover:bg-emerald-600 text-white flex items-center justify-center shadow-lg shadow-emerald-500/10 hover:scale-105 active:scale-95 transition-all"
              >
                <Mic className="w-6 h-6" />
              </button>
            ) : (
              <button 
                onClick={stopRecording}
                className="h-16 w-16 rounded-full bg-rose-500 hover:bg-rose-600 text-white flex items-center justify-center shadow-lg shadow-rose-500/10 animate-pulse hover:scale-105 active:scale-95 transition-all"
              >
                <Square className="w-6 h-6" />
              </button>
            )}
            
            <div className="text-center">
              <p className="text-sm font-semibold text-slate-700">
                {recording ? 'Listening closely...' : 'Tap Mic to Start Speech'}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Say your symptoms in your local language
              </p>
            </div>
          </div>

          {/* Assistant Outputs */}
          <div className="space-y-4">
            {loadingVoice && (
              <div className="flex items-center gap-2 text-xs text-slate-500 italic">
                <span className="animate-spin text-emerald-500">🔄</span> Processing speech transcripts & synthesis...
              </div>
            )}

            {voiceTranscript && (
              <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 text-xs">
                <span className="font-bold text-slate-500 block mb-1">ENGLISH TRANSLATION:</span>
                <p className="text-slate-700 font-medium italic">"{voiceTranscript}"</p>
              </div>
            )}

            {voiceAiResponse && (
              <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-100 text-xs">
                <span className="font-bold text-emerald-700 block mb-1 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5" /> AI HEALTH ADVICE ({voiceLanguage.toUpperCase()}):
                </span>
                <p className="text-slate-700 font-semibold">{voiceAiResponse}</p>
              </div>
            )}

            {voiceAudioUrl && (
              <div className="pt-2">
                <audio src={voiceAudioUrl} controls className="w-full h-8" />
              </div>
            )}
          </div>
        </div>

        {/* AI Clinical Command Center (Executive Insights) */}
        <div className="lg:col-span-2 p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-4">
              <h3 className="font-bold font-outfit text-slate-800 flex items-center gap-2">
                <span className="p-2 bg-blue-50 text-blue-600 rounded-xl"><Sparkles className="w-4 h-4" /></span>
                AI Clinical Executive Insights
              </h3>
              <span className="text-xs font-semibold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                Active Analysis
              </span>
            </div>

            <div className="mt-4 p-5 rounded-2xl bg-gradient-to-br from-emerald-50 to-blue-50/50 border border-emerald-100/50 text-slate-700 text-sm leading-relaxed font-medium">
              {summary?.village_insights?.village_summary || (
                summary && summary.total_patients === 0
                  ? 'No patients registered yet. Load the hackathon demo or register patients via Telegram.'
                  : 'AI insights will appear once patient data is available.'
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mt-6">
            <div className="p-3 border border-slate-100 rounded-xl bg-slate-50/50">
              <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">Top Disease Risk</span>
              <p className="text-xs font-semibold text-slate-700 mt-1">
                {summary?.village_insights?.top_diseases?.[0]
                  ? `${summary.village_insights.top_diseases[0].name} (${summary.village_insights.top_diseases[0].count})`
                  : 'No diseases logged'}
              </p>
            </div>
            <div className="p-3 border border-slate-100 rounded-xl bg-slate-50/50">
              <span className="text-[10px] text-slate-400 font-bold uppercase block tracking-wider">Village attention alert</span>
              <p className="text-xs font-semibold text-slate-700 mt-1">
                {summary?.village_insights?.top_risk_villages?.[0]
                  ? `${summary.village_insights.top_risk_villages[0].village} (${summary.village_insights.top_risk_villages[0].alert_count} alerts)`
                  : 'No active risks'}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Alerts and Command center details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Active Alerts Queue */}
        <section className="lg:col-span-2 space-y-4">
          <h3 className="text-lg font-bold font-outfit text-slate-800 flex items-center gap-2">
            🚨 Active Clinical Alerts Queue
          </h3>
          
          {alerts.length === 0 ? (
            <div className="p-12 text-center rounded-3xl bg-emerald-50/20 border border-emerald-100 text-slate-500 font-medium">
              ✅ No risk alerts detected. All patients within safe parameters.
            </div>
          ) : (
            <div className="space-y-4">
              {alerts.slice(0, 5).map((alert) => (
                <div 
                  key={alert.id} 
                  className="p-5 rounded-3xl bg-white border border-slate-100 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 transition duration-200 hover:border-slate-200 shadow-sm"
                >
                  <div className="space-y-1.5 max-w-xl">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 text-[10px] font-bold uppercase rounded-full border ${
                        alert.risk_level === 'critical' 
                          ? 'bg-rose-50 text-rose-600 border-rose-100' 
                          : alert.risk_level === 'high'
                          ? 'bg-amber-50 text-amber-600 border-amber-100'
                          : 'bg-blue-50 text-blue-600 border-blue-100'
                      }`}>
                        {alert.risk_level}
                      </span>
                      <h4 className="font-bold text-slate-800">{alert.patient_name}</h4>
                      <span className="text-xs text-slate-400 font-medium">• {alert.village}</span>
                    </div>
                    <p className="text-sm text-slate-600 font-medium">{alert.alert_message}</p>
                    <span className="text-[10px] text-slate-400 font-bold block">
                      Source: {alert.source.toUpperCase()} • {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </div>
                  
                  <button 
                    onClick={() => handleAcknowledgeAlert(alert.id)}
                    className="px-4 py-2 text-xs font-semibold bg-emerald-50 hover:bg-emerald-100 text-emerald-600 border border-emerald-100 rounded-xl transition self-end md:self-auto shadow-sm"
                  >
                    Resolve Alert
                  </button>
                </div>
              ))}
              {alerts.length > 5 && (
                <Link href="/dashboard/alerts" className="block text-center text-sm font-semibold text-emerald-600 hover:underline py-2">
                  View all {alerts.length} active alerts →
                </Link>
              )}
            </div>
          )}

          {/* Recent Activity Log Timeline */}
          <div className="space-y-4 pt-6">
            <h3 className="text-lg font-bold font-outfit text-slate-800 flex items-center gap-2">
              📋 Timeline Activity Feed
            </h3>
            
            {activities.length === 0 ? (
              <div className="p-12 text-center rounded-3xl bg-slate-50 border border-slate-200 text-slate-500 font-medium">
                No activity logged yet. Patient events will appear here in real-time.
              </div>
            ) : (
              <div className="border border-slate-100 rounded-3xl overflow-hidden bg-white max-h-[350px] overflow-y-auto divide-y divide-slate-100 shadow-sm">
                {activities.map((act) => (
                  <div key={act.id} className="p-4 hover:bg-slate-50/50 transition flex justify-between items-center gap-4 text-sm font-medium text-slate-700">
                    <span>{act.message}</span>
                    <span className="text-xs text-slate-400 whitespace-nowrap">
                      {new Date(act.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </section>

        {/* Village and command center aggregated trends */}
        <section className="space-y-6">
          {/* Village Compliance trends */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-outfit text-slate-800">
              📍 Village Compliance Trends
            </h3>
            <div className="p-6 rounded-3xl bg-white border border-slate-100 space-y-4 shadow-sm">
              {!summary?.village_analytics || summary.village_analytics.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-4 italic font-medium">No village compliance data yet.</p>
              ) : (
                summary.village_analytics.map((vil) => (
                  <div key={vil.village} className="space-y-2">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className="text-slate-600">{vil.village} ({vil.patient_count} patients)</span>
                      <span className={vil.compliance_rate >= 80 ? 'text-emerald-600' : 'text-rose-500 font-bold'}>
                        {vil.compliance_rate}% Compliance
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${vil.compliance_rate >= 80 ? 'bg-emerald-500' : 'bg-rose-500'}`}
                        style={{ width: `${vil.compliance_rate}%` }}
                      />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Advanced Command Center Lists */}
          <div className="space-y-4">
            <h3 className="text-lg font-bold font-outfit text-slate-800">
              🏛️ Command Center Insights
            </h3>
            <div className="p-6 rounded-3xl bg-white border border-slate-100 space-y-5 shadow-sm">
              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Top Chronic Conditions</span>
                <div className="flex flex-wrap gap-2">
                  {summary?.village_insights?.top_diseases.map((d, i) => (
                    <span key={i} className="px-2.5 py-1 bg-slate-50 border border-slate-200 text-slate-600 text-xs rounded-lg font-semibold shadow-sm">
                      {d.name} ({d.count})
                    </span>
                  ))}
                  {(!summary?.village_insights?.top_diseases || summary.village_insights.top_diseases.length === 0) && (
                    <span className="text-xs text-slate-400 italic">No conditions registered</span>
                  )}
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Top Risk Villages</span>
                <div className="flex flex-wrap gap-2">
                  {summary?.village_insights?.top_risk_villages.map((v, i) => (
                    <span key={i} className="px-2.5 py-1 bg-rose-50 border border-rose-100 text-rose-600 text-xs rounded-lg font-semibold shadow-sm">
                      {v.village} ({v.alert_count})
                    </span>
                  ))}
                  {(!summary?.village_insights?.top_risk_villages || summary.village_insights.top_risk_villages.length === 0) && (
                    <span className="text-xs text-slate-400 italic">No risks flagged</span>
                  )}
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Most Active Patients</span>
                <div className="flex flex-wrap gap-2">
                  {summary?.village_insights?.most_active_patients.map((p, i) => (
                    <span key={i} className="px-2.5 py-1 bg-emerald-50 border border-emerald-100 text-emerald-600 text-xs rounded-lg font-semibold shadow-sm">
                      {p.name} ({p.check_ins})
                    </span>
                  ))}
                  {(!summary?.village_insights?.most_active_patients || summary.village_insights.most_active_patients.length === 0) && (
                    <span className="text-xs text-slate-400 italic">No check-ins logged</span>
                  )}
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Patients Requiring Attention Today</span>
                <div className="flex flex-wrap gap-2">
                  {summary?.village_insights?.patients_requiring_attention?.map((p) => (
                    <Link key={p.id} href={`/dashboard/patients/${p.id}`}
                      className="px-2.5 py-1 bg-rose-50 border border-rose-100 text-rose-600 text-xs rounded-lg font-semibold shadow-sm hover:bg-rose-100 transition">
                      {p.name} — Score {p.risk_score}
                    </Link>
                  ))}
                  {(!summary?.village_insights?.patients_requiring_attention || summary.village_insights.patients_requiring_attention.length === 0) && (
                    <span className="text-xs text-slate-400 italic">No patients require immediate attention</span>
                  )}
                </div>
              </div>

              <div>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block mb-2">Most Missed Medicines</span>
                <div className="flex flex-wrap gap-2">
                  {summary?.village_insights?.most_missed_medicines.map((m, i) => (
                    <span key={i} className="px-2.5 py-1 bg-amber-50 border border-amber-100 text-amber-600 text-xs rounded-lg font-semibold shadow-sm">
                      {m.medicine} ({m.missed_count})
                    </span>
                  ))}
                  {(!summary?.village_insights?.most_missed_medicines || summary.village_insights.most_missed_medicines.length === 0) && (
                    <span className="text-xs text-slate-400 italic">No missed logs</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      {/* Patient Database Directory */}
      <section className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-bold font-outfit text-slate-800 flex items-center gap-2">
            👥 Patient Roster Directory
          </h3>
          <span className="text-xs font-semibold text-slate-400 bg-slate-50 border border-slate-100 px-3 py-1 rounded-full">
            Database Sync
          </span>
        </div>
        
        {patients.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-white border border-slate-200 text-slate-400 font-medium">
            <AlertCircle className="w-8 h-8 mx-auto text-slate-300 mb-3" />
            No patients registered yet. Patients must join via the Telegram bot (/start).
          </div>
        ) : (
          <div className="border border-slate-100 rounded-3xl overflow-hidden bg-white shadow-sm">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-150 bg-slate-50/50 text-slate-500 text-xs font-bold uppercase tracking-wider">
                  <th className="py-4 px-6">Name</th>
                  <th className="py-4 px-6">Demographics</th>
                  <th className="py-4 px-6">Village</th>
                  <th className="py-4 px-6">Language</th>
                  <th className="py-4 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm font-medium text-slate-700">
                {patients.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/30 transition">
                    <td className="py-4 px-6 font-bold text-slate-800">{p.full_name}</td>
                    <td className="py-4 px-6 text-xs text-slate-400">
                      {p.age ? `${p.age} yrs` : 'N/A'} • {p.gender || 'N/A'}
                    </td>
                    <td className="py-4 px-6">{p.village || 'N/A'}</td>
                    <td className="py-4 px-6 capitalize">{p.preferred_language}</td>
                    <td className="py-4 px-6 text-right">
                      <Link 
                        href={`/dashboard/patients/${p.id}`}
                        className="inline-flex items-center gap-1.5 px-4.5 py-2 text-xs font-bold bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-xl transition shadow-sm"
                      >
                        Clinical Record <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
