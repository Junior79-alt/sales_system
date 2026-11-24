"""
PDF Invoice Generator — Tumia reportlab
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generate_invoice_pdf(invoice_data: dict, output_path: str) -> str:
    """
    Generate PDF invoice for an agent.
    
    Args:
        invoice_data: dict with keys:
            - staff_name, staff_email, month, days_worked
            - total_cash, total_float, total_lipa, total_all
            - initial_capital, monthly_profit
            - daily_data: list of dicts
        output_path: where to save PDF
    
    Returns:
        output_path
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=22,
        textColor=colors.HexColor('#1a237e'),
        alignment=TA_CENTER,
        spaceAfter=6,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=13,
        textColor=colors.HexColor('#1a237e'),
        spaceBefore=15,
        spaceAfter=8,
    )

    # ============ HEADER ============
    elements.append(Paragraph("📊 SALES SYSTEM", title_style))
    elements.append(Paragraph(
        f"Monthly Invoice — {invoice_data['month']}",
        subtitle_style
    ))

    # ============ STAFF INFO BOX ============
    staff_info = [
        [
            Paragraph(f"<b>👤 Staff:</b> {invoice_data['staff_name']}", styles['Normal']),
            Paragraph(f"<b>📅 Month:</b> {invoice_data['month']}", styles['Normal']),
        ],
        [
            Paragraph(f"<b>📧 Email:</b> {invoice_data['staff_email']}", styles['Normal']),
            Paragraph(f"<b>📊 Days worked:</b> {invoice_data['days_worked']}", styles['Normal']),
        ],
    ]
    info_table = Table(staff_info, colWidths=[3.5 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#e8eaf6')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#1a237e')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 0.2 * inch))

    # ============ SUMMARY TABLE ============
    elements.append(Paragraph("💰 Summary", heading_style))

    profit_color = '#2e7d32' if invoice_data['monthly_profit'] >= 0 else '#d32f2f'

    summary_data = [
        ['Item', 'Amount (TSh)'],
        ['💰 Total Cash', f"{invoice_data['total_cash']:,.0f}"],
        ['📱 Total Float', f"{invoice_data['total_float']:,.0f}"],
        ['💳 Total Lipa', f"{invoice_data['total_lipa']:,.0f}"],
        ['📊 Grand Total', f"{invoice_data['total_all']:,.0f}"],
        ['💼 Initial Capital', f"{invoice_data['initial_capital']:,.0f}"],
    ]
    summary_table = Table(summary_data, colWidths=[4 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(summary_table)

    # Profit row (highlighted)
    profit_data = [['📈 Monthly Profit', f"{invoice_data['monthly_profit']:,.0f} TSh"]]
    profit_table = Table(profit_data, colWidths=[4 * inch, 3 * inch])
    profit_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor(profit_color)),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor(profit_color)),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(profit_table)

    # ============ DAILY BREAKDOWN ============
    if invoice_data.get('daily_data'):
        elements.append(PageBreak())
        elements.append(Paragraph("📋 Daily Breakdown", heading_style))

        daily_data = [['#', 'Date', 'Cash', 'Float', 'Lipa', 'Total', 'Profit']]
        for i, d in enumerate(invoice_data['daily_data'], 1):
            daily_data.append([
                str(i),
                d['date'],
                f"{d['cash']:,.0f}",
                f"{d['total_float']:,.0f}",
                f"{d['total_lipa']:,.0f}",
                f"{d['daily_total']:,.0f}",
                f"{d['daily_profit']:,.0f}",
            ])

        daily_table = Table(
            daily_data,
            colWidths=[0.4 * inch, 1.1 * inch, 1 * inch, 1 * inch, 1 * inch, 1 * inch, 1 * inch],
            repeatRows=1,
        )
        daily_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a237e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#cccccc')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(daily_table)

    # ============ FOOTER ============
    elements.append(Spacer(1, 0.3 * inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#888888'),
        alignment=TA_CENTER,
    )
    elements.append(Paragraph(
        f"Generated by Sales System • {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}<br/>"
        "This invoice is generated automatically. Contact admin for any questions.",
        footer_style
    ))

    # Build PDF
    doc.build(elements)
    return output_path