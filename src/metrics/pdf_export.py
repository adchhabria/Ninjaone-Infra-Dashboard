"""
Executive PDF Audit Report Generator for NinjaOne Infra Dashboard.

Generates a publication-grade, multi-page executive PDF compliance & operational audit document
containing the exact visual charts, world map, speedometer gauges, donut charts, bar charts,
and detailed audit data tables identical to the live browser dashboard.
"""

from __future__ import annotations

import io
from datetime import datetime, timezone
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from src.dashboard import charts, theme as T
from src.metrics.aggregator import DashboardData


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
    """Two-pass canvas to draw running headers, footers, and 'Page X of Y'."""

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

        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(40, 580, "NinjaOne IT Infrastructure & Compliance Executive Audit Report")
            self.drawRightString(750, 580, datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"))
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(40, 574, 750, 574)

        # Footer (all pages)
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(40, 30, 750, 30)

        self.drawString(40, 20, "CONFIDENTIAL — For Internal Management & Compliance Audit Use Only")
        self.drawRightString(750, 20, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def _fig_to_image_flowable(fig, width: int = 340, height: int = 180, scale: int = 1) -> Optional[Image]:
    """Converts a Plotly figure to a ReportLab Image Flowable via Kaleido."""
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, scale=scale, engine="kaleido")
        buf = io.BytesIO(img_bytes)
        return Image(buf, width=width, height=height)
    except Exception as e:
        print(f"[!] Chart render warning: {e}")
        return None


def generate_pdf_report(data: DashboardData, dashboard_url: str | None = None) -> bytes:
    """
    Generates a high-fidelity multi-page PDF audit report with embedded Plotly charts,
    world maps, speedometer gauges, and comprehensive compliance data tables.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=PRIMARY_COLOR,
        spaceAfter=3,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13,
        textColor=MUTED_TEXT,
        spaceAfter=8,
    )

    h2_style = ParagraphStyle(
        "Heading2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=PRIMARY_COLOR,
        spaceBefore=8,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
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

    # =======================================================================
    # PAGE 1: Executive KPI Summary & World Map
    # =======================================================================
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    story.append(Paragraph("NinjaOne IT Infrastructure & Compliance Audit Report", title_style))
    story.append(
        Paragraph(
            f"<b>Scope:</b> {data.active_filter_label} &nbsp;|&nbsp; "
            f"<b>Generated:</b> {ts} &nbsp;|&nbsp; "
            f"<b>Platform:</b> Live NinjaOne REST API Operational Engine",
            subtitle_style,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_BLUE, spaceBefore=0, spaceAfter=10))

    # Executive KPI Table Strip
    story.append(Paragraph("1. Executive Overview & Fleet Key Performance Indicators", h2_style))

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
            Paragraph(f"<font size=13><b>{data.total_devices}</b></font>", body_style),
            Paragraph(f"<font size=13><b>{data.online_pct:.1f}%</b></font>", body_style),
            Paragraph(f"<font size=13 color='{rag_color.hexval()}'><b>{data.overall_compliance_score:.1f}% ({data.compliance_rag})</b></font>", body_style),
            Paragraph(f"<font size=13><b>{patch_pct:.1f}%</b></font>", body_style),
            Paragraph(f"<font size=13><b>{data.total_servers}</b></font>", body_style),
            Paragraph(f"<font size=13 color='#CF222E'><b>{data.eol_risk_count}</b></font>", body_style),
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
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # World Map Graphic
    story.append(Paragraph("2. Geographic Infrastructure & Fleet Distribution Map", h2_style))
    map_fig = charts.world_map_chart(data.map_data, data.active_region)
    map_img = _fig_to_image_flowable(map_fig, width=710, height=270, scale=1)
    if map_img:
        story.append(map_img)

    story.append(PageBreak())

    # =======================================================================
    # PAGE 2: OS Landscape & Server Fleet Compliance
    # =======================================================================
    story.append(Paragraph("3. Operating System Landscape Breakdown (Windows & Linux)", h2_style))

    win_donut_fig = charts.windows_os_donut(data.os.get("windows_version_counts", {}))
    linux_donut_fig = charts.linux_os_donut(data.os.get("linux_version_counts", {}))

    win_img = _fig_to_image_flowable(win_donut_fig, width=350, height=200, scale=1)
    linux_img = _fig_to_image_flowable(linux_donut_fig, width=350, height=200, scale=1)

    if win_img and linux_img:
        os_charts_table = Table([[win_img, linux_img]], colWidths=[355, 355])
        os_charts_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(os_charts_table)
    elif win_img or linux_img:
        story.append(win_img or linux_img)

    story.append(Spacer(1, 8))

    story.append(Paragraph("4. Server Infrastructure: Multi-Cloud Hosting & Organization Distribution", h2_style))

    host_donut_fig = charts.hosting_donut(data.servers.get("hosting_counts", {}))
    stacked_bar_fig = charts.hosting_org_stacked_bar(data.servers.get("org_distribution", []))

    host_img = _fig_to_image_flowable(host_donut_fig, width=350, height=200, scale=1)
    stacked_img = _fig_to_image_flowable(stacked_bar_fig, width=350, height=200, scale=1)

    if host_img and stacked_img:
        server_charts_table = Table([[host_img, stacked_img]], colWidths=[355, 355])
        server_charts_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(server_charts_table)
    elif host_img or stacked_img:
        story.append(host_img or stacked_img)

    story.append(PageBreak())

    # =======================================================================
    # PAGE 3: Patch Speedometer Gauge & EOL Lifecycle
    # =======================================================================
    story.append(Paragraph("5. Patch Compliance Speedometer Gauge & SLA Backlog", h2_style))

    gauge_fig = charts.patch_gauge(patch_pct)
    gauge_img = _fig_to_image_flowable(gauge_fig, width=350, height=200, scale=1)

    # SLA Table beside Gauge
    sla_counts = data.sla.get("sla_counts", {})
    sla_data = [
        [
            Paragraph("SLA Aging Bracket", header_cell_style),
            Paragraph("Patches", header_cell_style),
            Paragraph("Risk Rating", header_cell_style),
        ],
        [
            Paragraph("< 7 Days", body_style),
            Paragraph(str(sla_counts.get("< 7 Days (Within SLA)", 0)), body_bold),
            Paragraph("<font color='#2EA043'><b>Within SLA</b></font>", body_style),
        ],
        [
            Paragraph("8 - 30 Days", body_style),
            Paragraph(str(sla_counts.get("8 - 30 Days (Warning)", 0)), body_bold),
            Paragraph("<font color='#D29922'><b>Warning</b></font>", body_style),
        ],
        [
            Paragraph("31 - 90 Days", body_style),
            Paragraph(str(sla_counts.get("31 - 90 Days (High Risk)", 0)), body_bold),
            Paragraph("<font color='#FF9800'><b>High Risk</b></font>", body_style),
        ],
        [
            Paragraph("> 90 Days", body_style),
            Paragraph(str(sla_counts.get("> 90 Days (SLA Breach)", 0)), body_bold),
            Paragraph("<font color='#CF222E'><b>CRITICAL BREACH</b></font>", body_style),
        ],
    ]

    sla_mini_table = Table(sla_data, colWidths=[130, 80, 130])
    sla_mini_table.setStyle(
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

    if gauge_img:
        patch_row_table = Table([[gauge_img, sla_mini_table]], colWidths=[355, 355])
        patch_row_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(patch_row_table)
    else:
        story.append(sla_mini_table)

    story.append(Spacer(1, 8))

    # EOL Charts
    story.append(Paragraph("6. End-of-Life (EOL) Analytics & At-Risk OS Versions", h2_style))

    eol_donut_fig = charts.eol_status_donut(data.os.get("eol_status_counts", {}))
    eol_bar_fig = charts.eol_by_os_bar(data.os.get("eol_by_os", {}))

    eol_donut_img = _fig_to_image_flowable(eol_donut_fig, width=350, height=200, scale=1)
    eol_bar_img = _fig_to_image_flowable(eol_bar_fig, width=350, height=200, scale=1)

    if eol_donut_img and eol_bar_img:
        eol_charts_table = Table([[eol_donut_img, eol_bar_img]], colWidths=[355, 355])
        eol_charts_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (0, 0), (-1, -1), "CENTER")]))
        story.append(eol_charts_table)
    elif eol_donut_img or eol_bar_img:
        story.append(eol_donut_img or eol_bar_img)

    story.append(PageBreak())

    # =======================================================================
    # PAGE 4: Detailed EOL Device Ledger
    # =======================================================================
    story.append(Paragraph("7. Detailed End-of-Life (EOL) Device Inventory & Risk Ledger", h2_style))
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

        for r in eol_rows[:28]:
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

    story.append(PageBreak())

    # =======================================================================
    # PAGE 5: Organization Compliance Ledger
    # =======================================================================
    story.append(Paragraph("8. Organization Compliance & Fleet Health Ledger", h2_style))
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

        for org in org_rows[:35]:
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

    # Build PDF
    doc.build(story, canvasmaker=MultiPageNumberedCanvas)
    return buffer.getvalue()
