"""
AI Ads Strategist — Fully Functional, Enhanced PDF (April 2026)
═══════════════════════════════════════════════════════════════
• Button now works perfectly
• 100+ business types, business name, refined PDF with proper formatting
• Groq API, Plotly charts, clean markdown-to-ReportLab conversion
"""

import streamlit as st
import re, time, io
from datetime import datetime
from groq import Groq

# ── Optional imports ──
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor, white
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, ListFlowable, ListItem, KeepTogether
    )
    from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Wedge
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ═══════════ PAGE CONFIG ═══════════
st.set_page_config(page_title="AI Ads Strategist", page_icon="🎯", layout="wide")
st.markdown("""
<style>
    .hero-header {
        background: linear-gradient(135deg, #1E3A5F, #2563EB);
        color: white; padding: 2rem; border-radius: 16px; margin-bottom: 2rem;
        text-align: center; box-shadow: 0 8px 30px rgba(37,99,235,0.2);
    }
    .metric-card {
        background: white; border-radius: 12px; padding: 1.2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E2E8F0;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; }
    .metric-label { color: #64748B; font-size: 0.8rem; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)


# ═══════════ DATA ═══════════
BUSINESS_TYPES_EXTENDED = [
    "Beauty Products (General)", "Hair Oils & Serums", "Hair Tonics",
    "Skin Care (Creams, Serums)", "Cosmetics / Makeup", "Nail Care & Art",
    "Fragrances / Perfumes", "Personal Hygiene", "Men's Grooming",
    "Organic/Natural Beauty", "Beauty Salon / Spa", "Barber Shop",
    "Food Supplements", "Vitamins & Minerals", "Herbal Remedies",
    "Weight Loss Products", "Sports Nutrition", "Protein & Fitness Supplements",
    "Yoga & Meditation", "Mental Wellness Apps", "Telemedicine",
    "Dental Care Products", "Eye Care", "Hearing Aids",
    "Restaurant / Café", "Fast Food Chain", "Bakery & Confectionery",
    "Organic Food Store", "Meal Delivery Service", "Cloud Kitchen",
    "Spices & Condiments", "Tea / Coffee Brand", "Juice & Smoothie Bar",
    "Dietary Specific Foods", "Frozen Foods", "Imported Groceries",
    "Clothing Brand (Men)", "Clothing Brand (Women)", "Kids Wear",
    "Footwear", "Luxury Fashion", "Streetwear", "Ethnic / Traditional Wear",
    "Activewear / Sportswear", "Accessories (Bags, Belts)", "Jewelry",
    "Watches", "Eyewear / Sunglasses",
    "Furniture Store", "Home Decor", "Kitchenware & Appliances",
    "Bedding & Linen", "Smart Home Devices", "Gardening Supplies",
    "Cleaning Products", "Interior Design Service",
    "Mobile Phones & Accessories", "Laptops & Computers", "Audio / Headphones",
    "Gaming Gear", "Wearable Tech", "Camera & Photography",
    "Real Estate Agency", "Property Developer", "Cleaning Service",
    "Plumbing / Electrical", "Home Renovation", "Pest Control",
    "Legal Services", "Accounting / Tax", "Insurance Agent",
    "Travel Agency", "Event Planning", "Photography Studio",
    "Digital Marketing Agency", "Web Development", "Graphic Design",
    "Content Writing", "SEO Consultant", "Social Media Manager",
    "Tutoring / Academy", "Online Courses", "Language Learning",
    "Business Coaching", "Fitness Coaching", "Career Counseling",
    "Doctor / Clinic", "Dentist", "Physiotherapist", "Pharmacy",
    "Veterinary Clinic", "Diagnostic Lab",
    "Car Dealership", "Auto Repair Garage", "Car Wash / Detailing",
    "Spare Parts Shop", "Tire Shop",
    "E-commerce (Multi-category)", "Dropshipping Store", "Print on Demand",
    "Handicrafts / Artisan Products", "Pet Supplies", "Toys & Games",
    "Stationery / Office Supplies", "Bookstore", "Music Instruments",
    "Fitness Equipment", "Subscription Box", "Sustainable/Eco Products",
    "Baby Products", "Maternity Wear", "Religious / Cultural Items",
    "Agriculture / Farming Supplies", "Industrial Machinery",
    "Software / SaaS (B2B)", "Mobile App (Consumer)", "FinTech",
]

COUNTRIES = ["Pakistan", "India", "United States", "United Kingdom", "Canada",
             "United Arab Emirates", "Saudi Arabia", "Australia", "Bangladesh",
             "Malaysia", "Indonesia", "Singapore", "Other"]

PROVINCES_BY_COUNTRY = {
    "Pakistan": ["Punjab","Sindh","Khyber Pakhtunkhwa","Balochistan","Islamabad","Gilgit-Baltistan","Azad Jammu & Kashmir","All Provinces"],
    "India": ["Maharashtra","Delhi","Karnataka","Tamil Nadu","Gujarat","All States"],
    "United States": ["California","New York","Texas","Florida","All States"],
    "United Kingdom": ["England","Scotland","Wales","Northern Ireland","All UK"],
    "Canada": ["Ontario","Quebec","British Columbia","Alberta","All Provinces"],
    "United Arab Emirates": ["Dubai","Abu Dhabi","Sharjah","All Emirates"],
    "Saudi Arabia": ["Riyadh","Jeddah","Makkam","Dammam","All Regions"],
}

LANGUAGES_BY_COUNTRY = {
    "Pakistan": ["Urdu","English","Punjabi","Sindhi","Pashto","Balochi","Saraiki"],
    "India": ["Hindi","English","Bengali","Telugu","Marathi","Tamil","Gujarati"],
    "United States": ["English","Spanish"],
    "United Kingdom": ["English"],
    "Canada": ["English","French"],
    "United Arab Emirates": ["Arabic","English","Urdu","Hindi"],
    "Saudi Arabia": ["Arabic","English"],
}


# ═══════════ GROQ CLIENT ═══════════
@st.cache_resource
def get_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

try:
    client = get_client()
except Exception as e:
    st.error(f"Groq API key missing. Add to secrets.")
    st.stop()


# ═══════════ AGENT PROMPT BUILDER ═══════════
def build_prompt(agent, **ctx):
    name = ctx.get('business_name','')
    url = ctx.get('url','')
    country = ctx.get('country','')
    provinces = ctx.get('provinces',[])
    cities = ctx.get('cities','')
    langs = ctx.get('languages',['English'])
    bilingual = ctx.get('bilingual',False)
    btype = ctx.get('business_type','')
    objective = ctx.get('objective','')
    budget = ctx.get('budget',3000)
    competitors = ctx.get('competitor_urls','')
    assets = ctx.get('creative_assets',[])
    platform = ctx.get('platform','Meta')

    lang_instruction = f"Create content in {', '.join(langs)}."
    if bilingual and len(langs)>=2:
        lang_instruction = f"Create bilingual content mixing {langs[0]} and {langs[1]} naturally (code-switching)."

    location = f"{country}"
    if provinces and 'All' not in provinces[0]:
        location += f", specifically {', '.join(provinces)}"
    if cities: location += f". Cities: {cities}"

    base = f"""
BUSINESS: {name} ({url})
LOCATION: {location}
LANGUAGE: {lang_instruction}
BUSINESS TYPE: {btype}
OBJECTIVE: {objective}
COMPETITORS: {competitors}
ASSETS: {', '.join(assets)}
"""
    if country == "Pakistan":
        base += "\n[Pakistan Market: Meta CPM PKR 120-480, CPC PKR 5-20. Short vertical video 80% of growth. Bilingual ads +20-30% CTR.]"

    prompts = {
        "audience": base + "Build 2-4 personas with demographics, psychographics, platform targeting, and hooks. End with SCORE:XX.",
        "creative": base + "Generate 10 hooks, platform copy, 30s video script, creative brief. End with SCORE:XX.",
        "funnel": base + "Design TOFU(40%)-MOFU(30%)-BOFU(20%)-Retarget(10%) funnel with KPIs. End with SCORE:XX.",
        "competitive": base + "Identify 3-5 competitors, gaps, counter-positioning. End with SCORE:XX.",
        "budget": base + f"Allocate ${budget}/month across platforms with local CPM/CPC, ROAS projections. End with SCORE:XX.",
        "quick": base + "60-second snapshot: value prop, CTA, platform rec, budget. End with SCORE:XX.",
        "keywords": base + "Keyword strategy, match types, negatives. No score.",
        "copy": base + f"Platform-specific copy for {platform}. No score.",
        "hooks": base + "20 hooks (pattern interrupts, curiosity, bold claims). No score.",
        "creative_brief": base + "Creative brief with visuals, formats. No score.",
        "video_script": base + "30s vertical video script. No score.",
        "funnel_only": base + "Full funnel architecture. No score.",
        "testing": base + "A/B testing plan. No score.",
        "landing_audit": base + "Landing page audit. No score.",
        "ad_audit": base + "Ad performance audit. No score.",
    }
    return prompts.get(agent, prompts["quick"])


# ═══════════ API CALL ═══════════
def call_groq(prompt, max_tok=4096):
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7, max_tokens=max_tok
    )
    return resp.choices[0].message.content

def extract_score(text):
    m = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 65

def score_grade(s):
    if s>=95: return "A+"
    if s>=90: return "A"
    if s>=85: return "A-"
    if s>=80: return "B+"
    if s>=75: return "B"
    if s>=70: return "B-"
    if s>=65: return "C+"
    if s>=60: return "C"
    if s>=55: return "C-"
    if s>=50: return "D+"
    if s>=45: return "D"
    if s>=40: return "D-"
    return "F"

def score_color(s):
    if s>=80: return "#10B981"
    if s>=65: return "#3B82F6"
    if s>=50: return "#F59E0B"
    return "#EF4444"


# ═══════════ PDF GENERATION (REFINED) ═══════════
def markdown_to_flowables(text, base_style):
    """Convert text with **bold** and - lists into ReportLab flowables."""
    flowables = []
    blocks = re.split(r'\n\s*\n', text.strip())
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        lines = block.split('\n')
        # Check if bullet list
        is_bullet = all(re.match(r'^\s*[\-\*]\s', l) for l in lines if l.strip())
        if is_bullet:
            items = []
            for line in lines:
                content = re.sub(r'^\s*[\-\*]\s*', '', line)
                # Convert **bold** to <b>...</b>
                content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
                items.append(ListItem(Paragraph(content, base_style)))
            flowables.append(ListFlowable(items, bulletType='bullet', start='•', leftIndent=20, bulletFontSize=8))
            flowables.append(Spacer(1, 6))
        else:
            # Normal paragraph
            para_text = '<br/>'.join(lines)
            para_text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', para_text)
            flowables.append(Paragraph(para_text, base_style))
            flowables.append(Spacer(1, 8))
    return flowables

def generate_pdf(data):
    if not PDF_AVAILABLE:
        return None
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.6*inch, bottomMargin=0.6*inch)
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9.5, leading=14, textColor="#1E293B")
    cover_title = ParagraphStyle('CoverTitle', parent=styles['Title'], fontSize=24, textColor="#1E3A5F", alignment=TA_CENTER)
    section_head = ParagraphStyle('SectionHead', parent=styles['Heading2'], fontSize=14, textColor="#1E3A5F", spaceBefore=20, spaceAfter=12)

    story = []
    name = data.get('business_name') or data.get('url','Business')
    url = data.get('url','')
    total = data.get('total',0)
    grade = data.get('grade','')

    # Cover
    story.append(Spacer(1, 1.4*inch))
    story.append(Paragraph("AI Advertising Strategy Report", cover_title))
    story.append(Spacer(1, 0.15*inch))
    story.append(Paragraph(f"<font size='16' color='#1E3A5F'><b>{name}</b></font>", ParagraphStyle('NameCenter', alignment=TA_CENTER, fontSize=16)))
    story.append(Spacer(1, 0.1*inch))
    story.append(Paragraph(f"<font size='11' color='#64748B'>{url}</font>", ParagraphStyle('UrlCenter', alignment=TA_CENTER)))
    story.append(Spacer(1, 0.25*inch))
    # Gauge
    d = Drawing(250, 140)
    d.add(Circle(125, 80, 80, fillColor=HexColor("#F1F5F9"), strokeColor=HexColor("#E2E8F0")))
    d.add(String(125, 95, str(int(total)), fontSize=36, fillColor=HexColor(score_color(total)), textAnchor="middle", fontName="Helvetica-Bold"))
    d.add(String(125, 70, f"/100  Grade: {grade}", fontSize=10, fillColor=HexColor("#64748B"), textAnchor="middle"))
    story.append(d)
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<font size='11' color='#94A3B8'>{datetime.now().strftime('%B %d, %Y')}</font>", ParagraphStyle('DateCenter', alignment=TA_CENTER)))
    story.append(PageBreak())

    # Score breakdown table
    story.append(Paragraph("Score Breakdown", section_head))
    scores = data.get('scores',{})
    weights = {"audience":25,"creative":20,"funnel":20,"competitive":15,"budget":20}
    table_data = [["Category","Score","Weight","Status"]]
    for k,label in [("audience","Audience"),("creative","Creative"),("funnel","Funnel"),("competitive","Competitive"),("budget","Budget")]:
        s = scores.get(k,65)
        status = "✅ Strong" if s>=80 else "⚠️ Needs Work" if s>=65 else "🔴 Critical"
        table_data.append([label, str(s), f"{weights[k]}%", status])
    tbl = Table(table_data, colWidths=[1.6*inch,0.8*inch,0.8*inch,1.4*inch])
    tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),'#1E3A5F'),
        ('TEXTCOLOR',(0,0),(-1,0),white),
        ('ALIGN',(1,1),(-1,-1),'CENTER'),
        ('GRID',(0,0),(-1,-1),0.5, HexColor("#E2E8F0")),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[white,HexColor("#F8FAFC")]),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.2*inch))

    # Agent sections
    for agent_key, title in [("audience","Audience Personas"),("creative","Ad Creative & Copy"),
                               ("funnel","Funnel Architecture"),("competitive","Competitive Intelligence"),
                               ("budget","Budget Allocation")]:
        text = data.get('results',{}).get(agent_key,'')
        if text:
            story.append(PageBreak())
            story.append(Paragraph(title, section_head))
            flowables = markdown_to_flowables(text, body_style)
            story.extend(flowables)

    doc.build(story)
    buf.seek(0)
    return buf


# ═══════════ UI ═══════════
st.markdown("""
<div class="hero-header">
    <h1>🎯 AI Ads Strategist</h1>
    <p>100+ business types · Pakistan Optimized · Professional PDF Reports</p>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1,2])
