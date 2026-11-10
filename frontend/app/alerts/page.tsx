"use client";

import { useEffect, useMemo, useState } from "react";
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
  Bell,
  AlertTriangle,
  CheckCircle2,
  Clock,
  User,
  BrainCircuit,
  Filter,
  Search,
  ChevronRight,
  ShieldAlert,
  PlusCircle,
  X,
  Activity,
  Check,
} from "lucide-react";

type AlertEvent = {
  id: number;
  rule_id?: number;
  patient_id?: number;
  status: "open" | "acknowledged" | "resolved" | string;
  created_at?: string;
  acknowledged_at?: string;
  payload?: Record<string, unknown>;
};

type PatientOption = {
  id: number;
  patient_identifier: string;
  first_name?: string;
  last_name?: string;
};

type StatusFilter = "all" | "open" | "acknowledged" | "resolved";

export default function AlertsPage() {
  const api = useApi();
  const { notify } = useToast();

  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [patients, setPatients] = useState<PatientOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [searchQuery, setSearchQuery] = useState("");

  // Create Alert Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [newAlert, setNewAlert] = useState({
    patient_id: "",
    severity: "critical",
    message: "Rapid eGFR decline (>5 mL/min/year) detected alongside elevated albuminuria.",
  });

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [alertsData, patientsData] = await Promise.all([
        api.get<AlertEvent[]>("/alerts/events"),
        api.get<PatientOption[]>("/patients/"),
      ]);
      setAlerts(alertsData || []);
      setPatients(patientsData || []);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load clinical alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [api]);

  const patientMap = useMemo(() => {
    const map = new Map<number, PatientOption>();
    for (const p of patients) {
      map.set(p.id, p);
    }
    return map;
  }, [patients]);

  const statusCounts = useMemo(() => {
    const counts = { open: 0, acknowledged: 0, resolved: 0 };
    for (const a of alerts) {
      if (a.status === "open") counts.open++;
      else if (a.status === "acknowledged") counts.acknowledged++;
      else if (a.status === "resolved") counts.resolved++;
    }
    return counts;
  }, [alerts]);

  const filteredAlerts = useMemo(() => {
    return alerts.filter((a) => {
      if (statusFilter !== "all" && a.status !== statusFilter) return false;
      if (!searchQuery.trim()) return true;

      const q = searchQuery.toLowerCase();
      const patient = a.patient_id ? patientMap.get(a.patient_id) : undefined;
      const patientName = `${patient?.first_name || ""} ${patient?.last_name || ""}`.toLowerCase();
      const patientIdentifier = (patient?.patient_identifier || "").toLowerCase();
      const message = String(a.payload?.message || a.payload?.detail || "").toLowerCase();

      return (
        patientName.includes(q) ||
        patientIdentifier.includes(q) ||
        message.includes(q) ||
        String(a.id).includes(q)
      );
    });
  }, [alerts, statusFilter, searchQuery, patientMap]);

  const handleAcknowledge = async (alertId: number) => {
    try {
      await api.post(`/alerts/events/${alertId}/ack`, {});
      notify(`Alert #${alertId} acknowledged`, "info");
      loadData();
    } catch (err: unknown) {
      notify(err instanceof Error ? err.message : "Failed to acknowledge alert", "error");
    }
  };

  const handleResolve = async (alertId: number) => {
    try {
      await api.post(`/alerts/events/${alertId}/resolve`, {});
      notify(`Alert #${alertId} marked as resolved`, "success");
      loadData();
    } catch (err: unknown) {
      notify(err instanceof Error ? err.message : "Failed to resolve alert", "error");
    }
  };

  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAlert.message.trim()) {
      notify("Alert message description is required", "error");
      return;
    }

    setSubmitting(true);
    try {
      const payload: Record<string, unknown> = {
        status: "open",
        payload: {
          message: newAlert.message.trim(),
          severity: newAlert.severity,
          source: "Manual Clinical Escalation",
        },
      };
      if (newAlert.patient_id) {
        payload.patient_id = Number(newAlert.patient_id);
      }

      await api.post("/alerts/events", payload);
      notify("Clinical surveillance alert dispatched successfully", "success");
      setShowCreateModal(false);
      setNewAlert({
        patient_id: "",
        severity: "critical",
        message: "",
      });
      loadData();
    } catch (err: unknown) {
      notify(err instanceof Error ? err.message : "Failed to dispatch alert", "error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between border-b border-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight text-primary">Critical Clinical Alerts</h1>
            <span className="rounded bg-red-100 px-2 py-0.5 text-xs font-semibold text-risk-critical">
              {statusCounts.open} Active Escalations
            </span>
          </div>
          <p className="text-xs text-text-secondary mt-1">
            Real-time threshold surveillance for rapid eGFR decline, critical albuminuria spikes, and cognitive deterioration.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="primary" size="sm" onClick={() => setShowCreateModal(true)}>
            <PlusCircle className="h-4 w-4 mr-1.5" />
            Dispatch Clinical Alert
          </Button>
          <Link href="/prediction">
            <Button variant="teal" size="sm">
              <BrainCircuit className="h-4 w-4 mr-1.5" />
              Risk Stratification
            </Button>
          </Link>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}

      {/* Metrics Ribbon & Filter Bar */}
      <Card>
        <CardContent className="p-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Status Filter Buttons */}
          <div className="flex flex-wrap items-center gap-1.5">
            <button
              onClick={() => setStatusFilter("all")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                statusFilter === "all"
                  ? "bg-primary text-white shadow-subtle"
                  : "bg-surface-subtle text-text-secondary hover:bg-slate-200"
              }`}
            >
              All Alerts ({alerts.length})
            </button>
            <button
              onClick={() => setStatusFilter("open")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                statusFilter === "open"
                  ? "bg-risk-critical text-white shadow-subtle"
                  : "bg-red-50 text-risk-critical hover:bg-red-100"
              }`}
            >
              Open / Urgent ({statusCounts.open})
            </button>
            <button
              onClick={() => setStatusFilter("acknowledged")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                statusFilter === "acknowledged"
                  ? "bg-risk-moderate text-white shadow-subtle"
                  : "bg-amber-50 text-risk-moderate hover:bg-amber-100"
              }`}
            >
              Acknowledged ({statusCounts.acknowledged})
            </button>
            <button
              onClick={() => setStatusFilter("resolved")}
              className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                statusFilter === "resolved"
                  ? "bg-risk-normal text-white shadow-subtle"
                  : "bg-emerald-50 text-risk-normal hover:bg-emerald-100"
              }`}
            >
              Resolved ({statusCounts.resolved})
            </button>
          </div>

          {/* Search Box */}
          <div className="relative w-72">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-text-muted" />
            <Input
              placeholder="Search alert text, MRN, or patient..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 text-xs h-9 bg-surface-subtle"
            />
          </div>
        </CardContent>
      </Card>

      {loading && <Spinner label="Loading clinical surveillance alerts..." />}

      {/* Alerts Grid */}
      <div className="space-y-3">
        {filteredAlerts.map((a) => {
          const patient = a.patient_id ? patientMap.get(a.patient_id) : undefined;
          const patientName = patient
            ? `${patient.first_name || ""} ${patient.last_name || ""}`.trim() || patient.patient_identifier
            : null;
          const isOpen = a.status === "open";
          const isAck = a.status === "acknowledged";
          const isResolved = a.status === "resolved";
          const messageText = String(a.payload?.message || a.payload?.detail || "Clinical surveillance threshold exceeded.");

          return (
            <Card
              key={a.id}
              className={`transition-all duration-150 ${
                isOpen
                  ? "border-red-300 bg-red-50/20 shadow-subtle"
                  : isAck
                  ? "border-amber-200 bg-amber-50/10"
                  : "border-border bg-surface"
              }`}
            >
              <CardContent className="p-4 sm:p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex items-start gap-3.5">
                    {/* Status Icon */}
                    <div
                      className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl border ${
                        isOpen
                          ? "border-red-200 bg-red-100 text-risk-critical"
                          : isAck
                          ? "border-amber-200 bg-amber-100 text-risk-moderate"
                          : "border-emerald-200 bg-emerald-100 text-risk-normal"
                      }`}
                    >
                      {isOpen ? (
                        <AlertTriangle className="h-5 w-5" />
                      ) : isAck ? (
                        <Clock className="h-5 w-5" />
                      ) : (
                        <CheckCircle2 className="h-5 w-5" />
                      )}
                    </div>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {isOpen && <Badge variant="critical">Urgent Escalation</Badge>}
                        {isAck && <Badge variant="elevated">Acknowledged</Badge>}
                        {isResolved && <Badge variant="normal">Resolved</Badge>}

                        <span className="text-[11px] font-mono text-text-muted">
                          Alert #{a.id}
                        </span>

                        {patient && (
                          <Link
                            href={`/patients/${patient.id}`}
                            className="inline-flex items-center gap-1 rounded bg-surface-subtle px-2 py-0.5 text-xs font-semibold text-primary hover:text-clinical-teal hover:bg-slate-200 transition-colors"
                          >
                            <User className="h-3 w-3 text-clinical-teal" />
                            <span>{patientName}</span>
                            <span className="font-mono text-[10px] text-text-muted">({patient.patient_identifier})</span>
                          </Link>
                        )}
                      </div>

                      <p className="text-sm font-semibold text-text-primary pt-0.5">
                        {messageText}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 text-[11px] text-text-muted pt-1">
                        <span>
                          Triggered: <strong className="text-text-secondary">{a.created_at ? new Date(a.created_at).toLocaleString() : "Recent"}</strong>
                        </span>
                        {a.acknowledged_at && (
                          <span>
                            • Acknowledged: <strong className="text-text-secondary">{new Date(a.acknowledged_at).toLocaleTimeString()}</strong>
                          </span>
                        )}
                        {Boolean(a.payload?.source) && (
                          <span>
                            • Source: <strong className="text-text-secondary">{String(a.payload?.source)}</strong>
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Action Controls */}
                  <div className="flex flex-wrap items-center gap-2 sm:self-center">
                    {isOpen && (
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => handleAcknowledge(a.id)}
                        className="text-xs"
                      >
                        <Clock className="h-3.5 w-3.5 mr-1 text-risk-moderate" />
                        Acknowledge
                      </Button>
                    )}

                    {!isResolved && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleResolve(a.id)}
                        className="text-xs hover:border-emerald-500 hover:text-risk-normal"
                      >
                        <Check className="h-3.5 w-3.5 mr-1 text-risk-normal" />
                        Resolve
                      </Button>
                    )}

                    {patient && (
                      <Link href={`/patients/${patient.id}`}>
                        <Button variant="ghost" size="sm" className="text-xs text-clinical-teal">
                          Patient Profile
                          <ChevronRight className="h-3.5 w-3.5 ml-0.5" />
                        </Button>
                      </Link>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}

        {!loading && !filteredAlerts.length && (
          <div className="rounded-xl border border-dashed border-border bg-surface py-12 text-center text-text-muted">
            <CheckCircle2 className="h-10 w-10 text-emerald-400 mx-auto mb-2" />
            <p className="text-xs font-semibold text-text-primary">No Clinical Alerts Match Filters</p>
            <p className="text-[11px] text-text-muted mt-1">Patient cohort parameters are within safe monitoring thresholds.</p>
          </div>
        )}
      </div>

      {/* DISPATCH NEW CLINICAL ALERT MODAL */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-xl border border-border bg-surface p-6 shadow-modal">
            <div className="flex items-center justify-between border-b border-border pb-3">
              <div className="flex items-center gap-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-risk-critical text-white">
                  <ShieldAlert className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-primary">Dispatch Clinical Surveillance Alert</h3>
                  <p className="text-[11px] text-text-muted">Trigger immediate notification for care team surveillance.</p>
                </div>
              </div>
              <button
                onClick={() => setShowCreateModal(false)}
                className="rounded p-1 text-text-muted hover:bg-surface-subtle"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleCreateAlert} className="mt-4 space-y-4">
              <div>
                <label className="text-xs font-semibold text-text-primary">Target Patient (Optional)</label>
                <select
                  value={newAlert.patient_id}
                  onChange={(e) => setNewAlert({ ...newAlert, patient_id: e.target.value })}
                  className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2.5 text-xs text-text-primary focus:border-clinical-teal focus:outline-none"
                >
                  <option value="">System-Wide Cohort Alert</option>
                  {patients.map((p) => (
                    <option key={p.id} value={String(p.id)}>
                      {p.patient_identifier} — {p.first_name || ""} {p.last_name || ""}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-text-primary">Alert Severity Tier</label>
                <select
                  value={newAlert.severity}
                  onChange={(e) => setNewAlert({ ...newAlert, severity: e.target.value })}
                  className="mt-1 h-9 w-full rounded-lg border border-border bg-surface px-2.5 text-xs text-text-primary focus:border-clinical-teal focus:outline-none"
                >
                  <option value="critical">Critical (Immediate Care Team Escalation)</option>
                  <option value="moderate">Moderate (Review at Next Encounter)</option>
                  <option value="info">Informational Note</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-text-primary">Clinical Alert Message*</label>
                <textarea
                  required
                  rows={3}
                  value={newAlert.message}
                  onChange={(e) => setNewAlert({ ...newAlert, message: e.target.value })}
                  className="mt-1 w-full rounded-lg border border-border bg-surface p-2.5 text-xs text-text-primary focus:border-clinical-teal focus:outline-none"
                  placeholder="e.g. Rapid eGFR decline detected (>5 mL/min/year) along with sudden albuminuria spike."
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-2 border-t border-border">
                <Button type="button" variant="secondary" size="sm" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
                <Button type="submit" variant="teal" size="sm" disabled={submitting}>
                  {submitting ? <Spinner label="Dispatching..." /> : "Dispatch Alert"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
