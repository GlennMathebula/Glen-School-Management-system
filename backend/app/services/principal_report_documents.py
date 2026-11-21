"""Professional aggregated Principal Executive Reports (PDF and editable DOCX).

All figures are supplied by the same live report snapshot used in the charts.
No record-level personal information is exported.
"""
from datetime import datetime
from html import escape
from io import BytesIO
from textwrap import shorten

from PIL import Image, ImageDraw, ImageFont

NAVY = (14, 43, 74)
ORANGE = (225, 149, 64)
BLUE = (32, 105, 164)
TEAL = (33, 149, 137)
GREY = (110, 128, 144)
PALETTE = [BLUE, ORANGE, TEAL, (122, 91, 171), (213, 102, 103), (76, 153, 205), (153, 164, 74)]


def _font(size, bold=False):
    path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _clean(value):
    return str(value if value is not None else "Not recorded")


def _money(value):
    return "R {:,.2f}".format(float(value or 0))


def _png_donut(rows):
    """Generate a static chart so downloadable reports keep the visual evidence."""
    values = [(str(r["label"]), max(0,int(r.get("value") or 0))) for r in rows if int(r.get("value") or 0) > 0]
    if not values:
        return None
    im = Image.new("RGB", (1120, 390), "white")
    d = ImageDraw.Draw(im)
    total = sum(n for _,n in values)
    start = -90
    for ix,(_,n) in enumerate(values):
        stop = start+360*n/total
        d.pieslice((28, 26, 350, 348), start=start, end=stop, fill=PALETTE[ix%len(PALETTE)], outline="white", width=3)
        start=stop
    d.ellipse((116,114,262,260), fill="white")
    d.text((189,178), f"{total:,}", font=_font(33,True), fill=NAVY, anchor="mm")
    d.text((189,215),"records",font=_font(16),fill=GREY,anchor="mm")
    for ix,(name,n) in enumerate(values[:8]):
        yy=38+ix*42
        d.rounded_rectangle((390, yy, 416, yy+24),radius=5,fill=PALETTE[ix%len(PALETTE)])
        d.text((435, yy-2),shorten(name,width=49,placeholder="..."),font=_font(19),fill=NAVY)
        d.text((1020,yy-2),f"{n:,}  ({n/total*100:.1f}%)",font=_font(17,True),fill=NAVY,anchor="ra")
    out=BytesIO();im.save(out,format="PNG");out.seek(0);return out


def _png_bars(rows, k1="applications", k2="registrations"):
    if not rows:
        return None
    rows=rows[:9]
    vmax=max([int(row.get(k,0) or 0) for row in rows for k in (k1,k2)]+[1])
    im=Image.new("RGB",(1120,max(290,110+len(rows)*66)),"white")
    d=ImageDraw.Draw(im);font=_font(16);bold=_font(15,True)
    d.text((400,18),"Applications",font=font,fill=BLUE)
    d.text((640,18),"Registrations",font=font,fill=ORANGE)
    for ix,row in enumerate(rows):
        y=70+ix*66
        name=shorten(str(row.get("label") or row.get("code") or "Unknown"),width=25,placeholder="...")
        d.text((12,y+10),name,font=font,fill=NAVY)
        for which,(key,col,off) in enumerate(((k1,BLUE,0),(k2,ORANGE,23))):
            v=int(row.get(key,0) or 0)
            width=int(640*v/vmax)
            if width:d.rounded_rectangle((350,y+off,350+width,y+off+16),radius=4,fill=col)
            d.text((360+width,y+off-2),str(v),font=bold,fill=NAVY)
    out=BytesIO();im.save(out,format="PNG");out.seek(0);return out


def _format_row(item):
    if "value" in item:
        return _clean(item.get("label")),f"{int(item.get('value') or 0):,}"
    if "amount" in item:
        return _clean(item.get("label")),f"{int(item.get('count') or 0):,} records | {_money(item.get('amount'))}"
    if "applications" in item:
        return _clean(item.get("label")),f"{int(item.get('applications') or 0):,} applications | {int(item.get('registrations') or 0):,} registrations"
    if "active" in item:
        return _clean(item.get("label")),f"{int(item.get('active') or 0):,} active | {int(item.get('total') or 0):,} accounts"
    return _clean(item.get("label")),_clean(item)


def _overview_facts(stats):
    s=stats["summary"]
    return [
        ("Application records",f"{s['applications']:,}"),
        ("Distinct applicant numbers",f"{s['unique_applicants']:,}"),
        ("Accepted applications",f"{s['accepted_applications']:,}"),
        ("Actual registration records",f"{s['registrations']:,}"),
        ("Programmes represented",f"{s['programmes']:,}"),
        ("Classes",f"{s['classes']:,}"),
        ("Digital attendance entries",f"{s['digital_attendance_entries']:,}"),
        ("Weekly paper-register entries",f"{s['weekly_attendance_entries']:,}"),
        ("Summative assessment attempts",f"{s['summative_attempts']:,}"),
        ("Published digital FISA outcomes",f"{s['published_fisa_outcomes']:,}"),
        ("Workplace placements",f"{s['workplace_placements']:,}"),
        ("Learner support tickets",f"{s['learner_support_tickets']:,}"),
        ("Non-cancelled invoice face value",_money(s['billable_invoice_value'])),
        ("Unreversed recorded payment value",_money(s['unreversed_payment_value'])),
    ]