with col1:
    command = st.selectbox("Choose a service:", [
        "📊 Full Strategy (all 5 agents)",
        "⚡ 60-Second Snapshot",
        "🎯 Audience Personas",
        "🔍 Competitor Analysis",
        "🔑 Keyword Strategy",
        "✍️ Ad Copy Generator",
        "🪝 Hook Generator (20 hooks)",
        "🎨 Creative Brief",
        "🎬 Video Ad Script",
        "🔽 Funnel Architecture",
        "💰 Budget Allocation",
        "🧪 A/B Testing Plan",
        "📄 Landing Page Audit",
        "📊 Ad Performance Audit",
        "📑 Generate PDF Report (from last strategy)",
    ])
with col2:
    url = st.text_input("Business Website URL:", "https://example.com")
    business_name = st.text_input("Business Name (optional):", "")

with st.expander("🌍 Target Market & Strategy Settings", expanded=True):
    c1,c2,c3 = st.columns(3)
    with c1:
        country = st.selectbox("Country:", COUNTRIES, index=0)
        provinces = st.multiselect("Provinces/Regions:", PROVINCES_BY_COUNTRY.get(country, ["All"]), default=["All Provinces"])
    with c2:
        cities = st.text_input("Cities/Areas:", "")
        langs = st.multiselect("Languages:", LANGUAGES_BY_COUNTRY.get(country, ["English"]), default=["Urdu","English"] if country=="Pakistan" else ["English"])
    with c3:
        biz_type = st.selectbox("Business Type:", [""] + BUSINESS_TYPES_EXTENDED)
        objective = st.selectbox("Campaign Objective:", ["","Brand Awareness","Website Traffic","Lead Generation","Sales/Conversions","App Installs","Engagement"])
        bilingual = st.checkbox("Bilingual copy", value=(country=="Pakistan" and len(langs)>=2))

