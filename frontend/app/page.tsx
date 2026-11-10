import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  Database,
  FileSpreadsheet,
  LineChart,
  ShieldCheck,
  Stethoscope,
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background text-text-primary">
      {/* Top Navigation */}
      <header className="border-b border-border bg-surface px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary text-white shadow-subtle">
              <Activity className="h-5 w-5 text-teal-300" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-primary">CKD-CI</span>
              <span className="ml-2 rounded bg-clinical-teal-light px-1.5 py-0.5 text-[10px] font-semibold text-clinical-teal-dark">
                CDS Platform
              </span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="outline" size="sm">Clinician Sign In</Button>
            </Link>
            <Link href="/command-center">
              <Button variant="primary" size="sm">Open Command Center</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="border-b border-border bg-surface px-6 py-16 lg:py-24">
        <div className="mx-auto max-w-4xl text-center">
          <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-teal-200 bg-clinical-teal-light px-3 py-1 text-xs font-medium text-clinical-teal-dark">
            <ShieldCheck className="h-4 w-4" />
            Clinical Decision Support System for Nephrology
          </div>
          <h1 className="text-4xl font-bold tracking-tight text-primary sm:text-5xl lg:text-6xl">
            Early Cognitive Impairment Stratification in Chronic Kidney Disease
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-base text-text-secondary sm:text-lg">
            A validated clinical decision-support platform designed to assist nephrologists and care teams
            in detecting subclinical neurocognitive vulnerability across 18 biomarkers.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link href="/prediction">
              <Button variant="teal" size="lg" className="shadow-elevated">
                <BrainCircuit className="h-5 w-5 mr-1" />
                Launch Prediction Studio
                <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
            <Link href="/command-center">
              <Button variant="secondary" size="lg">
                View Cohort Surveillance
              </Button>
            </Link>
          </div>

          {/* Research Prototype Governance Disclaimer */}
          <div className="mt-8 inline-block rounded-lg border border-border bg-surface-subtle px-4 py-2 text-xs text-text-muted">
            <strong className="text-text-secondary">Clinical Governance Notice:</strong> Intended for clinical research and decision-support triage. Not an autonomous diagnostic instrument.
          </div>
        </div>
      </section>

      {/* 3-Step Guided Clinical Architecture */}
      <section className="px-6 py-16">
        <div className="mx-auto max-w-6xl">
          <div className="text-center mb-12">
            <h2 className="text-2xl font-bold tracking-tight text-primary sm:text-3xl">
              Engineered for the Clinician's Workflow
            </h2>
            <p className="mt-2 text-sm text-text-muted">
              Evidence-based predictive triage integrated seamlessly with standard nephrology laboratory panels.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-xl border border-border bg-surface p-6 shadow-subtle">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-subtle text-primary mb-4">
                <FileSpreadsheet className="h-5 w-5 text-clinical-teal" />
              </div>
              <div className="text-xs font-semibold text-clinical-teal uppercase tracking-wider">Step 1: Input Panel</div>
              <h3 className="mt-1 text-base font-semibold text-text-primary">18 Biomarker Intake</h3>
              <p className="mt-2 text-xs leading-relaxed text-text-secondary">
                Standardizes routine renal markers (eGFR, UACR, BUN, Creatinine), electrolytes, and metabolic comorbidities with configurable reference ranges.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-surface p-6 shadow-subtle">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-subtle text-primary mb-4">
                <BrainCircuit className="h-5 w-5 text-clinical-teal" />
              </div>
              <div className="text-xs font-semibold text-clinical-teal uppercase tracking-wider">Step 2: Inference Engine</div>
              <h3 className="mt-1 text-base font-semibold text-text-primary">Calibrated Probability</h3>
              <p className="mt-2 text-xs leading-relaxed text-text-secondary">
                Evaluates risk across 4 balanced tiers with Platt/Isotonic calibration to reflect true empirical likelihood instead of arbitrary heuristic scores.
              </p>
            </div>

            <div className="rounded-xl border border-border bg-surface p-6 shadow-subtle">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-surface-subtle text-primary mb-4">
                <LineChart className="h-5 w-5 text-clinical-teal" />
              </div>
              <div className="text-xs font-semibold text-clinical-teal uppercase tracking-wider">Step 3: Explainability</div>
              <h3 className="mt-1 text-base font-semibold text-text-primary">Explainable AI & Next Steps</h3>
              <p className="mt-2 text-xs leading-relaxed text-text-secondary">
                Surfaces the dominant laboratory contributors driving each prediction with KDIGO concordance guidelines and auditable records.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Model Specifications & Technical Audit */}
      <section className="border-t border-border bg-surface px-6 py-12">
        <div className="mx-auto max-w-6xl">
          <div className="rounded-xl border border-border bg-surface-subtle p-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <span className="text-xs font-semibold uppercase tracking-wider text-clinical-teal">Model Traceability</span>
                <h4 className="text-sm font-semibold text-text-primary mt-0.5">Active Production Pipeline Specification</h4>
                <p className="text-xs text-text-muted mt-1">
                  Engine: Multiclass Logistic Regression + StandardScaler (18 features) • Serialized at <code className="text-primary font-mono text-[11px]">results/model_bundle.pkl</code>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <Link href="/monitoring">
                  <Button variant="secondary" size="sm">Inspect Model Governance</Button>
                </Link>
                <Link href="/login">
                  <Button variant="primary" size="sm">Access Portal</Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
