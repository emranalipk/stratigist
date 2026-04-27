"""
AI Ads Strategist — Dual API (Groq + Gemini)
═══════════════════════════════════════════════════
• Groq for single-agent, fast commands
• Gemini 2.5 Flash for full 5-agent strategies
• API key in Streamlit Secrets
"""

import streamlit as st
import re, time, io
from datetime import datetime

# ── Both API clients ──────────────────────────────────
from groq import Groq
import google.generativeai as genai

# ── Optional imports ──
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


# ═══════════ API CONFIGURATION ═══════════

# ── Read keys from Streamlit Secrets ──
try:
    groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except KeyError:
    groq_client = None

try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
except KeyError:
    gemini_model = None

# ── Show provider status ──
if not groq_client and not gemini_model:
    st.error("🔴 No API keys found. Add GROQ_API_KEY and/or GEMINI_API_KEY to Streamlit Secrets.")
    st.stop()
elif groq_client and gemini_model:
    st.sidebar.success("🟢 Dual API mode — Groq + Gemini")
elif groq_client:
    st.sidebar.info("🟡 Groq only — Gemini key not set")
elif gemini_model:
    st.sidebar.info("🟡 Gemini only — Groq key not set")


# ═══════════ API ROUTER ═══════════

def call_llm(prompt: str, use_gemini: bool = False) -> str:
    """
    Route prompt to the best available API.
    - use_gemini=True forces Gemini (for full strategy)
    - Falls back to whichever API is available
    """
    if use_gemini and gemini_model:
        try:
            response = gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            st.warning(f"Gemini failed ({e}), falling back...")
    
    # Fallback to Groq
    if groq_client:
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4096,
            )
            return response.choices[0].message.content
        except Exception as e:
            # Final fallback — try Gemini if not tried yet
            if gemini_model and not use_gemini:
                st.warning(f"Groq failed ({e}), trying Gemini...")
                try:
                    response = gemini_model.generate_content(prompt)
                    return response.text
                except:
                    pass
            raise RuntimeError(f"Both APIs failed. Groq error: {e}")
    
    # Only Gemini available
    if gemini_model:
        response = gemini_model.generate_content(prompt)
        return response.text
    
    raise RuntimeError("No API available")


# ═══════════ DATA (same as before) ═══════════
BUSINESS_TYPES_EXTENDED = [
    "Beauty Products (General)", "Hair Oils & Serums", "Hair Tonics",
    "Skin Care (Creams, Serums)", "Cosmetics / Makeup", "Nail Care & Art",
    "Fragrances / Perfumes", "Personal Hygiene", "Men's Grooming",
    "Organic/Natural Beauty", "Beauty Salon / Spa", "Barber Shop",
    "Food Supplements", "Vitamins & Minerals", "Herbal Remedies",
    "Weight Loss Products", "Sports Nutrition", "Protein & Fitness Supplements",
    "Yoga & Meditation", "Mental Wellness Apps", "Telemedicine",
    "Restaurant / Café", "Fast Food Chain", "Bakery & Confectionery",
    "Organic Food Store", "Meal Delivery Service", "Cloud Kitchen",
    "Spices & Condiments", "Tea / Coffee Brand", "Juice & Smoothie Bar",
    "Clothing Brand (Men)", "Clothing Brand (Women)", "Kids Wear",
    "Footwear", "Luxury Fashion", "Streetwear", "Ethnic / Traditional Wear",
    "Activewear / Sportswear", "Accessories (Bags, Belts)", "Jewelry",
    "Furniture Store", "Home Decor", "Kitchenware & Appliances",
    "Smart Home Devices", "Mobile Phones & Accessories", "Laptops & Computers",
    "Audio / Headphones", "Gaming Gear", "Wearable Tech",
    "Real Estate Agency", "Legal Services", "Accounting / Tax",
    "Digital Marketing Agency", "Web Development", "Graphic Design",
    "Online Courses", "Business Coaching", "Fitness Coaching",
    "Doctor / Clinic", "Dentist", "Pharmacy", "Veterinary Clinic",
    "Car Dealership", "Auto Repair Garage", "Car Wash / Detailing",
    "E-commerce (Multi-category)", "Dropshipping Store",
    "Pet Supplies", "Toys & Games", "Baby Products",
    "Software / SaaS (B2B)", "Mobile App (Consumer)", "FinTech",
]

COUNTRIES = ["Pakistan", "India", "United States", "United Kingdom", "Canada",
             "United Arab Emirates", "Saudi Arabia", "Australia"]

