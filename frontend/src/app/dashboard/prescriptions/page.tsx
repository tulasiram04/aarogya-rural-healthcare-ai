'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/api';
import { useDataFilter } from '@/lib/dataFilter';
import { FileText, Search, RefreshCw, ZoomIn, Download, ExternalLink } from 'lucide-react';

interface Prescription {
  id: string;
  patient_id: string;
  patient_name: string;
  uploaded_at: string | null;
  raw_image_url: string;
  raw_ocr_text: string | null;
  structured_data: Array<{
    name: string;
    dosage: string;
    frequency: string;
    duration?: string;
  }>;
  issue_date: string | null;
  telegram_id: number | null;
  diagnosis: string | null;
}

export default function PrescriptionsPage() {
  const { dataFilter } = useDataFilter();
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const fetchPrescriptions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPrescriptions(dataFilter);
      setPrescriptions(data);
    } catch (err) {
      console.error(err);
      if (err instanceof ApiError) {
        setError(`Failed to fetch prescriptions (Status ${err.status}).`);
      } else {
        setError('Network connection error to AAROGYA servers.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrescriptions();
  }, [dataFilter]);

  const filteredPrescriptions = prescriptions.filter(rx => 
    rx.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (rx.diagnosis && rx.diagnosis.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getFullImageUrl = (path: string) => {
    if (path.startsWith('http')) return path;
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';
    return baseUrl.replace('/api/v1', '') + path;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <span className="text-4xl animate-spin text-emerald-500">🔄</span>
        <h3 className="font-semibold text-lg text-slate-650">Loading uploaded prescriptions catalog...</h3>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 max-w-md mx-auto text-center">
        <span className="text-5xl">📡</span>
        <h3 className="font-bold text-xl text-rose-500">Connection Error</h3>
        <p className="text-sm text-slate-500">{error}</p>
        <button onClick={fetchPrescriptions} className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-md transition">
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
            📋 Prescriptions Records
          </h2>
          <p className="text-slate-500 text-sm mt-1">{prescriptions.length} total prescriptions extracted by AI</p>
        </div>
        <button 
          onClick={fetchPrescriptions} 
          className="px-4 py-2 text-sm font-semibold bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 shadow-sm transition flex items-center gap-2"
        >
          <RefreshCw className="w-4 h-4" /> Refresh
        </button>
      </div>

      {/* Search filter */}
      <div className="max-w-md relative">
        <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
          <Search className="w-4 h-4" />
        </span>
        <input
          type="text"
          placeholder="Search by patient name or diagnosis..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-800 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 transition shadow-sm"
        />
      </div>

      {/* Content grid */}
      {filteredPrescriptions.length === 0 ? (
        <div className="p-16 text-center rounded-3xl bg-white border border-slate-150 shadow-sm">
          <span className="text-5xl block mb-4">📋</span>
          <h3 className="text-lg font-bold text-slate-700">No Prescriptions Found</h3>
          <p className="text-sm text-slate-500 mt-2 font-semibold">No handwritten or printed prescription images matched your search or have been uploaded yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredPrescriptions.map((rx) => (
            <div key={rx.id} className="p-6 rounded-3xl bg-white border border-slate-100 flex flex-col md:flex-row gap-6 hover:shadow-md transition duration-200 shadow-sm">
              
              {/* Prescription image preview */}
              <div className="w-full md:w-32 h-44 rounded-2xl overflow-hidden border border-slate-200 flex-shrink-0 bg-slate-50 flex items-center justify-center relative group">
                {rx.raw_image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img 
                    src={getFullImageUrl(rx.raw_image_url)} 
                    alt="Prescription Scan" 
                    className="w-full h-full object-cover transition duration-300 group-hover:scale-105" 
                  />
                ) : (
                  <span className="text-xs text-slate-400">No Image</span>
                )}
                <div className="absolute inset-0 bg-slate-900/60 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                  <a 
                    href={getFullImageUrl(rx.raw_image_url)} 
                    target="_blank" 
                    rel="noreferrer"
                    className="p-2 bg-white rounded-full text-slate-850 hover:text-emerald-600 transition shadow-md"
                  >
                    <ZoomIn className="w-4 h-4" />
                  </a>
                </div>
              </div>

              {/* Prescription metadata details */}
              <div className="flex-1 flex flex-col justify-between min-w-0">
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between items-start">
                      <Link href={`/dashboard/patients/${rx.patient_id}`} className="font-bold text-slate-800 hover:text-emerald-600 hover:underline truncate text-base block">
                        {rx.patient_name}
                      </Link>
                      <span className="text-[10px] text-slate-400 font-bold font-mono whitespace-nowrap">
                        {rx.uploaded_at ? new Date(rx.uploaded_at).toLocaleDateString() : 'N/A'}
                      </span>
                    </div>
                    <span className="text-xs text-emerald-600 font-bold block mt-0.5">Diagnosis: {rx.diagnosis || 'Unspecified'}</span>
                  </div>

                  <div className="space-y-1.5">
                    <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Extracted Medicines</span>
                    {rx.structured_data && rx.structured_data.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5 max-h-[80px] overflow-y-auto pr-1">
                        {rx.structured_data.map((med, idx) => (
                          <span key={idx} className="px-2 py-0.5 text-[10px] bg-slate-50 border border-slate-150 text-slate-600 font-semibold rounded-md">
                            {med.name}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-xs text-slate-400 italic block">No medicines parsed.</span>
                    )}
                  </div>
                </div>

                <div className="pt-4 flex gap-2">
                  <Link 
                    href={`/dashboard/patients/${rx.patient_id}`}
                    className="inline-flex items-center gap-1 px-3 py-2 text-xs font-bold bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-xl transition shadow-sm"
                  >
                    Patient Profile <ExternalLink className="w-3 h-3" />
                  </Link>
                  <a 
                    href={getFullImageUrl(rx.raw_image_url)} 
                    download={`Prescription-${rx.id}.jpg`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 px-3 py-2 text-xs font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-600 border border-emerald-100 rounded-xl transition shadow-sm"
                  >
                    <Download className="w-3 h-3" /> Download
                  </a>
                </div>
              </div>

            </div>
          ))}
        </div>
      )}
    </div>
  );
}
