'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { api, ApiError } from '@/lib/api';
import { useDataFilter } from '@/lib/dataFilter';

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

export default function PatientsPage() {
  const { dataFilter } = useDataFilter();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchPatients = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getPatients(dataFilter);
      setPatients(data);
    } catch (err) {
      setError(err instanceof ApiError ? `Failed to fetch patients (Status ${err.status}).` : 'Connection error.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPatients(); }, [dataFilter]);

  const filtered = patients.filter(p =>
    p.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.village || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (p.phone || '').includes(searchQuery)
  );

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <span className="text-4xl animate-spin">🔄</span>
        <h3 className="font-semibold text-lg text-slate-500">Loading patient directory...</h3>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-6 text-center">
        <span className="text-5xl">📡</span>
        <h3 className="font-bold text-xl text-rose-500">Connection Error</h3>
        <p className="text-sm text-slate-500">{error}</p>
        <button onClick={fetchPatients} className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl transition">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold font-outfit text-slate-800">👥 Patient Directory</h2>
          <p className="text-slate-500 text-sm mt-1">{patients.length} registered patients</p>
        </div>
        <button onClick={fetchPatients} className="px-4 py-2 text-sm bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 transition">🔄 Refresh</button>
      </div>

      <input
        type="text"
        placeholder="Search by name, village, or phone..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="w-full max-w-md px-4 py-3 rounded-xl bg-white border border-slate-200 text-slate-800 placeholder-slate-400 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 transition shadow-sm"
      />

      {filtered.length === 0 ? (
        <div className="p-12 text-center rounded-3xl border border-slate-200 bg-white text-slate-500 font-medium">
          {searchQuery ? 'No patients match your search.' : 'No patients registered yet. Patients must join via the Telegram bot (/start).'}
        </div>
      ) : (
        <div className="border border-slate-100 rounded-3xl overflow-hidden bg-white shadow-sm">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50/50 text-slate-500 text-xs font-bold uppercase tracking-wider">
                <th className="py-4 px-6">Name</th>
                <th className="py-4 px-6">Demographics</th>
                <th className="py-4 px-6">Village</th>
                <th className="py-4 px-6">Language</th>
                <th className="py-4 px-6">Telegram</th>
                <th className="py-4 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
              {filtered.map((p) => (
                <tr key={p.id} className="hover:bg-slate-50/50 transition">
                  <td className="py-4 px-6 font-bold text-slate-800">{p.full_name}</td>
                  <td className="py-4 px-6 text-xs text-slate-400">{p.age ? `${p.age} yrs` : 'N/A'} • {p.gender || 'N/A'}</td>
                  <td className="py-4 px-6">{p.village || 'N/A'}</td>
                  <td className="py-4 px-6 capitalize">{p.preferred_language}</td>
                  <td className="py-4 px-6">{p.telegram_id ? '✅ Linked' : '—'}</td>
                  <td className="py-4 px-6 text-right">
                    <Link href={`/dashboard/patients/${p.id}`} className="px-4 py-2 text-xs font-bold bg-emerald-50 hover:bg-emerald-100 text-emerald-700 border border-emerald-100 rounded-xl transition">
                      View Profile →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