PROVINCES_BY_COUNTRY = {
    "Pakistan": ["Punjab","Sindh","Khyber Pakhtunkhwa","Balochistan","Islamabad","All Provinces"],
    "India": ["Maharashtra","Delhi","Karnataka","Tamil Nadu","Gujarat","All States"],
    "United States": ["California","New York","Texas","Florida","All States"],
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


# ═══════════ PROMPT BUILDER ═══════════
def build_prompt(agent: str, **ctx) -> str:
    name = ctx.get('business_name','')
    url = ctx.get('url','')
    country = ctx.get('country','')
    langs = ctx.get('languages',['English'])
    bilingual = ctx.get('bilingual',False)
    biz_type = ctx.get('business_type','')
    objective = ctx.get('objective','')
    budget = ctx.get('budget',3000)
    competitors = ctx.get('competitor_urls','')

    lang_instruction = f"Create content in {', '.join(langs)}."
    if bilingual and len(langs)>=2:
        lang_instruction = f"Create bilingual content mixing {langs[0]} and {langs[1]} naturally (code-switching)."

    location = f"{country}"
    if ctx.get('provinces') and 'All' not in ctx['provinces'][0]:
        location += f", specifically {', '.join(ctx['provinces'])}"
    if ctx.get('cities'): location += f". Cities: {ctx['cities']}"

    base = f"""
BUSINESS: {name} ({url})
LOCATION: {location}
LANGUAGE: {lang_instruction}
BUSINESS TYPE: {biz_type}
OBJECTIVE: {objective}
COMPETITORS: {competitors}
"""
    if country == "Pakistan":
        base += "\n[Pakistan Market: Meta CPM PKR 120-480, CPC PKR 5-20. Short vertical video 80% of growth. Bilingual ads +20-30% CTR.]"

    prompts = {
        "audience": base + "Build 2-4 personas with demographics, psychographics, platform targeting, and hooks. End with SCORE:XX.",
        "creative": base + "Generate 10 hooks, platform copy, 30s video script, creative brief. End with SCORE:XX.",
        "funnel": base + "Design TOFU(40%)-MOFU(30%)-BOFU(20%)-Retarget(10%) funnel with KPIs. End with SCORE:XX.",
        "competitive": base + "Identify 3-5 competitors, gaps, counter-positioning. End with SCORE:XX.",
        "budget": base + f"Allocate ${budget}/month across platforms with local CPM/CPC, ROAS projections. End with SCORE:XX.",
        "quick": base + "60-second snapshot. End with SCORE:XX.",
        "keywords": base + "Keyword strategy. No score needed.",
        "copy": base + f"Platform copy for {ctx.get('platform','Meta')}. No score needed.",
        "hooks": base + "20 hooks. No score needed.",
        "creative_brief": base + "Creative brief. No score needed.",
        "video_script": base + "30s vertical video script. No score needed.",
        "funnel_only": base + "Full funnel architecture. No score needed.",
        "testing": base + "A/B testing plan. No score needed.",
        "landing_audit": base + "Landing page audit. No score needed.",
        "ad_audit": base + "Ad performance audit. No score needed.",
    }
    return prompts.get(agent, prompts["quick"])


# ═══════════ HELPERS ═══════════
def extract_score(text: str) -> int:
    m = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 65

def score_grade(s: float) -> str:
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

def score_color(s: float) -> str:
    if s>=80: return "#10B981"
    if s>=65: return "#3B82F6"
    if s>=50: return "#F59E0B"
    return "#EF4444"


# ═══════════ PDF (same as before) ═══════════
def markdown_to_flowables(text, base_style):
    flowables = []
    for block in re.split(r'\n\s*\n', text.strip()):
        block = block.strip()
        if not block: continue
        if all(re.match(r'^\s*[\-\*]\s', l) for l in block.split('\n') if l.strip()):
            items = []
            for line in block.split('\n'):
                content = re.sub(r'^\s*[\-\*]\s*', '', line)
                content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
                items.append(ListItem(Paragraph(content, base_style)))
            flowables.append(ListFlowable(items, bulletType='bullet', start='•', leftIndent=20, bulletFontSize=8))
            flowables.append(Spacer(1, 6))
        else:
            para = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', '<br/>'.join(block.split('\n')))
            flowables.append(Paragraph(para, base_style))
            flowables.append(Spacer(1, 8))
    return flowables

def generate_pdf(data):
    if not PDF_AVAILABLE: return None
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=0.7*inch, rightMargin=0.7*inch, topMargin=0.6*inch, bottomMargin=0.6*inch)
    styles = getSampleStyleSheet()
    body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9.5, leading=14, textColor="#1E293B")
    section = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=14, textColor="#1E3A5F", spaceBefore=20, spaceAfter=12)
    story = [Spacer(1,1.4*inch), Paragraph("AI Advertising Strategy Report", ParagraphStyle('T',parent=styles['Title'],fontSize=24,textColor="#1E3A5F",alignment=TA_CENTER)),
             Spacer(1,0.15*inch), Paragraph(f"<b>{data.get('business_name') or data.get('url','')}</b>", ParagraphStyle('N',alignment=TA_CENTER,fontSize=16)),
             PageBreak(), Paragraph("Score Breakdown", section)]
    scores = data.get('scores',{})
    t = [["Category","Score","Weight","Status"]]
    for k,label,w in [("audience","Audience",25),("creative","Creative",20),("funnel","Funnel",20),("competitive","Competitive",15),("budget","Budget",20)]:
        s = scores.get(k,65)
        t.append([label,str(s),f"{w}%","✅" if s>=80 else "⚠️" if s>=65 else "🔴"])
    tbl = Table(t, colWidths=[1.6*inch,0.8*inch,0.8*inch,1.4*inch])
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),'#1E3A5F'),('TEXTCOLOR',(0,0),(-1,0),white),('GRID',(0,0),(-1,-1),0.5,HexColor("#E2E8F0"))]))
    story.append(tbl)
    for k, title in [("audience","Audience"),("creative","Ad Creative & Copy"),("funnel","Funnel"),("competitive","Competitive Intel"),("budget","Budget")]:
        if data.get('results',{}).get(k):
            story.append(PageBreak())
            story.append(Paragraph(title, section))
            story.extend(markdown_to_flowables(data['results'][k], body))
    doc.build(story)
    buf.seek(0)
    return buf


