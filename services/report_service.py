from __future__ import annotations

from io import BytesIO
from typing import Dict, List

from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt


def _line_items(data: Dict[str, object]) -> List[str]:
    items = [
        "CKD Cognitive Risk Report",
        "",
        f"Patient: {data.get('patient_identifier', 'n/a')}",
        f"Prediction ID: {data.get('prediction_id', 'n/a')}",
        f"Model Version: {data.get('model_version', 'n/a')}",
        f"Predicted Label: {data.get('predicted_label', 'n/a')}",
        f"Confidence: {data.get('confidence', 'n/a')}",
        "",
        "Clinical Interpretation:",
        str(data.get('interpretation', 'n/a')),
        "",
        "Recommended Next Step:",
        str(data.get('recommended_next_step', 'n/a')),
        "",
        "Top Risk Drivers:",
    ]

    for i, driver in enumerate(data.get("risk_drivers", [])[:10], start=1):
        items.append(f"{i}. {driver}")

    items.append("")
    items.append("Actions:")
    for i, action in enumerate(data.get("actions", []), start=1):
        items.append(f"{i}. {action}")

    return items


def build_pdf_report(data: Dict[str, object]) -> bytes:
    buffer = BytesIO()
    with PdfPages(buffer) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69))
        ax = fig.add_subplot(111)
        ax.axis("off")

        lines = _line_items(data)
        y = 0.98
        for line in lines:
            ax.text(0.03, y, line, fontsize=10, va="top", ha="left", family="DejaVu Sans")
            y -= 0.028
            if y < 0.06:
                pdf.savefig(fig)
                plt.close(fig)
                fig = plt.figure(figsize=(8.27, 11.69))
                ax = fig.add_subplot(111)
                ax.axis("off")
                y = 0.98

        pdf.savefig(fig)
        plt.close(fig)

    return buffer.getvalue()
