"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { SummaryCards } from "@/components/sections/summary-cards";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useApi } from "@/hooks/use-api";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";
import {
  Bell,
  CheckCircle2,
  Clock,
  ExternalLink,
  ShieldAlert,
  AlertTriangle,
  BrainCircuit,
  Activity,
  User,
  FlaskConical,
  ChevronRight,
  TrendingDown,
  Stethoscope,
  HeartPulse,
  Sparkles,
  ClipboardList,
} from "lucide-react";

type AlertEvent = {
  id: number;
  status: string;
  patient_id?: number;
  payload?: Record<string, unknown>;
  created_at?: string;
};

type Task = {
  id: number;
  title: string;
  status: string;
  priority?: string;
  patient_id?: number;
};

type Patient = {
  id: number;
  patient_identifier: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  sex?: string;
  medical_history?: Record<string, unknown>;
  features?: Record<string, unknown>;
};

type PredictionHistory = {
  id: number;
  patient_id?: number;
  model_version?: string;
  predicted_label?: string;
  confidence?: number;
  probabilities?: Record<string, number>;
  created_at?: string;
};

function getCkdStage(egfr: number): { stage: string; desc: string; rank: number } {
  if (egfr >= 90) return { stage: "G1", desc: "Normal / High (≥90)", rank: 1 };
  if (egfr >= 60) return { stage: "G2", desc: "Mild Reduction (60–89)", rank: 2 };
  if (egfr >= 45) return { stage: "G3a", desc: "Mild-to-Mod (45–59)", rank: 3 };
  if (egfr >= 30) return { stage: "G3b", desc: "Mod-to-Severe (30–44)", rank: 4 };
  if (egfr >= 15) return { stage: "G4", desc: "Severe (15–29)", rank: 5 };
  return { stage: "G5", desc: "Kidney Failure (<15)", rank: 6 };
}

function getUacrStage(uacr: number): "A1" | "A2" | "A3" {
  if (uacr > 300) return "A3";
  if (uacr >= 30) return "A2";
  return "A1";
}

