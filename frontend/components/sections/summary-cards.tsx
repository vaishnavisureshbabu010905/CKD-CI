import { Card, CardContent } from "@/components/ui/card";
import { Users, AlertTriangle, CheckSquare, BrainCircuit } from "lucide-react";

type Props = {
  patientCount: number;
  alertCount: number;
  taskCount: number;
  predictionCount: number;
};

export function SummaryCards({ patientCount, alertCount, taskCount, predictionCount }: Props) {
  const cards = [
    {
      title: "Active Patients",
      value: String(patientCount),
      subtitle: "Enrolled in Surveillance",
      icon: Users,
      color: "text-primary",
      bg: "bg-surface-subtle",
    },
    {
      title: "High-Risk Alerts",
      value: String(alertCount),
      subtitle: "Requires Clinical Action",
      icon: AlertTriangle,
      color: "text-risk-critical",
      bg: "bg-risk-critical-bg",
    },
    {
      title: "Pending Care Tasks",
      value: String(taskCount),
      subtitle: "Lab & MoCA Follow-ups",
      icon: CheckSquare,
      color: "text-risk-moderate",
      bg: "bg-risk-moderate-bg",
    },
    {
      title: "Model Inferences",
      value: String(predictionCount),
      subtitle: "Logged Predictions",
      icon: BrainCircuit,
      color: "text-clinical-teal",
      bg: "bg-clinical-teal-light",
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((c) => {
        const Icon = c.icon;
        return (
          <Card key={c.title} className="bg-surface hover:shadow-card transition-shadow duration-150">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                  {c.title}
                </div>
                <div className="text-2xl font-bold tracking-tight text-text-primary mt-1 tabular-nums">
                  {c.value}
                </div>
                <div className="text-[11px] text-text-muted mt-0.5">{c.subtitle}</div>
              </div>
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${c.bg}`}>
                <Icon className={`h-5 w-5 ${c.color}`} />
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
