from html import escape
from io import BytesIO
from pathlib import Path

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    KeepTogether,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    TableStyle,
)

from app.reports.domain import AccessReport
from app.reports.template import AccessReportTemplate

TITLE = "Relatório de acessos"
OWNER_NOTE = "Os identificadores representam proprietários de treinos, sem identificar o autor da requisição."
PERIOD_NOTE = "O período inclui o início e exclui o fim. Horários em UTC."
EMPTY_MESSAGE = "Nenhum acesso no período."

for name, filename in (("ReportSans", "Vera.ttf"), ("ReportSans-Bold", "VeraBd.ttf")):
    pdfmetrics.registerFont(
        TTFont(name, str(Path(reportlab.__file__).parent / "fonts" / filename))
    )


def pdf_styles():
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = "ReportSans"
    for name in ("Title", "Heading2", "Heading4"):
        styles[name].fontName = "ReportSans-Bold"
    styles["BodyText"].fontSize = 9
    styles["BodyText"].leading = 13
    return styles


class HtmlAccessReport(AccessReportTemplate):
    media_type = "text/html"

    def render(self, report: AccessReport) -> bytes:
        users = "".join(
            f"<tr><td>{user_id}</td><td>{count}</td></tr>"
            for user_id, count in report.users
        )
        operations = "".join(
            f"<tr><td>{escape(operation)}</td><td>{count}</td></tr>"
            for operation, count in report.operations
        )
        empty = f"<p>{EMPTY_MESSAGE}</p>" if report.total == 0 else ""
        return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<style>
body {{ font-family: sans-serif; color: #182638; max-width: 760px; margin: 40px auto; padding: 0 20px; }}
h1 {{ border-bottom: 3px solid #23766e; padding-bottom: 16px; }}
h2 {{ margin-top: 32px; }}
table {{ border-collapse: collapse; width: 100%; margin: 12px 0 24px; }}
th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #dde4eb; }}
th {{ background: #eaf3f2; }}
th:last-child, td:last-child {{ text-align: right; }}
.total {{ font-size: 22px; }}
.note {{ color: #526174; line-height: 1.5; }}
</style></head><body>
<h1>{TITLE}</h1>
<p>Início (UTC): {escape(report.start.isoformat())}</p>
<p>Fim (UTC): {escape(report.end.isoformat())}</p>
<p class="note">{PERIOD_NOTE}</p>
<p class="total">Total de acessos: <strong>{report.total}</strong></p>
{empty}
<h2>Por proprietário</h2>
<table><thead><tr><th scope="col">Usuário proprietário</th><th scope="col">Acessos</th></tr></thead>
<tbody>{users}</tbody></table>
<h2>Por operação</h2>
<table><thead><tr><th scope="col">Operação</th><th scope="col">Acessos</th></tr></thead>
<tbody>{operations}</tbody></table>
<p class="note">{OWNER_NOTE}</p>
</body></html>""".encode()


def pdf_table(
    header: tuple[str, str], rows: tuple[tuple[object, int], ...]
) -> LongTable:
    styles = pdf_styles()
    number = ParagraphStyle("Number", parent=styles["BodyText"], alignment=TA_RIGHT)
    data = [[Paragraph(escape(title), styles["Heading4"]) for title in header]]
    data.extend(
        [Paragraph(escape(str(key)), styles["BodyText"]), Paragraph(str(count), number)]
        for key, count in rows
    )
    table = LongTable(data, colWidths=[300, 175], repeatRows=1, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf3f2")),
                ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#dde4eb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return table


def pdf_footer(canvas: Canvas, document: SimpleDocTemplate) -> None:
    canvas.saveState()
    canvas.setFont("ReportSans", 9)
    canvas.setFillColor(colors.HexColor("#526174"))
    canvas.drawRightString(
        A4[0] - 48, 24, f"Training Platform | Página {document.page}"
    )
    canvas.restoreState()


class PdfAccessReport(AccessReportTemplate):
    media_type = "application/pdf"

    def render(self, report: AccessReport) -> bytes:
        output = BytesIO()
        styles = pdf_styles()
        document = SimpleDocTemplate(
            output,
            pagesize=A4,
            rightMargin=48,
            leftMargin=48,
            topMargin=42,
            bottomMargin=42,
            title=TITLE,
            author="Training Platform",
        )
        story = [
            Paragraph(TITLE, styles["Title"]),
            Spacer(1, 14),
            Paragraph(f"Início (UTC): {report.start.isoformat()}", styles["BodyText"]),
            Paragraph(f"Fim (UTC): {report.end.isoformat()}", styles["BodyText"]),
            Paragraph(PERIOD_NOTE, styles["BodyText"]),
            Spacer(1, 14),
            Paragraph(f"Total de acessos: {report.total}", styles["Heading2"]),
        ]
        if report.total == 0:
            story.append(Paragraph(EMPTY_MESSAGE, styles["BodyText"]))
        story.extend(
            [
                Paragraph("Por proprietário", styles["Heading2"]),
                pdf_table(("Usuário proprietário", "Acessos"), report.users),
                KeepTogether(
                    [
                        Paragraph("Por operação", styles["Heading2"]),
                        pdf_table(("Operação", "Acessos"), report.operations),
                        Spacer(1, 14),
                        Paragraph(OWNER_NOTE, styles["BodyText"]),
                    ]
                ),
            ]
        )
        document.build(story, onFirstPage=pdf_footer, onLaterPages=pdf_footer)
        return output.getvalue()
