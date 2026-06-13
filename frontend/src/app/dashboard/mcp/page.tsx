/* src/app/dashboard/mcp/page.tsx */

"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users,
  Activity,
  FileText,
  AlertTriangle,
  Search,
  Cpu,
  Play,
  CheckCircle2,
  AlertCircle,
  TrendingUp,
  RefreshCw,
  User,
  MapPin,
  Phone,
  Calendar,
  ChevronRight,
  Info,
  Heart,
  Pill,
} from "lucide-react";
import { api } from "@/lib/api";
import { useDataFilter } from "@/lib/dataFilter";

interface PatientInfo {
  id: string;
  name: string;
  age?: number;
  gender?: string;
  phone?: string;
  village?: string;
  sub_center?: string;
  preferred_language?: string;
  risk_score?: number;
  risk_level?: string;
  is_active?: boolean;
  created_at?: string;
}

interface RiskInfo {
  patient_id: string;
  patient_name?: string;
  risk_score: number;
  risk_level: string;
  risk_factors?: string[];
}

interface PrescriptionInfo {
  patient_name: string;
  total_prescriptions: number;
  prescriptions: Array<{
    diagnosis?: string;
    medicines?: Array<{ name: string } | string>;
    issue_date?: string;
  }>;
}

export default function McpDashboard() {
  const { dataFilter } = useDataFilter();
  const [patientId, setPatientId] = useState("");
  const [patient, setPatient] = useState<PatientInfo | null>(null);
  const [risk, setRisk] = useState<RiskInfo | null>(null);
  const [prescriptions, setPrescriptions] = useState<PrescriptionInfo | null>(null);
  const [summary, setSummary] = useState<any>(null);
  const [patientsList, setPatientsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [error, setError] = useState<string>("");
  const [activeTool, setActiveTool] = useState<string | null>(null);

  // Load dashboard summary and patients for quick select
  const loadDashboardData = async () => {
    setLoadingSummary(true);
    try {
      const sum = await api.getDashboardSummary(dataFilter);
      setSummary(sum);
      const pts = await api.getPatients(dataFilter);
      setPatientsList(pts.slice(0, 5));
    } catch (err) {
      console.error("Failed to load dashboard summary:", err);
    } finally {
      setLoadingSummary(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [dataFilter]);

  const handleSearch = async (targetId?: string) => {
    const searchId = targetId || patientId;
    if (!searchId) return;

    if (!targetId) {
      setPatientId(searchId);
    }

    setLoading(true);
    setError("");
    try {
      const pRes = await api.getPatientMcp(searchId);
      console.log("MCP search_patient response:", JSON.stringify(pRes));
      const patientData = pRes?.result ?? pRes ?? null;
      if (patientData?.error) {
        setError(patientData.error);
        setPatient(null);
        setRisk(null);
        setPrescriptions(null);
        return;
      }
      setPatient(patientData);

      const rRes = await api.getPatientRiskMcp(searchId);
      console.log("MCP get_patient_risk response:", JSON.stringify(rRes));
      const riskData = rRes?.result ?? rRes ?? null;
      setRisk(riskData?.error ? null : riskData);

      const prRes = await api.getPatientPrescriptionsMcp(searchId);
      console.log("MCP get_patient_prescriptions response:", JSON.stringify(prRes));
      const prData = prRes?.result ?? prRes ?? { prescriptions: [] };
      const normalizedPrescriptions = {
        ...prData,
        prescriptions: Array.isArray(prData.prescriptions) ? prData.prescriptions : [],
        total_prescriptions: prData.total_prescriptions ?? 0,
      };
      setPrescriptions(normalizedPrescriptions);
    } catch (e: any) {
      setError(e?.message ?? "Failed to fetch patient data via MCP tools.");
      setPatient(null);
      setRisk(null);
      setPrescriptions(null);
    } finally {
      setLoading(false);
    }
  };


  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.06 },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 12 },
    show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 120, damping: 18 } },
  };

  const getRiskColor = (score: number) => {
    if (score >= 70) return "text-rose-600";
    if (score >= 40) return "text-amber-600";
    return "text-emerald-600";
  };

  const getRiskBg = (score: number) => {
    if (score >= 70) return "bg-rose-50 text-rose-600 border-rose-100";
    if (score >= 40) return "bg-amber-50 text-amber-600 border-amber-100";
    return "bg-emerald-50 text-emerald-600 border-emerald-100";
  };

  const getRiskTrackColor = (score: number) => {
    if (score >= 70) return "#f43f5e";
    if (score >= 40) return "#f59e0b";
    return "#10b981";
  };

  const mcpTools = [
    {
      name: "search_patient",
      label: "Search Patient",
      tag: "Query",
      tagColor: "bg-emerald-50 text-emerald-600 border-emerald-100",
      description: "Look up patient demographics and clinical status by UUID.",
      args: "{ patient_id }",
    },
    {
      name: "get_patient_risk",
      label: "Get Patient Risk",
      tag: "Analyze",
      tagColor: "bg-amber-50 text-amber-600 border-amber-100",
      description: "Compute real-time risk score, level, and identified risk factors.",
      args: "{ patient_id }",
    },
    {
      name: "get_patient_prescriptions",
      label: "Get Prescriptions",
      tag: "Medical",
      tagColor: "bg-blue-50 text-blue-600 border-blue-100",
      description: "Retrieve all uploaded prescriptions, diagnoses, and medicines.",
      args: "{ patient_id }",
    },
    {
      name: "dashboard_summary",
      label: "Dashboard Summary",
      tag: "Overview",
      tagColor: "bg-slate-100 text-slate-600 border-slate-200",
      description: "Aggregate platform metrics — patients, alerts, prescriptions, health score.",
      args: "{ }",
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h2 className="text-3xl font-bold font-outfit text-slate-800 flex items-center gap-2">
            🧩 MCP Tools
          </h2>
          <p className="text-slate-500 text-sm mt-1">
            Model Context Protocol tools for querying patient data, risk assessments, and clinical summaries.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 border border-emerald-100 text-emerald-600 text-xs font-medium">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
            MCP Server Active
          </div>
          <button
            onClick={loadDashboardData}
            disabled={loadingSummary}
            className="px-4 py-2.5 text-sm font-semibold bg-white border border-slate-200 text-slate-700 rounded-xl hover:bg-slate-50 shadow-sm transition flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loadingSummary ? "animate-spin" : ""}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <motion.section
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
      >
        {/* Total Patients */}
        <motion.div variants={itemVariants} className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Total Patients</span>
            <span className="p-2 rounded-xl bg-emerald-50 text-emerald-600"><Users className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-slate-800">{summary?.total_patients ?? "—"}</h3>
          <p className="text-[10px] text-emerald-600 font-semibold mt-1 flex items-center gap-1">
            <span>●</span> Live records
          </p>
        </motion.div>

        {/* Active Alerts */}
        <motion.div variants={itemVariants} className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-rose-500 uppercase tracking-wider">Active Alerts</span>
            <span className="p-2 rounded-xl bg-rose-50 text-rose-600"><AlertTriangle className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-rose-600">{summary?.active_alerts ?? summary?.risk_alerts ?? "—"}</h3>
          <p className="text-[10px] text-rose-500/80 font-medium mt-1">Requires review</p>
        </motion.div>

        {/* Prescriptions */}
        <motion.div variants={itemVariants} className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Prescriptions</span>
            <span className="p-2 rounded-xl bg-blue-50 text-blue-600"><FileText className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-blue-600">{summary?.prescriptions_uploaded ?? "—"}</h3>
          <p className="text-[10px] text-slate-400 mt-1">AI OCR extracted</p>
        </motion.div>

        {/* Village Health Score */}
        <motion.div variants={itemVariants} className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm hover:shadow-md transition-all duration-300">
          <div className="flex justify-between items-start">
            <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Village Health Score</span>
            <span className="p-2 rounded-xl bg-emerald-50 text-emerald-600"><Activity className="w-4 h-4" /></span>
          </div>
          <h3 className="text-3xl font-bold mt-2 text-emerald-600">
            {summary?.village_health_score ? `${summary.village_health_score}%` : "—"}
          </h3>
          <div className="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden">
            <div
              className="bg-emerald-500 h-full rounded-full transition-all duration-500"
              style={{ width: `${summary?.village_health_score ?? 0}%` }}
            />
          </div>
        </motion.div>
      </motion.section>

      {/* Main Content Grid: Lookup + MCP Tools */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

        {/* LEFT: Patient Lookup Console */}
        <div className="lg:col-span-2 space-y-6">

          {/* Search Card */}
          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm">
            <div className="flex items-center gap-2 mb-4">
              <span className="p-2 bg-emerald-50 text-emerald-600 rounded-xl"><Search className="w-4 h-4" /></span>
              <h3 className="font-bold font-outfit text-slate-800">Patient Lookup</h3>
            </div>

            <p className="text-xs text-slate-500 mb-4">
              Search for a patient by their UUID to retrieve demographics, risk assessment, and prescription records via MCP tools.
            </p>

            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="Enter patient UUID (e.g. 550e8400-e29b-41d4-a716-446655440000)"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  className="w-full pl-4 pr-10 py-3 rounded-xl bg-slate-50 border border-slate-200 text-slate-800 text-sm outline-none focus:border-emerald-400 focus:ring-1 focus:ring-emerald-400 transition-all font-mono placeholder-slate-400"
                />
                {patientId && (
                  <button
                    onClick={() => setPatientId("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 text-xs font-semibold"
                  >
                    Clear
                  </button>
                )}
              </div>
              <button
                onClick={() => handleSearch()}
                disabled={loading}
                className="py-3 px-6 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-semibold text-sm tracking-wide disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm flex items-center justify-center gap-2 whitespace-nowrap"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" /> Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" /> Search Patient
                  </>
                )}
              </button>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-600 text-xs flex items-center gap-2 font-medium"
              >
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}

            {/* Quick Select Patients */}
            {patientsList.length > 0 && (
              <div className="mt-5 border-t border-slate-100 pt-4">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest block mb-2.5">
                  Quick Select Patient
                </span>
                <div className="flex flex-wrap gap-2">
                  {patientsList.map((p) => (
                    <button
                      key={p.id}
                      onClick={() => handleSearch(p.id)}
                      className={`text-xs px-3 py-1.5 rounded-lg border transition-all duration-200 text-left font-medium flex items-center gap-2 ${
                        patientId === p.id
                          ? "bg-emerald-50 text-emerald-600 border-emerald-200 shadow-sm"
                          : "bg-white text-slate-600 border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      <User className="w-3.5 h-3.5" />
                      <span>{p.full_name}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({p.id.slice(0, 6)}…)</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Results Cards */}
          <AnimatePresence mode="wait">
            {patient && (
              <motion.div
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -15 }}
                className="grid grid-cols-1 md:grid-cols-2 gap-6"
              >
                {/* Patient Demographics Card */}
                <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm">
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center gap-2">
                      <span className="p-1.5 bg-emerald-50 text-emerald-600 rounded-lg"><User className="w-3.5 h-3.5" /></span>
                      <h4 className="font-outfit font-bold text-sm text-slate-800">Patient Demographics</h4>
                    </div>
                    <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded-full border ${
                      patient.is_active !== false
                        ? "bg-emerald-50 text-emerald-600 border-emerald-100"
                        : "bg-slate-50 text-slate-400 border-slate-200"
                    }`}>
                      {patient.is_active !== false ? "Active" : "Archived"}
                    </span>
                  </div>

                  <div className="space-y-3 text-xs text-slate-600">
                    <div className="flex justify-between items-center py-1 border-b border-slate-100">
                      <span className="text-slate-400 font-medium">Full Name</span>
                      <span className="font-bold text-slate-800">{patient.name}</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-slate-100">
                      <span className="text-slate-400 font-medium">Age / Gender</span>
                      <span className="font-semibold">{patient.age ?? "-"} yrs / {patient.gender ?? "-"}</span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-slate-100">
                      <span className="text-slate-400 font-medium">Village</span>
                      <span className="flex items-center gap-1">
                        <MapPin className="w-3.5 h-3.5 text-slate-400" /> {patient.village ?? "Unknown"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1 border-b border-slate-100">
                      <span className="text-slate-400 font-medium">Contact</span>
                      <span className="flex items-center gap-1 font-mono">
                        <Phone className="w-3.5 h-3.5 text-slate-400" /> {patient.phone ?? "No record"}
                      </span>
                    </div>
                    <div className="flex justify-between items-center py-1">
                      <span className="text-slate-400 font-medium">Patient ID</span>
                      <span className="font-mono text-[9px] text-emerald-600 select-all">{patient.id}</span>
                    </div>
                  </div>
                </div>

                {/* Risk Score + Prescriptions Card */}
                <div className="p-5 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col gap-5">

                  {/* Risk Section */}
                  {risk && (
                    <div>
                      <div className="flex items-center gap-2 mb-3">
                        <span className="p-1.5 bg-amber-50 text-amber-600 rounded-lg"><Heart className="w-3.5 h-3.5" /></span>
                        <h4 className="font-outfit font-bold text-sm text-slate-800">Risk Assessment</h4>
                      </div>

                      <div className="flex items-center gap-4 p-3 rounded-2xl bg-slate-50 border border-slate-100">
                        {/* Circular Gauge */}
                        <div className="relative w-16 h-16 flex items-center justify-center shrink-0">
                          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
                            <circle cx="18" cy="18" r="15" fill="none" stroke="#e2e8f0" strokeWidth="3" />
                            <circle
                              cx="18" cy="18" r="15" fill="none"
                              stroke={getRiskTrackColor(risk.risk_score)}
                              strokeWidth="3"
                              strokeLinecap="round"
                              strokeDasharray={`${(risk.risk_score / 100) * 94.2} 94.2`}
                            />
                          </svg>
                          <div className="absolute text-center">
                            <span className={`text-sm font-bold ${getRiskColor(risk.risk_score)}`}>{risk.risk_score}</span>
                          </div>
                        </div>
                        <div className="space-y-1">
                          <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Risk Level</span>
                          <div className="flex items-center gap-2">
                            <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${getRiskBg(risk.risk_score)}`}>
                              {risk.risk_level}
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Risk Factors */}
                      {risk.risk_factors && Array.isArray(risk.risk_factors) && risk.risk_factors.length > 0 && (
                        <div className="mt-3">
                          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">Risk Factors</span>
                          <div className="flex flex-wrap gap-1.5">
                            {risk.risk_factors.map((factor, i) => (
                              <span key={i} className="text-[10px] font-medium px-2 py-1 bg-amber-50 text-amber-700 border border-amber-100 rounded-md">
                                ⚠️ {factor}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Prescriptions Section */}
                  <div className="flex-1 flex flex-col">
                    <div className="flex items-center gap-2 mb-3">
                      <span className="p-1.5 bg-blue-50 text-blue-600 rounded-lg"><Pill className="w-3.5 h-3.5" /></span>
                      <h4 className="font-outfit font-bold text-sm text-slate-800">
                        Prescriptions ({prescriptions?.total_prescriptions ?? 0})
                      </h4>
                    </div>

                    {prescriptions && Array.isArray(prescriptions.prescriptions) && (prescriptions?.prescriptions?.length ?? 0) > 0 ? (
                      <div className="space-y-2 max-h-[160px] overflow-y-auto pr-1">
                        {prescriptions.prescriptions.slice(0, 3).map((rx, idx) => (
                          <div key={idx} className="p-3 rounded-xl bg-slate-50 border border-slate-100 space-y-1">
                            <div className="flex justify-between items-center text-[11px] font-semibold text-slate-700">
                              <span className="text-emerald-600">{rx.diagnosis ?? "Routine Checkup"}</span>
                              {rx.issue_date && (
                                <span className="text-slate-400 flex items-center gap-1 text-[10px]">
                                  <Calendar className="w-3 h-3" /> {rx.issue_date}
                                </span>
                              )}
                            </div>
                            <p className="text-[10px] text-slate-500 leading-relaxed">
                              {Array.isArray(rx.medicines)
                                ? rx.medicines.map((m: any) => (typeof m === "object" ? m.name : m)).join(", ")
                                : "N/A"}
                            </p>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-6 border border-dashed border-slate-200 rounded-xl bg-slate-50/50">
                        <p className="text-xs text-slate-400 font-medium">No prescription history found</p>
                      </div>
                    )}

                    {prescriptions && Array.isArray(prescriptions.prescriptions) && (prescriptions?.prescriptions?.length ?? 0) > 3 && (
                      <span className="text-[10px] text-slate-400 font-semibold text-right block mt-1.5">
                        + {(prescriptions?.prescriptions?.length ?? 0) - 3} more records
                      </span>
                    )}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* RIGHT: MCP Tools Panel */}
        <div>
          <div className="p-6 rounded-3xl bg-white border border-slate-100 shadow-sm flex flex-col h-full">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
              <h3 className="font-bold font-outfit text-slate-800 flex items-center gap-2">
                <span className="p-2 bg-emerald-50 text-emerald-600 rounded-xl"><Cpu className="w-4 h-4" /></span>
                MCP Tools
              </h3>
              <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            </div>

            <p className="text-xs text-slate-500 mb-4 leading-relaxed">
              Available Model Context Protocol tools. Click a tool to highlight it, then use Patient Lookup to execute.
            </p>

            <div className="space-y-3 flex-1">
              {mcpTools.map((tool) => (
                <div
                  key={tool.name}
                  onClick={() => {
                    setActiveTool(tool.name);
                    if (patient?.id) setPatientId(patient.id);
                  }}
                  className={`p-4 rounded-2xl border text-left cursor-pointer transition-all duration-200 ${
                    activeTool === tool.name
                      ? "bg-emerald-50/50 border-emerald-200 shadow-sm"
                      : "bg-white border-slate-100 hover:border-slate-200 hover:bg-slate-50/50"
                  }`}
                >
                  <div className="flex justify-between items-center mb-1.5">
                    <span className={`text-xs font-bold font-mono ${activeTool === tool.name ? "text-emerald-600" : "text-slate-700"}`}>
                      {tool.name}
                    </span>
                    <span className={`text-[9px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full border ${tool.tagColor}`}>
                      {tool.tag}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 leading-normal mb-2">
                    {tool.description}
                  </p>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-semibold text-slate-400 font-mono">args: {tool.args}</span>
                    <ChevronRight className={`w-3 h-3 ${activeTool === tool.name ? "text-emerald-500" : "text-slate-300"}`} />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-5 p-3 rounded-xl bg-slate-50 border border-slate-100 flex gap-2.5 items-start">
              <Info className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
              <p className="text-[10px] text-slate-500 leading-normal">
                MCP server provides structured context for AI agents. Tools map clinical intents to data endpoints automatically.
              </p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
