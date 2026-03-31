"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useApi } from "@/hooks/use-api";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";

type Patient = {
  id: number;
  patient_identifier: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  sex?: string;
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

type TimelineEvent = {
  id: number;
  source_type: string;
  summary?: string;
  event_time: string;
};

type RiskFilter = "all" | "high" | "moderate" | "low" | "unknown";
type TimeWindow = "all" | "7d" | "30d" | "90d";

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
  return age;
}

function normalizeRisk(value?: string): RiskFilter {
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

function getWindowDays(window: TimeWindow): number | null {
  if (window === "7d") return 7;
  if (window === "30d") return 30;
  if (window === "90d") return 90;
  return null;
}

function isInWindow(iso: string | undefined, window: TimeWindow): boolean {
  if (!iso) return false;
  const days = getWindowDays(window);
  if (!days) return true;
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return false;
  return dt.getTime() >= Date.now() - days * 24 * 60 * 60 * 1000;
}

function buildSparklinePath(points: number[], width: number, height: number): string {
  if (points.length === 0) return "";
  const max = Math.max(1, ...points);
  return points
    .map((v, i) => {
      const x = (i / Math.max(1, points.length - 1)) * width;
      const y = height - (v / max) * height;
      return `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
}

export default function PatientsPage() {
  const api = useApi();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [predictions, setPredictions] = useState<PredictionHistory[]>([]);
  const [timelineByPatient, setTimelineByPatient] = useState<Map<number, TimelineEvent[]>>(new Map());
  const [query, setQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState<RiskFilter>("all");
  const [timeWindow, setTimeWindow] = useState<TimeWindow>("30d");
  const [sortBy, setSortBy] = useState<"name" | "age" | "risk">("name");
  const [loading, setLoading] = useState(true);
  const [timelineLoading, setTimelineLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [patientData, predictionData] = await Promise.allSettled([
          api.get<Patient[]>("/patients/"),
          api.get<PredictionHistory[]>("/predictions/history?limit=300"),
        ]);
        if (!mounted) return;
        setPatients(patientData.status === "fulfilled" ? patientData.value || [] : []);
        setPredictions(predictionData.status === "fulfilled" ? predictionData.value || [] : []);

        const failures: string[] = [];
        if (patientData.status === "rejected") failures.push("patients");
        if (predictionData.status === "rejected") failures.push("predictions");
        if (failures.length) setError(`Some data could not be loaded: ${failures.join(", ")}`);
      } catch (e: unknown) {
        const err = e as Error;
        if (mounted) setError(err.message || "Failed to load patients");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [api]);

  useEffect(() => {
    let mounted = true;
    const loadTimelines = async () => {
      if (!patients.length) {
        setTimelineByPatient(new Map());
        return;
      }
      setTimelineLoading(true);
      try {
        const responses = await Promise.allSettled(
          patients.map((p) => api.get<TimelineEvent[]>(`/timeline/${p.id}`))
        );
        if (!mounted) return;
        const next = new Map<number, TimelineEvent[]>();
        responses.forEach((resp, idx) => {
          if (resp.status === "fulfilled") {
            next.set(patients[idx].id, resp.value || []);
          } else {
            next.set(patients[idx].id, []);
          }
        });
        setTimelineByPatient(next);
      } catch {
        if (mounted) setTimelineByPatient(new Map());
      } finally {
        if (mounted) setTimelineLoading(false);
      }
    };
    void loadTimelines();
    return () => {
      mounted = false;
    };
  }, [api, patients]);

  const latestPredictionByPatient = useMemo(() => {
    const grouped = new Map<number, PredictionHistory[]>();
    for (const p of predictions) {
      if (!p.patient_id) continue;
      const arr = grouped.get(p.patient_id) || [];
      arr.push(p);
      grouped.set(p.patient_id, arr);
    }

    const selected = new Map<number, PredictionHistory>();
    grouped.forEach((arr, patientId) => {
      const inWindow = arr.find((entry) => isInWindow(entry.created_at, timeWindow));
      if (inWindow) {
        selected.set(patientId, inWindow);
      } else if (timeWindow === "all" && arr[0]) {
        selected.set(patientId, arr[0]);
      }
    });
    return selected;
  }, [predictions, timeWindow]);

  const filtered = useMemo(() => {
    const value = query.trim().toLowerCase();
    let list = patients.filter((p) => {
      const name = `${p.first_name || ""} ${p.last_name || ""}`.trim().toLowerCase();
      const matchesText = !value || p.patient_identifier.toLowerCase().includes(value) || name.includes(value);
      if (!matchesText) return false;

      if (riskFilter === "all") return true;
      const prediction = latestPredictionByPatient.get(p.id);
      return normalizeRisk(prediction?.predicted_label) === riskFilter;
    });

    if (sortBy === "age") {
      list = [...list].sort((a, b) => (getAge(b.date_of_birth) || -1) - (getAge(a.date_of_birth) || -1));
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

  const riskCounts = useMemo(() => {
    const counts = { high: 0, moderate: 0, low: 0, unknown: 0 };
    for (const p of patients) {
      const risk = normalizeRisk(latestPredictionByPatient.get(p.id)?.predicted_label);
      counts[risk] += 1;
    }
    return counts;
  }, [patients, latestPredictionByPatient]);

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-border bg-gradient-to-r from-slate-900 to-slate-950 p-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-xl font-semibold">Patients</h1>
          <Input className="max-w-xs" placeholder="Search patients" value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2">
          <Button variant={riskFilter === "all" ? "default" : "outline"} onClick={() => setRiskFilter("all")}>All ({patients.length})</Button>
          <Button variant={riskFilter === "high" ? "default" : "outline"} onClick={() => setRiskFilter("high")}>High ({riskCounts.high})</Button>
          <Button variant={riskFilter === "moderate" ? "default" : "outline"} onClick={() => setRiskFilter("moderate")}>Moderate ({riskCounts.moderate})</Button>
          <Button variant={riskFilter === "low" ? "default" : "outline"} onClick={() => setRiskFilter("low")}>Low ({riskCounts.low})</Button>
          <Button variant={riskFilter === "unknown" ? "default" : "outline"} onClick={() => setRiskFilter("unknown")}>Unknown ({riskCounts.unknown})</Button>
          <div className="flex items-center gap-1 rounded-md border border-border/70 bg-slate-900/50 p-1">
            <Button size="sm" variant={timeWindow === "7d" ? "default" : "ghost"} onClick={() => setTimeWindow("7d")}>7d</Button>
            <Button size="sm" variant={timeWindow === "30d" ? "default" : "ghost"} onClick={() => setTimeWindow("30d")}>30d</Button>
            <Button size="sm" variant={timeWindow === "90d" ? "default" : "ghost"} onClick={() => setTimeWindow("90d")}>90d</Button>
            <Button size="sm" variant={timeWindow === "all" ? "default" : "ghost"} onClick={() => setTimeWindow("all")}>All</Button>
          </div>
          <div className="ml-auto flex items-center gap-2 text-sm text-slate-300">
            <span>Sort</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as "name" | "age" | "risk")}
              className="h-9 rounded-md border border-border bg-background px-2"
            >
              <option value="name">Name</option>
              <option value="age">Age</option>
              <option value="risk">Risk</option>
            </select>
          </div>
        </div>
      </div>
      {loading && <Spinner label="Loading patients..." />}
      {timelineLoading && !loading && <Spinner label="Updating patient trend windows..." />}
      {error && <ErrorBanner message={error} />}
      <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
        {filtered.map((p) => (
          <Link key={p.id} href={`/patients/${p.id}`}>
            <Card className="group border-border/70 transition-all duration-200 hover:-translate-y-0.5 hover:border-accent/70 hover:shadow-[0_10px_30px_rgba(0,0,0,0.25)]">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">{`${p.first_name || ""} ${p.last_name || ""}`.trim() || "Unknown Patient"}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-slate-300">
                {(() => {
                  const age = getAge(p.date_of_birth);
                  const latestPrediction = latestPredictionByPatient.get(p.id);
                  const risk = normalizeRisk(latestPrediction?.predicted_label);
                  const probs = latestPrediction?.probabilities || {};
                  const high = Math.max(0, Math.round((probs.high || 0) * 100));
                  const moderate = Math.max(0, Math.round((probs.moderate || 0) * 100));
                  const low = Math.max(0, Math.round((probs.low || 0) * 100));
                  const unknown = Math.max(0, 100 - high - moderate - low);
                  const features = p.features || {};
                  const egfr = valueAsNumber(features.egfr || features.eGFR, 0);
                  const creatinine = valueAsNumber(features.creatinine, 0);
                  const uacr = valueAsNumber(features.uacr, 0);
                  const metricMax = Math.max(1, egfr, creatinine * 30, uacr / 10);
                  const timeline = timelineByPatient.get(p.id) || [];
                  const windowedTimeline = timeline.filter((t) => isInWindow(t.event_time, timeWindow));

                  const bins = 10;
                  const startTs = (() => {
                    const days = getWindowDays(timeWindow);
                    if (days) return Date.now() - days * 24 * 60 * 60 * 1000;
                    const firstEvent = timeline.length ? new Date(timeline[timeline.length - 1].event_time).getTime() : Date.now() - 90 * 24 * 60 * 60 * 1000;
                    return Number.isFinite(firstEvent) ? firstEvent : Date.now() - 90 * 24 * 60 * 60 * 1000;
                  })();
                  const endTs = Date.now();
                  const step = Math.max(1, Math.floor((endTs - startTs) / bins));
                  const sparklinePoints = Array.from({ length: bins }, (_, i) => {
                    const bucketStart = startTs + i * step;
                    const bucketEnd = bucketStart + step;
                    return windowedTimeline.filter((t) => {
                      const ts = new Date(t.event_time).getTime();
                      return ts >= bucketStart && ts < bucketEnd;
                    }).length;
                  });
                  const sparklinePath = buildSparklinePath(sparklinePoints, 180, 36);

                  return (
                    <>
                      <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                        <div>ID: <span className="text-slate-200">{p.patient_identifier}</span></div>
                        <div>Sex: <span className="text-slate-200 capitalize">{p.sex || "N/A"}</span></div>
                        <div>Age: <span className="text-slate-200">{age ?? "N/A"}</span></div>
                        <div>Date: <span className="text-slate-200">{p.date_of_birth || "N/A"}</span></div>
                      </div>

                      <div className="rounded-md border border-border/80 bg-slate-900/60 p-2">
                        <div className="mb-2 flex items-center justify-between text-xs">
                          <span className="text-slate-400">Risk Pie</span>
                          <span className={`capitalize ${risk === "high" ? "text-rose-300" : risk === "moderate" ? "text-amber-300" : risk === "low" ? "text-emerald-300" : "text-slate-400"}`}>{risk}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <div
                            className="h-14 w-14 rounded-full border border-border transition-transform duration-200 group-hover:scale-105"
                            title={`High: ${high}% | Moderate: ${moderate}% | Low: ${low}% | Unknown: ${unknown}%`}
                            style={{
                              background: `conic-gradient(#f43f5e 0 ${high}%, #f59e0b ${high}% ${high + moderate}%, #34d399 ${high + moderate}% ${high + moderate + low}%, #64748b ${high + moderate + low}% 100%)`,
                            }}
                          />
                          <div className="space-y-1 text-[11px] text-slate-400">
                            <div>High {high}%</div>
                            <div>Moderate {moderate}%</div>
                            <div>Low {low}%</div>
                            {unknown > 0 && <div>Unknown {unknown}%</div>}
                          </div>
                        </div>
                      </div>

                      <div className="rounded-md border border-border/80 bg-slate-900/60 p-2">
                        <div className="mb-2 text-xs text-slate-400">Clinical Graph</div>
                        <div className="flex h-20 items-end gap-2">
                          {[
                            { key: "eGFR", value: egfr, color: "bg-cyan-400" },
                            { key: "Creat", value: creatinine * 30, color: "bg-fuchsia-400" },
                            { key: "UACR", value: uacr / 10, color: "bg-emerald-400" },
                          ].map((item) => {
                            const h = Math.max(8, Math.round((item.value / metricMax) * 64));
                            return (
                              <div key={item.key} className="flex flex-1 flex-col items-center gap-1">
                                <div className="text-[10px] text-slate-400">{item.key}</div>
                                <div
                                  title={`${item.key}: ${item.key === "Creat" ? creatinine.toFixed(2) : item.key === "UACR" ? uacr.toFixed(0) : egfr.toFixed(0)}`}
                                  className={`w-full rounded-t ${item.color} transition-all duration-200 group-hover:brightness-110`}
                                  style={{ height: h }}
                                />
                              </div>
                            );
                          })}
                        </div>
                      </div>

                      <div className="rounded-md border border-border/80 bg-slate-900/60 p-2">
                        <div className="mb-2 flex items-center justify-between text-xs text-slate-400">
                          <span>Activity Trend ({timeWindow})</span>
                          <span>{windowedTimeline.length} events</span>
                        </div>
                        <svg width="100%" height="42" viewBox="0 0 180 42" preserveAspectRatio="none" className="block">
                          <path d="M0,40 L180,40" stroke="rgba(148,163,184,0.35)" strokeWidth="1" fill="none" />
                          <path d={sparklinePath} stroke="#22d3ee" strokeWidth="2" fill="none" />
                        </svg>
                      </div>
                    </>
                  );
                })()}
              </CardContent>
            </Card>
          </Link>
        ))}
        {!loading && !filtered.length && <div className="text-sm text-slate-400">No patients found.</div>}
      </div>
    </div>
  );
}
