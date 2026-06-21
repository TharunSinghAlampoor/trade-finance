from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO


# ======================================================
# TRADE PDF LAYOUT RENDERER (RESTRICTED TIMELINE)
# ======================================================
def render_trade_pdf(layout: dict) -> BytesIO:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    story = []

    # ==================================================
    # TITLE (WITH TRADE NUMBER)
    # ==================================================
    trade_number = layout["trade_table"][0][1]

    story.append(
        Paragraph(f"<b>TRADE — {trade_number}</b>", styles["Title"])
    )
    story.append(Spacer(1, 14))

    # ==================================================
    # TRADE TABLE
    # ==================================================
    trade_table = Table(
        layout["trade_table"],
        colWidths=[150, 350],
    )
    trade_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(trade_table)
    story.append(Spacer(1, 22))

    # ==================================================
    # PARTICIPANTS
    # ==================================================
    story.append(Paragraph("<b>Participants</b>", styles["Heading2"]))
    story.append(Spacer(1, 10))

    participants = layout["participants"]

    party_table = Table(
        [
            ["Buyer", "Seller", "Bank"],
            [
                f"ID: {participants['buyer']['id']}\nEmail: {participants['buyer']['email']}",
                f"ID: {participants['seller']['id']}\nEmail: {participants['seller']['email']}",
                f"ID: {participants['bank']['id']}\nEmail: {participants['bank']['email']}",
            ],
        ],
        colWidths=[170, 170, 170],
    )

    party_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("ALIGN", (0, 1), (-1, 1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(party_table)
    story.append(Spacer(1, 22))

    # ==================================================
    # TRADE TIMELINE (RESTRICTED TO CURRENT STATUS)
    # ==================================================
    story.append(Paragraph("<b>Trade Timeline</b>", styles["Heading2"]))
    story.append(Spacer(1, 10))

    # ---------- STATUS ORDER (CANONICAL) ----------
    status_order = [
        "initiated",
        "seller_confirmed",
        "documents_uploaded",
        "bank_reviewing",
        "bank_approved",
        "payment_released",
        "completed",
    ]

    current_status = layout.get("current_status")

    # Find cutoff index
    cutoff_index = None
    if current_status in status_order:
        cutoff_index = status_order.index(current_status)

    # Restrict history
    filtered_history = []
    for h in layout["history"]:
        if cutoff_index is None:
            filtered_history.append(h)
        else:
            if h["status"] in status_order and \
               status_order.index(h["status"]) <= cutoff_index:
                filtered_history.append(h)

    history_rows = [["S.No", "Status", "Remarks", "Changed By", "Created At"]]
    for h in filtered_history:
        history_rows.append([
            h["sno"],
            h["status"],
            h["remark"],
            h["changed_by"] or "-",
            str(h["created_at"]),
        ])

    history_table = Table(
        history_rows,
        repeatRows=1,
        colWidths=[40, 90, 170, 80, 120],
    )
    history_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (0, -1), "CENTER"),
        ("ALIGN", (1, 1), (2, -1), "LEFT"),
        ("ALIGN", (3, 1), (3, -1), "CENTER"),
        ("ALIGN", (4, 1), (4, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(history_table)
    story.append(Spacer(1, 22))

    # ==================================================
    # LEDGER TIMINGS (UNCHANGED)
    # ==================================================
    story.append(Paragraph("<b>Ledger Timings</b>", styles["Heading2"]))
    story.append(Spacer(1, 10))

    ledger_rows = [["Status", "Remarks", "Changed By", "Created At"]]
    for l in layout["ledger"]:
        ledger_rows.append([
            l["status"],
            l["remark"],
            l["changed_by"],
            str(l["created_at"]),
        ])

    ledger_table = Table(
        ledger_rows,
        repeatRows=1,
        colWidths=[90, 220, 90, 110],
    )
    ledger_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.75, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 1), (1, -1), "LEFT"),
        ("ALIGN", (2, 1), (2, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "LEFT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    story.append(ledger_table)

    doc.build(story)
    buffer.seek(0)
    return buffer
