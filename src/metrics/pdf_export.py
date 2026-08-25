"""
Executive PDF Audit Report Generator for NinjaOne Infra Dashboard.

Generates a publication-grade, multi-page PDF compliance and operational audit document
capturing the exact visual graphics, maps, speedometer gauges, donut charts, and data tables
as seen on the browser using Playwright headless rendering with a ReportLab fallback.
"""

from __future__ import annotations

import io
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

from src.metrics.aggregator import DashboardData


def generate_pdf_report(data: DashboardData, dashboard_url: str = "http://localhost:8050") -> bytes:
    """
    Generates a multi-page executive PDF report.
    Attempts high-fidelity Playwright browser rendering to capture exact dashboard
    charts, gauge, map, and tables. Falls back to ReportLab if Playwright is unavailable.
    """
    try:
        pdf_bytes = _generate_playwright_pdf(dashboard_url)
        if pdf_bytes and len(pdf_bytes) > 5000:
            return pdf_bytes
    except Exception as e:
        print(f"[!] Playwright PDF export fallback triggered: {e}")

    return _generate_reportlab_pdf(data)


def _generate_playwright_pdf(url: str = "http://localhost:8050") -> bytes:
    """
    Renders the exact live dashboard graphics (charts, gauge, maps, cards, tables)
    into a multi-page PDF via Playwright headless Chromium.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1200})
        page.goto(url, wait_until="networkidle", timeout=25000)

        # Ensure Executive Overview tab is displayed
        try:
            page.locator(".nav-link", has_text="Executive Overview").click(timeout=3000)
            page.wait_for_timeout(2000)
        except Exception:
            pass

        # Apply executive print styling
        page.evaluate("""() => {
            const style = document.createElement('style');
            style.innerHTML = `
                @page {
                    size: 1600px auto;
                    margin: 20px;
                }
                body {
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                    background-color: #0D1117 !important;
                }
                .card {
                    break-inside: avoid !important;
                    page-break-inside: avoid !important;
                    margin-bottom: 24px !important;
                }
                .sticky-top, header, #open-settings-btn, #refresh-btn {
                    box-shadow: none !important;
                }
            `;
            document.head.appendChild(style);
        }""")

        page.wait_for_timeout(1000)

        pdf_bytes = page.pdf(
            width="1600px",
            print_background=True,
            margin={"top": "20px", "bottom": "20px", "left": "20px", "right": "20px"},
        )
        browser.close()
        return pdf_bytes


# ---------------------------------------------------------------------------
# Pure-Python ReportLab Engine (Fallback)
# ---------------------------------------------------------------------------

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PRIMARY_COLOR = colors.HexColor("#0D1117")
SECONDARY_COLOR = colors.HexColor("#161B22")
ACCENT_BLUE = colors.HexColor("#2F81F7")
TEXT_COLOR = colors.HexColor("#24292F")
MUTED_TEXT = colors.HexColor("#57606A")
BORDER_COLOR = colors.HexColor("#D0D7DE")
RAG_GREEN = colors.HexColor("#2EA043")
RAG_AMBER = colors.HexColor("#D29922")
RAG_RED = colors.HexColor("#CF222E")
LIGHT_BG = colors.HexColor("#F6F8FA")


class MultiPageNumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(MUTED_TEXT)

        if self._pageNumber > 1:
            self.drawString(40, 580, "NinjaOne IT Infrastructure & Compliance Executive Audit Report")
            self.drawRightString(750, 580, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(40, 574, 750, 574)

        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(40, 35, 750, 35)

        self.drawString(40, 24, "CONFIDENTIAL — For Internal Management & Compliance Audit Use Only")
        self.drawRightString(750, 24, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def _generate_reportlab_pdf(data: DashboardData) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=MUTED_TEXT,
        spaceAfter=12,
    )

    h2_style = ParagraphStyle(
        "Heading2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=PRIMARY_COLOR,
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=TEXT_COLOR,
    )

    body_bold = ParagraphStyle(
        "BodyBold",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    header_cell_style = ParagraphStyle(
        "HeaderCell",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
        alignment=0,
    )

    story = []

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph("NinjaOne IT Infrastructure & Compliance Audit Report", title_style))
    story.append(
        Paragraph(
            f"<b>Scope:</b> {data.active_filter_label} &nbsp;|&nbsp; "
            f"<b>Generated:</b> {ts} &nbsp;|&nbsp; "
            f"<b>Source:</b> Live NinjaOne REST API Platform",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE, spaceBefore=0, spaceAfter=14))

    # 1. Executive Summary & KPIs Table
    story.append(Paragraph("1. Executive Summary & Key Performance Indicators", h2_style))

    rag_color = RAG_GREEN if data.compliance_rag == "GREEN" else RAG_AMBER if data.compliance_rag == "AMBER" else RAG_RED
    patch_pct = data.patches.get("patch_coverage_pct", 0.0)

    kpi_data = [
        [
            Paragraph("Total Managed Devices", body_bold),
            Paragraph("Online Fleet %", body_bold),
            Paragraph("Overall Compliance Score", body_bold),
            Paragraph("Patch Coverage %", body_bold),
            Paragraph("Servers Managed", body_bold),
            Paragraph("EOL / At-Risk Devices", body_bold),
        ],
        [
            Paragraph(f"<font size=14><b>{data.total_devices}</b></font>", body_style),
            Paragraph(f"<font size=14><b>{data.online_pct:.1f}%</b></font>", body_style),
            Paragraph(f"<font size=14 color='{rag_color.hexval()}'><b>{data.overall_compliance_score:.1f}% ({data.compliance_rag})</b></font>", body_style),
            Paragraph(f"<font size=14><b>{patch_pct:.1f}%</b></font>", body_style),
            Paragraph(f"<font size=14><b>{data.total_servers}</b></font>", body_style),
            Paragraph(f"<font size=14 color='#CF222E'><b>{data.eol_risk_count}</b></font>", body_style),
        ],
    ]

    kpi_table = Table(kpi_data, colWidths=[120, 115, 135, 115, 110, 115])
    kpi_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BG),
            ("BACKGROUND", (0, 1), (-1, 1), colors.white),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ])
    )
    story.append(kpi_table)
    story.append(Spacer(1, 14))

    # 2. Patch Operations & SLA Aging
    story.append(Paragraph("2. Patch Operations & SLA Aging Backlog", h2_style))

    sla_counts = data.sla.get("sla_counts", {})
    sla_data = [
        [
            Paragraph("SLA Aging Bracket", header_cell_style),
            Paragraph("Pending Patches", header_cell_style),
            Paragraph("Risk Rating", header_cell_style),
            Paragraph("Enterprise Policy SLA", header_cell_style),
        ],
        [
            Paragraph("< 7 Days", body_style),
            Paragraph(str(sla_counts.get("< 7 Days (Within SLA)", 0)), body_bold),
            Paragraph("<font color='#2EA043'><b>Within SLA</b></font>", body_style),
            Paragraph("Standard rollout window", body_style),
        ],
        [
            Paragraph("8 - 30 Days", body_style),
            Paragraph(str(sla_counts.get("8 - 30 Days (Warning)", 0)), body_bold),
            Paragraph("<font color='#D29922'><b>Warning</b></font>", body_style),
            Paragraph("Requires scheduling intervention", body_style),
        ],
        [
            Paragraph("31 - 90 Days", body_style),
            Paragraph(str(sla_counts.get("31 - 90 Days (High Risk)", 0)), body_bold),
            Paragraph("<font color='#FF9800'><b>High Risk</b></font>", body_style),
            Paragraph("Action plan required within 48 hours", body_style),
        ],
        [
            Paragraph("> 90 Days", body_style),
            Paragraph(str(sla_counts.get("> 90 Days (SLA Breach)", 0)), body_bold),
            Paragraph("<font color='#CF222E'><b>CRITICAL SLA BREACH</b></font>", body_style),
            Paragraph("Immediate remediation required", body_style),
        ],
    ]

    sla_table = Table(sla_data, colWidths=[150, 120, 180, 260])
    sla_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SECONDARY_COLOR),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(sla_table)
    story.append(Spacer(1, 14))

    # 3. Server Fleet & Hosting
    story.append(Paragraph("3. Server Fleet & Multi-Cloud Hosting Classification", h2_style))
    hosting_counts = data.servers.get("hosting_counts", {})
    hosting_data = [
        [
            Paragraph("AWS Cloud", header_cell_style),
            Paragraph("Microsoft Azure", header_cell_style),
            Paragraph("Google Cloud (GCP)", header_cell_style),
            Paragraph("Virtual Machines (VMs)", header_cell_style),
            Paragraph("Physical Bare-Metal", header_cell_style),
        ],
        [
            Paragraph(f"<b>{hosting_counts.get('AWS', 0)}</b> servers", body_style),
            Paragraph(f"<b>{hosting_counts.get('Azure', 0)}</b> servers", body_style),
            Paragraph(f"<b>{hosting_counts.get('GCP', 0)}</b> servers", body_style),
            Paragraph(f"<b>{hosting_counts.get('Virtual Machine', 0)}</b> servers", body_style),
            Paragraph(f"<b>{hosting_counts.get('Physical Hardware', 0)}</b> servers", body_style),
        ],
    ]
    host_table = Table(hosting_data, colWidths=[142, 142, 142, 142, 142])
    host_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), SECONDARY_COLOR),
            ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    story.append(host_table)

    story.append(PageBreak())

    # 4. EOL Ledger
    story.append(Paragraph("4. End-of-Life (EOL) & Obsolete OS Device Audit Ledger", h2_style))
    eol_rows = data.os.get("eol_table_data", [])

    if eol_rows:
        eol_table_headers = [
            Paragraph("Device Name", header_cell_style),
            Paragraph("Organization", header_cell_style),
            Paragraph("Region", header_cell_style),
            Paragraph("OS Build", header_cell_style),
            Paragraph("EOL Date", header_cell_style),
            Paragraph("Overdue", header_cell_style),
            Paragraph("Risk Level", header_cell_style),
        ]
        eol_table_content = [eol_table_headers]

        for r in eol_rows[:25]:
            risk_color = "#CF222E" if r.get("risk_level") in ["CRITICAL", "HIGH"] else "#D29922"
            eol_table_content.append([
                Paragraph(r.get("name", "N/A"), body_bold),
                Paragraph(r.get("org_name", "N/A"), body_style),
                Paragraph(r.get("region", "N/A"), body_style),
                Paragraph(r.get("os", "N/A"), body_style),
                Paragraph(str(r.get("eol_date", "N/A")), body_style),
                Paragraph(f"{r.get('days_overdue', 0)}d", body_style),
                Paragraph(f"<font color='{risk_color}'><b>{r.get('risk_level', 'MEDIUM')}</b></font>", body_style),
            ])

        eol_doc_table = Table(eol_table_content, colWidths=[120, 130, 95, 140, 85, 65, 75])
        eol_doc_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), SECONDARY_COLOR),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        story.append(eol_doc_table)
    else:
        story.append(Paragraph("✅ <b>No devices currently operating past End-of-Life date.</b>", body_style))

    story.append(Spacer(1, 14))

    # 5. Org Compliance Table
    story.append(Paragraph("5. Organization Compliance & Health Ledger", h2_style))
    org_rows = data.org_table

    if org_rows:
        org_headers = [
            Paragraph("Organization Name", header_cell_style),
            Paragraph("Region", header_cell_style),
            Paragraph("Devices", header_cell_style),
            Paragraph("Online %", header_cell_style),
            Paragraph("Patch %", header_cell_style),
            Paragraph("OS %", header_cell_style),
            Paragraph("EOL Devs", header_cell_style),
            Paragraph("Score", header_cell_style),
            Paragraph("Status", header_cell_style),
        ]
        org_content = [org_headers]

        for org in org_rows[:30]:
            rag = org.get("rag", "RED")
            r_col = "#2EA043" if rag == "GREEN" else "#D29922" if rag == "AMBER" else "#CF222E"
            org_content.append([
                Paragraph(org.get("org_name", "N/A"), body_bold),
                Paragraph(org.get("region", "N/A"), body_style),
                Paragraph(str(org.get("device_count", 0)), body_style),
                Paragraph(f"{org.get('online_pct', 0.0):.1f}%", body_style),
                Paragraph(f"{org.get('patch_pct', 0.0):.1f}%", body_style),
                Paragraph(f"{org.get('os_pct', 0.0):.1f}%", body_style),
                Paragraph(str(org.get("eol_count", 0)), body_style),
                Paragraph(f"<b>{org.get('compliance_score', 0.0):.1f}%</b>", body_style),
                Paragraph(f"<font color='{r_col}'><b>{rag}</b></font>", body_style),
            ])

        org_doc_table = Table(org_content, colWidths=[140, 100, 55, 60, 60, 60, 65, 55, 75])
        org_doc_table.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), SECONDARY_COLOR),
                ("BOX", (0, 0), (-1, -1), 1, BORDER_COLOR),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ])
        )
        story.append(org_doc_table)

    doc.build(story, canvasmaker=MultiPageNumberedCanvas)
    return buffer.getvalue()