# ═══════════ UI ═══════════
st.markdown("""<div class="hero-header"><h1>🎯 AI Ads Strategist</h1><p>100+ Types · Dual API (Groq + Gemini) · Pakistan Optimized</p></div>""", unsafe_allow_html=True)

col1, col2 = st.columns([1,2])
with col1:
    command = st.selectbox("Service:", ["📊 Full Strategy (all 5 agents)","⚡ 60-Second Snapshot","🎯 Audience Personas","🔍 Competitor Analysis","🔑 Keyword Strategy","✍️ Ad Copy Generator","🪝 Hook Generator","🎨 Creative Brief","🎬 Video Ad Script","🔽 Funnel Architecture","💰 Budget Allocation","🧪 A/B Testing Plan","📄 Landing Page Audit","📊 Ad Performance Audit","📑 Generate PDF"])
with col2:
    url = st.text_input("Website URL:", "https://example.com")
    business_name = st.text_input("Business Name (optional):", "")

with st.expander("🌍 Target Market & Settings", expanded=True):
    c1,c2,c3 = st.columns(3)
    with c1:
        country = st.selectbox("Country:", COUNTRIES, index=0)
        provinces = st.multiselect("Province/Region:", PROVINCES_BY_COUNTRY.get(country, ["All"]), default=["All Provinces"])
    with c2:
        cities = st.text_input("Cities/Areas:", "")
        langs = st.multiselect("Languages:", LANGUAGES_BY_COUNTRY.get(country, ["English"]), default=["Urdu","English"] if country=="Pakistan" else ["English"])
    with c3:
        biz_type = st.selectbox("Business Type:", [""] + BUSINESS_TYPES_EXTENDED)
        objective = st.selectbox("Objective:", ["","Brand Awareness","Website Traffic","Lead Generation","Sales/Conversions","App Installs","Engagement"])
        bilingual = st.checkbox("Bilingual copy", value=(country=="Pakistan"))

with st.expander("🎯 Advanced Options", expanded=False):
    a1,a2 = st.columns(2)
    with a1:
        competitors = st.text_area("Competitor URLs/names:", "", height=80)
        budget_val = st.number_input("Monthly Budget ($):", min_value=100, value=3000, step=500)
    with a2:
        creative_assets = st.multiselect("Creative assets:", ["Product photos","Testimonial videos","UGC/influencer content","Before/after images","Professional brand video","Nothing yet"])
        api_choice = st.radio("API Preference:", ["Auto (Gemini for strategy, Groq for quick)", "Gemini only", "Groq only"], index=0)


