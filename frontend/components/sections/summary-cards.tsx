import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type Props = {
  patientCount: number;
  alertCount: number;
  taskCount: number;
  predictionCount: number;
};

export function SummaryCards({ patientCount, alertCount, taskCount, predictionCount }: Props) {
  const cards = [
    { title: "Active Patients", value: String(patientCount) },
    { title: "High-Risk Alerts", value: String(alertCount) },
    { title: "Pending Tasks", value: String(taskCount) },
    { title: "Predictions", value: String(predictionCount) },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((c) => (
        <Card key={c.title} className="bg-card/90">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-slate-400">{c.title}</CardTitle>
          </CardHeader>
          <CardContent className="text-2xl font-bold">{c.value}</CardContent>
        </Card>
      ))}
    </div>
  );
}
