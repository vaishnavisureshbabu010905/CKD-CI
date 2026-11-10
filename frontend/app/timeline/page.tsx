"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useApi } from "@/hooks/use-api";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";
import {
  Clock,
  Activity,
  BrainCircuit,
  ClipboardList,
  AlertTriangle,
  User,
  FlaskConical,
  ChevronRight,
  TrendingDown,
  TrendingUp,
  Calendar,
  Filter,
  Search,
  Sparkles,
} from "lucide-react";

type Event = {
  id: number;
  patient_id?: number;
  source_type: string;
  summary?: string;
  event_time: string;
  payload?: Record<string, unknown>;
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

type EventTypeFilter = "all" | "clinical_visit" | "cognitive_assessment" | "prediction" | "alert" | "note";

export default function TimelinePage() {
  const api = useApi();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>("");
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [typeFilter, setTypeFilter] = useState<EventTypeFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Load patients list on mount
  useEffect(() => {
    let mounted = true;
    const loadPatients = async () => {
      try {
        const data = await api.get<Patient[]>("/patients/");
        if (!mounted) return;
        const list = data || [];
        setPatients(list);
        if (list.length > 0 && !selectedPatientId) {
          setSelectedPatientId(String(list[0].id));
        }
      } catch (e: unknown) {
        // Fallback gracefully
      }
    };
    loadPatients();
    return () => {
      mounted = false;
    };
  }, [api]);

  // Load timeline events whenever selected patient changes
  useEffect(() => {
    if (!selectedPatientId) return;

    let mounted = true;
    const loadEvents = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.get<Event[]>(`/timeline/${selectedPatientId}`);
        if (mounted) setEvents(data || []);
      } catch (e: unknown) {
        if (mounted) setError(e instanceof Error ? e.message : "Failed to load surveillance timeline");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    loadEvents();
    return () => {
      mounted = false;
    };
  }, [api, selectedPatientId]);

  const activePatient = useMemo(() => {
    return patients.find((p) => String(p.id) === selectedPatientId) || null;
  }, [patients, selectedPatientId]);

  const patientFeatures = activePatient?.features || {};
  const egfr = Number(patientFeatures.egfr ?? patientFeatures.eGFR ?? 0);
  const uacr = Number(patientFeatures.uacr ?? 0);
  const creatinine = Number(patientFeatures.creatinine ?? 0);

  // Filter events by source_type and search query
  const filteredEvents = useMemo(() => {
    return events.filter((e) => {
      const type = (e.source_type || "").toLowerCase();
      if (typeFilter !== "all") {
        if (typeFilter === "clinical_visit" && !type.includes("visit") && !type.includes("encounter")) return false;
        if (typeFilter === "cognitive_assessment" && !type.includes("cognitive")) return false;
        if (typeFilter === "prediction" && !type.includes("prediction")) return false;
        if (typeFilter === "alert" && !type.includes("alert")) return false;
        if (typeFilter === "note" && !type.includes("note") && !type.includes("task") && !type.includes("intake")) return false;
      }

      if (!searchQuery.trim()) return true;
      const q = searchQuery.toLowerCase();
      const summary = (e.summary || "").toLowerCase();
      return summary.includes(q) || type.includes(q);
    });
  }, [events, typeFilter, searchQuery]);

  // Extract longitudinal trends from event payload
  const visitEvents = useMemo(() => {
    return events.filter((e) => e.source_type.toLowerCase().includes("visit") || e.source_type.toLowerCase().includes("encounter"));
  }, [events]);

  const cognitiveEvents = useMemo(() => {
    return events.filter((e) => e.source_type.toLowerCase().includes("cognitive"));
  }, [events]);

  const latestCognitive = cognitiveEvents[0];
  const latestMoCA = latestCognitive?.payload?.scores
    ? (latestCognitive.payload.scores as Record<string, unknown>).moca_score
    : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-primary">Longitudinal Trends & Surveillance</h1>
            <span className="rounded bg-clinical-teal-light px-2 py-0.5 text-xs font-semibold text-clinical-teal-dark">
              Surveillance Trajectory
            </span>
          </div>
          <p className="text-xs text-text-secondary mt-1">
            Serial tracking of renal clearance (eGFR), albuminuria progression, and neurocognitive screening across hospital encounters.
          </p>
        </div>

        {activePatient && (
          <div className="flex items-center gap-2">
            <Link href={`/patients/${activePatient.id}`}>
              <Button variant="outline" size="sm">
                <User className="h-4 w-4 mr-1.5 text-primary" />
                View Patient Profile
              </Button>
            </Link>
            <Link href={`/prediction?patient=${activePatient.patient_identifier}`}>
              <Button variant="teal" size="sm">
                <BrainCircuit className="h-4 w-4 mr-1.5" />
                Assess AI Risk
              </Button>
            </Link>
          </div>
        )}
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Patient Selector Bar */}
      <Card>
        <CardContent className="p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <span className="text-xs font-semibold text-text-primary whitespace-nowrap">Select Surveillance Cohort:</span>
            <select
              value={selectedPatientId}
              onChange={(e) => setSelectedPatientId(e.target.value)}
              className="h-9 min-w-[280px] rounded-lg border border-border bg-surface px-3 text-xs font-medium text-text-primary focus:border-clinical-teal focus:outline-none"
            >
              <option value="">Select patient record...</option>
              {patients.map((p) => (
                <option key={p.id} value={String(p.id)}>
                  {p.patient_identifier} — {p.first_name || ""} {p.last_name || ""}
                </option>
              ))}
            </select>
          </div>

          {activePatient && (
            <div className="flex items-center gap-4 text-xs text-text-muted">
              <span>MRN: <strong className="font-mono text-text-primary">{activePatient.patient_identifier}</strong></span>
              <span>•</span>
              <span>Sex: <strong className="text-text-primary">{activePatient.sex || "N/A"}</strong></span>
              <span>•</span>
              <span>DOB: <strong className="text-text-primary">{activePatient.date_of_birth || "N/A"}</strong></span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Biomarker Trajectory & Longitudinal Metric Cards */}
      {activePatient && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {/* eGFR Trajectory */}
          <Card className="border-border shadow-subtle">
            <CardContent className="p-4">
              <div className="flex items-center justify-between text-xs text-text-muted">
                <span className="font-semibold uppercase text-[10px]">eGFR Trajectory</span>
                <FlaskConical className="h-4 w-4 text-clinical-teal" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-primary tabular-nums">
                  {egfr > 0 ? egfr.toFixed(0) : "—"}
                </span>
                <span className="text-xs text-text-muted">mL/min/1.73m²</span>
              </div>
              <div className="mt-2 flex items-center gap-1.5 text-[11px]">
                {egfr < 60 ? (
                  <span className="text-risk-moderate font-medium flex items-center gap-0.5">
                    <TrendingDown className="h-3 w-3" /> Reduced filtration
                  </span>
                ) : (
                  <span className="text-risk-normal font-medium flex items-center gap-0.5">
                    <Activity className="h-3 w-3" /> Preserved clearance
                  </span>
                )}
                <span className="text-text-muted">• Current baseline</span>
              </div>
            </CardContent>
          </Card>

          {/* Albuminuria (UACR) */}
          <Card className="border-border shadow-subtle">
            <CardContent className="p-4">
              <div className="flex items-center justify-between text-xs text-text-muted">
                <span className="font-semibold uppercase text-[10px]">Albuminuria (UACR)</span>
                <Activity className="h-4 w-4 text-amber-500" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-primary tabular-nums">
                  {uacr > 0 ? uacr.toFixed(0) : "—"}
                </span>
                <span className="text-xs text-text-muted">mg/g</span>
              </div>
              <div className="mt-2 text-[11px] text-text-muted">
                {uacr > 300 ? (
                  <span className="text-risk-critical font-medium">Stage A3 (Severe risk)</span>
                ) : uacr > 30 ? (
                  <span className="text-risk-moderate font-medium">Stage A2 (Microalbuminuria)</span>
                ) : (
                  <span className="text-risk-normal font-medium">Stage A1 (Normal / Optimum)</span>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Neurocognitive Surveillance */}
          <Card className="border-border shadow-subtle">
            <CardContent className="p-4">
              <div className="flex items-center justify-between text-xs text-text-muted">
                <span className="font-semibold uppercase text-[10px]">Neurocognitive Status</span>
                <ClipboardList className="h-4 w-4 text-sky-600" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-primary tabular-nums">
                  {latestMoCA !== null && latestMoCA !== undefined ? `${latestMoCA}/30` : "Assessed"}
                </span>
                <span className="text-xs text-text-muted">MoCA Score</span>
              </div>
              <div className="mt-2 text-[11px] text-text-muted">
                {latestCognitive?.summary ? (
                  <span className="truncate block font-medium text-sky-700" title={latestCognitive.summary}>
                    {latestCognitive.summary}
                  </span>
                ) : (
                  <span>Scheduled for MoCA screening</span>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Surveillance Frequency */}
          <Card className="border-border shadow-subtle">
            <CardContent className="p-4">
              <div className="flex items-center justify-between text-xs text-text-muted">
                <span className="font-semibold uppercase text-[10px]">Recorded Timeline</span>
                <Clock className="h-4 w-4 text-primary" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold tracking-tight text-primary tabular-nums">
                  {events.length}
                </span>
                <span className="text-xs text-text-muted">Surveillance Events</span>
              </div>
              <div className="mt-2 text-[11px] text-text-muted">
                <span>{visitEvents.length} visits • {cognitiveEvents.length} cognitive tests</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Interactive Filter & Search Ribbon */}
      <Card>
        <CardContent className="p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              onClick={() => setTypeFilter("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                typeFilter === "all"
                  ? "bg-primary text-white shadow-subtle"
                  : "bg-surface-subtle text-text-secondary hover:bg-slate-200"
              }`}
            >
              All Events ({events.length})
            </button>
            <button
              onClick={() => setTypeFilter("clinical_visit")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                typeFilter === "clinical_visit"
                  ? "bg-clinical-teal text-white shadow-subtle"
                  : "bg-teal-50 text-clinical-teal-dark hover:bg-teal-100"
              }`}
            >
              Clinical Visits
            </button>
            <button
              onClick={() => setTypeFilter("cognitive_assessment")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                typeFilter === "cognitive_assessment"
                  ? "bg-sky-700 text-white shadow-subtle"
                  : "bg-sky-50 text-sky-800 hover:bg-sky-100"
              }`}
            >
              Cognitive Tests
            </button>
            <button
              onClick={() => setTypeFilter("prediction")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                typeFilter === "prediction"
                  ? "bg-purple-700 text-white shadow-subtle"
                  : "bg-purple-50 text-purple-800 hover:bg-purple-100"
              }`}
            >
              AI Predictions
            </button>
            <button
              onClick={() => setTypeFilter("alert")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                typeFilter === "alert"
                  ? "bg-risk-critical text-white shadow-subtle"
                  : "bg-red-50 text-risk-critical hover:bg-red-100"
              }`}
            >
              Alerts
            </button>
          </div>

          <div className="relative w-64">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />
            <Input
              placeholder="Search event summary..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 text-xs h-9 bg-surface-subtle"
            />
          </div>
        </CardContent>
      </Card>

      {loading && <Spinner label="Loading longitudinal trajectory..." />}

      {/* Longitudinal Stream */}
      <Card>
        <CardHeader className="bg-surface-subtle/50 pb-3 border-b border-border">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Chronological Surveillance Trajectory</CardTitle>
              <CardDescription>Audited timeline of laboratory encounters, cognitive evaluations, and model inferences.</CardDescription>
            </div>
            <span className="text-xs font-semibold text-text-secondary tabular-nums">
              {filteredEvents.length} Recorded Milestone{filteredEvents.length === 1 ? "" : "s"}
            </span>
          </div>
        </CardHeader>

        <CardContent className="pt-6">
          <div className="space-y-6">
            {filteredEvents.map((e, idx) => {
              const type = (e.source_type || "").toLowerCase();
              const isVisit = type.includes("visit") || type.includes("encounter");
              const isCognitive = type.includes("cognitive");
              const isPred = type.includes("prediction");
              const isAlert = type.includes("alert");
              const isIntake = type.includes("intake") || type.includes("patient");

              return (
                <div key={e.id} className="relative flex gap-4 text-xs">
                  {idx !== filteredEvents.length - 1 && (
                    <span className="absolute left-4 top-8 h-full w-px bg-border" />
                  )}

                  {/* Icon Node */}
                  <div
                    className={`flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border shadow-subtle ${
                      isPred
                        ? "border-purple-200 bg-purple-50 text-purple-700"
                        : isAlert
                        ? "border-red-200 bg-red-50 text-risk-critical"
                        : isVisit
                        ? "border-teal-200 bg-clinical-teal-light text-clinical-teal-dark"
                        : isCognitive
                        ? "border-sky-200 bg-sky-50 text-sky-700"
                        : "border-slate-200 bg-surface-subtle text-text-secondary"
                    }`}
                  >
                    {isPred ? (
                      <BrainCircuit className="h-4 w-4" />
                    ) : isAlert ? (
                      <AlertTriangle className="h-4 w-4" />
                    ) : isVisit ? (
                      <FlaskConical className="h-4 w-4" />
                    ) : isCognitive ? (
                      <ClipboardList className="h-4 w-4" />
                    ) : (
                      <User className="h-4 w-4" />
                    )}
                  </div>

                  {/* Event Content Card */}
                  <div className="flex-1 rounded-xl border border-border bg-surface p-4 shadow-subtle hover:border-clinical-teal transition-colors">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-primary">
                          {isCognitive
                            ? "Formal Cognitive Assessment"
                            : isVisit
                            ? "Clinical Encounter & Lab Measurements"
                            : isPred
                            ? "AI Cognitive Impairment Prediction"
                            : isAlert
                            ? "Critical Clinical Alert"
                            : isIntake
                            ? "Patient Cohort Enrollment"
                            : e.source_type}
                        </span>

                        {isCognitive && <Badge variant="teal">Neurocognitive Ground Truth</Badge>}
                        {isPred && <Badge variant="moderate">AI Risk Inference</Badge>}
                        {isAlert && <Badge variant="critical">Clinical Alert</Badge>}
                      </div>

                      <span className="font-mono text-[11px] text-text-muted flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {new Date(e.event_time).toLocaleDateString()} at {new Date(e.event_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>

                    <p className="mt-1.5 text-xs text-text-secondary">
                      {e.summary || "Clinical encounter recorded."}
                    </p>

                    {/* Structured Payload Breakdown */}
                    {(() => {
                      const payload = e.payload;
                      if (!payload || Object.keys(payload).length === 0) return null;

                      const scores = payload.scores as Record<string, unknown> | undefined;
                      const measurements = payload.measurements as Record<string, unknown> | undefined;
                      const rawProbs = payload.probabilities;
                      const probabilities = (typeof rawProbs === "object" && rawProbs !== null ? rawProbs : {}) as Record<string, number>;

                      return (
                        <div className="mt-3 rounded-lg border border-border bg-surface-subtle p-3 text-[11px] space-y-2">
                          {/* Cognitive assessment scores */}
                          {Boolean(isCognitive && scores) && (
                            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                              {Object.entries(scores || {}).map(([k, v]) => (
                                <div key={k} className="rounded bg-surface p-2 border border-border/70">
                                  <span className="text-[10px] text-text-muted uppercase block">{k.replace("_", " ")}</span>
                                  <span className="font-bold text-xs text-text-primary">{String(v)}</span>
                                </div>
                              ))}
                            </div>
                          )}

                          {/* Clinical visit lab measurements */}
                          {Boolean(isVisit && measurements) && (
                            <div className="grid grid-cols-3 gap-2 sm:grid-cols-6 text-center">
                              {Object.entries(measurements || {})
                                .filter(([k]) => ["eGFR", "creatinine", "bun", "uacr", "systolic_bp", "bmi"].includes(k))
                                .map(([k, v]) => (
                                  <div key={k} className="rounded bg-surface p-1.5 border border-border/60">
                                    <span className="text-[9px] text-text-muted uppercase block">{k}</span>
                                    <span className="font-bold text-xs text-text-primary tabular-nums">{String(v)}</span>
                                  </div>
                                ))}
                            </div>
                          )}

                          {/* AI Prediction Probabilities Breakdown */}
                          {Boolean(isPred && rawProbs) && (
                            <div className="space-y-1.5">
                              <span className="text-[10px] uppercase font-semibold text-text-muted block">
                                Calibrated Multiclass Probabilities:
                              </span>
                              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                                {Object.entries(probabilities)
                                  .sort(([, a], [, b]) => Number(b) - Number(a))
                                  .map(([cls, prob]) => {
                                    const pct = Math.round(Number(prob) * 100);
                                    const isHigh = cls.toLowerCase().includes("high");
                                    const isMod = cls.toLowerCase().includes("moderate");
                                    const isLow = cls.toLowerCase().includes("low");

                                    return (
                                      <div key={cls} className="rounded bg-surface p-2 border border-border">
                                        <div className="flex items-center justify-between text-[11px]">
                                          <span className="font-medium text-text-primary truncate">{cls}</span>
                                          <span className="font-mono font-bold text-primary tabular-nums">{pct}%</span>
                                        </div>
                                        <div className="mt-1.5 h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                                          <div
                                            className={`h-full rounded-full ${
                                              isHigh
                                                ? "bg-risk-critical"
                                                : isMod
                                                ? "bg-risk-moderate"
                                                : isLow
                                                ? "bg-risk-normal"
                                                : "bg-slate-300"
                                            }`}
                                            style={{ width: `${Math.max(pct, 2)}%` }}
                                          />
                                        </div>
                                      </div>
                                    );
                                  })}
                              </div>
                            </div>
                          )}

                          {/* Other arbitrary payload items — format objects properly without [object Object] */}
                          {!isCognitive && !isVisit && (
                            <div className="flex flex-wrap gap-2 pt-1">
                              {Object.entries(payload)
                                .filter(([k]) => k !== "probabilities")
                                .map(([k, v]) => {
                                  if (v === null || v === undefined) return null;
                                  if (typeof v === "object") {
                                    return (
                                      <div key={k} className="w-full rounded bg-surface p-2 border border-border mt-1">
                                        <span className="font-semibold text-text-primary capitalize block text-[10px]">
                                          {k}:
                                        </span>
                                        <div className="flex flex-wrap gap-2 mt-1">
                                          {Object.entries(v as Record<string, unknown>).map(([subK, subV]) => (
                                            <span key={subK} className="rounded bg-surface-subtle px-2 py-0.5 text-[10px] text-text-secondary">
                                              <strong>{subK}:</strong> {String(subV)}
                                            </span>
                                          ))}
                                        </div>
                                      </div>
                                    );
                                  }
                                  return (
                                    <span key={k} className="inline-flex items-center gap-1 rounded bg-surface px-2 py-0.5 border border-border text-[10px]">
                                      <strong className="text-text-primary capitalize">{k}:</strong>
                                      <span className="text-text-secondary">{String(v)}</span>
                                    </span>
                                  );
                                })}
                            </div>
                          )}
                        </div>
                      );
                    })()}
                  </div>
                </div>
              );
            })}

            {!filteredEvents.length && !loading && (
              <div className="py-12 text-center text-text-muted">
                <Clock className="h-10 w-10 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-semibold text-text-primary">No Surveillance Events Match Filters</p>
                <p className="text-[11px] text-text-muted mt-1">Adjust filters or record a new visit encounter on the patient profile.</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
