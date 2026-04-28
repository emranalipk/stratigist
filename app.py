"""
AI Ads Strategist – Fixed PDF Gauge & Professional Design
═══════════════════════════════════════════════════════════
• Corrected Wedge division‑by‑zero in score gauge
• Gemini Pro model: gemini‑2.5‑pro (stable)
• Professional PDF: header/footer, gauge, bar chart, styled tables
• 3‑worker ensemble + dual‑judge quality review
• Simple MCQ qualification, Pakistan market intel
"""

import streamlit as st, re, io, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from groq import Groq
import google.generativeai as genai
from openai import OpenAI

PDF_AVAILABLE = True
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, ListFlowable, ListItem
    )
    from reportlab.graphics.shapes import Drawing, Circle, String, Wedge
    from reportlab.graphics.charts.barcharts import HorizontalBarChart
except ImportError:
    PDF_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY = True
except:
    PLOTLY = False

# ══════════════════════════════════════════════════════════
# Front‑end config & styling
# ══════════════════════════════════════════════════════════
st.set_page_config(page_title="AI Ads Strategist", page_icon="🎯", layout="wide")
st.markdown("""
<style>
    .hero { background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 100%); color: white;
            padding: 2rem; border-radius: 18px; margin-bottom: 2rem; text-align: center;
            box-shadow: 0 10px 30px rgba(37,99,235,0.3); }
    .hero h1 { font-size: 2.5rem; margin:0; }
    .stButton > button { background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white;
                         border: none; border-radius: 12px; padding: 0.8rem 2rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# API clients (cached)
# ══════════════════════════════════════════════════════════
@st.cache_resource
def init_apis():
    clients = {}
    try:
        clients["groq"] = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except: pass
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        clients["gemini_flash"] = genai.GenerativeModel("gemini-2.5-flash")
        clients["gemini_pro"] = genai.GenerativeModel("gemini-2.5-pro")
    except: pass
    try:
        clients["deepseek"] = OpenAI(
            api_key=st.secrets["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com/v1"
        )
    except: pass
    return clients

apis = init_apis()
if not any(k in apis for k in ["groq","gemini_flash","deepseek"]):
    st.error("Add at least one API key (GROQ, GEMINI, DEEPSEEK) to Streamlit Secrets.")
    st.stop()

# … (rest of the code identical to previous version, except the PDF gauge fix above)

# ══════════════════════════════════════════════════════════
# PDF GENERATION (with the fixed build_score_gauge)
# ══════════════════════════════════════════════════════════
C_NAVY   = HexColor("#1E3A5F")
C_BLUE   = HexColor("#2563EB")
C_GREEN  = HexColor("#10B981")
C_AMBER  = HexColor("#F59E0B")
C_RED    = HexColor("#EF4444")
C_LIGHT  = HexColor("#F8FAFC")
C_WHITE  = white
C_BORDER = HexColor("#E2E8F0")
C_TEXT   = HexColor("#1E293B")
C_MUTED  = HexColor("#64748B")

def score_to_colour(s):
    if s >= 80: return C_GREEN
    if s >= 65: return C_BLUE
    if s >= 50: return C_AMBER
    return C_RED

def page_header_footer(canvas, doc):
    canvas.saveState()
    page_w, page_h = A4
    canvas.setFillColor(C_NAVY)
    canvas.rect(0, page_h - 55, page_w, 55, fill=1, stroke=0)
    canvas.setFillColor(C_WHITE)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(0.75*inch, page_h - 35, "AI ADS STRATEGIST")
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.75*inch, page_h - 48, "Professional Strategy Report")
    canvas.setFillColor(C_MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(page_w/2, 0.4*inch, f"Page {canvas.getPageNumber()}")
    canvas.setStrokeColor(C_BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(0.75*inch, 0.7*inch, page_w-0.75*inch, 0.7*inch)
    canvas.restoreState()

def build_score_gauge(score):
    d = Drawing(280, 150)
    for i in range(0, 100, 2):
        a1 = 180 + (i * 180 / 100)
        a2 = 180 + ((i + 2) * 180 / 100)
        seg_c = (C_GREEN if i >= 80 else C_BLUE if i >= 60 else C_AMBER if i >= 40 else C_RED)
        if i <= score:
            end_angle = min(a2, 180 + score * 180 / 100)
            if end_angle - a1 > 0.01:          # avoid zero‑width wedge
                d.add(Wedge(140, 35, 90, a1, end_angle,
                            fillColor=seg_c, strokeColor=None))
    d.add(Circle(140, 35, 55, fillColor=C_WHITE, strokeColor=C_BORDER, strokeWidth=1))
    d.add(String(140, 42, str(int(score)), fontSize=34,
                 fillColor=score_to_colour(score),
                 textAnchor="middle", fontName="Helvetica-Bold"))
    d.add(String(140, 22, "/100", fontSize=10, fillColor=C_MUTED, textAnchor="middle"))
    return d

def build_breakdown_chart(scores_dict):
    d = Drawing(420, 165)
    bc = HorizontalBarChart()
    bc.x = 120; bc.y = 20; bc.width = 260; bc.height = 130
    agents = ["audience","creative","funnel","competitive","budget"]
    labels = ["Audience","Creative","Funnel","Competitive","Budget"]
    vals = [[scores_dict.get(a,65) for a in agents]]
    bc.data = vals
    bc.categoryAxis.categoryNames = labels[::-1]
    bc.categoryAxis.labels.fontSize = 9
    bc.categoryAxis.labels.fillColor = C_TEXT
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100
    bc.valueAxis.valueStep = 20
    bc.valueAxis.labels.fontSize = 8
    bc.bars[0].fillColor = C_BLUE
    colours = [score_to_colour(scores_dict.get(a,65)) for a in agents]
    for i, col in enumerate(colours[::-1]):
        bc.bars[(0, i)].fillColor = col
    bc.bars.strokeColor = None
    d.add(bc)
    return d

def text_to_flowables(text, base_style):
    flowables = []
    for block in re.split(r'\n\s*\n', text.strip()):
        block = block.strip()
        if not block: continue
        lines = block.split('\n')
        is_bullet = all(re.match(r'^\s*[\-\*]\s', l) for l in lines if l.strip())
        if is_bullet:
            items = []
            for line in lines:
                content = re.sub(r'^\s*[\-\*]\s*', '', line)
                content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
                items.append(ListItem(Paragraph(content, base_style), leftIndent=18, value='•'))
            flowables.append(ListFlowable(items, bulletType='bullet', start=''))
            flowables.append(Spacer(1, 6))
        elif '|' in block and block.count('|') > 2:
            table_data = []
            for line in lines:
                if line.startswith('|') and line.endswith('|'):
                    cells = [c.strip() for c in line.split('|')[1:-1]]
                    table_data.append(cells)
            if table_data:
                col_w = [1.4*inch]*len(table_data[0])
                tbl = Table(table_data, colWidths=col_w, hAlign='LEFT')
                tbl.setStyle(TableStyle([
                    ('GRID',(0,0),(-1,-1),0.5,C_BORDER),
                    ('BACKGROUND',(0,0),(-1,0),C_NAVY),
                    ('TEXTCOLOR',(0,0),(-1,0),C_WHITE),
                    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                    ('FONTSIZE',(0,0),(-1,-1),8),
                    ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
                    ('TOPPADDING',(0,0),(-1,-1),5),
                    ('BOTTOMPADDING',(0,0),(-1,-1),5),
                ]))
                flowables.append(tbl)
                flowables.append(Spacer(1, 10))
        else:
            para = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', '<br/>'.join(lines))
            flowables.append(Paragraph(para, base_style))
            flowables.append(Spacer(1, 8))
    return flowables

def generate_pdf(strategy_text, ctx):
    if not PDF_AVAILABLE:
        return None
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.85*inch, bottomMargin=0.85*inch,
                            title=f"AI Ads Strategy Report - {ctx.get('business_name','Business')}",
                            author="AI Ads Strategist")
    styles = getSampleStyleSheet()
    cover_title = ParagraphStyle('CoverTitle', parent=styles['Title'], fontSize=26, textColor=C_NAVY, alignment=TA_CENTER, spaceAfter=10)
    cover_sub = ParagraphStyle('CoverSub', parent=styles['Normal'], fontSize=14, textColor=C_MUTED, alignment=TA_CENTER, spaceAfter=6)
    section_head = ParagraphStyle('SectionHead', parent=styles['Heading2'], fontSize=14, textColor=C_NAVY, spaceBefore=22, spaceAfter=12)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9.5, leading=15, textColor=C_TEXT)
    exec_style = ParagraphStyle('Exec', parent=styles['Normal'], fontSize=10.5, leading=16, textColor=C_TEXT,
                                backColor=C_LIGHT, borderWidth=1, borderColor=C_BORDER, borderPadding=12, borderRadius=8)

    story = []
    # Cover page
    story.append(Spacer(1, 1.8*inch))
    story.append(Paragraph("Advertising Strategy Report", cover_title))
    story.append(Spacer(1, 0.15*inch))
    biz_display = ctx.get('business_name','') or ctx.get('url','').replace('https://','').replace('http://','')
    story.append(Paragraph(f"<b>{biz_display}</b>", cover_sub))
    story.append(Paragraph(f"{ctx.get('url','')}", ParagraphStyle('UrlC', parent=styles['Normal'], fontSize=10, textColor=C_MUTED, alignment=TA_CENTER)))
    story.append(Paragraph(f"{ctx.get('country','')}{' — '+ctx.get('cities','') if ctx.get('cities','') else ''}",
                           ParagraphStyle('LocC', parent=styles['Normal'], fontSize=10, textColor=C_MUTED, alignment=TA_CENTER)))
    story.append(Spacer(1, 0.5*inch))
    score = ctx.get('total', 70)
    grade_s = ctx.get('grade','C+')
    gauge = build_score_gauge(score)
    story.append(gauge)
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(f"<font size='18' color='{score_to_colour(score)}'><b>Grade: {grade_s}</b></font>",
                           ParagraphStyle('GradeDisp', alignment=TA_CENTER)))
    story.append(Spacer(1, 0.35*inch))
    story.append(Paragraph(f"<i>Report generated {datetime.now().strftime('%B %d, %Y')}</i>",
                           ParagraphStyle('DateDisp', fontSize=9, textColor=C_MUTED, alignment=TA_CENTER)))
    story.append(PageBreak())

    # Score breakdown
    story.append(Paragraph("📊 Score Breakdown", section_head))
    story.append(Spacer(1, 0.1*inch))
    scores_dict = ctx.get('scores', {})
    chart_d = build_breakdown_chart(scores_dict)
    story.append(chart_d)
    story.append(Spacer(1, 0.2*inch))
    agents = ["audience","creative","funnel","competitive","budget"]
    weights = {"audience":25,"creative":20,"funnel":20,"competitive":15,"budget":20}
    table_data = [["Category","Score","Weight","Status"]]
    for a, label in zip(agents, ["Audience Clarity","Creative Quality","Funnel Architecture",
                                  "Competitive Position","Budget Efficiency"]):
        s = scores_dict.get(a,65)
        status = "✅ Strong" if s>=80 else "⚠️ Needs Work" if s>=65 else "🔴 Critical"
        table_data.append([label, str(s), f"{weights[a]}%", status])
    tbl = Table(table_data, colWidths=[2.2*inch, 0.9*inch, 0.9*inch, 1.4*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),C_NAVY),
        ('TEXTCOLOR',(0,0),(-1,0),C_WHITE),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('GRID',(0,0),(-1,-1),0.5,C_BORDER),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[C_WHITE,C_LIGHT]),
        ('TOPPADDING',(0,0),(-1,-1),6),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # Strategy content
    sections = re.split(r'\n(?=## )', strategy_text)
    for section in sections:
        section = section.strip()
        if not section: continue
        lines = section.split('\n')
        heading = lines[0].replace('## ','').replace('# ','').strip()
        content = '\n'.join(lines[1:]).strip()
        if not content: continue
        story.append(Paragraph(heading, section_head))
        if 'executive summary' in heading.lower():
            clean = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content.replace('\n','<br/>'))
            story.append(Paragraph(clean, exec_style))
            story.append(Spacer(1, 0.2*inch))
        else:
            story.extend(text_to_flowables(content, body_style))

    doc.build(story, onFirstPage=page_header_footer, onLaterPages=page_header_footer)
    buf.seek(0)
    return buf

# … (rest of the app unchanged: prompt builder, LLM workers, ensemble, judges, UI, etc.)

# ══════════════════════════════════════════════════════════
# (The remainder of the app is exactly as in the previous version,
#  I'm truncating for brevity but the full fix is the gauge loop above)
# ══════════════════════════════════════════════════════════