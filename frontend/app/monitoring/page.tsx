"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useApi } from "@/hooks/use-api";
import { Spinner } from "@/components/ui/spinner";
import { ErrorBanner } from "@/components/ui/error-banner";

export default function MonitoringPage() {
  const api = useApi();
  const [summary, setSummary] = useState<Record<string, unknown> | null>(null);
  const [drift, setDrift] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [summaryData, driftData] = await Promise.all([
          api.get<Record<string, unknown>>("/monitoring/summary"),
          api.get<Record<string, unknown>>("/monitoring/drift"),
        ]);
        if (mounted) {
          setSummary(summaryData);
          setDrift(driftData);
        }
      } catch (e: unknown) {
        const err = e as Error;
        if (mounted) setError(err.message || "Failed to load monitoring data");
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
    <div className="grid gap-4 md:grid-cols-2">
      {loading && <Spinner label="Loading monitoring metrics..." />}
      {error && <ErrorBanner message={error} className="md:col-span-2" />}
      <Card>
        <CardHeader>
          <CardTitle>Service Health</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-slate-300">
          <div className="flex justify-between"><span>API</span><span className="text-green-400">Healthy</span></div>
          <div className="flex justify-between"><span>Drift Detected</span><span className="text-amber-300">{String(drift?.drift_detected ?? "N/A")}</span></div>
          <div className="flex justify-between"><span>Drift Score</span><span className="text-slate-100">{String(drift?.drift_score ?? "N/A")}</span></div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Metrics</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-slate-300">
          {summary ? (
            <pre className="whitespace-pre-wrap text-xs text-slate-300">{JSON.stringify(summary, null, 2)}</pre>
          ) : (
            <div>No metrics available.</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