export default function CommandCenterPage() {
  const api = useApi();
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [predictions, setPredictions] = useState<PredictionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      setLoading(true);
      setError(null);
      try {
        const [alertData, taskData, patientData, predictionData] = await Promise.allSettled([
          api.get<AlertEvent[]>("/alerts/events"),
          api.get<Task[]>("/collab/tasks"),
          api.get<Patient[]>("/patients/"),
          api.get<PredictionHistory[]>("/predictions/history"),
        ]);
        if (mounted) {
          setAlerts(alertData.status === "fulfilled" ? alertData.value || [] : []);
          setTasks(taskData.status === "fulfilled" ? taskData.value || [] : []);
          setPatients(patientData.status === "fulfilled" ? patientData.value || [] : []);
          setPredictions(predictionData.status === "fulfilled" ? predictionData.value || [] : []);
        }
      } catch (e: unknown) {
        const err = e as Error;
        if (mounted) setError(err.message || "Failed to load command center data");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [api]);

  // Latest prediction per patient
  const latestPredByPatient = useMemo(() => {
    const map = new Map<number, PredictionHistory>();
    for (const p of predictions) {
      if (!p.patient_id) continue;
      const existing = map.get(p.patient_id);
      if (!existing || new Date(p.created_at || 0).getTime() > new Date(existing.created_at || 0).getTime()) {
        map.set(p.patient_id, p);
      }
    }
    return map;
  }, [predictions]);

  // Aggregate Patient Clinical Problems Across Cohort
  const clinicalProblemStats = useMemo(() => {
    let highCognitiveRisk = 0;
    let moderateCognitiveRisk = 0;
    let severeRenalImpairment = 0; // eGFR < 30 (G4-G5)
    let severeAlbuminuria = 0; // UACR > 300 (A3)
    let diabeticNephropathy = 0;
    let vascularRisk = 0;

    for (const p of patients) {
      const pred = latestPredByPatient.get(p.id);
      const label = (pred?.predicted_label || "").toLowerCase();
      if (label.includes("high")) highCognitiveRisk++;
      else if (label.includes("moderate")) moderateCognitiveRisk++;

      const f = p.features || {};
      const egfr = Number(f.egfr ?? f.eGFR ?? 0);
      const uacr = Number(f.uacr ?? 0);
      if (egfr > 0 && egfr < 30) severeRenalImpairment++;
      if (uacr > 300) severeAlbuminuria++;

      const med = (p.medical_history || {}) as Record<string, unknown>;
      if (med.diabetes === "Yes" || f.diabetes === 1) diabeticNephropathy++;
      if (med.cvd === "Yes" || f.cvd === 1 || med.hypertension === "Yes" || f.hypertension === 1) vascularRisk++;
    }

    return {
      highCognitiveRisk,
      moderateCognitiveRisk,
      severeRenalImpairment,
      severeAlbuminuria,
      diabeticNephropathy,
      vascularRisk,
    };
  }, [patients, latestPredByPatient]);

  // Map Patients Into KDIGO Matrix Cells (Live cohort mapping)
  const kdigoMatrix = useMemo(() => {
    // 6 rows (G1, G2, G3a, G3b, G4, G5) x 3 cols (A1, A2, A3)
    const stages = ["G1", "G2", "G3a", "G3b", "G4", "G5"];
    const cats: ("A1" | "A2" | "A3")[] = ["A1", "A2", "A3"];

    const cellPatients: Record<string, Patient[]> = {};
    for (const s of stages) {
      for (const c of cats) {
        cellPatients[`${s}_${c}`] = [];
      }
    }

    for (const p of patients) {
      const f = p.features || {};
      const egfr = Number(f.egfr ?? f.eGFR ?? 0);
      const uacr = Number(f.uacr ?? 0);
      if (egfr > 0) {
        const stage = getCkdStage(egfr).stage;
        const cat = getUacrStage(uacr);
        const key = `${stage}_${cat}`;
        if (cellPatients[key]) {
          cellPatients[key].push(p);
        }
      }
    }

    return cellPatients;
  }, [patients]);

  return (
    <div className="space-y-6">
      {/* Top Hero KPI Summary Cards */}
      <SummaryCards
        patientCount={patients.length}
        alertCount={alerts.filter((a) => a.status === "open").length}
        taskCount={tasks.filter((t) => t.status !== "done").length}
        predictionCount={predictions.length}
      />

      {loading && <Spinner label="Loading clinical overview telemetry..." />}
      {error && <ErrorBanner message={error} />}

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 1: CLINICAL PROBLEMS AT SCALE (COHORT VULNERABILITY RADAR)
          ────────────────────────────────────────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-primary">Patient Problems & Risk Distribution (Cohort Scale)</h2>
            <p className="text-xs text-text-muted">Real-time clinical vulnerability breakdown across all enrolled patients.</p>
          </div>
          <span className="rounded bg-surface-subtle px-2.5 py-1 text-xs font-semibold text-text-secondary tabular-nums">
            N = {patients.length} Monitored Patients
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          {/* Problem 1: High Cognitive Impairment Risk */}
          <div className="rounded-xl border border-red-200 bg-red-50/40 p-3.5 space-y-1 shadow-subtle">
            <div className="flex items-center justify-between text-xs text-risk-critical font-semibold">
              <span>Cognitive Vulnerability</span>
              <BrainCircuit className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold text-risk-critical tabular-nums">
              {clinicalProblemStats.highCognitiveRisk}
            </div>
            <div className="text-[11px] text-red-700">
              High Risk ({Math.round((clinicalProblemStats.highCognitiveRisk / Math.max(1, patients.length)) * 100)}%)
            </div>
          </div>

          {/* Problem 2: Moderate Cognitive Risk */}
          <div className="rounded-xl border border-amber-200 bg-amber-50/40 p-3.5 space-y-1 shadow-subtle">
            <div className="flex items-center justify-between text-xs text-risk-moderate font-semibold">
              <span>Moderate Impairment</span>
              <Activity className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold text-risk-moderate tabular-nums">
              {clinicalProblemStats.moderateCognitiveRisk}
            </div>
            <div className="text-[11px] text-amber-700">
              MoCA Surveillance Req.
            </div>
          </div>

          {/* Problem 3: Advanced Renal Failure (G4-G5) */}
          <div className="rounded-xl border border-orange-200 bg-orange-50/40 p-3.5 space-y-1 shadow-subtle">
            <div className="flex items-center justify-between text-xs text-orange-800 font-semibold">
              <span>Stage G4–G5 Failure</span>
              <FlaskConical className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold text-orange-950 tabular-nums">
              {clinicalProblemStats.severeRenalImpairment}
            </div>
            <div className="text-[11px] text-orange-800">
              eGFR &lt; 30 mL/min
            </div>
          </div>

          {/* Problem 4: Severe Albuminuria (A3) */}
          <div className="rounded-xl border border-rose-200 bg-rose-50/40 p-3.5 space-y-1 shadow-subtle">
            <div className="flex items-center justify-between text-xs text-rose-800 font-semibold">
              <span>Severe Albuminuria (A3)</span>
              <TrendingDown className="h-4 w-4" />
            </div>
            <div className="text-2xl font-bold text-rose-950 tabular-nums">
              {clinicalProblemStats.severeAlbuminuria}
            </div>
            <div className="text-[11px] text-rose-800">
              UACR &gt; 300 mg/g
            </div>
          </div>

          {/* Problem 5: Diabetic Nephropathy */}
          <div className="rounded-xl border border-border bg-surface p-3.5 space-y-1 shadow-subtle">
            <div className="flex items-center justify-between text-xs text-text-muted font-semibold">
              <span>Diabetic Comorbidity</span>
              <Stethoscope className="h-4 w-4 text-clinical-teal" />
            </div>
            <div className="text-2xl font-bold text-primary tabular-nums">
              {clinicalProblemStats.diabeticNephropathy}
            </div>
            <div className="text-[11px] text-text-muted">
              Diabetic Nephropathy
            </div>
          </div>

          {/* Problem 6: Vascular Risk Exposure */}
          <div className="rounded-xl border border-border bg-surface p-3.5 space-y-1 shadow-subtle">
            <div className="flex items-center justify-between text-xs text-text-muted font-semibold">
              <span>Vascular Triad Burden</span>
              <HeartPulse className="h-4 w-4 text-sky-600" />
            </div>
            <div className="text-2xl font-bold text-primary tabular-nums">
              {clinicalProblemStats.vascularRisk}
            </div>
            <div className="text-[11px] text-text-muted">
              HTN / CAD / Stroke
            </div>
          </div>
        </div>
      </div>

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 2: ACTIONABLE PATIENT CLINICAL PROBLEM TRIAGE QUEUE
          Addressing individual patient problems directly on the overall scale
          ────────────────────────────────────────────────────────────────────────── */}
      <Card className="border-border shadow-subtle">
        <CardHeader className="bg-surface-subtle/50 pb-3 border-b border-border">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle>Cohort Clinical Problem Triage Queue</CardTitle>
              <CardDescription>
                Detailed patient-by-patient telemetry, identified clinical problems, and recommended care protocols.
              </CardDescription>
            </div>
            <Link href="/patients">
              <Button variant="outline" size="sm" className="text-xs">
                Patient Cohort Directory ({patients.length})
              </Button>
            </Link>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border bg-surface-subtle text-[11px] font-semibold text-text-muted uppercase">
                  <th className="py-3 px-4">Patient Profile</th>
                  <th className="py-3 px-3">Renal Telemetry</th>
                  <th className="py-3 px-3">Albuminuria (UACR)</th>
                  <th className="py-3 px-3">Clinical Problems Identified</th>
                  <th className="py-3 px-3">AI Cognitive Stratification</th>
                  <th className="py-3 px-3">Protocol Action</th>
                  <th className="py-3 px-4 text-right">Intervention</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {patients.map((p) => {
                  const f = p.features || {};
                  const egfr = Number(f.egfr ?? f.eGFR ?? 0);
                  const creatinine = Number(f.creatinine ?? 0);
                  const uacr = Number(f.uacr ?? 0);
                  const pred = latestPredByPatient.get(p.id);
                  const predLabel = pred?.predicted_label || "Awaiting Assessment";
                  const isHighRisk = predLabel.toLowerCase().includes("high");
                  const isModRisk = predLabel.toLowerCase().includes("moderate");
                  const isLowRisk = predLabel.toLowerCase().includes("low");

                  const med = (p.medical_history || {}) as Record<string, unknown>;
                  const ckd = getCkdStage(egfr);

                  // Detect problems for this specific patient
                  const problems: string[] = [];
                  if (egfr > 0 && egfr < 30) problems.push("Severe G4/G5 Failure");
                  else if (egfr > 0 && egfr < 60) problems.push("Moderate CKD (G3)");
                  if (uacr > 300) problems.push("Severe Albuminuria (A3)");
                  else if (uacr >= 30) problems.push("Microalbuminuria (A2)");
                  if (med.diabetes === "Yes" || f.diabetes === 1) problems.push("Diabetic Nephropathy");
                  if (med.hypertension === "Yes" || f.hypertension === 1) problems.push("Hypertension");
                  if (med.cvd === "Yes" || f.cvd === 1) problems.push("Cardiovascular History");
                  if (isHighRisk) problems.push("Critical Cognitive Risk");

                  // Protocol recommendation based on actual problems
                  let recommendedAction = "Routine Annual Surveillance";
                  if (isHighRisk || egfr < 30) {
                    recommendedAction = "Immediate MoCA & Nephrology Consult";
                  } else if (isModRisk || uacr > 300) {
                    recommendedAction = "Schedule 6-Month MoCA & Optimize SGLT2i";
                  } else if (egfr < 60) {
                    recommendedAction = "Monitor Clearance & Medication Review";
                  }

                  return (
                    <tr key={p.id} className="hover:bg-surface-subtle/60 transition-colors">
                      <td className="py-3 px-4">
                        <Link href={`/patients/${p.id}`} className="group block">
                          <div className="font-bold text-text-primary group-hover:text-clinical-teal transition-colors">
                            {p.first_name || ""} {p.last_name || "Unregistered"}
                          </div>
                          <div className="text-[10px] text-text-muted font-mono mt-0.5">
                            MRN: {p.patient_identifier} • {p.sex || "N/A"}
                          </div>
                        </Link>
                      </td>

                      <td className="py-3 px-3">
                        <div className="font-bold tabular-nums text-text-primary">
                          {egfr > 0 ? `${egfr.toFixed(0)} mL/min` : "—"}
                        </div>
                        <div className="text-[10px] text-text-muted">
                          Cr: {creatinine > 0 ? creatinine.toFixed(2) : "—"} mg/dL • Stage {ckd.stage}
                        </div>
                      </td>

                      <td className="py-3 px-3">
                        <div className="font-bold tabular-nums text-text-primary">
                          {uacr > 0 ? `${uacr.toFixed(0)} mg/g` : "—"}
                        </div>
                        <div className="text-[10px] text-text-muted">
                          {uacr > 300 ? (
                            <span className="text-risk-critical font-medium">Stage A3 (Severe)</span>
                          ) : uacr >= 30 ? (
                            <span className="text-risk-moderate font-medium">Stage A2 (Micro)</span>
                          ) : (
                            <span className="text-risk-normal font-medium">Stage A1 (Normal)</span>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-3 max-w-xs">
                        <div className="flex flex-wrap gap-1">
                          {problems.slice(0, 3).map((prob) => (
                            <span
                              key={prob}
                              className={`rounded px-1.5 py-0.5 text-[9px] font-semibold ${
                                prob.includes("Critical") || prob.includes("Severe")
                                  ? "bg-red-50 text-risk-critical border border-red-200"
                                  : prob.includes("Moderate") || prob.includes("Micro")
                                  ? "bg-amber-50 text-risk-moderate border border-amber-200"
                                  : "bg-surface-subtle text-text-secondary border border-border"
                              }`}
                            >
                              {prob}
                            </span>
                          ))}
                          {problems.length > 3 && (
                            <span className="text-[10px] text-text-muted font-medium">+{problems.length - 3} more</span>
                          )}
                        </div>
                      </td>

                      <td className="py-3 px-3">
                        {isHighRisk && <Badge variant="critical">High Risk</Badge>}
                        {isModRisk && <Badge variant="elevated">Moderate Risk</Badge>}
                        {isLowRisk && <Badge variant="normal">Low Risk</Badge>}
                        {!pred && <Badge variant="default">Awaiting CDS</Badge>}
                        {pred?.confidence && (
                          <div className="text-[10px] text-text-muted font-mono mt-0.5 tabular-nums">
                            Conf: {Math.round(pred.confidence * 100)}%
                          </div>
                        )}
                      </td>

                      <td className="py-3 px-3">
                        <span className="text-text-primary font-medium text-[11px] block">
                          {recommendedAction}
                        </span>
                      </td>

                      <td className="py-3 px-4 text-right">
                        <div className="flex items-center justify-end gap-1.5">
                          <Link href={`/prediction?patient=${p.patient_identifier}`}>
                            <Button variant="teal" size="sm" className="h-7 text-[11px]">
                              Assess
                            </Button>
                          </Link>
                          <Link href={`/patients/${p.id}`}>
                            <Button variant="outline" size="sm" className="h-7 text-[11px]">
                              Profile
                            </Button>
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 3: LIVE COHORT PROGNOSIS MATRIX (POPULATED KDIGO HEATMAP)
          Maps real patients into their corresponding grid cells
          ────────────────────────────────────────────────────────────────────────── */}
      <Card className="border-border shadow-subtle">
        <CardHeader className="bg-surface-subtle/50 pb-3 border-b border-border">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-2">
                <CardTitle>Cohort KDIGO Clinical Prognosis Distribution</CardTitle>
                <Badge variant="teal">Live Cohort Map</Badge>
              </div>
              <CardDescription>
                Visual distribution of all active cohort patients mapped across eGFR decline stages and persistent albuminuria tiers.
              </CardDescription>
            </div>

            <div className="flex items-center gap-3 text-xs">
              <span className="inline-flex items-center gap-1.5 text-text-secondary">
                <span className="h-2 w-2 rounded-full bg-emerald-500" /> Low Risk
              </span>
              <span className="inline-flex items-center gap-1.5 text-text-secondary">
                <span className="h-2 w-2 rounded-full bg-amber-500" /> Moderate Risk
              </span>
              <span className="inline-flex items-center gap-1.5 text-text-secondary">
                <span className="h-2 w-2 rounded-full bg-orange-500" /> High Risk
              </span>
              <span className="inline-flex items-center gap-1.5 text-text-secondary">
                <span className="h-2 w-2 rounded-full bg-red-600" /> Very High Risk
              </span>
            </div>
          </div>
        </CardHeader>

        <CardContent className="pt-4">
          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead>
                <tr className="border-b border-border bg-surface-subtle">
                  <th className="p-3 font-semibold text-text-primary w-44">eGFR Stage</th>
                  <th className="p-3 font-semibold text-text-primary text-center">
                    A1: Normal to Mild (&lt;30 mg/g)
                  </th>
                  <th className="p-3 font-semibold text-text-primary text-center">
                    A2: Moderate (30–300 mg/g)
                  </th>
                  <th className="p-3 font-semibold text-text-primary text-center">
                    A3: Severe (&gt;300 mg/g)
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {[
                  { stage: "G1", label: "Normal (≥90)", riskA1: "Low", riskA2: "Moderate", riskA3: "High" },
                  { stage: "G2", label: "Mild (60–89)", riskA1: "Low", riskA2: "Moderate", riskA3: "High" },
                  { stage: "G3a", label: "Mild-Mod (45–59)", riskA1: "Moderate", riskA2: "High", riskA3: "Very High" },
                  { stage: "G3b", label: "Mod-Severe (30–44)", riskA1: "Moderate", riskA2: "Very High", riskA3: "Very High" },
                  { stage: "G4", label: "Severe (15–29)", riskA1: "High", riskA2: "Very High", riskA3: "Very High" },
                  { stage: "G5", label: "Kidney Failure (<15)", riskA1: "Very High", riskA2: "Very High", riskA3: "Very High" },
                ].map((row) => (
                  <tr key={row.stage} className="hover:bg-surface-subtle/50 transition-colors">
                    <td className="p-3 font-medium text-text-primary whitespace-nowrap bg-surface-subtle/30">
                      <span className="font-bold text-primary mr-1.5">{row.stage}</span>
                      <span className="text-[11px] text-text-muted">{row.label}</span>
                    </td>

                    {/* A1 Cell */}
                    {(["A1", "A2", "A3"] as const).map((cat) => {
                      const cellKey = `${row.stage}_${cat}`;
                      const cellPatients = kdigoMatrix[cellKey] || [];
                      const hasPatients = cellPatients.length > 0;
                      const riskLevel = cat === "A1" ? row.riskA1 : cat === "A2" ? row.riskA2 : row.riskA3;

                      const bgBadge =
                        riskLevel === "Very High"
                          ? "bg-red-100 text-red-950 border-red-300"
                          : riskLevel === "High"
                          ? "bg-orange-100 text-orange-950 border-orange-300"
                          : riskLevel === "Moderate"
                          ? "bg-amber-100 text-amber-950 border-amber-300"
                          : "bg-emerald-100 text-emerald-950 border-emerald-300";

                      return (
                        <td key={cat} className="p-2 text-center align-top">
                          <div
                            className={`rounded-lg border p-2 min-h-[58px] transition-all ${
                              hasPatients
                                ? "ring-2 ring-clinical-teal bg-surface shadow-subtle"
                                : "bg-surface-subtle/40 border-border/70 opacity-70"
                            }`}
                          >
                            <div className="flex items-center justify-between text-[10px]">
                              <span className={`rounded px-1.5 py-0.2 font-semibold text-[9px] border ${bgBadge}`}>
                                {riskLevel}
                              </span>
                              <span className="font-bold text-text-primary tabular-nums">
                                {cellPatients.length} Pt{cellPatients.length === 1 ? "" : "s"}
                              </span>
                            </div>

                            {/* Patient names mapped inside the cell */}
                            {hasPatients && (
                              <div className="mt-1.5 space-y-1 text-left">
                                {cellPatients.map((cp) => (
                                  <Link
                                    key={cp.id}
                                    href={`/patients/${cp.id}`}
                                    className="block rounded bg-clinical-teal-light/40 px-1.5 py-0.5 text-[10px] font-semibold text-clinical-teal-dark hover:bg-clinical-teal hover:text-white transition-colors truncate"
                                    title={`${cp.first_name || ""} ${cp.last_name || ""} (${cp.patient_identifier})`}
                                  >
                                    {cp.first_name || ""} {cp.last_name || cp.patient_identifier}
                                  </Link>
                                ))}
                              </div>
                            )}

                            {!hasPatients && (
                              <span className="text-[10px] text-text-muted mt-2 block font-mono">—</span>
                            )}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="mt-3 flex items-center justify-between text-[11px] text-text-muted border-t border-border pt-2.5">
            <span>KDIGO 2024 Clinical Practice Guideline for Evaluation and Management of Chronic Kidney Disease.</span>
            <span className="text-clinical-teal font-medium">Mapped live against active clinical patient cohort.</span>
          </div>
        </CardContent>
      </Card>

      {/* ──────────────────────────────────────────────────────────────────────────
          SECTION 4: ACTIVE SURVEILLANCE ALERTS & CARE COORDINATION TASKS
          ────────────────────────────────────────────────────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Left: Active Clinical Alerts */}
        <div className="space-y-4 lg:col-span-7">
          <Card className="border-border shadow-subtle">
            <CardHeader className="bg-surface-subtle/50 pb-3 border-b border-border">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Live Clinical Surveillance Alerts</CardTitle>
                  <CardDescription>Real-time telemetry violations requiring immediate provider intervention.</CardDescription>
                </div>
                <Link href="/alerts">
                  <Badge variant="critical">
                    {alerts.filter((a) => a.status === "open").length} Urgent
                  </Badge>
                </Link>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {alerts.slice(0, 4).map((a) => (
                <div
                  key={a.id}
                  className={`flex items-center justify-between rounded-lg border p-3 transition-colors ${
                    a.status === "open"
                      ? "border-red-200 bg-red-50/50"
                      : "border-border bg-surface"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-4 w-4 text-risk-critical flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-xs font-semibold text-text-primary">
                        {String(a.payload?.message || a.payload?.detail || `Alert #${a.id}`)}
                      </div>
                      <div className="text-[10px] text-text-muted mt-0.5">
                        Status: <strong className="uppercase">{a.status}</strong> • Triggered: {a.created_at ? new Date(a.created_at).toLocaleDateString() : "Recent"}
                      </div>
                    </div>
                  </div>

                  <Link href="/alerts">
                    <Button variant="outline" size="sm" className="text-xs h-7">
                      Triage Alert
                    </Button>
                  </Link>
                </div>
              ))}

              {!alerts.length && !loading && (
                <div className="py-6 text-center text-xs text-text-muted">
                  No active clinical threshold escalations at this time.
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right: Care Coordination Tasks */}
        <div className="space-y-4 lg:col-span-5">
          <Card className="border-border shadow-subtle">
            <CardHeader className="bg-surface-subtle/50 pb-3 border-b border-border">
              <div>
                <CardTitle>Care Coordination & Tasks</CardTitle>
                <CardDescription>Scheduled cognitive evaluations and nephrology follow-ups.</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="pt-4 space-y-3">
              {tasks.slice(0, 4).map((t) => (
                <div
                  key={t.id}
                  className="flex items-center justify-between rounded-lg border border-border bg-surface p-3"
                >
                  <div className="flex items-start gap-2.5">
                    <Clock className="h-4 w-4 text-clinical-teal flex-shrink-0 mt-0.5" />
                    <div>
                      <div className="text-xs font-semibold text-text-primary">{t.title}</div>
                      <div className="text-[10px] text-text-muted mt-0.5">Assigned to Nephrology Team</div>
                    </div>
                  </div>
                  <Badge variant={t.status === "done" ? "normal" : "moderate"}>
                    {t.status}
                  </Badge>
                </div>
              ))}

              {!tasks.length && !loading && (
                <div className="py-6 text-center text-xs text-text-muted">No pending care tasks assigned.</div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