# ═══════════ GENERATE ═══════════
if st.button("🚀 Generate Report", type="primary", use_container_width=True):
    if not url.startswith("http"):
        st.error("Enter a valid URL.")
    else:
        ctx = dict(business_name=business_name, url=url, country=country, provinces=provinces, cities=cities, languages=langs, bilingual=bilingual, business_type=biz_type, objective=objective, budget=budget_val, competitor_urls=competitors, creative_assets=creative_assets)
        
        if command == "📊 Full Strategy (all 5 agents)":
            agents = ["audience","creative","funnel","competitive","budget"]
            weights = {"audience":25,"creative":20,"funnel":20,"competitive":15,"budget":20}
            results, scores = {}, {}
            progress = st.progress(0)
            
            # Decide API: Gemini for full strategy unless user forces Groq
            use_gemini = ("Groq only" not in api_choice) and gemini_model is not None
            
            for i, agent in enumerate(agents):
                progress.progress((i)/len(agents), f"Running {agent} agent via {'Gemini' if use_gemini else 'Groq'}...")
                prompt = build_prompt(agent, **ctx)
                try:
                    out = call_llm(prompt, use_gemini=use_gemini)
                except RuntimeError as e:
                    st.error(f"API error: {e}")
                    st.stop()
                results[agent] = out
                scores[agent] = extract_score(out)
                time.sleep(0.3)
            
            progress.progress(1.0, "Complete!"); progress.empty()
            total = sum(scores[a] * weights[a]/100 for a in agents)
            grade = score_grade(total)

            # Display
            st.markdown(f"## 📊 Ad Readiness Score: {total:.0f}/100 ({grade})")
            cols = st.columns(5)
            for idx, (k,label) in enumerate(zip(agents,["Audience","Creative","Funnel","Competitive","Budget"])):
                cols[idx].markdown(f"""<div class="metric-card"><div class="metric-value" style="color:{score_color(scores[k])}">{scores[k]}</div><div class="metric-label">{label}</div></div>""", unsafe_allow_html=True)
            if PLOTLY_AVAILABLE:
                fig = go.Figure(go.Indicator(mode="gauge+number", value=total, title={"text":"Ad Readiness Score"}, gauge={"axis":{"range":[0,100]},"bar":{"color":score_color(total)}}))
                fig.update_layout(height=300); st.plotly_chart(fig, use_container_width=True)
            
            for agent in agents:
                with st.expander(f"**{agent.title()}**", expanded=(agent=="audience")):
                    st.text(results[agent])
            
            st.session_state.last_strategy = dict(business_name=business_name, url=url, total=total, grade=grade, scores=scores, results=results)
            
            # Downloads
            report_md = f"# Strategy for {business_name or url}\nScore: {total}/100 ({grade})\n\n" + "\n\n".join(f"## {a}\n{results[a]}" for a in agents)
            st.download_button("⬇ Download (.md)", report_md, file_name="strategy.md")
            if PDF_AVAILABLE:
                pdf = generate_pdf(st.session_state.last_strategy)
                if pdf: st.download_button("📄 Download PDF", pdf, file_name="strategy.pdf")
            else:
                st.info("Install `reportlab` for PDF.")
        
        elif command == "📑 Generate PDF":
            if "last_strategy" not in st.session_state:
                st.warning("Run a full strategy first.")
            else:
                pdf = generate_pdf(st.session_state.last_strategy)
                if pdf: st.download_button("📄 Download PDF", pdf, file_name="report.pdf")
        
        else:
            agent_map = {"⚡ 60-Second Snapshot":"quick","🎯 Audience Personas":"audience","🔍 Competitor Analysis":"competitive","🔑 Keyword Strategy":"keywords","✍️ Ad Copy Generator":"copy","🪝 Hook Generator":"hooks","🎨 Creative Brief":"creative_brief","🎬 Video Ad Script":"video_script","🔽 Funnel Architecture":"funnel_only","💰 Budget Allocation":"budget","🧪 A/B Testing Plan":"testing","📄 Landing Page Audit":"landing_audit","📊 Ad Performance Audit":"ad_audit"}
            agent = agent_map.get(command, "quick")
            if command == "✍️ Ad Copy Generator":
                ctx["platform"] = st.selectbox("Platform:", ["Meta","Google Ads","TikTok","YouTube","LinkedIn","Pinterest"], key="plat")
            prompt = build_prompt(agent, **ctx)
            with st.spinner("Generating..."):
                result = call_llm(prompt, use_gemini=("Gemini only" in api_choice))
            st.success("Done!")
            st.text(result)
            st.download_button("⬇ Download", result, file_name=f"{agent}.txt")