def create_pdf(stats, staff_code):
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak, KeepTogether

    buffer=BytesIO();pagesize=A4
    pdf=SimpleDocTemplate(buffer,pagesize=pagesize,rightMargin=19*mm,leftMargin=19*mm,topMargin=22*mm,bottomMargin=19*mm,
                          title="Glen Moniques | Principal Executive Report",author="Glen Moniques SMS")
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name="GMTitle",parent=styles["Title"],fontSize=22,leading=28,textColor=colors.HexColor("#0e2b4a"),spaceAfter=13))
    styles.add(ParagraphStyle(name="GMHeading",parent=styles["Heading2"],fontSize=12,leading=16,textColor=colors.HexColor("#0e2b4a"),spaceBefore=17,spaceAfter=8))
    styles.add(ParagraphStyle(name="GMCell",parent=styles["Normal"],fontSize=8,leading=11))
    styles.add(ParagraphStyle(name="GMHeader",parent=styles["GMCell"],textColor=colors.white))
    styles.add(ParagraphStyle(name="GMNote",parent=styles["Normal"],fontSize=9,leading=14,textColor=colors.HexColor("#52677d"),spaceAfter=5))
    story=[Paragraph("GLEN MONIQUES (PTY) LTD",styles["GMTitle"]),
           Paragraph("PRINCIPAL EXECUTIVE & INSTITUTIONAL REPORT",styles["Heading2"]),Spacer(1,7*mm),
           Paragraph(f"<b>Scope:</b> {escape(stats['scope']['title'])}",styles["Normal"]),Spacer(1,3*mm),
           Paragraph(f"<b>Generated (UTC):</b> {escape(stats['scope']['generated_at'])}",styles["Normal"]),
           Paragraph(f"<b>Generated by:</b> {escape(staff_code)} | <b>Access:</b> Principal only",styles["Normal"]),
           Spacer(1,8*mm),Paragraph("Confidential management report. Aggregate statistics, not an audited statement.",styles["GMNote"])]

    def table(items):
        data=[[Paragraph("Indicator",styles["GMHeader"]),Paragraph("Recorded result",styles["GMHeader"])]]
        data += [[Paragraph(escape(_clean(k)),styles["GMCell"]),Paragraph(escape(_clean(v)),styles["GMCell"])] for k,v in items]
        t=Table(data,colWidths=[91*mm,82*mm],repeatRows=1,hAlign="LEFT")
        t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#0e2b4a")),
                              ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                              ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f2f6fa")]),
                              ("VALIGN",(0,0),(-1,-1),"TOP"),("BOTTOMPADDING",(0,0),(-1,-1),7),
                              ("TOPPADDING",(0,0),(-1,-1),7),
                              ("LINEBELOW",(0,-1),(-1,-1),0.4,colors.HexColor("#d4dee8"))]))
        return t

    story.append(Paragraph("1. Executive facts",styles["GMHeading"]))
    story.append(table(_overview_facts(stats)))
    cycle_details=stats["scope"].get("cycle_details")
    if cycle_details:
        story.append(Paragraph("2. Cycle details",styles["GMHeading"]))
        story.append(table([(k.replace("_"," ").title(),v) for k,v in cycle_details.items() if k not in ("id","created_at","updated_at")]))
    story.append(Paragraph("Visual overview",styles["GMHeading"]))
    for chart_key,title in [("application_status","Application decisions"),("gender","Applicant gender")]:
        png=_png_donut(stats["charts"].get(chart_key,[]))
        if png:
            story.append(KeepTogether([Paragraph(escape(title),styles["GMNote"]),RLImage(png,width=173*mm,height=60.2*mm)]))
    bar=_png_bars(stats["charts"].get("cycles") or stats["charts"].get("courses") or [])
    if bar:
        story.append(KeepTogether([Paragraph("Applications and registrations",styles["GMNote"]),RLImage(bar,width=173*mm,height=65*mm)]))
    story.append(Paragraph("Detailed source breakdowns",styles["GMHeading"]))
    for ix,section in enumerate(stats["sections"],1):
        story.append(Paragraph(f"{ix}. {escape(section['title'])}",styles["GMHeading"]))
        story.append(Paragraph(f"Unit: {escape(section['unit'])}",styles["GMNote"]))
        items=[_format_row(r) for r in section.get("rows",[])]
        story.append(table(items if items else [("No captured records","0")]))
    story.append(Paragraph("Methodology and interpretation",styles["GMHeading"]))
    for i,note in enumerate(stats["notes"],1):
        story.append(Paragraph(f"{i}. {escape(note)}",styles["GMNote"]))

    def page(canvas, doc):
        canvas.saveState();w,h=pagesize
        canvas.setStrokeColor(colors.HexColor("#d3dfe9"));canvas.line(19*mm,16*mm,w-19*mm,16*mm)
        canvas.setFont("Helvetica",8);canvas.setFillColor(colors.HexColor("#637789"))
        canvas.drawString(19*mm,11*mm,"Glen Moniques SMS | Confidential - Principal")
        canvas.drawRightString(w-19*mm,11*mm,f"Page {doc.page}")
        canvas.restoreState()
    pdf.build(story,onFirstPage=page,onLaterPages=page)
    return buffer.getvalue()


