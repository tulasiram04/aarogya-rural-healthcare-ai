'use client';

import React, { useEffect, useState } from 'react';
import { api, ApiError } from '@/lib/api';
import { useDataFilter } from '@/lib/dataFilter';
import { ClipboardCheck, RefreshCw, Phone, CheckCircle, AlertTriangle, ArrowRight } from 'lucide-react';

interface VisitTask {
  id: string;
  patientName: string;
  village: string;
  subCenter: string;
  reason: string;
  riskLevel: string;
  phone: string | null;
  completed: boolean;
}

export default function HcwDashboard() {
  const { dataFilter } = useDataFilter();
  const [tasks, setTasks] = useState<VisitTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = async () => {
    setLoading(true);
    setError(null);
    try {
      const activeAlerts = await api.getActiveAlerts(dataFilter);
      
      const mappedTasks = activeAlerts.map((a: any) => ({
        id: a.id,
        patientName: a.patient_name,
        village: a.village || 'Unknown Village',
        subCenter: a.sub_center || 'Sub-center area',
        reason: `${a.source.replace('_', ' ').toUpperCase()}: ${a.alert_message}`,
        riskLevel: a.risk_level,
        phone: null,
        completed: false
      }));

      setTasks(mappedTasks);
    } catch (err) {
      console.error(err);
      if (err instanceof ApiError) {
        setError(`Failed to fetch visit list (Status ${err.status}).`);
      } else {
        setError('Connection error to database servers.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTasks();
  }, [dataFilter]);

  const handleCompleteTask = async (id: string) => {
    try {
      await api.resolveAlert(id);
      setTasks(prev => 
        prev.map(t => t.id === id ? { ...t, completed: true } : t)
      );
    } catch (err) {
      alert('Failed to update alert state in database.');
    }
  };

  const activeCount = tasks.filter(t => !t.completed).length;

  if (loading) {
    return (
      <div className="max-w-md mx-auto flex flex-col items-center justify-center min-h-[50vh] space-y-4">
        <span className="text-3xl animate-spin text-emerald-500">🔄</span>
        <p className="text-sm text-slate-500 font-semibold">Loading home checkup routes list...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-md mx-auto flex flex-col items-center justify-center min-h-[50vh] space-y-4 text-center">
        <span className="text-4xl">📡</span>
        <h4 className="font-bold text-rose-500">Sync Error</h4>
        <p className="text-xs text-slate-500 font-semibold">{error}</p>
        <button 
          onClick={fetchTasks}
          className="px-4 py-2 bg-emerald-500 text-white font-semibold rounded-xl text-xs shadow-md"
        >
          Retry Sync
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto space-y-6 pb-12">
      {/* Mobile Card Header */}
      <div className="p-5 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-3xl text-white shadow-md">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-xl font-bold font-outfit">ANM Visit Companion</h2>
            <p className="text-xs text-emerald-100 font-medium">Worker: Kamla Devi • Sub-center: Hasanpur</p>
          </div>
          <span className="text-2xl">🎒</span>
        </div>
        
        <div className="mt-4 pt-4 border-t border-white/20 flex justify-between text-center font-semibold text-sm">
          <div>
            <span className="text-[10px] text-emerald-100 block uppercase font-bold tracking-wider">Today Visits</span>
            <span className="text-lg font-bold">{tasks.length}</span>
          </div>
          <div className="border-r border-white/20" />
          <div>
            <span className="text-[10px] text-emerald-105 block uppercase font-bold tracking-wider">Pending</span>
            <span className="text-lg font-bold text-rose-100">{activeCount}</span>
          </div>
          <div className="border-r border-white/20" />
          <div>
            <span className="text-[10px] text-emerald-105 block uppercase font-bold tracking-wider">Completed</span>
            <span className="text-lg font-bold text-emerald-100">{tasks.length - activeCount}</span>
          </div>
        </div>
      </div>

      {/* Task List */}
      <div className="space-y-4">
        <div className="flex justify-between items-center px-1">
          <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
            Priority Home Visits Checklist
          </h3>
          <button 
            onClick={fetchTasks} 
            className="text-xs font-bold text-emerald-600 hover:underline flex items-center gap-1"
          >
            <RefreshCw className="w-3 h-3" /> Sync
          </button>
        </div>

        {tasks.length === 0 ? (
          <div className="p-8 text-center rounded-3xl bg-white border border-slate-150 text-slate-400 font-semibold shadow-sm">
            🎉 All assigned patients are stable. No urgent home visits scheduled.
          </div>
        ) : (
          tasks.map(task => (
            <div 
              key={task.id} 
              className={`p-5 rounded-3xl border transition-all duration-200 shadow-sm ${
                task.completed 
                  ? 'bg-slate-50 border-slate-200 opacity-60 scale-98 shadow-none' 
                  : 'bg-white border-slate-100'
              }`}
            >
              <div className="flex justify-between items-start">
                <div>
                  <div className="flex items-center gap-2">
                    <h4 className={`font-bold ${task.completed ? 'line-through text-slate-400' : 'text-slate-800'}`}>
                      {task.patientName}
                    </h4>
                    <span className="text-xs text-slate-400 font-semibold">• {task.village}</span>
                  </div>
                  
                  <span className={`inline-block mt-1.5 text-[9px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                    task.riskLevel === 'critical'
                      ? 'bg-rose-50 text-rose-600 border-rose-100 animate-pulse'
                      : task.riskLevel === 'high'
                      ? 'bg-amber-50 text-amber-600 border-amber-100'
                      : 'bg-blue-50 text-blue-600 border-blue-100'
                  }`}>
                    {task.riskLevel} Risk
                  </span>
                </div>
              </div>

              <p className={`text-xs font-semibold mt-3 ${task.completed ? 'text-slate-400 line-through' : 'text-slate-600'}`}>
                {task.reason}
              </p>

              <div className="mt-4 pt-4 border-t border-slate-100 flex justify-between items-center">
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Record checkup during visit</span>
                <button 
                  disabled={task.completed}
                  onClick={() => handleCompleteTask(task.id)}
                  className={`px-4 py-1.5 text-xs font-bold rounded-xl border transition ${
                    task.completed
                      ? 'bg-slate-50 text-slate-400 border-slate-200'
                      : 'bg-emerald-50 text-emerald-600 border-emerald-100 hover:bg-emerald-100'
                  }`}
                >
                  {task.completed ? '✓ Resolved' : 'Mark Visited'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
