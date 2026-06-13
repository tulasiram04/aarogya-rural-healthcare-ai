/* src/app/page.tsx */
"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  Heart,
  Bot,
  Sparkles,
  Activity,
  CheckCircle2,
  ArrowRight,
  UploadCloud,
  Bell,
  FileText,
  BrainCircuit,
  Database,
  Smartphone,
  Globe,
  LineChart,
  Terminal,
  Server,
  Layers,
  ChevronRight,
  XCircle,
  Clock,
  Coins,
  ShieldCheck,
  Stethoscope,
  Network
} from "lucide-react";
import Link from "next/link";

export default function Home() {
  // Animation presets
  const fadeInUp = {
    hidden: { opacity: 0, y: 30 },
    visible: (custom = 0) => ({
      opacity: 1,
      y: 0,
      transition: {
        type: "spring",
        stiffness: 100,
        damping: 15,
        delay: custom * 0.1
      }
    })
  };

  const staggerContainer = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 selection:bg-emerald-100 selection:text-emerald-800 font-sans antialiased overflow-x-hidden">
      {/* Navigation Bar */}
      <header className="sticky top-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-200/60 px-6 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-2.5">
            <span className="p-2 bg-emerald-500 text-white rounded-xl shadow-md shadow-emerald-500/10">
              <Stethoscope className="w-5 h-5" />
            </span>
            <span className="font-outfit font-bold text-xl tracking-tight text-slate-800">
              AAROGYA
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-8 text-sm font-semibold text-slate-600">
            <a href="#problem" className="hover:text-emerald-600 transition-colors">The Challenge</a>
            <a href="#solution" className="hover:text-emerald-600 transition-colors">Our Approach</a>
            <a href="#features" className="hover:text-emerald-600 transition-colors">Features</a>
            <a href="#architecture" className="hover:text-emerald-600 transition-colors">Architecture</a>
            <a href="#timeline" className="hover:text-emerald-600 transition-colors">Interactive Flow</a>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="px-4.5 py-2 text-sm font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-200 rounded-xl shadow-sm transition-all"
            >
              Doctor Sign In
            </Link>
            <Link
              href="/login"
              className="px-5 py-2 text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl shadow-md shadow-emerald-600/10 hover:shadow-emerald-600/20 transition-all flex items-center gap-2"
            >
              Launch Dashboard <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* SECTION 1 — HERO */}
      <section className="relative px-6 py-20 md:py-32 overflow-hidden bg-gradient-to-b from-white via-emerald-50/20 to-slate-50">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px] pointer-events-none" />
        
        <div className="max-w-7xl mx-auto relative z-10">
          <div className="text-center max-w-4xl mx-auto space-y-6">
            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeInUp}
              custom={0}
              className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-100 text-emerald-700 text-xs font-semibold uppercase tracking-wider"
            >
              <Sparkles className="w-3.5 h-3.5" /> Hackathon Showcase Edition
            </motion.div>
            
            <motion.h1
              initial="hidden"
              animate="visible"
              variants={fadeInUp}
              custom={1}
              className="text-4xl sm:text-6xl md:text-7xl font-bold font-outfit tracking-tight text-slate-800 leading-[1.1]"
            >
              AAROGYA <br />
              <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                The Village Doctor Agent
              </span>
            </motion.h1>
            
            <motion.p
              initial="hidden"
              animate="visible"
              variants={fadeInUp}
              custom={2}
              className="text-lg md:text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed"
            >
              AI-Powered Rural Healthcare Companion that reads prescriptions, explains medicines in local languages, monitors patients daily, predicts health risks, and ensures no rural patient ever misses a medicine or follow-up.
            </motion.p>

            <motion.div
              initial="hidden"
              animate="visible"
              variants={fadeInUp}
              custom={3}
              className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <Link
                href="/login"
                className="w-full sm:w-auto px-8 py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-2xl shadow-lg shadow-emerald-600/20 hover:shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 text-base"
              >
                🚀 Launch Dashboard
              </Link>
              <a
                href="https://t.me/MyTAGI_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto px-8 py-4 bg-white hover:bg-slate-50 text-slate-800 font-semibold border border-slate-200 rounded-2xl shadow-sm transition-all flex items-center justify-center gap-2 text-base"
              >
                🤖 Open Telegram Bot
              </a>
              <a
                href="#architecture"
                className="w-full sm:w-auto px-6 py-4 bg-transparent hover:bg-slate-100 text-slate-600 hover:text-slate-800 font-semibold transition-all flex items-center justify-center gap-1.5 text-base"
              >
                📄 View Architecture
              </a>
            </motion.div>
          </div>

          {/* Stats Bar */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: "spring", stiffness: 80, delay: 0.5 }}
            className="mt-20 p-6 sm:p-8 rounded-3xl bg-white border border-slate-200/80 shadow-xl shadow-slate-100/50 grid grid-cols-2 md:grid-cols-5 gap-6 text-center"
          >
            {[
              { label: "10+ Languages", desc: "Regional voice companion" },
              { label: "24/7 Monitoring", desc: "No offline gaps" },
              { label: "5 AI Agents", desc: "Specialized StateGraph" },
              { label: "0₹ Patient Cost", desc: "Runs on basic Telegram" },
              { label: "95% Adherence", desc: "Medication compliance" }
            ].map((stat, i) => (
              <div key={i} className="space-y-1 py-2 md:py-0 border-r last:border-0 border-slate-100 md:block first:border-0 md:first:border-r">
                <h4 className="text-2xl sm:text-3xl font-extrabold text-emerald-600 font-outfit">{stat.label}</h4>
                <p className="text-xs text-slate-400 font-semibold tracking-wide uppercase">{stat.desc}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* SECTION 2 — THE PROBLEM */}
      <section id="problem" className="px-6 py-20 bg-white border-y border-slate-200/60">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="text-xs font-bold text-rose-500 uppercase tracking-widest">Global Challenges</h2>
            <h3 className="text-3xl sm:text-4xl font-bold font-outfit text-slate-800">
              Healthcare Access in Rural Communities is Broken
            </h3>
            <p className="text-slate-500 text-sm">
              Primary healthcare infrastructure fails at the last mile. Remote villages suffer from critical informational gaps and systemic operational deficits.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              {
                title: "Prescription Confusion",
                desc: "Patients receive physical cards but don't understand drug instructions, dosage timing, or safety protocols.",
                icon: <XCircle className="w-5 h-5 text-rose-500" />
              },
              {
                title: "Forgotten Medications",
                desc: "No interactive reminders mean scheduled drugs are missed, leading to critical treatment adherence drop-offs.",
                icon: <XCircle className="w-5 h-5 text-rose-500" />
              },
              {
                title: "Missed Follow-Ups",
                desc: "Without active clinical supervision, routine check-ups are skipped, compounding underlying chronic conditions.",
                icon: <XCircle className="w-5 h-5 text-rose-500" />
              },
              {
                title: "Zero Patient Monitoring",
                desc: "Doctors have no remote visibility once patients leave the clinic. Risk escalations are only identified when critical.",
                icon: <XCircle className="w-5 h-5 text-rose-500" />
              }
            ].map((card, idx) => (
              <div
                key={idx}
                className="p-6 rounded-2xl bg-rose-50/40 border border-rose-100 flex flex-col gap-4 shadow-sm"
              >
                <span className="p-2.5 bg-rose-50 text-rose-600 rounded-xl w-fit">
                  {card.icon}
                </span>
                <h4 className="font-bold text-slate-800 text-base">{card.title}</h4>
                <p className="text-xs text-slate-500 leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>

          {/* Visual Healthcare Illustration Representation */}
          <div className="p-8 rounded-3xl bg-slate-50/50 border border-slate-200/80 flex flex-col md:flex-row items-center gap-8 max-w-4xl mx-auto">
            <div className="p-6 bg-white border border-slate-200 rounded-2xl shadow-sm shrink-0">
              <div className="relative w-20 h-20 flex items-center justify-center">
                <span className="absolute animate-ping h-14 w-14 rounded-full bg-emerald-400 opacity-20" />
                <span className="p-4 bg-emerald-50 text-emerald-600 rounded-full z-10">
                  <Activity className="w-8 h-8" />
                </span>
              </div>
            </div>
            <div className="space-y-2.5 text-center md:text-left">
              <h4 className="font-bold text-slate-800 text-lg">Did you know?</h4>
              <p className="text-xs text-slate-500 leading-relaxed max-w-xl">
                Over 70% of medication failure in rural clinics stems from structural communication issues. Language barriers, low literacy, and the loss of physical doctor charts prevent safe, consistent outpatient recoveries.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3 — SOLUTION */}
      <section id="solution" className="px-6 py-20 bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div className="space-y-6">
            <h2 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">The Transformation</h2>
            <h3 className="text-3xl sm:text-5xl font-bold font-outfit text-slate-800">
              Meet AAROGYA
            </h3>
            <p className="text-slate-600 leading-relaxed text-sm">
              AAROGYA acts as an AI health companion that transforms physical prescriptions into understandable treatment plans, sends alerts, coordinates reminder check-ins, performs predictive risk assessments, and enables proactive, preventive healthcare delivery.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                "Prescription OCR",
                "Medicine Reminder Agent",
                "Risk Assessment",
                "Lab Report Explanation",
                "Telegram Healthcare Assistant",
                "MCP Intelligence Layer"
              ].map((item, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <span className="p-1 bg-emerald-50 border border-emerald-100 rounded-lg text-emerald-600">
                    <CheckCircle2 className="w-4 h-4" />
                  </span>
                  <span className="text-xs font-bold text-slate-700">{item}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="relative p-6 bg-white border border-slate-200 rounded-3xl shadow-xl shadow-slate-100/60 max-w-md mx-auto">
            <div className="absolute -top-3 -right-3 px-3 py-1 bg-emerald-500 text-white rounded-lg text-[10px] font-bold uppercase tracking-wider shadow">
              Core Engine
            </div>
            <div className="space-y-4">
              <div className="flex items-center gap-3 border-b border-slate-100 pb-3">
                <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg"><Bot className="w-4 h-4" /></span>
                <div>
                  <h4 className="text-xs font-bold text-slate-800">AAROGYA Agent Status</h4>
                  <span className="text-[10px] text-emerald-500 font-semibold">Active & Online</span>
                </div>
              </div>
              
              <div className="space-y-2 text-xs">
                <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-1">
                  <span className="font-bold text-emerald-600 text-[10px] block">Vision Pipeline Input</span>
                  <p className="text-slate-500">Image: Prescription card.jpeg received.</p>
                </div>
                <div className="p-3 bg-emerald-50/40 border border-emerald-100/50 rounded-xl space-y-1">
                  <span className="font-bold text-emerald-700 text-[10px] block">LangGraph Analysis Outcome</span>
                  <p className="text-slate-600">Extracted: Amoxicillin 500mg, 1 tab twice daily. Diagnosis: Respiratory Infection.</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4 — CORE FEATURES */}
      <section className="px-6 py-20 bg-white border-t border-slate-200/60">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Platform Core</h2>
            <h3 className="text-3xl sm:text-4xl font-bold font-outfit text-slate-800">
              Clinical Intelligence Suite
            </h3>
            <p className="text-slate-500 text-sm">
              Six tightly integrated AI-driven operations that optimize Last-Mile Rural Care.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                title: "Prescription Intelligence",
                desc: "Upload prescription images. AI automatically extracts the primary diagnosis, medications, dosage rules, and daily schedules.",
                icon: <UploadCloud className="w-5 h-5" />,
                color: "bg-blue-50 text-blue-600 border-blue-100"
              },
              {
                title: "Smart Reminder Agent",
                desc: "Medication adherence tracking with scheduled compliance push alerts. Prompts check-in prompts directly on Telegram.",
                icon: <Bell className="w-5 h-5" />,
                color: "bg-emerald-50 text-emerald-600 border-emerald-100"
              },
              {
                title: "Lab Report Explainer",
                desc: "Simplifies complicated laboratory biomarkers and chemical indices into plain-text summaries in the patient's local language.",
                icon: <FileText className="w-5 h-5" />,
                color: "bg-amber-50 text-amber-600 border-amber-100"
              },
              {
                title: "Risk Prediction Agent",
                desc: "Evaluates patient metrics, alerts, and medical history. Calculates predictive scores to detect clinical complications early.",
                icon: <BrainCircuit className="w-5 h-5" />,
                color: "bg-rose-50 text-rose-600 border-rose-100"
              },
              {
                title: "Telegram Health Companion",
                desc: "Provides 24/7 multilingual healthcare assistant support. Supports voice transcripts, translations, and interactive button logging.",
                icon: <Smartphone className="w-5 h-5" />,
                color: "bg-indigo-50 text-indigo-600 border-indigo-100"
              },
              {
                title: "MCP Clinical Intelligence",
                desc: "Standardizes clinical capabilities into Model Context Protocol tools, enabling instant client integrations and analytics.",
                icon: <Network className="w-5 h-5" />,
                color: "bg-teal-50 text-teal-600 border-teal-100"
              }
            ].map((feature, idx) => (
              <motion.div
                key={idx}
                variants={fadeInUp}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true, margin: "-100px" }}
                custom={idx % 3}
                className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm hover:shadow-md hover:border-slate-300 transition-all duration-300 flex flex-col gap-4"
              >
                <span className={`p-3 rounded-xl w-fit ${feature.color}`}>
                  {feature.icon}
                </span>
                <h4 className="font-bold text-slate-800 text-base font-outfit">{feature.title}</h4>
                <p className="text-xs text-slate-500 leading-relaxed">{feature.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 5 — AI + MCP ARCHITECTURE */}
      <section id="architecture" className="px-6 py-20 bg-slate-50 border-t border-slate-200/60">
        <div className="max-w-5xl mx-auto space-y-12">
          <div className="text-center space-y-4">
            <h2 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Protocol & Pipeline</h2>
            <h3 className="text-3xl sm:text-4xl font-bold font-outfit text-slate-800">
              AI Agent & System Architecture
            </h3>
            <p className="text-slate-500 text-sm max-w-2xl mx-auto">
              How patient touchpoints, agents, pipelines, databases, and monitoring UI connect securely.
            </p>
          </div>

          {/* Architecture Flow Representation */}
          <div className="p-8 rounded-3xl bg-white border border-slate-200 shadow-sm space-y-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4 text-center md:text-left">
              {[
                { step: "Telegram Patient", desc: "User Touchpoint" },
                { step: "FastAPI Gateway", desc: "REST / JWT Endpoint" },
                { step: "LangGraph System", desc: "AI Orchestrator" },
                { step: "MCP Tool Layer", desc: "Clinical Functions" },
                { step: "PostgreSQL DB", desc: "Patient Records" },
                { step: "Clinical Dashboard", desc: "Doctor Monitoring" }
              ].map((node, i) => (
                <React.Fragment key={i}>
                  <div className="flex flex-col items-center p-3.5 bg-slate-50 border border-slate-100 rounded-2xl min-w-[130px] shadow-sm">
                    <span className="text-xs font-bold text-slate-800 font-mono">{node.step}</span>
                    <span className="text-[10px] text-slate-400 font-semibold">{node.desc}</span>
                  </div>
                  {i < 5 && (
                    <ChevronRight className="w-5 h-5 text-slate-300 hidden md:block shrink-0" />
                  )}
                </React.Fragment>
              ))}
            </div>

            {/* Tech Badges */}
            <div className="border-t border-slate-100 pt-6">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-3.5 text-center">
                Verified System Technologies
              </span>
              <div className="flex flex-wrap justify-center gap-2">
                {[
                  "Gemini 2.5 Flash",
                  "LangGraph",
                  "MCP",
                  "FastAPI",
                  "PostgreSQL",
                  "Redis",
                  "Celery",
                  "Telegram Bot API",
                  "Next.js"
                ].map((badge, idx) => (
                  <span
                    key={idx}
                    className="text-[11px] font-bold px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100 text-emerald-700 shadow-sm"
                  >
                    {badge}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 6 — PROJECT SCREENSHOTS SHOWCASE */}
      <section className="px-6 py-20 bg-white border-y border-slate-200/60">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Interface Preview</h2>
            <h3 className="text-3xl sm:text-4xl font-bold font-outfit text-slate-800">
              Modern Portal Designs
            </h3>
            <p className="text-slate-500 text-sm">
              Explore the interfaces designed for doctors, health workers, and patient interaction.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {[
              {
                title: "Dashboard Overview",
                desc: "Consolidated health metrics, active risk notifications, interactive regional voice widget, and AI village reports.",
                label: "Admin & Doctor Overview Console"
              },
              {
                title: "Patient Management",
                desc: "Demographic lists, compliance logs, prescription charts, and doctor copilot medical recommendations.",
                label: "Clinical Records Portal"
              },
              {
                title: "MCP Tools Console",
                desc: "Standardized model context protocol tool selection, lookup testing, and risk extraction screens.",
                label: "AI Protocol Testing Workspace"
              },
              {
                title: "Telegram Assistant",
                desc: "Telegram bot client chat. Supports audio symptom transcription, document uploads, and daily check-ins.",
                label: "Patient Communication Interface"
              }
            ].map((mockup, idx) => (
              <div
                key={idx}
                className="group p-5 bg-slate-50 border border-slate-200 rounded-3xl shadow-sm hover:shadow-md transition-all flex flex-col gap-4"
              >
                {/* Mockup Placeholder Frame */}
                <div className="aspect-[16/10] bg-white border border-slate-200 rounded-2xl flex flex-col justify-between p-6 relative overflow-hidden shadow-inner group-hover:border-emerald-300 transition-colors">
                  <div className="flex justify-between items-center border-b border-slate-100 pb-3">
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                      {mockup.label}
                    </span>
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shadow shadow-emerald-500/50" />
                  </div>
                  <div className="flex flex-col items-center justify-center gap-2 text-center flex-1">
                    <span className="p-3 bg-emerald-50 text-emerald-600 rounded-full">
                      <Layers className="w-5 h-5" />
                    </span>
                    <h5 className="font-bold text-slate-800 text-sm">{mockup.title}</h5>
                    <p className="text-[11px] text-slate-400 leading-normal max-w-xs">{mockup.desc}</p>
                  </div>
                  <div className="flex items-center gap-1.5 border-t border-slate-100 pt-3">
                    <span className="h-2 w-2 rounded-full bg-slate-200" />
                    <span className="h-2 w-2 rounded-full bg-slate-200" />
                    <span className="h-2 w-2 rounded-full bg-slate-200" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 7 — IMPACT */}
      <section className="px-6 py-20 bg-slate-50">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Real Metrics</h2>
            <h3 className="text-3xl sm:text-4xl font-bold font-outfit text-slate-800">
              Real Impact for Rural Healthcare
            </h3>
            <p className="text-slate-500 text-sm">
              Quantifiable outcomes engineered directly into the platform to verify performance and scale.
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-6">
            {[
              { num: "10+", label: "Languages Supported", desc: "Regional voice notes" },
              { num: "24/7", label: "AI Monitoring", desc: "Continuous assistant availability" },
              { num: "100%", label: "Prescription Understanding", desc: "Plain language explanations" },
              { num: "95%", label: "Adherence Tracking", desc: "Taken/missed response logs" },
              { num: "Real-Time", label: "Risk Detection", desc: "Instant clinical alarms" },
              { num: "Doctor", label: "Dashboard Insights", desc: "Clean oversight analytics" }
            ].map((metric, idx) => (
              <div key={idx} className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm flex flex-col gap-2">
                <span className="text-3xl sm:text-4xl font-extrabold text-emerald-600 font-outfit block">
                  {metric.num}
                </span>
                <h4 className="font-bold text-slate-800 text-sm">{metric.label}</h4>
                <p className="text-xs text-slate-400 font-medium leading-relaxed">{metric.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 8 — HACKATHON HIGHLIGHTS */}
      <section className="px-6 py-20 bg-white border-t border-slate-200/60">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Judges Guide</h2>
            <h3 className="text-3xl sm:text-4xl font-bold font-outfit text-slate-800">
              Innovation Highlights
            </h3>
            <p className="text-slate-500 text-sm">
              Key areas of technological execution built during the hackathon.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                title: "AI Vision OCR",
                desc: "Uses Gemini's visual models to analyze raw images of physical prescriptions, recognizing handwritten diagnoses and medicines."
              },
              {
                title: "Agentic AI Workflows",
                desc: "Managed by LangGraph nodes to dynamically route patient messages, classify intents, and rating clinical severity."
              },
              {
                title: "Model Context Protocol",
                desc: "Implements standardization protocol interfaces. Simplifies remote tool integrations, analytics, and clinical lookups."
              },
              {
                title: "Multilingual Voice Assistant",
                desc: "Integrated recording console supporting instant translation and audio responses in local rural dialects."
              },
              {
                title: "Clinical Risk Intelligence",
                desc: "Risk engine combining compliance statistics and symptoms to calculate predictive risks and issue clinician alerts."
              },
              {
                title: "Rural Healthcare Accessibility",
                desc: "Delivers clinical oversight using standard messaging applications, bypassing the need for complex, heavy apps."
              }
            ].map((highlight, idx) => (
              <div key={idx} className="p-6 rounded-3xl bg-slate-50 border border-slate-100 flex flex-col gap-3">
                <span className="text-xs font-bold text-emerald-600 uppercase tracking-widest">0{idx + 1}</span>
                <h4 className="font-bold text-slate-800 text-base font-outfit">{highlight.title}</h4>
                <p className="text-xs text-slate-500 leading-relaxed">{highlight.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 9 — TECHNOLOGY STACK */}
      <section className="px-6 py-20 bg-slate-50 border-t border-slate-200/60">
        <div className="max-w-7xl mx-auto space-y-12">
          <div className="text-center max-w-3xl mx-auto space-y-4">
            <h2 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Build Stack</h2>
            <h3 className="text-3xl sm:text-4xl font-bold font-outfit text-slate-800">
              Full-Stack Platform Details
            </h3>
            <p className="text-slate-500 text-sm">
              Optimized development stack verified and deployed under Docker compose configurations.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
            {[
              {
                category: "Frontend",
                tech: ["Next.js 14", "TypeScript", "TailwindCSS", "Framer Motion"],
                icon: <Layers className="w-4 h-4 text-emerald-600" />
              },
              {
                category: "Backend",
                tech: ["FastAPI", "PostgreSQL", "SQLAlchemy", "Uvicorn"],
                icon: <Server className="w-4 h-4 text-emerald-600" />
              },
              {
                category: "AI Engine",
                tech: ["Gemini 2.5 Flash", "LangGraph", "JSON schemas"],
                icon: <BrainCircuit className="w-4 h-4 text-emerald-600" />
              },
              {
                category: "Communication",
                tech: ["Telegram Bot API", "MCP Tools Schema"],
                icon: <Smartphone className="w-4 h-4 text-emerald-600" />
              },
              {
                category: "Infrastructure",
                tech: ["Docker", "Docker Compose", "Redis", "Celery"],
                icon: <Database className="w-4 h-4 text-emerald-600" />
              }
            ].map((stack, idx) => (
              <div key={idx} className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-sm space-y-4">
                <div className="flex items-center gap-2 border-b border-slate-100 pb-2.5">
                  <span className="p-1.5 bg-emerald-50 rounded-lg">{stack.icon}</span>
                  <h4 className="font-bold text-slate-800 text-xs tracking-wide uppercase">{stack.category}</h4>
                </div>
                <div className="flex flex-col gap-1.5">
                  {stack.tech.map((t, idx2) => (
                    <span key={idx2} className="text-xs font-semibold text-slate-600 flex items-center gap-1.5">
                      <span className="h-1.5 w-1.5 rounded-full bg-slate-300 shrink-0" />
                      {t}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 10 — DEMO FLOW TIMELINE */}
      <section id="timeline" className="px-6 py-20 bg-white border-y border-slate-200/60">
        <div className="max-w-4xl mx-auto space-y-16">
          <div className="text-center space-y-4">
            <h2 className="text-xs font-bold text-emerald-600 uppercase tracking-widest">Step-By-Step</h2>
            <h3 className="text-3xl sm:text-4xl font-bold font-outfit text-slate-800">
              Interactive Patient & Clinician Flow
            </h3>
            <p className="text-slate-500 text-sm max-w-2xl mx-auto">
              Follow the data pipeline from a patient's mobile upload to the physician's web terminal.
            </p>
          </div>

          {/* Timeline Layout */}
          <div className="relative border-l border-emerald-100 ml-4 md:ml-32 space-y-12">
            {[
              {
                title: "Patient uploads prescription",
                desc: "User clicks 'Upload Prescription' button on Telegram bot client, capturing a clear camera photo of their paper prescription card."
              },
              {
                title: "AI extracts medicines",
                desc: "Gemini Vision OCR parses the text, identifying medicines, quantities, schedules, and primary diagnoses."
              },
              {
                title: "Schedule generated",
                desc: "AAROGYA parses extracted times (e.g. 'morning & evening') and populates medication schedules in the PostgreSQL database."
              },
              {
                title: "Reminders sent",
                desc: "Celery task scheduler monitors logs, dispatching Daily Check-in reminders to patients with Taken/Missed log buttons."
              },
              {
                title: "Risk calculated",
                desc: "Risk engine evaluates compliance rates and symptoms. High-risk profiles trigger immediate clinical escalations."
              },
              {
                title: "Dashboard updated",
                desc: "Doctors and Health Workers access the dashboard to view patient compliance logs, risk profiles, and copilot guidelines."
              }
            ].map((step, idx) => (
              <div key={idx} className="relative pl-8 md:pl-12">
                {/* Timeline dot */}
                <span className="absolute -left-[9px] top-1 h-4 w-4 rounded-full border border-emerald-300 bg-white flex items-center justify-center">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                </span>
                
                {/* Left side step labels on desktop */}
                <div className="hidden md:block absolute -left-36 top-0 text-right w-24">
                  <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider font-mono">
                    Step 0{idx + 1}
                  </span>
                </div>
                
                <div className="space-y-1.5 max-w-2xl">
                  <span className="text-[10px] font-bold text-emerald-600 uppercase tracking-wider font-mono md:hidden block">
                    Step 0{idx + 1}
                  </span>
                  <h4 className="font-bold text-slate-800 text-base font-outfit">{step.title}</h4>
                  <p className="text-xs text-slate-500 leading-relaxed">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SECTION 11 — JUDGE CTA */}
      <section className="px-6 py-20 bg-slate-50">
        <div className="max-w-4xl mx-auto">
          <div className="relative p-8 md:p-12 rounded-3xl bg-gradient-to-r from-emerald-600 to-teal-600 text-white overflow-hidden shadow-xl shadow-emerald-700/20 text-center space-y-6">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(255,255,255,0.15),transparent_60%)] pointer-events-none" />
            
            <h3 className="text-3xl md:text-5xl font-bold font-outfit tracking-tight">
              Experience AAROGYA Live
            </h3>
            
            <p className="text-emerald-100 max-w-xl mx-auto text-sm leading-relaxed">
              Explore the AI-powered rural healthcare companion built for accessible, proactive and intelligent healthcare delivery. Load demo datasets to view instant evaluations.
            </p>

            <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
              <Link
                href="/login"
                className="w-full sm:w-auto px-8 py-3.5 bg-white hover:bg-slate-50 text-emerald-700 font-semibold rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
              >
                🚀 Access Dashboard
              </Link>
              <a
                href="https://t.me/MyTAGI_bot"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full sm:w-auto px-8 py-3.5 bg-emerald-700 hover:bg-emerald-800 text-white font-semibold border border-emerald-500/30 rounded-xl transition-all flex items-center justify-center gap-2"
              >
                🤖 Open Telegram Bot
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 12 — FOOTER */}
      <footer className="bg-slate-900 text-slate-400 px-6 py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8 mb-8 border-b border-slate-800 pb-8">
          <div className="space-y-4">
            <div className="flex items-center gap-2.5 text-white">
              <span className="p-2 bg-emerald-500 rounded-xl text-white">
                <Stethoscope className="w-5 h-5" />
              </span>
              <span className="font-outfit font-bold text-lg tracking-tight">
                AAROGYA
              </span>
            </div>
            <p className="text-xs leading-relaxed max-w-xs">
              AI-Powered Rural Healthcare Companion addressing medical adherence, clinical risk mapping, and language accessibility.
            </p>
          </div>

          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">Interface Links</h4>
            <div className="flex flex-col gap-2 text-xs">
              <Link href="/login" className="hover:text-white transition-colors">Dashboard Portal</Link>
              <a href="https://t.me/MyTAGI_bot" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors">Telegram Bot</a>
              <a href="#timeline" className="hover:text-white transition-colors">Interactive Flow</a>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">Framework Components</h4>
            <div className="flex flex-col gap-2 text-xs">
              <span>Gemini 2.5 Flash API</span>
              <span>LangGraph Agent Workflows</span>
              <span>Model Context Protocol</span>
              <span>FastAPI REST Middleware</span>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="text-xs font-bold text-white uppercase tracking-wider">Project Scope</h4>
            <p className="text-xs leading-relaxed">
              Designed and built for rural healthcare hackathon demonstration. Advisory AI diagnostic capabilities only.
            </p>
          </div>
        </div>

        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4 text-xs font-semibold">
          <span>
            © 2026 AAROGYA Project. All rights reserved.
          </span>
          <span className="flex items-center gap-1.5 text-slate-500">
            Built using: <span className="text-emerald-500">Gemini + LangGraph + MCP + FastAPI + Next.js</span>
          </span>
        </div>
      </footer>
    </div>
  );
}
