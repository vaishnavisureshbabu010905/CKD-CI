"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useApi } from "@/hooks/use-api";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";

type AlertEvent = {
  id: number;
  patient_id?: number;
  status: string;
  payload?: Record<string, unknown>;
};

export default function AlertsPage() {
  const api = useApi();
  const [alerts, setAlerts] = useState<AlertEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await api.get<AlertEvent[]>("/alerts/events");
        if (mounted) setAlerts(data || []);
      } catch (e: unknown) {
        const err = e as Error;
        if (mounted) setError(err.message || "Failed to load alerts");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [api]);

  return (
    <div className="space-y-4">
      <h1 className="text-xl font-semibold">Alerts & Escalations</h1>
      {loading && <Spinner label="Loading alerts..." />}
      {error && <ErrorBanner message={error} />}
      <div className="grid gap-3 md:grid-cols-2">
        {alerts.map((a) => (
          <Card key={a.id} className="bg-card/80">
            <CardHeader className="flex items-center justify-between">
              <CardTitle>{a.patient_id ? `Patient #${a.patient_id}` : "System Alert"}</CardTitle>
              <Badge className={a.status === "open" ? "bg-red-500/30 text-red-100" : "bg-amber-500/30 text-amber-100"}>{a.status}</Badge>
            </CardHeader>
            <CardContent className="text-sm text-slate-300">{String(a.payload?.message || a.payload?.detail || `Alert ${a.id}`)}</CardContent>
          </Card>
        ))}
        {!loading && !alerts.length && <div className="text-sm text-slate-400">No alerts at the moment.</div>}
      </div>
    </div>
  );
}
