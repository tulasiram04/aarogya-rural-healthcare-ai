'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api, ApiError } from '@/lib/api';
import { KeyRound, Phone, RefreshCw, ShieldCheck } from 'lucide-react';

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    if (api.isAuthenticated()) {
      router.replace('/dashboard');
    } else {
      setCheckingAuth(false);
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      console.log(`[FORM SUBMIT] Phone: ${phone}, Password: ${password}`);
      const data = await api.login(phone, password);
      console.log(`[FORM SUCCESS] Token acquired:`, data.access_token);
      router.push('/dashboard');
    } catch (err) {
      console.error(`[FORM ERROR]`, err);
      if (err instanceof ApiError) {
        try {
          const parsed = JSON.parse(err.message);
          setError(parsed.detail || 'Invalid phone number or password.');
        } catch {
          setError('Invalid phone number or password.');
        }
      } else {
        setError('Unable to connect to the AAROGYA server. Please check if the backend is running.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (checkingAuth) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC]">
        <span className="text-4xl animate-spin text-emerald-500">🔄</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#F8FAFC] px-4 relative overflow-hidden">
      {/* Ambient background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-emerald-500/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
      </div>

      <div className="w-full max-w-md relative z-10">
        {/* Brand Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-3">
            <span className="text-5xl">🌿</span>
          </div>
          <h1 className="font-outfit font-bold text-4xl tracking-wide text-emerald-600">
            AAROGYA
          </h1>
          <p className="text-slate-450 text-xs mt-2 font-bold tracking-wider uppercase">
            AI-Powered Rural Healthcare Companion
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-white border border-slate-200/60 rounded-3xl p-8 shadow-xl">
          <h2 className="text-lg font-bold text-slate-800 mb-1">Clinician Onboarding</h2>
          <p className="text-xs text-slate-500 mb-6 font-semibold">Sign in to your clinical gateway coordinator profile</p>

          {error && (
            <div className="mb-6 p-4 rounded-2xl bg-rose-50 border border-rose-100 text-rose-700 text-xs flex items-start gap-3">
              <span className="text-lg mt-0.5">⚠️</span>
              <div>
                <p className="font-bold">Authentication Failed</p>
                <p className="text-xs text-rose-600/80 mt-1.5 font-semibold leading-relaxed">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div className="relative">
              <label htmlFor="login-phone" className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
                Phone Number
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <Phone className="w-4 h-4" />
                </span>
                <input
                  id="login-phone"
                  type="text"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="e.g. 9876543210"
                  required
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 placeholder-slate-400 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 transition shadow-sm font-semibold"
                />
              </div>
            </div>

            <div>
              <label htmlFor="login-password" className="block text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">
                Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
                  <KeyRound className="w-4 h-4" />
                </span>
                <input
                  id="login-password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter credential password"
                  required
                  className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 placeholder-slate-400 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500 transition shadow-sm font-semibold"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !phone || !password}
              className="w-full py-3.5 rounded-xl font-bold text-sm bg-emerald-500 hover:bg-emerald-600 text-white shadow-md shadow-emerald-500/10 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <RefreshCw className="w-4 h-4 animate-spin" /> Authenticating...
                </span>
              ) : (
                'Sign In to Dashboard'
              )}
            </button>
          </form>

          {/* Seeding Demo hints */}
          <div className="mt-6 pt-6 border-t border-slate-100">
            <p className="text-[9px] text-slate-400 text-center uppercase tracking-widest font-bold mb-3">Clinician Pre-fills</p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => { setPhone('9876543210'); setPassword('doctor123'); }}
                className="flex-1 py-2 px-3 text-xs rounded-xl bg-slate-50 text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-250 transition-all font-semibold"
              >
                👨‍⚕️ Doctor
              </button>
              <button
                type="button"
                onClick={() => { setPhone('9876543211'); setPassword('hcw123'); }}
                className="flex-1 py-2 px-3 text-xs rounded-xl bg-slate-50 text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-250 transition-all font-semibold"
              >
                👩‍⚕️ Coordinator
              </button>
              <button
                type="button"
                onClick={() => { setPhone('9876543200'); setPassword('admin123'); }}
                className="flex-1 py-2 px-3 text-xs rounded-xl bg-slate-50 text-slate-600 hover:text-emerald-600 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-250 transition-all font-semibold"
              >
                ⚙️ Admin
              </button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[10px] text-slate-400 mt-6 tracking-wide font-bold flex items-center justify-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-55" /> AAROGYA Secure Clinical Portal
        </p>
      </div>
    </div>
  );
}
