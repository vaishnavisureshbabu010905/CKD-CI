"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useApi } from "@/hooks/use-api";
import { useToast } from "@/hooks/use-toast";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";
import {
  Users,
  Search,
  BrainCircuit,
  ChevronRight,
  UserPlus,
  X,
  Activity,
  FlaskConical,
  Heart,
  Calendar,
  CheckCircle2,
  Stethoscope,
  ShieldCheck,
  ChevronLeft,
  FileText,
  AlertCircle,
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

type PredictionHistory = {
  id: number;
  patient_id?: number;
  predicted_label?: string;
  probabilities?: Record<string, number>;
  confidence?: number;
  created_at?: string;
};

type RiskFilter = "all" | "high" | "moderate" | "low" | "unknown";

function calculateAge(dateOfBirth?: string): number | null {
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

function normalizeRisk(value?: string): "high" | "moderate" | "low" | "unknown" {
  const label = (value || "").toLowerCase();
  if (label.includes("high")) return "high";
  if (label.includes("moderate")) return "moderate";
  if (label.includes("low")) return "low";
  return "unknown";
}

function valueAsNumber(v: unknown, fallback = 0) {
  const n = Number(v);
  return Number.isFinite(n) ? n : fallback;
}

const EDUCATION_LEVEL_MAP: { label: string; defaultYears: number }[] = [
  { label: "No formal education", defaultYears: 0 },
  { label: "Primary education", defaultYears: 5 },
  { label: "Secondary education", defaultYears: 10 },
  { label: "Higher secondary", defaultYears: 12 },
  { label: "Undergraduate / Graduate", defaultYears: 16 },
  { label: "Postgraduate or above", defaultYears: 18 },
];

const CVD_CONDITIONS = [
  "Coronary artery disease (CAD)",
  "Previous stroke",
  "Heart failure",
  "Other cardiovascular condition",
];

type Step = 1 | 2 | 3;

export default function PatientsPage() {
  const api = useApi();
  const { notify } = useToast();

  const [patients, setPatients] = useState<Patient[]>([]);
  const [predictions, setPredictions] = useState<PredictionHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [sortBy, setSortBy] = useState<"name" | "age" | "risk">("name");

  // Multi-step Registration Modal State
  const [showAddModal, setShowAddModal] = useState(false);
  const [currentStep, setCurrentStep] = useState<Step>(1);
  const [submitting, setSubmitting] = useState(false);

  // Step 1: Patient Profile
  const [profile, setProfile] = useState({
    patient_identifier: "",
    first_name: "",
    last_name: "",
    date_of_birth: "1960-05-15",
    sex: "Male",
    education_level: "Higher secondary",
    education_years: 12,
  });

  // Step 2: Medical History
  const [history, setHistory] = useState({
    diabetes: "No" as "No" | "Yes" | "Unknown",
    diabetes_type: "Type 2" as "Type 1" | "Type 2" | "Other / unspecified",
    diabetes_duration: 0,
    hypertension: "No" as "No" | "Yes" | "Unknown",
    hypertension_duration: 0,
    cvd: "No" as "No" | "Yes" | "Unknown",
    cvd_conditions: [] as string[],
    ckd_diagnosis: "Yes" as "Yes" | "No" | "Unknown",
    ckd_stage: "G3a" as "G1" | "G2" | "G3a" | "G3b" | "G4" | "G5" | "Not recorded",
    ckd_duration: 2,
    dialysis_status: "Not on dialysis" as "Not on dialysis" | "Hemodialysis" | "Peritoneal dialysis" | "Kidney transplant" | "Unknown",
  });

  // Step 3: Optional Baseline Measurements (Recorded at visit 1 if available)
  const [hasBaselineLabs, setHasBaselineLabs] = useState(true);
  const [baselineLabs, setBaselineLabs] = useState({
    eGFR: 52,
    creatinine: 1.6,
    bun: 24,
    uacr: 180,
    systolic_bp: 135,
    bmi: 27.0,
    hemoglobin: 12.0,
    albumin: 3.8,
    hsCRP: 2.2,
    potassium: 4.3,
    phosphate: 3.8,
    calcium: 9.2,
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [patientsData, predictionsData] = await Promise.all([
        api.get<Patient[]>("/patients/"),
        api.get<PredictionHistory[]>("/predictions/history"),
      ]);
      setPatients(patientsData || []);
      setPredictions(predictionsData || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load patient records");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [api]);

  const latestPredictionByPatient = useMemo(() => {
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

  const riskCounts = useMemo(() => {
    const counts = { high: 0, moderate: 0, low: 0, unknown: 0 };
    for (const p of patients) {
      const risk = normalizeRisk(latestPredictionByPatient.get(p.id)?.predicted_label);
      counts[risk] += 1;
    }
    return counts;
  }, [patients, latestPredictionByPatient]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    let list = patients.filter((p) => {
      const name = `${p.first_name || ""} ${p.last_name || ""}`.trim().toLowerCase();
      const matches = !q || p.patient_identifier.toLowerCase().includes(q) || name.includes(q);
      if (!matches) return false;

      if (riskFilter === "all") return true;
      const pred = latestPredictionByPatient.get(p.id);
      return normalizeRisk(pred?.predicted_label) === riskFilter;
    });

    if (sortBy === "age") {
      list = [...list].sort((a, b) => (calculateAge(b.date_of_birth) || -1) - (calculateAge(a.date_of_birth) || -1));
    } else if (sortBy === "risk") {
      const rank: Record<RiskFilter, number> = { high: 4, moderate: 3, low: 2, unknown: 1, all: 0 };
      list = [...list].sort((a, b) => {
        const ar = rank[normalizeRisk(latestPredictionByPatient.get(a.id)?.predicted_label)];
        const br = rank[normalizeRisk(latestPredictionByPatient.get(b.id)?.predicted_label)];
        return br - ar;
      });
    } else {
      list = [...list].sort((a, b) => {
        const an = `${a.first_name || ""} ${a.last_name || ""}`.trim().toLowerCase();
        const bn = `${b.first_name || ""} ${b.last_name || ""}`.trim().toLowerCase();
        return an.localeCompare(bn);
      });
    }
    return list;
  }, [patients, query, riskFilter, sortBy, latestPredictionByPatient]);

  // Handle Education Level change & automatically derive completed years
  const handleEducationChange = (lvl: string) => {
    const found = EDUCATION_LEVEL_MAP.find((e) => e.label === lvl);
    setProfile((prev) => ({
      ...prev,
      education_level: lvl,
      education_years: found ? found.defaultYears : prev.education_years,
    }));
  };

  // Toggle CVD condition in multiselect
  const toggleCvdCondition = (cond: string) => {
    setHistory((prev) => {
      const exists = prev.cvd_conditions.includes(cond);
      return {
        ...prev,
        cvd_conditions: exists
          ? prev.cvd_conditions.filter((c) => c !== cond)
          : [...prev.cvd_conditions, cond],
      };
    });
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profile.patient_identifier.trim()) {
      notify("Medical Record Number (MRN) is required.", "error");
      setCurrentStep(1);
      return;
    }

    setSubmitting(true);
    try {
      const calculatedAge = calculateAge(profile.date_of_birth) ?? 60;
      const genderBinary = profile.sex === "Female" ? 0 : 1;
      const diabetesBinary = history.diabetes === "Yes" ? 1 : 0;
      const hypertensionBinary = history.hypertension === "Yes" ? 1 : 0;
      const cvdBinary = history.cvd === "Yes" ? 1 : 0;

      // Construct model-ready features dictionary
      const features: Record<string, number> = {
        age: calculatedAge,
        gender: genderBinary,
        education_years: Number(profile.education_years),
        diabetes: diabetesBinary,
        hypertension: hypertensionBinary,
        cvd: cvdBinary,
      };

      if (hasBaselineLabs) {
        features.eGFR = Number(baselineLabs.eGFR);
        features.creatinine = Number(baselineLabs.creatinine);
        features.bun = Number(baselineLabs.bun);
        features.uacr = Number(baselineLabs.uacr);
        features.systolic_bp = Number(baselineLabs.systolic_bp);
        features.bmi = Number(baselineLabs.bmi);
        features.hemoglobin = Number(baselineLabs.hemoglobin);
        features.albumin = Number(baselineLabs.albumin);
        features.hsCRP = Number(baselineLabs.hsCRP);
        features.potassium = Number(baselineLabs.potassium);
        features.phosphate = Number(baselineLabs.phosphate);
        features.calcium = Number(baselineLabs.calcium);
      }

      const payload = {
        patient_identifier: profile.patient_identifier.trim(),
        first_name: profile.first_name.trim(),
        last_name: profile.last_name.trim(),
        date_of_birth: profile.date_of_birth,
        sex: profile.sex,
        medical_history: {
          education_level: profile.education_level,
          education_years: profile.education_years,
          diabetes: history.diabetes,
          diabetes_type: history.diabetes === "Yes" ? history.diabetes_type : null,
          diabetes_duration: history.diabetes === "Yes" ? Number(history.diabetes_duration) : null,
          hypertension: history.hypertension,
          hypertension_duration: history.hypertension === "Yes" ? Number(history.hypertension_duration) : null,
          cvd: history.cvd,
          cvd_conditions: history.cvd === "Yes" ? history.cvd_conditions : [],
          ckd_diagnosis: history.ckd_diagnosis,
          ckd_stage: history.ckd_stage,
          ckd_duration: Number(history.ckd_duration),
          dialysis_status: history.dialysis_status,
        },
        features,
      };

      await api.post("/patients/", payload);
      notify(`Registered ${profile.first_name} ${profile.last_name} (${profile.patient_identifier}) successfully!`, "success");
      setShowAddModal(false);
      setCurrentStep(1);
      // Reset form
      setProfile({
        patient_identifier: "",
        first_name: "",
        last_name: "",
        date_of_birth: "1960-05-15",
        sex: "Male",
        education_level: "Higher secondary",
        education_years: 12,
      });
      loadData();
    } catch (err: unknown) {
      notify(err instanceof Error ? err.message : "Failed to register patient", "error");
    } finally {
      setSubmitting(false);
    }
  };

  const calculatedProfileAge = calculateAge(profile.date_of_birth);

  return (
    <div className="space-y-6">
      {/* Patient Directory Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-primary">Patient Cohort Directory</h1>
            <span className="rounded bg-surface-subtle px-2 py-0.5 text-xs font-semibold text-text-secondary tabular-nums">
              {patients.length} Active Profiles
            </span>
          </div>
          <p className="text-xs text-text-secondary mt-1">
            Clinical profiles, longitudinal biomarker values, and cognitive risk stratification status.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Button
            variant="primary"
            size="sm"
            onClick={() => {
              setShowAddModal(true);
              setCurrentStep(1);
            }}
            className="shadow-subtle"
          >
            <UserPlus className="h-4 w-4 mr-1.5" />
            Enroll New Patient
          </Button>
          <Link href="/prediction">
            <Button variant="teal" size="sm" className="shadow-subtle">
              <BrainCircuit className="h-4 w-4 mr-1.5" />
              New Risk Assessment
            </Button>
          </Link>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Filter and Search Ribbon */}
      <Card>
        <CardContent className="p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Quick Risk Filters */}
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              onClick={() => setRiskFilter("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                riskFilter === "all"
                  ? "bg-primary text-white shadow-subtle"
                  : "bg-surface-subtle text-text-secondary hover:bg-slate-200"
              }`}
            >
              All ({patients.length})
            </button>
            <button
              onClick={() => setRiskFilter("high")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                riskFilter === "high"
                  ? "bg-risk-critical text-white shadow-subtle"
                  : "bg-red-50 text-risk-critical hover:bg-red-100"
              }`}
            >
              High Risk ({riskCounts.high})
            </button>
            <button
              onClick={() => setRiskFilter("moderate")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                riskFilter === "moderate"
                  ? "bg-risk-moderate text-white shadow-subtle"
                  : "bg-amber-50 text-risk-moderate hover:bg-amber-100"
              }`}
            >
              Moderate ({riskCounts.moderate})
            </button>
            <button
              onClick={() => setRiskFilter("low")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                riskFilter === "low"
                  ? "bg-risk-normal text-white shadow-subtle"
                  : "bg-emerald-50 text-risk-normal hover:bg-emerald-100"
              }`}
            >
              Low ({riskCounts.low})
            </button>
          </div>

          {/* Search Input & Sorter */}
          <div className="flex items-center gap-2">
            <div className="relative w-64">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />
              <Input
                placeholder="Search patient name or MRN..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="pl-8 text-xs h-9 bg-surface-subtle"
              />
            </div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "name" | "age" | "risk")}
              className="h-9 rounded-lg border border-border bg-surface-subtle px-2.5 text-xs text-text-primary focus:border-clinical-teal focus:outline-none"
            >
              <option value="name">Sort: Name (A-Z)</option>
              <option value="age">Sort: Age (Desc)</option>
              <option value="risk">Sort: Risk Severity</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {loading && <Spinner label="Loading patient cohort..." />}

      {/* Patient Cards Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((p) => {
          const age = calculateAge(p.date_of_birth);
          const latestPred = latestPredictionByPatient.get(p.id);
          const risk = normalizeRisk(latestPred?.predicted_label);
          const features = p.features || {};
          const egfr = valueAsNumber(features.egfr || features.eGFR, 0);
          const creatinine = valueAsNumber(features.creatinine, 0);
          const uacr = valueAsNumber(features.uacr, 0);
          const hasRenal = egfr > 0 || creatinine > 0;
          const medHistory = (p.medical_history || {}) as Record<string, unknown>;
          const ckdStage = (medHistory.ckd_stage as string) || (egfr > 0 ? (egfr < 60 ? "G3a" : "G2") : "Not recorded");

          return (
            <Link key={p.id} href={`/patients/${p.id}`} className="group block">
              <Card className="h-full transition-all duration-150 hover:border-clinical-teal hover:shadow-card">
                <CardHeader className="pb-3 border-b border-border/60">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="text-sm font-bold tracking-tight text-primary group-hover:text-clinical-teal transition-colors">
                        {`${p.first_name || ""} ${p.last_name || ""}`.trim() || "Unregistered Patient"}
                      </div>
                      <div className="text-[11px] text-text-muted mt-0.5">
                        MRN: <span className="font-mono text-text-secondary">{p.patient_identifier}</span>
                      </div>
                    </div>
                    {risk === "high" && <Badge variant="critical">High Risk</Badge>}
                    {risk === "moderate" && <Badge variant="elevated">Moderate</Badge>}
                    {risk === "low" && <Badge variant="normal">Low Risk</Badge>}
                    {risk === "unknown" && <Badge variant="default">Unstratified</Badge>}
                  </div>
                </CardHeader>

                <CardContent className="space-y-3 pt-4">
                  {/* Demographics Strip */}
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="rounded-lg bg-surface-subtle p-2 text-center">
                      <span className="text-[10px] text-text-muted block">Age</span>
                      <span className="font-semibold text-text-primary tabular-nums">
                        {age ? `${age} yr` : "N/A"}
                      </span>
                    </div>
                    <div className="rounded-lg bg-surface-subtle p-2 text-center">
                      <span className="text-[10px] text-text-muted block">Sex</span>
                      <span className="font-semibold text-text-primary">
                        {p.sex || "N/A"}
                      </span>
                    </div>
                    <div className="rounded-lg bg-surface-subtle p-2 text-center">
                      <span className="text-[10px] text-text-muted block">CKD Stage</span>
                      <span className="font-semibold text-clinical-teal">
                        {ckdStage}
                      </span>
                    </div>
                  </div>

                  {/* Medical History Tags */}
                  {medHistory.diabetes || medHistory.hypertension || medHistory.cvd ? (
                    <div className="flex flex-wrap gap-1.5 text-[10px]">
                      {medHistory.diabetes === "Yes" && (
                        <span className="rounded bg-amber-50 px-2 py-0.5 font-medium text-amber-700 border border-amber-200">
                          DM {medHistory.diabetes_type ? `(${medHistory.diabetes_type})` : ""}
                        </span>
                      )}
                      {medHistory.hypertension === "Yes" && (
                        <span className="rounded bg-sky-50 px-2 py-0.5 font-medium text-sky-700 border border-sky-200">
                          HTN
                        </span>
                      )}
                      {medHistory.cvd === "Yes" && (
                        <span className="rounded bg-rose-50 px-2 py-0.5 font-medium text-rose-700 border border-rose-200">
                          CVD
                        </span>
                      )}
                    </div>
                  ) : null}

                  {/* Renal Telemetry Metrics */}
                  {hasRenal ? (
                    <div className="rounded-lg border border-border p-3 bg-surface">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-1 text-[10px] font-semibold text-text-secondary uppercase tracking-wide">
                          <FlaskConical className="h-3 w-3 text-clinical-teal" />
                          Visit Laboratory Telemetry
                        </div>
                        <span className="text-[9px] text-clinical-teal font-medium">Last Recorded</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div>
                          <div className="text-[10px] text-text-muted">eGFR</div>
                          <div className={`font-bold text-sm tabular-nums ${egfr < 60 ? "text-risk-moderate" : "text-text-primary"}`}>
                            {egfr > 0 ? egfr.toFixed(0) : "—"}
                          </div>
                          <div className="text-[9px] text-text-muted">mL/min</div>
                        </div>
                        <div>
                          <div className="text-[10px] text-text-muted">Creatinine</div>
                          <div className={`font-bold text-sm tabular-nums ${creatinine > 1.3 ? "text-risk-moderate" : "text-text-primary"}`}>
                            {creatinine > 0 ? creatinine.toFixed(1) : "—"}
                          </div>
                          <div className="text-[9px] text-text-muted">mg/dL</div>
                        </div>
                        <div>
                          <div className="text-[10px] text-text-muted">UACR</div>
                          <div className={`font-bold text-sm tabular-nums ${uacr > 30 ? "text-risk-moderate" : "text-text-primary"}`}>
                            {uacr > 0 ? uacr.toFixed(0) : "—"}
                          </div>
                          <div className="text-[9px] text-text-muted">mg/g</div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-border p-3 text-center text-[11px] text-text-muted bg-surface">
                      <FlaskConical className="h-4 w-4 mx-auto mb-1 text-slate-300" />
                      No visit laboratory measurements recorded yet
                    </div>
                  )}

                  {/* Latest Prediction Result */}
                  {latestPred?.predicted_label ? (
                    <div className="flex items-center gap-2 rounded-lg border border-border bg-surface-subtle px-3 py-2">
                      <Activity className="h-3.5 w-3.5 text-clinical-teal flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <div className="text-[10px] text-text-muted">Cognitive Stratification</div>
                        <div className="text-xs font-semibold text-text-primary truncate">{latestPred.predicted_label}</div>
                      </div>
                      {latestPred.confidence && (
                        <span className="text-[10px] font-mono text-text-muted tabular-nums">
                          {Math.round(latestPred.confidence * 100)}%
                        </span>
                      )}
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 rounded-lg border border-dashed border-border px-3 py-2 text-[11px] text-text-muted">
                      <Heart className="h-3.5 w-3.5 text-slate-300" />
                      Awaiting cognitive risk assessment
                    </div>
                  )}

                  {/* Action Link Footer */}
                  <div className="flex items-center justify-end text-xs pt-1 border-t border-border">
                    <span className="flex items-center gap-1 text-clinical-teal font-semibold group-hover:translate-x-0.5 transition-transform">
                      View Profile & History <ChevronRight className="h-3.5 w-3.5" />
                    </span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          );
        })}
      </div>

      {!filtered.length && !loading && (
        <div className="rounded-xl border border-dashed border-border bg-surface py-12 text-center text-text-muted">
          <Users className="h-10 w-10 text-slate-300 mx-auto mb-2" />
          <p className="text-xs font-semibold text-text-primary">No Patients Match Filter</p>
          <p className="text-[11px] text-text-muted mt-1">Adjust search query or enroll a new patient.</p>
        </div>
      )}

      {/* ════════════════════════════════════════════════════════════════════════
          MULTI-STEP PATIENT REGISTRATION MODAL
          Step 1: Patient Profile | Step 2: Medical History | Step 3: Review & Baseline
          ════════════════════════════════════════════════════════════════════════ */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/40 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-2xl rounded-xl border border-border bg-surface shadow-modal my-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-border px-6 py-4">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary text-white shadow-subtle">
                  <UserPlus className="h-5 w-5 text-teal-300" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-primary">Patient Registration Workflow</h3>
                  <p className="text-xs text-text-muted">Establish patient identity, medical history & baseline clinical profile.</p>
                </div>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                className="rounded p-1 text-text-muted hover:bg-surface-subtle"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Step Indicator Wizard Bar */}
            <div className="border-b border-border bg-surface-subtle px-6 py-3">
              <div className="flex items-center justify-between">
                {[
                  { step: 1 as Step, title: "1. Patient Profile", desc: "Identity & Demographics" },
                  { step: 2 as Step, title: "2. Medical History", desc: "Comorbidities & CKD" },
                  { step: 3 as Step, title: "3. Review & Baseline", desc: "Optional Labs & Save" },
                ].map((s) => {
                  const isActive = currentStep === s.step;
                  const isDone = currentStep > s.step;

                  return (
                    <button
                      key={s.step}
                      type="button"
                      onClick={() => setCurrentStep(s.step)}
                      className={`flex items-center gap-2 text-left transition-colors ${
                        isActive
                          ? "text-clinical-teal font-semibold"
                          : isDone
                          ? "text-primary font-medium"
                          : "text-text-muted"
                      }`}
                    >
                      <div
                        className={`flex h-6 w-6 items-center justify-center rounded-full text-xs font-bold ${
                          isActive
                            ? "bg-clinical-teal text-white"
                            : isDone
                            ? "bg-primary text-white"
                            : "bg-slate-200 text-text-secondary"
                        }`}
                      >
                        {isDone ? <CheckCircle2 className="h-4 w-4" /> : s.step}
                      </div>
                      <div className="hidden sm:block">
                        <div className="text-xs leading-none">{s.title}</div>
                        <div className="text-[10px] text-text-muted mt-0.5">{s.desc}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>

            <form onSubmit={handleRegisterSubmit}>
              <div className="px-6 py-5 space-y-4">

                {/* ──────────────────────────────────────────────────────────
                    STEP 1: PATIENT PROFILE
                    ────────────────────────────────────────────────────────── */}
                {currentStep === 1 && (
                  <div className="space-y-4">
                    <div className="rounded-lg border border-teal-200 bg-clinical-teal-light/30 p-3 text-xs text-clinical-teal-dark flex items-center gap-2">
                      <ShieldCheck className="h-4 w-4 flex-shrink-0" />
                      <span>Collected once at registration to establish clinical identity and baseline cognitive reserve.</span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-semibold text-text-primary">
                          Medical Record Number (MRN)*
                        </label>
                        <Input
                          required
                          placeholder="e.g. CKD-1004"
                          value={profile.patient_identifier}
                          onChange={(e) => setProfile({ ...profile, patient_identifier: e.target.value })}
                          className="mt-1 text-xs"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-text-primary">
                          Biological Sex
                        </label>
                        <select
                          value={profile.sex}
                          onChange={(e) => setProfile({ ...profile, sex: e.target.value })}
                          className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2.5 text-xs text-text-primary focus:border-clinical-teal focus:outline-none"
                        >
                          <option value="Male">Male</option>
                          <option value="Female">Female</option>
                          <option value="Other / not recorded">Other / not recorded</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs font-semibold text-text-primary">First Name</label>
                        <Input
                          placeholder="e.g. Eleanor"
                          value={profile.first_name}
                          onChange={(e) => setProfile({ ...profile, first_name: e.target.value })}
                          className="mt-1 text-xs"
                        />
                      </div>
                      <div>
                        <label className="text-xs font-semibold text-text-primary">Last Name</label>
                        <Input
                          placeholder="e.g. Vance"
                          value={profile.last_name}
                          onChange={(e) => setProfile({ ...profile, last_name: e.target.value })}
                          className="mt-1 text-xs"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <div className="flex items-center justify-between">
                          <label className="text-xs font-semibold text-text-primary">Date of Birth*</label>
                          {calculatedProfileAge !== null && (
                            <span className="text-[11px] font-semibold text-clinical-teal">
                              Age: {calculatedProfileAge} years
                            </span>
                          )}
                        </div>
                        <Input
                          type="date"
                          required
                          value={profile.date_of_birth}
                          onChange={(e) => setProfile({ ...profile, date_of_birth: e.target.value })}
                          className="mt-1 text-xs"
                        />
                      </div>

                      <div>
                        <div className="flex items-center justify-between">
                          <label className="text-xs font-semibold text-text-primary">Education Level</label>
                          <span className="text-[11px] text-text-muted">
                            {profile.education_years} yrs derived
                          </span>
                        </div>
                        <select
                          value={profile.education_level}
                          onChange={(e) => handleEducationChange(e.target.value)}
                          className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2.5 text-xs text-text-primary focus:border-clinical-teal focus:outline-none"
                        >
                          {EDUCATION_LEVEL_MAP.map((item) => (
                            <option key={item.label} value={item.label}>
                              {item.label} ({item.defaultYears} yrs)
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* ──────────────────────────────────────────────────────────
                    STEP 2: MEDICAL HISTORY
                    ────────────────────────────────────────────────────────── */}
                {currentStep === 2 && (
                  <div className="space-y-4">
                    {/* Diabetes */}
                    <div className="rounded-lg border border-border p-3.5 bg-surface space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="font-semibold text-xs text-primary">1. Diabetes Mellitus</div>
                        <div className="flex gap-2">
                          {(["No", "Yes", "Unknown"] as const).map((opt) => (
                            <button
                              key={opt}
                              type="button"
                              onClick={() => setHistory({ ...history, diabetes: opt })}
                              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                                history.diabetes === opt
                                  ? "bg-primary text-white"
                                  : "bg-surface-subtle text-text-secondary hover:bg-slate-200"
                              }`}
                            >
                              {opt}
                            </button>
                          ))}
                        </div>
                      </div>

                      {history.diabetes === "Yes" && (
                        <div className="grid grid-cols-2 gap-3 pt-2 border-t border-border">
                          <div>
                            <label className="text-[11px] font-medium text-text-secondary">Diabetes Type</label>
                            <select
                              value={history.diabetes_type}
                              onChange={(e) => setHistory({ ...history, diabetes_type: e.target.value as any })}
                              className="mt-1 h-8 w-full rounded border border-border bg-surface px-2 text-xs text-text-primary"
                            >
                              <option value="Type 1">Type 1</option>
                              <option value="Type 2">Type 2</option>
                              <option value="Other / unspecified">Other / unspecified</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-[11px] font-medium text-text-secondary">Duration (years)</label>
                            <Input
                              type="number"
                              min={0}
                              max={60}
                              value={history.diabetes_duration}
                              onChange={(e) => setHistory({ ...history, diabetes_duration: parseFloat(e.target.value) || 0 })}
                              className="mt-1 h-8 text-xs"
                            />
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Hypertension */}
                    <div className="rounded-lg border border-border p-3.5 bg-surface space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="font-semibold text-xs text-primary">2. Hypertension</div>
                        <div className="flex gap-2">
                          {(["No", "Yes", "Unknown"] as const).map((opt) => (
                            <button
                              key={opt}
                              type="button"
                              onClick={() => setHistory({ ...history, hypertension: opt })}
                              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                                history.hypertension === opt
                                  ? "bg-primary text-white"
                                  : "bg-surface-subtle text-text-secondary hover:bg-slate-200"
                              }`}
                            >
                              {opt}
                            </button>
                          ))}
                        </div>
                      </div>

                      {history.hypertension === "Yes" && (
                        <div className="pt-2 border-t border-border">
                          <label className="text-[11px] font-medium text-text-secondary">Duration of Hypertension (years)</label>
                          <Input
                            type="number"
                            min={0}
                            max={60}
                            value={history.hypertension_duration}
                            onChange={(e) => setHistory({ ...history, hypertension_duration: parseFloat(e.target.value) || 0 })}
                            className="mt-1 h-8 text-xs w-48"
                          />
                        </div>
                      )}
                    </div>

                    {/* Cardiovascular Disease */}
                    <div className="rounded-lg border border-border p-3.5 bg-surface space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="font-semibold text-xs text-primary">3. Cardiovascular Disease (CVD)</div>
                        <div className="flex gap-2">
                          {(["No", "Yes", "Unknown"] as const).map((opt) => (
                            <button
                              key={opt}
                              type="button"
                              onClick={() => setHistory({ ...history, cvd: opt })}
                              className={`rounded px-2.5 py-1 text-xs font-medium transition-colors ${
                                history.cvd === opt
                                  ? "bg-primary text-white"
                                  : "bg-surface-subtle text-text-secondary hover:bg-slate-200"
                              }`}
                            >
                              {opt}
                            </button>
                          ))}
                        </div>
                      </div>

                      {history.cvd === "Yes" && (
                        <div className="pt-2 border-t border-border space-y-1.5">
                          <label className="text-[11px] font-medium text-text-secondary">Specific Conditions (select all that apply):</label>
                          <div className="grid grid-cols-2 gap-2 pt-1">
                            {CVD_CONDITIONS.map((cond) => {
                              const checked = history.cvd_conditions.includes(cond);
                              return (
                                <label
                                  key={cond}
                                  className={`flex items-center gap-2 rounded-lg border p-2 text-xs cursor-pointer transition-colors ${
                                    checked ? "border-clinical-teal bg-clinical-teal-light/20 text-clinical-teal-dark font-medium" : "border-border text-text-secondary"
                                  }`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={() => toggleCvdCondition(cond)}
                                    className="rounded border-border text-clinical-teal"
                                  />
                                  <span>{cond}</span>
                                </label>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Kidney Disease History */}
                    <div className="rounded-lg border border-border p-3.5 bg-surface space-y-3">
                      <div className="font-semibold text-xs text-primary">4. Kidney Disease History & Staging</div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-[11px] font-medium text-text-secondary">Known CKD Stage</label>
                          <select
                            value={history.ckd_stage}
                            onChange={(e) => setHistory({ ...history, ckd_stage: e.target.value as any })}
                            className="mt-1 h-8 w-full rounded border border-border bg-surface px-2 text-xs text-text-primary"
                          >
                            <option value="G1">G1 — Normal / High (eGFR ≥90)</option>
                            <option value="G2">G2 — Mild Reduction (eGFR 60-89)</option>
                            <option value="G3a">G3a — Mild-to-Moderate (eGFR 45-59)</option>
                            <option value="G3b">G3b — Moderate-to-Severe (eGFR 30-44)</option>
                            <option value="G4">G4 — Severe Reduction (eGFR 15-29)</option>
                            <option value="G5">G5 — Kidney Failure (eGFR &lt;15)</option>
                            <option value="Not recorded">Not recorded</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-[11px] font-medium text-text-secondary">Duration of CKD (years)</label>
                          <Input
                            type="number"
                            min={0}
                            max={50}
                            value={history.ckd_duration}
                            onChange={(e) => setHistory({ ...history, ckd_duration: parseFloat(e.target.value) || 0 })}
                            className="mt-1 h-8 text-xs"
                          />
                        </div>
                      </div>

                      <div>
                        <label className="text-[11px] font-medium text-text-secondary">Dialysis Status</label>
                        <select
                          value={history.dialysis_status}
                          onChange={(e) => setHistory({ ...history, dialysis_status: e.target.value as any })}
                          className="mt-1 h-8 w-full rounded border border-border bg-surface px-2 text-xs text-text-primary"
                        >
                          <option value="Not on dialysis">Not on dialysis</option>
                          <option value="Hemodialysis">Hemodialysis</option>
                          <option value="Peritoneal dialysis">Peritoneal dialysis</option>
                          <option value="Kidney transplant">Kidney transplant</option>
                          <option value="Unknown">Unknown</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* ──────────────────────────────────────────────────────────
                    STEP 3: REVIEW & OPTIONAL BASELINE MEASUREMENTS
                    ────────────────────────────────────────────────────────── */}
                {currentStep === 3 && (
                  <div className="space-y-4">
                    {/* Clinical Summary Review Card */}
                    <div className="rounded-lg border border-border bg-surface-subtle p-3.5 space-y-2 text-xs">
                      <div className="flex items-center justify-between border-b border-border pb-2">
                        <span className="font-semibold text-primary">Patient Profile Summary</span>
                        <span className="font-mono text-clinical-teal font-semibold">{profile.patient_identifier}</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-text-secondary">
                        <div>Name: <strong className="text-text-primary">{profile.first_name} {profile.last_name || "—"}</strong></div>
                        <div>Sex / Age: <strong className="text-text-primary">{profile.sex} / {calculatedProfileAge} yrs</strong></div>
                        <div>Education: <strong className="text-text-primary">{profile.education_level} ({profile.education_years} yrs)</strong></div>
                        <div>CKD Staging: <strong className="text-text-primary">{history.ckd_stage} ({history.dialysis_status})</strong></div>
                        <div>Comorbidities: <strong className="text-text-primary">
                          {history.diabetes === "Yes" ? "DM, " : ""}{history.hypertension === "Yes" ? "HTN, " : ""}{history.cvd === "Yes" ? "CVD" : "None"}
                        </strong></div>
                      </div>
                    </div>

                    {/* Baseline Measurements Accordion */}
                    <div className="rounded-lg border border-border p-3.5 bg-surface space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-semibold text-xs text-primary">Baseline Visit Measurements (Optional)</div>
                          <div className="text-[11px] text-text-muted">Can be recorded now or entered during clinical hospital visits.</div>
                        </div>
                        <label className="flex items-center gap-1.5 text-xs text-text-secondary cursor-pointer">
                          <input
                            type="checkbox"
                            checked={hasBaselineLabs}
                            onChange={(e) => setHasBaselineLabs(e.target.checked)}
                            className="rounded border-border text-clinical-teal"
                          />
                          <span>Include Baseline Labs</span>
                        </label>
                      </div>

                      {hasBaselineLabs && (
                        <div className="space-y-3 pt-2 border-t border-border">
                          <div className="grid grid-cols-3 gap-2">
                            <div>
                              <label className="text-[10px] font-medium text-text-secondary">eGFR (mL/min)</label>
                              <Input
                                type="number"
                                value={baselineLabs.eGFR}
                                onChange={(e) => setBaselineLabs({ ...baselineLabs, eGFR: parseFloat(e.target.value) || 0 })}
                                className="mt-0.5 h-8 text-xs"
                              />
                            </div>
                            <div>
                              <label className="text-[10px] font-medium text-text-secondary">Creatinine (mg/dL)</label>
                              <Input
                                type="number"
                                step="0.1"
                                value={baselineLabs.creatinine}
                                onChange={(e) => setBaselineLabs({ ...baselineLabs, creatinine: parseFloat(e.target.value) || 0 })}
                                className="mt-0.5 h-8 text-xs"
                              />
                            </div>
                            <div>
                              <label className="text-[10px] font-medium text-text-secondary">UACR (mg/g)</label>
                              <Input
                                type="number"
                                value={baselineLabs.uacr}
                                onChange={(e) => setBaselineLabs({ ...baselineLabs, uacr: parseFloat(e.target.value) || 0 })}
                                className="mt-0.5 h-8 text-xs"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-3 gap-2">
                            <div>
                              <label className="text-[10px] font-medium text-text-secondary">BUN (mg/dL)</label>
                              <Input
                                type="number"
                                value={baselineLabs.bun}
                                onChange={(e) => setBaselineLabs({ ...baselineLabs, bun: parseFloat(e.target.value) || 0 })}
                                className="mt-0.5 h-8 text-xs"
                              />
                            </div>
                            <div>
                              <label className="text-[10px] font-medium text-text-secondary">Systolic BP (mmHg)</label>
                              <Input
                                type="number"
                                value={baselineLabs.systolic_bp}
                                onChange={(e) => setBaselineLabs({ ...baselineLabs, systolic_bp: parseFloat(e.target.value) || 0 })}
                                className="mt-0.5 h-8 text-xs"
                              />
                            </div>
                            <div>
                              <label className="text-[10px] font-medium text-text-secondary">BMI (kg/m²)</label>
                              <Input
                                type="number"
                                step="0.1"
                                value={baselineLabs.bmi}
                                onChange={(e) => setBaselineLabs({ ...baselineLabs, bmi: parseFloat(e.target.value) || 0 })}
                                className="mt-0.5 h-8 text-xs"
                              />
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Wizard Footer Controls */}
              <div className="flex items-center justify-between border-t border-border px-6 py-4">
                {currentStep > 1 ? (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => setCurrentStep((prev) => (prev - 1) as Step)}
                  >
                    <ChevronLeft className="h-4 w-4 mr-1" />
                    Back
                  </Button>
                ) : (
                  <Button type="button" variant="secondary" size="sm" onClick={() => setShowAddModal(false)}>
                    Cancel
                  </Button>
                )}

                <div className="flex items-center gap-2">
                  {currentStep < 3 ? (
                    <Button
                      type="button"
                      variant="teal"
                      size="sm"
                      onClick={() => {
                        if (currentStep === 1 && !profile.patient_identifier.trim()) {
                          notify("Please enter a valid Patient Identifier (MRN).", "error");
                          return;
                        }
                        setCurrentStep((prev) => (prev + 1) as Step);
                      }}
                    >
                      Next: {currentStep === 1 ? "Medical History" : "Review & Complete"}
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  ) : (
                    <Button type="submit" variant="teal" size="sm" disabled={submitting}>
                      {submitting ? <Spinner label="Enrolling..." /> : "Complete Registration"}
                    </Button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