def create_docx(stats,staff_code):
    from docx import Document
    from docx.shared import Inches,Pt,RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    doc=Document()
    sec=doc.sections[0];sec.top_margin=Inches(.77);sec.bottom_margin=Inches(.75)
    sec.left_margin=Inches(.8);sec.right_margin=Inches(.8)
    styles=doc.styles;styles["Normal"].font.name="Arial";styles["Normal"].font.size=Pt(9)
    for title in ("Heading 1","Heading 2"):
        styles[title].font.name="Arial";styles[title].font.color.rgb=RGBColor(*NAVY)
    p=doc.add_paragraph();r=p.add_run("GLEN MONIQUES (PTY) LTD");r.bold=True;r.font.size=Pt(22);r.font.color.rgb=RGBColor(*NAVY)
    doc.add_heading("Principal Executive & Institutional Report",level=1)
    doc.add_paragraph(f"Scope: {stats['scope']['title']}")
    doc.add_paragraph(f"Generated (UTC): {stats['scope']['generated_at']} | Generated by: {staff_code}")
    p=doc.add_paragraph("CONFIDENTIAL - PRINCIPAL ONLY");p.runs[0].bold=True;p.runs[0].font.color.rgb=RGBColor(173,68,53)
    doc.add_paragraph("Live aggregate system data. This is a management report, not an audited statement.")
    def tbl(items):
        t=doc.add_table(rows=1,cols=2);t.style="Table Grid";t.alignment=WD_TABLE_ALIGNMENT.CENTER
        t.rows[0].cells[0].text="Indicator";t.rows[0].cells[1].text="Recorded result"
        for k,v in items:
            c=t.add_row().cells;c[0].text=_clean(k);c[1].text=_clean(v)
        for index,row in enumerate(t.rows):
            for cell in row.cells:
                tcPr=cell._tc.get_or_add_tcPr()
                shade=OxmlElement("w:shd");shade.set(qn("w:fill"),"0E2B4A" if index==0 else ("F1F6FA" if index%2 else "FFFFFF"))
                tcPr.append(shade)
                for para in cell.paragraphs:
                    for run in para.runs:
                        run.font.name="Arial";run.font.size=Pt(9)
                        if index==0:
                            run.bold=True;run.font.color.rgb=RGBColor(255,255,255)
                        else:run.font.color.rgb=RGBColor(25,51,76)
    doc.add_heading("1. Executive facts",level=2);tbl(_overview_facts(stats))
    details=stats["scope"].get("cycle_details")
    if details:
        doc.add_heading("2. Cycle details",level=2);tbl([(k.replace("_"," ").title(),v) for k,v in details.items() if k not in ("id","created_at","updated_at")])
    doc.add_heading("Visual overview",level=2)
    for key,title in [("application_status","Application decisions"),("gender","Applicant gender")]:
        img=_png_donut(stats["charts"].get(key,[]))
        if img:
            p=doc.add_paragraph(title);p.paragraph_format.keep_with_next=True;doc.add_picture(img,width=Inches(6.5))
    img=_png_bars(stats["charts"].get("cycles") or stats["charts"].get("courses") or [])
    if img:
        p=doc.add_paragraph("Applications and registrations");p.paragraph_format.keep_with_next=True;doc.add_picture(img,width=Inches(6.5))
    doc.add_heading("Detailed source breakdowns",level=1)
    for index,section in enumerate(stats["sections"],1):
        doc.add_heading(f"{index}. {section['title']}",level=2)
        doc.add_paragraph(f"Unit: {section['unit']}")
        items=[_format_row(r) for r in section.get("rows",[])]
        tbl(items if items else [("No captured records","0")])
    doc.add_heading("Methodology and interpretation",level=1)
    for i,note in enumerate(stats["notes"],1):doc.add_paragraph(f"{i}. {note}")
    foot=sec.footer.paragraphs[0];foot.text="Glen Moniques SMS | Confidential Principal management report"
    foot.alignment=WD_ALIGN_PARAGRAPH.CENTER
    stream=BytesIO();doc.save(stream);return stream.getvalue()
