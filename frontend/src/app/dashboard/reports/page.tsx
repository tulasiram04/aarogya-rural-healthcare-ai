'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/api';
import { useDataFilter } from '@/lib/dataFilter';
import { Activity, RefreshCw, ZoomIn, ExternalLink, Sparkles } from 'lucide-react';

interface LabReport {
  id: string;
  patient_id: string;
  patient_name: string;
  uploaded_at: string | null;
  file_url: string;
  report_type: string | null;
  raw_ocr_text: string | null;
  extracted_metrics: Record<string, any>;
  ai_explanation: string | null;
}

export default function ReportsPage() {
  const { dataFilter } = useDataFilter();
  const [reports, setReports] = useState<LabReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getReports(dataFilter);
      setReports(data);
    } catch (err) {
      console.error(err);
      if (err instanceof ApiError) {
        setError(`Failed to fetch reports (Status ${err.status}).`);
      } else {
        setError('Connection error to AAROGYA servers.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [dataFilter]);

  const getFullImageUrl = (path: string) => {
    if (path.startsWith('http')) return path;
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    return baseUrl.replace('/api/v1', '') + path;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <span className="text-4xl animate-spin text-emerald-500">🔄</span>
        <h3 className="font-semibold text-lg text-slate-655">Loading lab reports...</h3>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 max-w-md mx-auto text-center">
        <span className="text-5xl">📡</span>
        <h3 className="font-bold text-xl text-rose-500">Connection Error</h3>
        <p className="text-sm text-slate-500">{error}</p>
        <button onClick={fetchReports} className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-md transition">
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
            🧬 Lab Reports & Diagnostics
          </h2>
          <p className="text-slate-500 text-sm mt-1">{reports.length} reports logged across patients</p>
        </div>
        <button 
          onClick={fetchReports} 
          className="px-4 py-2 text-sm font-semibold bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 shadow-sm transition flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Reports List */}
      {reports.length === 0 ? (
        <div className="p-16 text-center rounded-3xl bg-white border border-slate-150 shadow-sm">
          <span className="text-5xl block mb-4">🩸</span>
          <h3 className="text-lg font-bold text-slate-700">No Lab Reports</h3>
          <p className="text-sm text-slate-500 mt-2 font-semibold">No blood diagnostic tests have been processed yet. Upload lab report images through the Telegram bot.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {reports.map((rep) => (
            <div key={rep.id} className="p-6 rounded-3xl bg-white border border-slate-100 flex flex-col lg:flex-row gap-6 hover:shadow-md transition duration-200 shadow-sm">
              
              {/* Lab report thumbnail */}
              <div className="w-full lg:w-32 h-44 rounded-2xl overflow-hidden border border-slate-200 flex-shrink-0 bg-slate-50 flex items-center justify-center relative group">
                {rep.file_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img 
                    src={getFullImageUrl(rep.file_url)} 
                    alt="Lab Report Scan" 
                    className="w-full h-full object-cover transition duration-300 group-hover:scale-105" 
                  />
                ) : (
                  <span className="text-xs text-slate-400">No Image</span>
                )}
                <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                  <a 
                    href={getFullImageUrl(rep.file_url)} 
                    target="_blank" 
                    rel="noreferrer"
                    className="p-2 bg-white rounded-full text-slate-800 hover:text-emerald-600 transition shadow-md"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </a>
                </div>
              </div>

              {/* Lab report details */}
              <div className="flex-1 space-y-4 min-w-0">
                <div className="flex justify-between items-start border-b border-slate-100 pb-3">
                  <div>
                    <h3 className="text-lg font-bold text-slate-800">{rep.patient_name}</h3>
                    <span className="text-xs text-emerald-600 font-bold block mt-0.5">{rep.report_type || 'Lab Report'}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400 font-semibold block">Uploaded {rep.uploaded_at ? new Date(rep.uploaded_at).toLocaleDateString() : 'N/A'}</span>
                    <Link href={`/dashboard/patients/${rep.patient_id}`} className="text-xs font-semibold text-emerald-650 hover:underline mt-1.5 inline-flex items-center gap-1">
                      View Profile <ExternalLink className="w-3.5 h-3.5" />
                    </Link>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {Object.entries(rep.extracted_metrics).map(([key, details]: [string, any]) => {
                    const isHigh = details?.status === 'high';
                    const isLow = details?.status === 'low';
                    return (
                      <div key={key} className="p-3 rounded-2xl bg-slate-50 border border-slate-150">
                        <span className="text-[10px] text-slate-450 font-bold uppercase tracking-wider block">{key}</span>
                        <span className={`text-lg font-extrabold block mt-1 ${isHigh ? 'text-rose-600 animate-pulse' : isLow ? 'text-amber-600' : 'text-slate-800'}`}>
                          {details?.value} <span className="text-xs font-semibold text-slate-400">{details?.unit}</span>
                        </span>
                        {details?.reference_range && (
                          <span className="text-[9px] text-slate-400 font-bold font-mono block mt-0.5">Ref: {details.reference_range}</span>
                        )}
                      </div>
                    );
                  })}
                </div>

                {rep.ai_explanation && (
                  <div className="space-y-1.5">
                    <span className="text-[10px] text-emerald-700 font-bold uppercase tracking-wider block flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5 animate-pulse" /> AI Doctor Insight
                    </span>
                    <p className="text-xs font-semibold text-slate-600 leading-relaxed bg-emerald-50/50 p-4 rounded-2xl border border-emerald-100/50">
                      {rep.ai_explanation}
                    </p>
                  </div>
                )}
              </div>

            </div>
          ))}
        </div>
      )}
    </div>
  );
}
