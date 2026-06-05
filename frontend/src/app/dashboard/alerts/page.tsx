'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/api';
import { useDataFilter } from '@/lib/dataFilter';
import { AlertCircle, RefreshCw, CheckCircle, ExternalLink, ShieldAlert } from 'lucide-react';

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
  severity?: string;
  reason?: string;
  status?: string;
}

export default function AlertsPage() {
  const { dataFilter } = useDataFilter();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const fetchAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getActiveAlerts(dataFilter);
      setAlerts(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`Failed to fetch alerts (Status ${err.status}).`);
      } else {
        setError('Connection error to AAROGYA servers.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [dataFilter]);

  const handleAcknowledge = async (id: string) => {
    setActionLoading(id);
    try {
      await api.acknowledgeAlert(id);
      setAlerts(prev => prev.filter(a => a.id !== id));
    } catch {
      alert('Failed to acknowledge alert.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleResolve = async (id: string) => {
    setActionLoading(id);
    try {
      await api.resolveAlert(id);
      setAlerts(prev => prev.filter(a => a.id !== id));
    } catch {
      alert('Failed to resolve alert.');
    } finally {
      setActionLoading(null);
    }
  };

  const criticalCount = alerts.filter(a => a.risk_level === 'critical').length;
  const highCount = alerts.filter(a => a.risk_level === 'high').length;

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <span className="text-4xl animate-spin text-emerald-500">🔄</span>
        <h3 className="font-semibold text-lg text-slate-655">Loading risk alert queue...</h3>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 max-w-md mx-auto text-center">
        <span className="text-5xl">📡</span>
        <h3 className="font-bold text-xl text-rose-500">Connection Error</h3>
        <p className="text-sm text-slate-500">{error}</p>
        <button onClick={fetchAlerts} className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-md transition">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold font-outfit text-slate-800 flex items-center gap-2">
            🚨 Clinical Risk Alerts Queue
          </h2>
          <p className="text-slate-500 text-sm mt-1 font-semibold">Active risk alerts requiring medical attention</p>
        </div>
        <button 
          onClick={fetchAlerts} 
          className="px-4 py-2 text-sm font-semibold bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 shadow-sm transition flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Stats Strip */}
      <div className="grid grid-cols-3 gap-6">
        <div className="p-4 rounded-2xl bg-white border border-slate-100 text-center shadow-sm">
          <span className="text-xs text-slate-400 font-bold uppercase block">Total Active</span>
          <span className="text-2xl font-extrabold text-slate-700 mt-1 block">{alerts.length}</span>
        </div>
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-100 text-center shadow-sm">
          <span className="text-xs text-rose-500 font-bold uppercase block">Critical</span>
          <span className="text-2xl font-extrabold text-rose-600 mt-1 block">{criticalCount}</span>
        </div>
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-100 text-center shadow-sm">
          <span className="text-xs text-amber-500 font-bold uppercase block">High Risk</span>
          <span className="text-2xl font-extrabold text-amber-600 mt-1 block">{highCount}</span>
        </div>
      </div>

      {/* Alert List */}
      {alerts.length === 0 ? (
        <div className="p-16 text-center rounded-3xl bg-white border border-slate-150 shadow-sm">
          <span className="text-5xl block mb-4">✅</span>
          <h3 className="text-lg font-bold text-slate-700">All Clear</h3>
          <p className="text-sm text-slate-500 mt-2 font-semibold font-semibold">No active clinical risk alerts. All patient profiles are stable.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div 
              key={alert.id}
              className={`p-6 rounded-3xl border transition-all duration-200 shadow-sm ${
                alert.risk_level === 'critical'
                  ? 'bg-rose-50 border-rose-100 hover:border-rose-200'
                  : 'bg-amber-50 border-amber-100 hover:border-amber-200'
              }`}
            >
              <div className="flex flex-col md:flex-row justify-between items-start gap-4">
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className={`px-2.5 py-0.5 text-[10px] font-bold uppercase rounded-full border ${
                      alert.risk_level === 'critical'
                        ? 'bg-rose-500/10 text-rose-700 border-rose-200 animate-pulse'
                        : 'bg-amber-500/10 text-amber-700 border-amber-200'
                    }`}>
                      {alert.risk_level === 'critical' ? '🔴' : '🟡'} {alert.severity || alert.risk_level || 'High'}
                    </span>
                    <h4 className="font-extrabold text-slate-800 text-base">{alert.patient_name}</h4>
                    <span className="text-xs text-slate-400 font-semibold">📍 {alert.village} • {alert.sub_center || 'N/A'}</span>
                  </div>
                  
                  <p className="text-sm text-slate-650 font-semibold leading-relaxed">
                    <strong>Reason:</strong> {alert.reason || alert.alert_message}
                  </p>
                  
                  <div className="flex items-center gap-4 text-[10px] text-slate-400 font-bold flex-wrap">
                    <span>Source: {alert.source.replace(/_/g, ' ').toUpperCase()}</span>
                    <span>•</span>
                    <span>Status: <span className="text-rose-600 font-bold uppercase tracking-wider">{alert.status || 'Raised'}</span></span>
                    <span>•</span>
                    <span>Date: {new Date(alert.created_at).toLocaleString()}</span>
                  </div>
                </div>
                
                <div className="flex gap-2 flex-shrink-0 self-end md:self-auto">
                  <Link
                    href={`/dashboard/patients/${alert.patient_id}`}
                    className="inline-flex items-center gap-1 px-3 py-2 text-xs font-bold bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-xl transition shadow-sm"
                  >
                    Profile <ExternalLink className="w-3 h-3" />
                  </Link>
                  <button 
                    onClick={() => handleAcknowledge(alert.id)}
                    disabled={actionLoading === alert.id}
                    className="px-3 py-2 text-xs font-bold bg-amber-50 hover:bg-amber-100 border border-amber-100 text-amber-700 rounded-xl transition disabled:opacity-50 shadow-sm"
                  >
                    Acknowledge
                  </button>
                  <button 
                    onClick={() => handleResolve(alert.id)}
                    disabled={actionLoading === alert.id}
                    className="px-3 py-2 text-xs font-bold bg-emerald-50 hover:bg-emerald-100 border border-emerald-100 text-emerald-600 rounded-xl transition disabled:opacity-50 shadow-sm"
                  >
                    Resolve
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
