'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { DataFilterProvider, useDataFilter } from '@/lib/dataFilter';
import { DataFilterBar } from '@/components/DataFilterBar';

interface UserProfile {
  id: string;
  full_name: string;
  role: string;
  phone: string;
}

function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { dataFilter, setDataFilter } = useDataFilter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [alertCount, setAlertCount] = useState(0);
  const [newPrescriptionsCount, setNewPrescriptionsCount] = useState(0);
  const [newReportsCount, setNewReportsCount] = useState(0);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    if (!api.isAuthenticated()) {
      router.replace('/login');
      return;
    }
    const load = async () => {
      try {
        const [me, summary] = await Promise.all([
          api.getMe(),
          api.getDashboardSummary(dataFilter),
        ]);
        setUser({ id: me.id, full_name: me.full_name, role: me.role, phone: me.phone });
        setAlertCount(summary.risk_alerts || 0);
        setNewPrescriptionsCount(summary.new_prescriptions || 0);
        setNewReportsCount(summary.new_reports || 0);
      } catch {
        api.logout();
      } finally {
        setAuthChecked(true);
      }
    };
    load();
    const interval = setInterval(load, 10000);
    return () => clearInterval(interval);
  }, [router, dataFilter]);

  if (!authChecked) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[#F8FAFC]">
        <div className="flex flex-col items-center gap-4">
          <span className="text-4xl animate-spin">🔄</span>
          <p className="text-sm text-slate-500 font-medium">Authenticating clinical session...</p>
        </div>
      </div>
    );
  }

  const userInitials = user?.full_name?.split(' ').map((w) => w[0]).join('').toUpperCase().slice(0, 2) || '??';
  const roleLabel =
    user?.role === 'doctor' ? 'Primary Physician'
    : user?.role === 'hcw' ? 'Healthcare Worker'
    : user?.role === 'admin' ? 'Administrator'
    : 'Medical Staff';

  const navItems = [
    { name: 'Overview', path: '/dashboard', icon: '📊' },
    { name: 'Patients', path: '/dashboard/patients', icon: '👥' },
    { name: 'Prescriptions', path: '/dashboard/prescriptions', icon: '💊', count: newPrescriptionsCount || undefined, badgeColor: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
    { name: 'Lab Reports', path: '/dashboard/reports', icon: '🧪', count: newReportsCount || undefined, badgeColor: 'bg-blue-50 text-blue-600 border-blue-100' },
    { name: 'Risk Alerts', path: '/dashboard/alerts', icon: '⚠️', count: alertCount || undefined, badgeColor: 'bg-rose-50 text-rose-600 border-rose-100' },
    { name: 'HCW Checklist', path: '/dashboard/hcw', icon: '📋' },
    { name: 'MCP Tools', path: '/dashboard/mcp', icon: '🧩' },
  ];

  return (
    <div className="flex min-h-screen bg-[#F8FAFC] text-slate-800">
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between shrink-0 hidden md:flex">
        <div>
          <div className="p-6 border-b border-slate-100 flex items-center gap-3">
            <span className="text-3xl">🌿</span>
            <div>
              <h1 className="font-outfit font-bold text-xl text-emerald-600">AAROGYA</h1>
              <p className="text-[9px] text-slate-400 font-semibold">AI-Powered Rural Healthcare Companion</p>
            </div>
          </div>
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const isActive = pathname === item.path || (item.path !== '/dashboard' && pathname.startsWith(item.path));
              return (
                <Link key={item.name} href={item.path}
                  className={`flex items-center justify-between px-4 py-3 rounded-xl text-sm font-medium transition border ${
                    isActive ? 'bg-emerald-50 text-emerald-600 border-emerald-100 shadow-sm' : 'text-slate-600 hover:bg-slate-50 border-transparent'
                  }`}>
                  <div className="flex items-center gap-3"><span className="text-lg">{item.icon}</span><span>{item.name}</span></div>
                  {item.count ? <span className={`px-2 py-0.5 text-xs font-bold rounded-full border ${item.badgeColor}`}>{item.count}</span> : null}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="p-4 border-t border-slate-200 space-y-3">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm border border-emerald-100">{userInitials}</div>
            <div className="min-w-0"><h4 className="text-sm font-semibold truncate">{user?.full_name}</h4><p className="text-xs text-slate-500">{roleLabel}</p></div>
          </div>
          <button onClick={() => api.logout()} className="w-full py-2.5 text-xs font-semibold text-slate-600 hover:text-rose-600 bg-white border border-slate-200 rounded-xl transition">🚪 Sign Out</button>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="border-b border-slate-200 bg-white/85 backdrop-blur-md px-4 lg:px-8 py-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="font-outfit text-lg font-semibold text-slate-800">Clinical Command Center</h2>
          <div className="flex flex-wrap items-center gap-3">
            <DataFilterBar value={dataFilter} onChange={setDataFilter} />
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100 text-emerald-600 text-xs font-medium">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />AI Assistant Live
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
}

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <DataFilterProvider>
      <DashboardShell>{children}</DashboardShell>
    </DataFilterProvider>
  );
}
