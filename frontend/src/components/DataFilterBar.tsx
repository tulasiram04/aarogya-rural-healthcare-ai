'use client';

import React from 'react';

export type DataFilter = 'all' | 'real' | 'demo';

interface DataFilterBarProps {
  value: DataFilter;
  onChange: (filter: DataFilter) => void;
}

const OPTIONS: { value: DataFilter; label: string; icon: string }[] = [
  { value: 'all', label: 'All Data', icon: '📊' },
  { value: 'real', label: 'Real Data', icon: '🏥' },
  { value: 'demo', label: 'Demo Data', icon: '🚀' },
];

export function DataFilterBar({ value, onChange }: DataFilterBarProps) {
  return (
    <div className="flex items-center gap-1 p-1 bg-slate-100 rounded-xl border border-slate-200">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onChange(opt.value)}
          className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
            value === opt.value
              ? 'bg-white text-emerald-700 shadow-sm border border-emerald-100'
              : 'text-slate-500 hover:text-slate-700'
          }`}
        >
          <span>{opt.icon}</span>
          {opt.label}
        </button>
      ))}
    </div>
  );
}
