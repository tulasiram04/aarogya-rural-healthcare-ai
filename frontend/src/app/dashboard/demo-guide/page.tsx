'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Rocket, ChevronRight, HelpCircle } from 'lucide-react';

const steps = [
  { 
    step: 1, 
    title: 'Register Patient via Telegram', 
    icon: '👤', 
    desc: 'Patient initiates onboarding by sending /start to the Telegram Bot, registering their name, age, gender, and preferred language.' 
  },
  { 
    step: 2, 
    title: 'Upload Prescription Card', 
    icon: '🩺', 
    desc: 'The health worker or patient uploads an image of the handwritten physical prescription card directly to the Telegram Bot chat.' 
  },
  { 
    step: 3, 
    title: 'AI OCR Extraction', 
    icon: '🤖', 
    desc: 'Gemini analyzes the prescription card, extracts structured medicines, schedules, dosages, duration, and diagnosis.' 
  },
  { 
    step: 4, 
    title: 'Medication Reminders Scheduled', 
    icon: '⏰', 
    desc: 'Deduplicated reminders are immediately inserted in the PostgreSQL database, mapping daily adherence check schedules.' 
  },
  { 
    step: 5, 
    title: 'Upload Lab Report Diagnostics', 
    icon: '🩸', 
    desc: 'Lab report sheets are sent to the Bot to parse blood sugar, creatinine, hemoglobin, or blood pressure values.' 
  },
  { 
    step: 6, 
    title: 'AI Biomarker Explanations', 
    icon: '🧪', 
    desc: 'Gemini reviews diagnostic parameters and generates a simplified, reassuring, patient-friendly summary in their language.' 
  },
  { 
    step: 7, 
    title: 'Daily Symptom Check-Ins', 
    icon: '🌡️', 
    desc: 'Patients report daily updates via conversational text or voice notes. Regional speech is translated to English.' 
  },
  { 
    step: 8, 
    title: 'AI Risk Alerts Triggered', 
    icon: '⚠️', 
    desc: 'Clinical rules check for indicators (e.g. fever > 5 days, glucose > 250, BP > 180), raising active risk alarms in the DB.' 
  },
  { 
    step: 9, 
    title: 'Doctor Dashboard Updates', 
    icon: '💻', 
    desc: 'Coordinators review the profile, inspect the live Risk Gauge, and review AI Doctor Copilot diagnostic recommendations.' 
  },
  { 
    step: 10, 
    title: 'Village Analytics Aggregation', 
    icon: '📈', 
    desc: 'Overall village compliance trends, top chronic conditions, and command center insights refresh dynamically.' 
  },
];

export default function DemoGuide() {
  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <Link href="/dashboard" className="text-xs font-semibold text-emerald-600 hover:underline flex items-center gap-1">
          <ArrowLeft className="w-3.5 h-3.5" /> Return to Command Center
        </Link>
        <h2 className="text-3xl font-bold font-outfit mt-2 text-slate-800 flex items-center gap-2">
          <Rocket className="w-6 h-6 text-emerald-500" /> Hackathon Demo Guide
        </h2>
        <p className="text-slate-500 text-sm mt-1">
          Follow this visual timeline to demonstrate AAROGYA's end-to-end clinical workflow to judges and investors.
        </p>
      </div>

      {/* Visual Vertical Timeline */}
      <div className="relative pl-8 border-l border-slate-200 ml-4 py-4 space-y-12">
        {steps.map((item) => (
          <div key={item.step} className="relative group">
            {/* Timeline bullet indicator */}
            <div className="absolute -left-[53px] top-1.5 w-10 h-10 rounded-xl bg-white border border-slate-200 flex items-center justify-center text-lg shadow-sm font-bold text-slate-800 z-10 transition-all group-hover:border-emerald-500 group-hover:text-emerald-600">
              {item.icon}
            </div>

            {/* Content card */}
            <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition duration-200 space-y-2">
              <div className="flex justify-between items-center">
                <span className="px-2.5 py-0.5 text-[9px] font-bold uppercase rounded-full bg-emerald-50 text-emerald-600 border border-emerald-100">
                  Step {item.step} of 10
                </span>
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">AAROGYA Flow</span>
              </div>
              
              <h4 className="text-base font-bold text-slate-800">{item.title}</h4>
              <p className="text-sm text-slate-500 font-semibold leading-relaxed">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Info Box */}
      <div className="p-6 rounded-3xl bg-slate-50 border border-slate-200 flex items-start gap-4">
        <HelpCircle className="w-6 h-6 text-slate-400 flex-shrink-0" />
        <div className="space-y-1">
          <h5 className="text-sm font-bold text-slate-700">Quick Seeding Tip</h5>
          <p className="text-xs text-slate-500 font-semibold leading-relaxed">
            You can reset the database and seed a realistic set of 10 patients matching this exact lifecycle timeline using the **🚀 Load Hackathon Demo** button located on the dashboard overview page (requires Admin login credentials: `9876543200` / `admin123`).
          </p>
        </div>
      </div>
    </div>
  );
}