with st.expander("🎯 Advanced Options (optional)", expanded=False):
    a1,a2 = st.columns(2)
    with a1:
        competitors = st.text_area("Competitor URLs/names:", "", height=80)
        budget_val = st.number_input("Monthly Budget ($):", min_value=100, value=3000, step=500)
    with a2:
        creative_assets = st.multiselect("Creative assets:", ["Product photos","Testimonial videos","UGC/influencer content","Before/after images","Professional brand video","Nothing yet"])
        extra_notes = st.text_area("Additional context:", "", height=100)


# ═══════════ GENERATE BUTTON LOGIC ═══════════
if st.button("🚀 Generate Report", type="primary", use_container_width=True):
    if not url.startswith("http"):
        st.error("Enter a valid URL starting with http:// or https://")
    else:
        ctx = {
            "business_name": business_name,
            "url": url,
            "country": country,
            "provinces": provinces,
            "cities": cities,
            "languages": langs,
            "bilingual": bilingual,
            "business_type": biz_type,
            "objective": objective,
            "budget": budget_val,
            "competitor_urls": competitors,
            "creative_assets": creative_assets,
        }
        # ── Full Strategy ──
        if command == "📊 Full Strategy (all 5 agents)":
            agents = ["audience","creative","funnel","competitive","budget"]
            weights = {"audience":25,"creative":20,"funnel":20,"competitive":15,"budget":20}
            results = {}
            scores = {}
            progress = st.progress(0)
            for i, agent in enumerate(agents):
                prompt = build_prompt(agent, **ctx)
                out = call_groq(prompt)
                results[agent] = out
                scores[agent] = extract_score(out)
                progress.progress((i+1)/len(agents))
                time.sleep(0.3)
            progress.empty()
            total = sum(scores[a] * weights[a]/100 for a in agents)
            grade = score_grade(total)

            # --- Display score dashboard ---
            st.markdown("## 📊 Ad Readiness Score")
            cols = st.columns(5)
            for idx, (k,label) in enumerate(zip(agents,["Audience","Creative","Funnel","Competitive","Budget"])):
                s = scores[k]
                c = score_color(s)
                cols[idx].markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color:{c}">{s}</div>
                    <div class="metric-label">{label}</div>
                </div>""", unsafe_allow_html=True)
            if PLOTLY_AVAILABLE:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=total, title={"text":"Ad Readiness Score"},
                                             gauge={"axis":{"range":[0,100]},"bar":{"color":score_color(total)}}))
                fig.update_layout(height=300); st.plotly_chart(fig, use_container_width=True)

            # Agent reports in expanders
            for agent in agents:
                with st.expander(f"**{agent.title()}**", expanded=(agent=="audience")):
                    st.text(results[agent])

            # Save to session state for PDF
            st.session_state.last_strategy = {
                "business_name": business_name, "url": url, "total": total, "grade": grade,
                "scores": scores, "results": results
            }
            # Downloads
            report_md = f"# Strategy for {business_name or url}\nScore: {total}/100 ({grade})\n\n"
            for a in agents:
                report_md += f"## {a}\n{results[a]}\n\n"
            st.download_button("⬇ Download Report (.md)", report_md, file_name="strategy_report.md")
            if PDF_AVAILABLE:
                pdf = generate_pdf(st.session_state.last_strategy)
                if pdf:
                    st.download_button("📄 Download PDF Report", pdf, file_name="strategy_report.pdf")
            else:
                st.info("Install `reportlab` for PDF export.")

        # ── PDF only command ──
        elif command == "📑 Generate PDF Report (from last strategy)":
            if "last_strategy" not in st.session_state:
                st.warning("Run a full strategy first.")
            else:
                pdf = generate_pdf(st.session_state.last_strategy)
                if pdf:
                    st.download_button("📄 Download PDF", pdf, file_name="report.pdf")
                else:
                    st.error("PDF generation failed.")
        # ── Single-agent commands ──
        else:
            agent_key_map = {
                "⚡ 60-Second Snapshot": "quick",
                "🎯 Audience Personas": "audience",
                "🔍 Competitor Analysis": "competitive",
                "🔑 Keyword Strategy": "keywords",
                "✍️ Ad Copy Generator": "copy",
                "🪝 Hook Generator (20 hooks)": "hooks",
                "🎨 Creative Brief": "creative_brief",
                "🎬 Video Ad Script": "video_script",
                "🔽 Funnel Architecture": "funnel_only",
                "💰 Budget Allocation": "budget",
                "🧪 A/B Testing Plan": "testing",
                "📄 Landing Page Audit": "landing_audit",
                "📊 Ad Performance Audit": "ad_audit",
            }
            agent = agent_key_map.get(command, "quick")
            if command == "✍️ Ad Copy Generator":
                platform = st.selectbox("Platform:", ["Meta","Google Ads","TikTok","YouTube","LinkedIn","Pinterest"], key="plat")
                ctx["platform"] = platform
            prompt = build_prompt(agent, **ctx)
            with st.spinner("Generating..."):
                result = call_groq(prompt)
            st.success("Done!")
            st.text(result)
            st.download_button("⬇ Download", result, file_name=f"{agent}.txt")
