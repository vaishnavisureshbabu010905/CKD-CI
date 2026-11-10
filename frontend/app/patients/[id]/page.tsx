"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useApi } from "@/hooks/use-api";
import { useToast } from "@/hooks/use-toast";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";
import {
  ArrowLeft,
  Calendar,
  FileDown,
  User,
  Activity,
  BrainCircuit,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Stethoscope,
  ChevronRight,
  PlusCircle,
  X,
  FileText,
  ShieldAlert,
  ClipboardList,
  FlaskConical,
  Heart,
} from "lucide-react";

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

type TimelineEvent = {
  id: number;
  source_type: string;
  summary?: string;
  event_time: string;
  payload?: Record<string, unknown>;
};

function getAge(dateOfBirth?: string) {
  if (!dateOfBirth) return null;
  const dob = new Date(dateOfBirth);
  if (Number.isNaN(dob.getTime())) return null;
  const today = new Date();
  let age = today.getFullYear() - dob.getFullYear();
  const monthDelta = today.getMonth() - dob.getMonth();
  if (monthDelta < 0 || (monthDelta === 0 && today.getDate() < dob.getDate())) {
    age -= 1;
  }
  return age >= 0 ? age : null;
}

export default function PatientDetailPage({ params }: { params: { id: string } }) {
  const api = useApi();
  const { notify } = useToast();

  const [patient, setPatient] = useState<Patient | null>(null);
  const [history, setHistory] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [showVisitModal, setShowVisitModal] = useState(false);
  const [visitSubmitting, setVisitSubmitting] = useState(false);
  const [visitData, setVisitData] = useState({
    visit_date: new Date().toISOString().split("T")[0],
    eGFR: 48,
    creatinine: 1.8,
    bun: 26,
    uacr: 210,
    systolic_bp: 140,
    bmi: 27.5,
    hemoglobin: 11.5,
    albumin: 3.7,
    hsCRP: 3.2,
    potassium: 4.4,
    phosphate: 4.0,
    calcium: 9.1,
    notes: "Routine nephrology clinical evaluation and lab panel intake.",
  });

  const [showCognitiveModal, setShowCognitiveModal] = useState(false);
  const [cognitiveSubmitting, setCognitiveSubmitting] = useState(false);
  const [cognitiveData, setCognitiveData] = useState({
    assessment_date: new Date().toISOString().split("T")[0],
    moca_score: 24,
    mmse_score: 27,
    dsst_score: 42,
    cerad_score: "Normal delayed recall",
    clinical_outcome: "Mild Cognitive Impairment (MCI)",
    examiner_notes: "Executive dysfunction and mild working memory delay noted on MoCA subtests.",
  });

  const loadPatientData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [patientData, timelineData] = await Promise.all([
        api.get<Patient>(`/patients/${params.id}`),
        api.get<TimelineEvent[]>(`/timeline/${params.id}`),
      ]);
      setPatient(patientData);
      setHistory(timelineData || []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load patient profile");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPatientData();
  }, [api, params.id]);

  if (loading) return <Spinner label="Loading clinical profile..." />;
  if (error) return <ErrorBanner message={error} />;
  if (!patient) return <ErrorBanner message="Patient record not found" />;

  const patientName = `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || "Unregistered Name";
  const age = getAge(patient.date_of_birth);
  const features = patient.features || {};
  const medHistory = (patient.medical_history || {}) as Record<string, unknown>;

  // Read biomarkers from patient features — null means "not on record"
  const egfr = Number(features.egfr ?? features.eGFR ?? null);
  const creatinine = Number(features.creatinine ?? null);
  const bun = Number(features.bun ?? null);
  const uacr = Number(features.uacr ?? null);
  const systolic_bp = Number(features.systolic_bp ?? null);
  const bmi = Number(features.bmi ?? null);
  const hemoglobin = Number(features.hemoglobin ?? null);
  const albumin = Number(features.albumin ?? null);
  const hsCRP = Number(features.hsCRP ?? features.hscrp ?? null);
  const potassium = Number(features.potassium ?? null);
  const phosphate = Number(features.phosphate ?? null);
  const calcium = Number(features.calcium ?? null);

  const fmt = (v: number, decimals = 0) =>
    Number.isFinite(v) && v > 0 ? v.toFixed(decimals) : "—";

  const getUacrStage = (v: number) => {
    if (!Number.isFinite(v) || v <= 0) return "";
    if (v < 30) return "A1 (Normal)";
    if (v < 300) return "A2 (Microalbuminuria)";
    return "A3 (Severe Albuminuria)";
  };

  // CKD Staging
  const getCkdStage = (gfr: number) => {
    if (gfr >= 90) return { stage: "G1", desc: "Normal / High", color: "normal" as const };
    if (gfr >= 60) return { stage: "G2", desc: "Mild Reduction", color: "normal" as const };
    if (gfr >= 45) return { stage: "G3a", desc: "Mild-to-Moderate", color: "moderate" as const };
    if (gfr >= 30) return { stage: "G3b", desc: "Moderate-to-Severe", color: "elevated" as const };
    if (gfr >= 15) return { stage: "G4", desc: "Severe Reduction", color: "critical" as const };
    return { stage: "G5", desc: "Kidney Failure", color: "critical" as const };
  };

  const knownStage = (medHistory.ckd_stage as string) || (Number.isFinite(egfr) && egfr > 0 ? getCkdStage(egfr).stage : "G3a");
  const ckd = getCkdStage(Number.isFinite(egfr) && egfr > 0 ? egfr : 60);

  const downloadReport = async () => {
    setDownloading(true);
    try {
      const blob = await api.download(`/patients/${params.id}/report.pdf`);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `${patient.patient_identifier || `patient-${params.id}`}-clinical-report.pdf`;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to generate report PDF");
    } finally {
      setDownloading(false);
    }
  };

  const handleRecordVisit = async (e: React.FormEvent) => {
    e.preventDefault();
    setVisitSubmitting(true);
    try {
      await api.post(`/patients/${patient.id}/visits`, visitData);
      notify("Clinical visit and laboratory measurements recorded successfully!", "success");
      setShowVisitModal(false);
      loadPatientData();
    } catch (err: unknown) {
      notify(err instanceof Error ? err.message : "Failed to record visit", "error");
    } finally {
      setVisitSubmitting(false);
    }
  };

  const handleRecordCognitive = async (e: React.FormEvent) => {
    e.preventDefault();
    setCognitiveSubmitting(true);
    try {
      await api.post(`/patients/${patient.id}/cognitive-assessments`, cognitiveData);
      notify("Cognitive assessment logged to clinical timeline (isolated from model features)!", "success");
      setShowCognitiveModal(false);
      loadPatientData();
    } catch (err: unknown) {
      notify(err instanceof Error ? err.message : "Failed to log cognitive test", "error");
    } finally {
      setCognitiveSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Back Button & Top Navigation */}
      <div className="flex items-center justify-between border-b border-border pb-4">
        <Link href="/patients" className="inline-flex items-center gap-1.5 text-xs font-medium text-text-muted hover:text-text-primary transition-colors">
          <ArrowLeft className="h-4 w-4" />
          Back to Patient Directory
        </Link>
        <div className="flex flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setShowVisitModal(true)}>
            <Activity className="h-3.5 w-3.5 mr-1 text-clinical-teal" />
            Log Clinical Visit
          </Button>
          <Button variant="outline" size="sm" onClick={() => setShowCognitiveModal(true)}>
            <ClipboardList className="h-3.5 w-3.5 mr-1 text-sky-600" />
            Record Cognitive Test
          </Button>
          <Button variant="outline" size="sm" onClick={downloadReport} disabled={downloading}>
            <FileDown className="h-3.5 w-3.5 mr-1 text-primary" />
            {downloading ? "Exporting..." : "PDF Report"}
          </Button>
          <Link href={`/prediction?patient=${patient.patient_identifier}`}>
            <Button variant="teal" size="sm">
              <BrainCircuit className="h-3.5 w-3.5 mr-1" />
              Assess AI Risk
            </Button>
          </Link>
        </div>
      </div>

      {/* Patient Clinical Profile Header Card */}
      <Card className="border-border shadow-subtle">
        <CardContent className="p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-white shadow-subtle">
                <User className="h-7 w-7 text-teal-300" />
              </div>
              <div>
                <div className="flex items-center gap-2.5">
                  <h1 className="text-2xl font-bold tracking-tight text-primary">{patientName}</h1>
                  <Badge variant={ckd.color}>CKD Stage {knownStage}</Badge>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-xs text-text-muted mt-1">
                  <span>MRN: <strong className="font-mono text-text-primary">{patient.patient_identifier}</strong></span>
                  <span>•</span>
                  <span>Age: <strong className="text-text-primary tabular-nums">{age ?? "N/A"} years</strong></span>
                  <span>•</span>
                  <span>Sex: <strong className="text-text-primary">{patient.sex || "N/A"}</strong></span>
                  <span>•</span>
                  <span>DOB: <strong className="text-text-primary">{patient.date_of_birth || "N/A"}</strong></span>
                </div>
              </div>
            </div>

            {/* Stage Summary Badge */}
            <div className="rounded-xl border border-border bg-surface-subtle p-3 text-right">
              <div className="text-[10px] uppercase font-semibold text-text-muted">Prognosis Classification</div>
              <div className="text-sm font-bold text-primary">{ckd.desc}</div>
              <div className="text-[11px] text-text-muted tabular-nums">eGFR: {fmt(egfr)} mL/min/1.73m²</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Medical History Strip */}
      <Card>
        <CardHeader className="pb-3 bg-surface-subtle/50">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Medical History & Comorbidities</CardTitle>
              <CardDescription>Clinical background recorded once at registration.</CardDescription>
            </div>
            <Badge variant="outline">Permanent Record</Badge>
          </div>
        </CardHeader>
        <CardContent className="pt-4">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4 text-xs">
            {/* Diabetes */}
            <div className="rounded-lg border border-border p-3 bg-surface">
              <span className="text-[10px] text-text-muted font-semibold uppercase block">Diabetes Mellitus</span>
              <span className="font-bold text-sm text-text-primary mt-0.5 block">
                {medHistory.diabetes === "Yes" ? `Yes (${medHistory.diabetes_type || "Type 2"})` : (medHistory.diabetes as string) || "No"}
              </span>
              {medHistory.diabetes === "Yes" && (
                <span className="text-[10px] text-text-muted">
                  Duration: {String(medHistory.diabetes_duration || 0)} yrs
                </span>
              )}
            </div>

            {/* Hypertension */}
            <div className="rounded-lg border border-border p-3 bg-surface">
              <span className="text-[10px] text-text-muted font-semibold uppercase block">Hypertension</span>
              <span className="font-bold text-sm text-text-primary mt-0.5 block">
                {(medHistory.hypertension as string) || "No"}
              </span>
              {medHistory.hypertension === "Yes" && (
                <span className="text-[10px] text-text-muted">
                  Duration: {String(medHistory.hypertension_duration || 0)} yrs
                </span>
              )}
            </div>

            {/* CVD */}
            <div className="rounded-lg border border-border p-3 bg-surface">
              <span className="text-[10px] text-text-muted font-semibold uppercase block">Cardiovascular History</span>
              <span className="font-bold text-sm text-text-primary mt-0.5 block">
                {(medHistory.cvd as string) || "No"}
              </span>
              {Array.isArray(medHistory.cvd_conditions) && medHistory.cvd_conditions.length > 0 && (
                <span className="text-[10px] text-text-muted block truncate" title={medHistory.cvd_conditions.join(", ")}>
                  {medHistory.cvd_conditions.join(", ")}
                </span>
              )}
            </div>

            {/* CKD & Dialysis */}
            <div className="rounded-lg border border-border p-3 bg-surface">
              <span className="text-[10px] text-text-muted font-semibold uppercase block">Dialysis & Duration</span>
              <span className="font-bold text-sm text-text-primary mt-0.5 block">
                {(medHistory.dialysis_status as string) || "Not on dialysis"}
              </span>
              <span className="text-[10px] text-text-muted">
                CKD: {String(medHistory.ckd_duration || 2)} yrs duration
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Grid: Biomarker Telemetry Panel & Clinical Timeline */}
      <div className="grid gap-6 lg:grid-cols-12">
        {/* Left: Recorded Biomarker Telemetry */}
        <div className="space-y-6 lg:col-span-7">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Clinical Visit Measurements</CardTitle>
                <CardDescription>Most recent hospital encounter laboratory values.</CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => setShowVisitModal(true)}>
                  <PlusCircle className="h-3 w-3 mr-1 text-clinical-teal" />
                  New Visit
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {/* Primary 6 Tiles */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                <div className={`rounded-lg border p-3 ${Number.isFinite(egfr) && egfr > 0 && egfr < 60 ? "border-amber-200 bg-amber-50/40" : "border-border bg-surface"}`}>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">eGFR (CKD-EPI)</div>
                  <div className={`text-xl font-bold mt-1 tabular-nums ${Number.isFinite(egfr) && egfr > 0 && egfr < 60 ? "text-risk-moderate" : "text-text-primary"}`}>
                    {fmt(egfr)}
                  </div>
                  <div className="text-[10px] text-text-muted">mL/min/1.73m² · Ref ≥60</div>
                </div>

                <div className={`rounded-lg border p-3 ${Number.isFinite(creatinine) && creatinine > 1.3 ? "border-amber-200 bg-amber-50/40" : "border-border bg-surface"}`}>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">Serum Creatinine</div>
                  <div className="text-xl font-bold text-text-primary mt-1 tabular-nums">{fmt(creatinine, 2)}</div>
                  <div className="text-[10px] text-text-muted">mg/dL · Ref: 0.7 – 1.3</div>
                </div>

                <div className={`rounded-lg border p-3 ${Number.isFinite(bun) && bun > 20 ? "border-amber-200 bg-amber-50/40" : "border-border bg-surface"}`}>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">BUN</div>
                  <div className="text-xl font-bold text-text-primary mt-1 tabular-nums">{fmt(bun)}</div>
                  <div className="text-[10px] text-text-muted">mg/dL · Ref: 7 – 20</div>
                </div>

                <div className={`rounded-lg border p-3 ${Number.isFinite(uacr) && uacr > 30 ? "border-amber-200 bg-amber-50/40" : "border-border bg-surface"}`}>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">UACR (Albuminuria)</div>
                  <div className="text-xl font-bold text-text-primary mt-1 tabular-nums">{fmt(uacr)}</div>
                  <div className="text-[10px] text-text-muted">mg/g · {getUacrStage(uacr) || "—"}</div>
                </div>

                <div className={`rounded-lg border p-3 ${Number.isFinite(systolic_bp) && systolic_bp > 135 ? "border-amber-200 bg-amber-50/40" : "border-border bg-surface"}`}>
                  <div className="text-[10px] text-text-muted uppercase font-semibold">Systolic BP</div>
                  <div className="text-xl font-bold text-text-primary mt-1 tabular-nums">{fmt(systolic_bp)}</div>
                  <div className="text-[10px] text-text-muted">mmHg · Ref: 90 – 130</div>
                </div>

                <div className="rounded-lg border border-border bg-surface p-3">
                  <div className="text-[10px] text-text-muted uppercase font-semibold">BMI</div>
                  <div className="text-xl font-bold text-text-primary mt-1 tabular-nums">{fmt(bmi, 1)}</div>
                  <div className="text-[10px] text-text-muted">kg/m² · Ref: 18.5 – 24.9</div>
                </div>
              </div>

              {/* Additional Metabolic Markers (if available) */}
              <div className="mt-4 pt-3 border-t border-border">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-2">Metabolic & Electrolyte Panel</div>
                <div className="grid grid-cols-3 gap-2.5 sm:grid-cols-6 text-center">
                  <div className="rounded-lg border border-border p-2 bg-surface">
                    <span className="text-[9px] text-text-muted block">Hemoglobin</span>
                    <span className="font-bold text-xs tabular-nums text-text-primary">{fmt(hemoglobin, 1)}</span>
                    <span className="text-[8px] text-text-muted block">g/dL</span>
                  </div>
                  <div className="rounded-lg border border-border p-2 bg-surface">
                    <span className="text-[9px] text-text-muted block">Albumin</span>
                    <span className="font-bold text-xs tabular-nums text-text-primary">{fmt(albumin, 1)}</span>
                    <span className="text-[8px] text-text-muted block">g/dL</span>
                  </div>
                  <div className="rounded-lg border border-border p-2 bg-surface">
                    <span className="text-[9px] text-text-muted block">hsCRP</span>
                    <span className="font-bold text-xs tabular-nums text-text-primary">{fmt(hsCRP, 1)}</span>
                    <span className="text-[8px] text-text-muted block">mg/L</span>
                  </div>
                  <div className="rounded-lg border border-border p-2 bg-surface">
                    <span className="text-[9px] text-text-muted block">Potassium</span>
                    <span className="font-bold text-xs tabular-nums text-text-primary">{fmt(potassium, 1)}</span>
                    <span className="text-[8px] text-text-muted block">mmol/L</span>
                  </div>
                  <div className="rounded-lg border border-border p-2 bg-surface">
                    <span className="text-[9px] text-text-muted block">Phosphate</span>
                    <span className="font-bold text-xs tabular-nums text-text-primary">{fmt(phosphate, 1)}</span>
                    <span className="text-[8px] text-text-muted block">mg/dL</span>
                  </div>
                  <div className="rounded-lg border border-border p-2 bg-surface">
                    <span className="text-[9px] text-text-muted block">Calcium</span>
                    <span className="font-bold text-xs tabular-nums text-text-primary">{fmt(calcium, 1)}</span>
                    <span className="text-[8px] text-text-muted block">mg/dL</span>
                  </div>
                </div>
              </div>

              {/* Protocol Recommendation Banner */}
              <div className="mt-4 rounded-lg border border-teal-200 bg-clinical-teal-light/40 p-3.5">
                <div className="flex items-center gap-2 text-xs font-semibold text-clinical-teal-dark">
                  <Stethoscope className="h-4 w-4" />
                  Clinical Protocol Notice
                </div>
                <p className="mt-1 text-xs text-text-secondary leading-relaxed">
                  Patient exhibits Stage {knownStage} renal insufficiency. Recommend routine Montreal Cognitive Assessment (MoCA) every 6 months to detect early executive cognitive decline.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right: Longitudinal Clinical Timeline */}
        <div className="space-y-6 lg:col-span-5">
          <Card>
            <CardHeader>
              <div>
                <CardTitle>Longitudinal Surveillance Timeline</CardTitle>
                <CardDescription>Chronological visits, assessments & model runs.</CardDescription>
              </div>
              <Clock className="h-4 w-4 text-text-muted" />
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {history.map((h, idx) => {
                  const type = h.source_type.toLowerCase();
                  const isPred = type.includes("prediction");
                  const isAlert = type.includes("alert");
                  const isVisit = type.includes("visit") || type.includes("encounter");
                  const isCognitive = type.includes("cognitive");
                  const isIntake = type.includes("intake") || type.includes("patient");

                  return (
                    <div key={h.id} className="relative flex gap-3 text-xs">
                      {idx !== history.length - 1 && (
                        <span className="absolute left-3.5 top-6 h-full w-px bg-border" />
                      )}
                      <div
                        className={`flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border ${
                          isPred
                            ? "border-teal-200 bg-clinical-teal-light text-clinical-teal"
                            : isAlert
                            ? "border-red-200 bg-red-50 text-risk-critical"
                            : isVisit
                            ? "border-emerald-200 bg-emerald-50 text-emerald-600"
                            : isCognitive
                            ? "border-sky-200 bg-sky-50 text-sky-600"
                            : "border-slate-200 bg-surface-subtle text-text-muted"
                        }`}
                      >
                        {isPred ? (
                          <BrainCircuit className="h-3.5 w-3.5" />
                        ) : isAlert ? (
                          <AlertTriangle className="h-3.5 w-3.5" />
                        ) : isVisit ? (
                          <Activity className="h-3.5 w-3.5" />
                        ) : isCognitive ? (
                          <ClipboardList className="h-3.5 w-3.5" />
                        ) : (
                          <User className="h-3.5 w-3.5" />
                        )}
                      </div>
                      <div className="flex-1 pb-3">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-text-primary capitalize">
                            {isCognitive
                              ? "Cognitive Assessment"
                              : isVisit
                              ? "Clinical Visit Encounter"
                              : isIntake
                              ? "Patient Registration"
                              : h.source_type}
                          </span>
                          <span className="text-[10px] text-text-muted tabular-nums">
                            {new Date(h.event_time).toLocaleDateString()}
                          </span>
                        </div>
                        <div className="text-text-secondary mt-0.5">{h.summary || "Recorded clinical observation"}</div>
                      </div>
                    </div>
                  );
                })}

                {!history.length && (
                  <div className="py-8 text-center text-xs text-text-muted">
                    No surveillance events recorded yet for this profile.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* ════════════════════════════════════════════════════════════════════════
          LOG CLINICAL VISIT MODAL (Every Visit Workflow)
          ════════════════════════════════════════════════════════════════════════ */}
      {showVisitModal && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-xl border border-border bg-surface shadow-modal my-6">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white">
                  <Activity className="h-5 w-5 text-teal-300" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">Log Clinical Encounter / Labs</h3>
                  <p className="text-[11px] text-text-muted">Records fresh laboratory results for {patientName}.</p>
                </div>
              </div>
              <button onClick={() => setShowVisitModal(false)} className="rounded p-1 text-text-muted hover:bg-surface-subtle">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleRecordVisit}>
              <div className="p-6 space-y-4">
                <div>
                  <label className="text-xs font-semibold text-text-primary">Visit Encounter Date</label>
                  <Input
                    type="date"
                    required
                    value={visitData.visit_date}
                    onChange={(e) => setVisitData({ ...visitData, visit_date: e.target.value })}
                    className="mt-1 text-xs"
                  />
                </div>

                {/* Renal Panel */}
                <div className="rounded-lg border border-border bg-surface-subtle p-3 space-y-3">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-clinical-teal">Renal Function Panel</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-text-secondary">eGFR (mL/min)</label>
                      <Input
                        type="number"
                        value={visitData.eGFR}
                        onChange={(e) => setVisitData({ ...visitData, eGFR: parseFloat(e.target.value) || 0 })}
                        className="mt-1 text-xs bg-surface"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-text-secondary">Serum Creatinine (mg/dL)</label>
                      <Input
                        type="number"
                        step="0.1"
                        value={visitData.creatinine}
                        onChange={(e) => setVisitData({ ...visitData, creatinine: parseFloat(e.target.value) || 0 })}
                        className="mt-1 text-xs bg-surface"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-text-secondary">BUN (mg/dL)</label>
                      <Input
                        type="number"
                        value={visitData.bun}
                        onChange={(e) => setVisitData({ ...visitData, bun: parseFloat(e.target.value) || 0 })}
                        className="mt-1 text-xs bg-surface"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-text-secondary">UACR (mg/g)</label>
                      <Input
                        type="number"
                        value={visitData.uacr}
                        onChange={(e) => setVisitData({ ...visitData, uacr: parseFloat(e.target.value) || 0 })}
                        className="mt-1 text-xs bg-surface"
                      />
                    </div>
                  </div>
                </div>

                {/* Vitals & Metabolic */}
                <div className="rounded-lg border border-border bg-surface-subtle p-3 space-y-3">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-clinical-teal">Vitals & Key Markers</div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="text-xs font-medium text-text-secondary">Systolic BP (mmHg)</label>
                      <Input
                        type="number"
                        value={visitData.systolic_bp}
                        onChange={(e) => setVisitData({ ...visitData, systolic_bp: parseFloat(e.target.value) || 0 })}
                        className="mt-1 text-xs bg-surface"
                      />
                    </div>
                    <div>
                      <label className="text-xs font-medium text-text-secondary">BMI (kg/m²)</label>
                      <Input
                        type="number"
                        step="0.1"
                        value={visitData.bmi}
                        onChange={(e) => setVisitData({ ...visitData, bmi: parseFloat(e.target.value) || 0 })}
                        className="mt-1 text-xs bg-surface"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-[10px] font-medium text-text-secondary">Hemoglobin</label>
                      <Input
                        type="number"
                        step="0.1"
                        value={visitData.hemoglobin}
                        onChange={(e) => setVisitData({ ...visitData, hemoglobin: parseFloat(e.target.value) || 0 })}
                        className="mt-0.5 text-xs bg-surface"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-medium text-text-secondary">Albumin</label>
                      <Input
                        type="number"
                        step="0.1"
                        value={visitData.albumin}
                        onChange={(e) => setVisitData({ ...visitData, albumin: parseFloat(e.target.value) || 0 })}
                        className="mt-0.5 text-xs bg-surface"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] font-medium text-text-secondary">hsCRP</label>
                      <Input
                        type="number"
                        step="0.1"
                        value={visitData.hsCRP}
                        onChange={(e) => setVisitData({ ...visitData, hsCRP: parseFloat(e.target.value) || 0 })}
                        className="mt-0.5 text-xs bg-surface"
                      />
                    </div>
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-text-primary">Encounter Notes</label>
                  <Input
                    value={visitData.notes}
                    onChange={(e) => setVisitData({ ...visitData, notes: e.target.value })}
                    className="mt-1 text-xs"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-border px-6 py-4">
                <Button type="button" variant="secondary" size="sm" onClick={() => setShowVisitModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="teal" size="sm" disabled={visitSubmitting}>
                  {visitSubmitting ? <Spinner label="Saving..." /> : "Save Visit Measurements"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════════
          RECORD COGNITIVE ASSESSMENT MODAL (When Assessed Workflow)
          ════════════════════════════════════════════════════════════════════════ */}
      {showCognitiveModal && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-xl border border-border bg-surface shadow-modal my-6">
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-700 text-white">
                  <ClipboardList className="h-5 w-5 text-sky-200" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">Record Cognitive Assessment</h3>
                  <p className="text-[11px] text-text-muted">Formal neurocognitive screening for {patientName}.</p>
                </div>
              </div>
              <button onClick={() => setShowCognitiveModal(false)} className="rounded p-1 text-text-muted hover:bg-surface-subtle">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleRecordCognitive}>
              <div className="p-6 space-y-4">
                {/* Clinical Target Leakage Safeguard Banner */}
                <div className="rounded-lg border border-sky-200 bg-sky-50/60 p-3 text-xs text-sky-900 flex items-start gap-2">
                  <ShieldAlert className="h-4 w-4 text-sky-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold block">Target Leakage Prevention Safeguard</span>
                    <span>These scores establish clinical ground truth and patient surveillance. They are strictly isolated and NOT fed into the predictive AI model as input features.</span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-text-primary">Assessment Date</label>
                    <Input
                      type="date"
                      required
                      value={cognitiveData.assessment_date}
                      onChange={(e) => setCognitiveData({ ...cognitiveData, assessment_date: e.target.value })}
                      className="mt-1 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-text-primary">Clinical Impression</label>
                    <select
                      value={cognitiveData.clinical_outcome}
                      onChange={(e) => setCognitiveData({ ...cognitiveData, clinical_outcome: e.target.value })}
                      className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2.5 text-xs text-text-primary focus:border-clinical-teal focus:outline-none"
                    >
                      <option value="Normal Cognition">Normal Cognition (MoCA ≥26)</option>
                      <option value="Mild Cognitive Impairment (MCI)">Mild Cognitive Impairment (MCI)</option>
                      <option value="Moderate Impairment / Dementia">Moderate Impairment / Dementia</option>
                      <option value="Severe Cognitive Impairment">Severe Cognitive Impairment</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3">
                  <div>
                    <label className="text-xs font-semibold text-text-primary">MoCA Score (/30)</label>
                    <Input
                      type="number"
                      min={0}
                      max={30}
                      value={cognitiveData.moca_score}
                      onChange={(e) => setCognitiveData({ ...cognitiveData, moca_score: parseFloat(e.target.value) || 0 })}
                      className="mt-1 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-text-primary">MMSE Score (/30)</label>
                    <Input
                      type="number"
                      min={0}
                      max={30}
                      value={cognitiveData.mmse_score}
                      onChange={(e) => setCognitiveData({ ...cognitiveData, mmse_score: parseFloat(e.target.value) || 0 })}
                      className="mt-1 text-xs"
                    />
                  </div>
                  <div>
                    <label className="text-xs font-semibold text-text-primary">DSST Score</label>
                    <Input
                      type="number"
                      min={0}
                      max={120}
                      value={cognitiveData.dsst_score}
                      onChange={(e) => setCognitiveData({ ...cognitiveData, dsst_score: parseFloat(e.target.value) || 0 })}
                      className="mt-1 text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-xs font-semibold text-text-primary">CERAD Assessment / Memory Recall</label>
                  <Input
                    placeholder="e.g. Normal delayed recall, Word list 18/30"
                    value={cognitiveData.cerad_score}
                    onChange={(e) => setCognitiveData({ ...cognitiveData, cerad_score: e.target.value })}
                    className="mt-1 text-xs"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-text-primary">Assessor Clinical Observations</label>
                  <Input
                    value={cognitiveData.examiner_notes}
                    onChange={(e) => setCognitiveData({ ...cognitiveData, examiner_notes: e.target.value })}
                    className="mt-1 text-xs"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 border-t border-border px-6 py-4">
                <Button type="button" variant="secondary" size="sm" onClick={() => setShowCognitiveModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="teal" size="sm" disabled={cognitiveSubmitting}>
                  {cognitiveSubmitting ? <Spinner label="Saving..." /> : "Save Cognitive Assessment"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
