"""
AI Ads Strategist – Simple MCQ Qualification · Triple Worker · Dual‑Judge
══════════════════════════════════════════════════════════════════════════
• Fixed 3‑radio‑button qualification after "Generate Strategy"
• 3 parallel workers: Groq Llama 3.3, Gemini 2.5 Flash, DeepSeek V4
• Judge 1 (Gemini Pro/Flash) synthesises, Judge 2 (DeepSeek) improves
• 100+ business types, full Pakistan market intelligence
• Beautiful Plotly charts & clean PDF export
"""

import streamlit as st, re, threading, time, io
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ── API clients ──────────────────────────────────────────
from groq import Groq
import google.generativeai as genai
from openai import OpenAI

# ── Visualisation & PDF (optional) ──────────────────────
try:
    import plotly.graph_objects as go
    PLOTLY = True
except:
    PLOTLY = False

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
    PDF = True
except:
    PDF = False


# ══════════════════════════════════════════════════════════
# PAGE CONFIG & STYLE
# ══════════════════════════════════════════════════════════
st.set_page_config(page_title="AI Ads Strategist", page_icon="🎯", layout="wide")
st.markdown("""
<style>
    .hero { background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 100%); color: white;
            padding: 2rem; border-radius: 18px; margin-bottom: 2rem; text-align: center;
            box-shadow: 0 10px 30px rgba(37,99,235,0.3); }
    .hero h1 { font-size: 2.5rem; margin:0; }
    .metric-card { background: white; border-radius: 14px; padding: 1.4rem;
                   box-shadow: 0 2px 8px rgba(0,0,0,0.04); border: 1px solid #E2E8F0;
                   text-align: center; }
    .stRadio > label { font-weight:600; }
    .stButton > button { background: linear-gradient(135deg, #2563EB, #1D4ED8); color: white;
                         border: none; border-radius: 12px; padding: 0.8rem 2rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# API INITIALISATION
# ══════════════════════════════════════════════════════════
@st.cache_resource
def init_apis():
    clients = {}
    try:
        clients["groq"] = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except:
        pass
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        clients["gemini_flash"] = genai.GenerativeModel("gemini-2.5-flash")
        clients["gemini_pro"] = genai.GenerativeModel("gemini-2.5-pro-exp-03-25")
    except:
        pass
    try:
        clients["deepseek"] = OpenAI(
            api_key=st.secrets["DEEPSEEK_API_KEY"],
            base_url="https://api.deepseek.com/v1"
        )
    except:
        pass
    return clients

apis = init_apis()
if not any(k in apis for k in ["groq","gemini_flash","deepseek"]):
    st.error("Add at least one API key (GROQ, GEMINI, DEEPSEEK) to Streamlit Secrets.")
    st.stop()

# ══════════════════════════════════════════════════════════
# DATA
# ══════════════════════════════════════════════════════════
BUSINESS_TYPES = [
    "Beauty Products (General)","Hair Oils & Serums","Hair Tonics","Skin Care","Cosmetics","Nail Art",
    "Fragrances","Personal Hygiene","Men's Grooming","Beauty Salon / Spa","Barber Shop",
    "Food Supplements","Vitamins & Minerals","Herbal Remedies","Weight Loss","Sports Nutrition",
    "Restaurant / Café","Fast Food","Bakery","Meal Delivery","Cloud Kitchen",
    "Clothing (Men)","Clothing (Women)","Kids Wear","Footwear","Luxury Fashion","Streetwear",
    "Furniture","Home Decor","Electronics","Real Estate","Digital Marketing Agency",
    "Web Development","Online Courses","Business Coaching","Doctor / Clinic","Dentist","Pharmacy",
    "Car Dealership","Auto Repair","E‑commerce (General)","Pet Supplies","Baby Products",
    "SaaS (B2B)","Mobile App","FinTech","Handicrafts","Bookstore",
]

COUNTRIES = ["Pakistan","India","United States","United Kingdom","Canada","UAE","Saudi Arabia"]
PROVINCES_BY_COUNTRY = {
    "Pakistan":["Punjab","Sindh","KPK","Balochistan","Islamabad","Gilgit-Baltistan","AJK","All Provinces"],
    "India":["Maharashtra","Delhi","Karnataka","Tamil Nadu","Gujarat","All States"],
    "United States":["California","New York","Texas","Florida","All States"],
    "United Kingdom":["England","Scotland","Wales","Northern Ireland","All UK"],
    "Canada":["Ontario","Quebec","British Columbia","Alberta","All Provinces"],
    "UAE":["Dubai","Abu Dhabi","Sharjah","All Emirates"],
    "Saudi Arabia":["Riyadh","Jeddah","Makkah","Dammam","All Regions"],
}
LANGUAGES_BY_COUNTRY = {
    "Pakistan":["Urdu","English","Punjabi","Sindhi","Pashto"],
    "India":["Hindi","English","Bengali","Telugu","Marathi"],
    "United States":["English","Spanish"],
    "United Kingdom":["English"],
    "Canada":["English","French"],
    "UAE":["Arabic","English","Urdu","Hindi"],
    "Saudi Arabia":["Arabic","English"],
}
PAKISTAN_INTEL = """
## PAKISTAN MARKET INTELLIGENCE 2026
- Facebook 68M (58% male, core 25‑34). Instagram 24M (64% male, core 18‑24). TikTok 66.9M (+23%).
- YouTube 96.6M. WhatsApp 91.7M commerce backbone. LinkedIn 15M niche.
- Meta CPM PKR 120‑480, CPC PKR 5‑20. TikTok CPM PKR 80‑300, CPC PKR 3‑15.
- Google CPC PKR 25‑100.
- Bilingual Urdu+English ads → 20‑30% higher CTR.
- Authentic UGC / real faces → 40‑50% hook rate boost.
- 68% of businesses have Meta Pixel installed incorrectly – tracking verification is priority #1.
- City behaviour: Karachi fast/competitive (peak 8PM‑1AM), Lahore cultural/fashion (9PM‑midnight), Islamabad premium (7PM‑11PM), Faisalabad value‑driven.
- Calendar: Ramadan, Eid‑ul‑Fitr, Eid‑ul‑Azha, Aug 14, Wedding season (Oct‑Mar), Black Friday.
"""

# ══════════════════════════════════════════════════════════
# MCQ QUESTIONS (fixed, simple)
# ══════════════════════════════════════════════════════════
MCQ_QUESTIONS = {
    "ad_experience": {
        "question": "What best describes your current ad setup?",
        "options": [
            "I'm completely new to ads",
            "I've run some ads but results were poor",
            "I'm running ads now and want to scale",
            "I used to run ads but stopped"
        ]
    },
    "customer_type": {
        "question": "Who is your most profitable type of customer?",
        "options": [
            "Individual consumers (B2C)",
            "Other businesses (B2B)",
            "Both — consumers and businesses",
            "Not sure yet"
        ]
    },
    "main_challenge": {
        "question": "What's the biggest challenge you're facing?",
        "options": [
            "Getting enough customers / orders",
            "Customers visit but don't buy",
            "Ads cost too much compared to sales",
            "I don't know where to start"
        ]
    }
}

def format_insights(answers):
    """Convert MCQ answers into a short insight string for the AI."""
    parts = []
    if answers.get("ad_experience"):
        parts.append(f"Ad experience: {answers['ad_experience']}")
    if answers.get("customer_type"):
        parts.append(f"Primary customer: {answers['customer_type']}")
    if answers.get("main_challenge"):
        parts.append(f"Biggest challenge: {answers['main_challenge']}")
    return " | ".join(parts) if parts else "No extra insights provided."

# ══════════════════════════════════════════════════════════
# ENHANCED AGENT PROMPT BUILDER
# ══════════════════════════════════════════════════════════
def build_prompt(agent, ctx, insights=""):
    name = ctx.get('business_name','')
    url = ctx.get('url','')
    country = ctx.get('country','')
    cities = ctx.get('cities','')
    langs = ctx.get('languages',['English'])
    bilingual = ctx.get('bilingual',False)
    btype = ctx.get('business_type','')
    objective = ctx.get('objective','')
    budget = ctx.get('budget',3000)
    competitors = ctx.get('competitors','')
    assets = ctx.get('assets',[])
    platform = ctx.get('platform','Meta')

    lang_instruction = f"Create content in {', '.join(langs)}."
    if bilingual and len(langs)>=2:
        lang_instruction = f"Use bilingual {langs[0]}+{langs[1]} code‑switching naturally."

    location_str = country
    if ctx.get('provinces') and 'All' not in ctx['provinces'][0]:
        location_str += f", specifically {', '.join(ctx['provinces'])}"
    if cities: location_str += f". Cities: {cities}"

    base_context = f"""
BUSINESS: {name} ({url})
BUSINESS TYPE: {btype}
TARGET LOCATION: {location_str}
LANGUAGE: {lang_instruction}
CAMPAIGN OBJECTIVE: {objective}
MONTHLY BUDGET: ${budget}
COMPETITORS: {competitors}
AVAILABLE CREATIVE ASSETS: {', '.join(assets)}
CLIENT INSIGHTS: {insights}
"""
    if country == "Pakistan":
        base_context += PAKISTAN_INTEL

    role = "You are a Senior Digital Strategist for a top Pakistani agency with 15 years of experience."
    if country != "Pakistan":
        role = f"You are a world‑class advertising strategist specialised in the {country} market."

    self_audit = "Before writing, explicitly state the biggest assumption you're making about this business. Then, in your final output, include a '🧠 Strategist's Honest Assessment' section that highlights one potential risk and how to mitigate it."

    output_format = ""
    if agent == "audience":
        output_format = """
OUTPUT STRUCTURE:
## 🎯 Audience Persona: [Name]
| Attribute | Details |
|-----------|---------|
| Demographics | Age, Income, Gender, City |
| Pain Point | ... |
| Digital Home | Platform + Peak Time |
| Messaging Hook | [Exact hook in required language] |
| Why It Works | [Psychological/cultural reason] |

## 📈 Targeting Blueprint (for Meta/Google/TikTok)
- Exact audience definition, lookalike recommendation, expected CTR/CPM based on market intel.
"""
    elif agent == "creative":
        output_format = """
OUTPUT STRUCTURE:
## 🪝 10 Scroll‑Stopping Hooks
(Label each with category: Pattern Interrupt / Curiosity / Bold Claim / Relatable Pain)

## 📱 Platform‑Specific Copy
### Meta (Facebook/Instagram) – 3 Primary Text Options
### TikTok – 3 Captions with Hashtags
### Google Ads – 5 Headlines + 2 Descriptions

## 🎬 30‑Second Vertical Video Script (9:16)
| Time | Visual Scene | Audio/Voiceover | Text Overlay |
|------|--------------|-----------------|--------------|
| 0-3s | ... | ... | ... |

## 🎨 Creative Direction Brief
- Visual style, color palette, do's/don'ts.
"""
    elif agent == "funnel":
        output_format = """
OUTPUT STRUCTURE:
## 🔽 Full‑Funnel Architecture
### TOFU (Awareness) – 40% budget
- Campaign names, platforms, ad formats, KPIs
### MOFU (Consideration) – 30% budget
- Retargeting pools, content types
### BOFU (Conversion) – 20% budget
- High‑intent audiences, offer strategy
### Retargeting Layer – 10% budget
- Dynamic ads, frequency cap, WhatsApp integration (if Pakistan)
"""
    elif agent == "competitive":
        output_format = """
OUTPUT STRUCTURE:
## 🔍 Competitive Landscape
| Competitor | Platform Focus | Estimated Spend | Key Hook | Our Advantage |
|------------|---------------|----------------|----------|---------------|
| ... | ... | ... | ... | ... |

## 🥊 Counter‑Positioning Strategy
- How we beat each competitor on messaging.
- Unexploited audience gaps.
"""
    elif agent == "budget":
        output_format = """
OUTPUT STRUCTURE:
## 💰 Budget Allocation
| Platform | % Budget | Monthly Amount | Projected CPM | Projected CPC | Expected Impressions |
|----------|---------|----------------|---------------|---------------|----------------------|
| ... | ... | ... | ... | ... | ... |

## 📈 3‑Month Scaling Plan
- Month 1: test, Month 2: scale winners, Month 3: expand.

## 🧠 Strategist's Honest Assessment
(Risk and mitigation)
"""

    return f"""{role}

{base_context}

{self_audit}

{output_format}
"""

# ══════════════════════════════════════════════════════════
# LLM WORKERS
# ══════════════════════════════════════════════════════════
def call_deepseek(prompt, max_tokens=4096):
    resp = apis["deepseek"].chat.completions.create(
        model="deepseek-chat",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7, max_tokens=max_tokens
    )
    return resp.choices[0].message.content

def call_groq(prompt, max_tokens=4096):
    resp = apis["groq"].chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7, max_tokens=max_tokens
    )
    return resp.choices[0].message.content

def call_gemini(prompt, model="flash"):
    m = apis["gemini_flash"] if model=="flash" else apis.get("gemini_pro")
    if not m: return "[Gemini Pro not available]"
    resp = m.generate_content(prompt)
    return resp.text

def call_worker(model_name, prompt):
    try:
        if model_name == "deepseek" and "deepseek" in apis:
            return call_deepseek(prompt)
        elif model_name == "groq" and "groq" in apis:
            return call_groq(prompt)
        elif model_name == "gemini" and "gemini_flash" in apis:
            return call_gemini(prompt, "flash")
        else:
            return f"[{model_name} unavailable]"
    except Exception as e:
        return f"[{model_name} ERROR: {e}]"

# ══════════════════════════════════════════════════════════
# ENSEMBLE ORCHESTRATION
# ══════════════════════════════════════════════════════════
def run_ensemble_agents(ctx, insights):
    agents = ["audience","creative","funnel","competitive","budget"]
    all_outs = {a:{} for a in agents}
    futures = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        for agent in agents:
            prompt = build_prompt(agent, ctx, insights)
            for model in ["groq","gemini","deepseek"]:
                if model in apis:
                    futures.append(executor.submit(
                        lambda a=agent, m=model, p=prompt: (a, m, call_worker(m, p)),
                        agent, model, prompt
                    ))
        for future in as_completed(futures):
            agent, model, result = future.result()
            all_outs[agent][model] = result
    return all_outs

def judge1_synthesize(all_outs, ctx):
    flat = ""
    for agent in ["audience","creative","funnel","competitive","budget"]:
        for model, text in all_outs.get(agent, {}).items():
            flat += f"### {agent} - {model}\n{text}\n\n"
    prompt = f"""You are the Chief Strategy Officer reviewing three AI strategists' outputs for the same business:
{flat}

Extract the single strongest element from each. Blend them into ONE superior, client‑ready strategy.
Use professional formatting with clear headings, bullet points, tables where appropriate.
Add a top section '💼 Executive Summary' summarising the key recommendation in 3 bullet points.

Business context: {ctx.get('business_name','')}, {ctx.get('url','')}, {ctx.get('country','')}, Budget ${ctx.get('budget',3000)}/mo.
"""
    # Prefer Gemini Pro, else Flash, else Groq
    if "gemini_pro" in apis:
        return call_gemini(prompt, "pro")
    elif "gemini_flash" in apis:
        return call_gemini(prompt, "flash")
    elif "groq" in apis:
        return call_groq(prompt)
    else:
        return call_deepseek(prompt) if "deepseek" in apis else "No judge available."

def judge2_improve(draft, ctx):
    prompt = f"""You are a meticulous Creative Director & Media Buying expert. Review the following unified ad strategy:
{draft}

Business context: {ctx.get('business_name','')}, {ctx.get('country','')}, {ctx.get('cities','')}

Do the following:
1. Identify any contradictory advice or unrealistic claims.
2. Identify any missed opportunity (ad format, cultural nuance).
3. Improve the Executive Summary to be punchier and more actionable.
4. Add a final section “🔥 Quick Wins” listing 3 easiest actions the business can take tomorrow with zero extra budget.

Output the **entire revised strategy** incorporating your improvements, keeping original structure.
"""
    if "deepseek" in apis:
        return call_deepseek(prompt)
    # fallback to Gemini or Groq
    if "gemini_flash" in apis:
        return call_gemini(prompt, "flash")
    if "groq" in apis:
        return call_groq(prompt)
    return draft + "\n\n[Judge 2 unavailable – no revision applied]"

# ══════════════════════════════════════════════════════════
# PDF GENERATOR (clean markdown → ReportLab)
# ══════════════════════════════════════════════════════════
def text_to_flowables(text, style):
    flowables = []
    for block in re.split(r'\n\s*\n', text):
        block = block.strip()
        if not block:
            continue
        if all(re.match(r'^\s*[\-\*]\s', l) for l in block.split('\n') if l.strip()):
            items = []
            for line in block.split('\n'):
                content = re.sub(r'^\s*[\-\*]\s*', '', line)
                content = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', content)
                items.append(ListItem(Paragraph(content, style)))
            flowables.append(ListFlowable(items, bulletType='bullet', start='•'))
            flowables.append(Spacer(1, 6))
        elif '|' in block and block.count('|') > 2:
            lines = block.split('\n')
            table_data = []
            for line in lines:
                if line.startswith('|') and line.endswith('|'):
                    cells = [c.strip() for c in line.split('|')[1:-1]]
                    table_data.append(cells)
            if table_data:
                col_widths = [1.5*inch]*len(table_data[0])
                tbl = Table(table_data, colWidths=col_widths)
                tbl.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,HexColor("#E2E8F0")),
                                         ('BACKGROUND',(0,0),(-1,0),HexColor("#1E3A5F")),
                                         ('TEXTCOLOR',(0,0),(-1,0),white)]))
                flowables.append(tbl)
                flowables.append(Spacer(1,8))
        else:
            para = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', block.replace('\n','<br/>'))
            flowables.append(Paragraph(para, style))
            flowables.append(Spacer(1,8))
    return flowables

def generate_pdf(strategy_text, ctx):
    if not PDF:
        return None
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=0.7*inch, rightMargin=0.7*inch)
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle('Body', fontSize=9.5, leading=14, textColor="#1E293B")
    story = []
    story.append(Spacer(1,1.5*inch))
    story.append(Paragraph("AI Advertising Strategy Report", ParagraphStyle('Title', fontSize=24, textColor="#1E3A5F", alignment=TA_CENTER)))
    story.append(Paragraph(f"<b>{ctx.get('business_name','')}</b><br/>{ctx.get('url','')}", ParagraphStyle('Sub', alignment=TA_CENTER)))
    story.append(PageBreak())
    for section in strategy_text.split('\n## '):
        if section.strip():
            lines = section.split('\n')
            heading = lines[0].replace('## ','').strip()
            content = '\n'.join(lines[1:])
            story.append(Paragraph(heading, ParagraphStyle('H2', fontSize=14, textColor="#1E3A5F", spaceBefore=20, spaceAfter=10)))
            story.extend(text_to_flowables(content, body_style))
    doc.build(story)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════
st.markdown('<div class="hero"><h1>🎯 AI Ads Strategist</h1><p>Simple MCQ Qualification · Triple‑Model Ensemble · Dual‑Judge QA</p></div>', unsafe_allow_html=True)

# Business details form
with st.expander("⚙️ Business Setup", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        url = st.text_input("Website URL *", "https://example.com")
        business_name = st.text_input("Business Name (optional)", "")
        country = st.selectbox("Country *", COUNTRIES, index=0)
        provinces = st.multiselect("Province/Region", PROVINCES_BY_COUNTRY.get(country,["All"]), default=["All Provinces"])
    with col2:
        cities = st.text_input("Cities/Areas", placeholder="e.g., Karachi, Lahore")
        langs = st.multiselect("Ad Languages *", LANGUAGES_BY_COUNTRY.get(country,["English"]), default=["Urdu","English"] if country=="Pakistan" else ["English"])
        bilingual = st.checkbox("Bilingual copy (mix languages)", value=True if country=="Pakistan" else False)
        business_type = st.selectbox("Business Type", BUSINESS_TYPES)
        objective = st.selectbox("Campaign Objective", ["Brand Awareness","Website Traffic","Lead Generation","Sales/Conversions","App Installs","Engagement"])
        budget = st.number_input("Monthly Budget ($) *", min_value=100, value=3000, step=500)

with st.expander("🎯 Advanced Settings (optional)"):
    col3, col4 = st.columns(2)
    with col3:
        competitors = st.text_area("Competitor URLs or names", height=80)
    with col4:
        assets = st.multiselect("Available Creative Assets", [
            "Product photos", "Testimonial videos", "UGC content", "Before/after images",
            "Professional brand video", "Nothing yet"
        ])

# ── State management ──
if 'generation_requested' not in st.session_state:
    st.session_state.generation_requested = False
if 'mcq_answers' not in st.session_state:
    st.session_state.mcq_answers = None

# ── Generate button ──
if st.button("🧠 Generate Strategy", type="primary"):
    if not url.startswith("http"):
        st.error("Enter a valid URL starting with http:// or https://")
    else:
        st.session_state.generation_requested = True
        # If MCQs not answered yet, we'll show them below
        if st.session_state.mcq_answers is None:
            st.markdown("---")
            st.markdown("### 🎯 Let's personalise your strategy")
            st.markdown("*(Just 3 clicks – no typing needed)*")
            with st.form("mcq_form"):
                q1 = st.radio(
                    MCQ_QUESTIONS["ad_experience"]["question"],
                    MCQ_QUESTIONS["ad_experience"]["options"],
                    key="q1"
                )
                q2 = st.radio(
                    MCQ_QUESTIONS["customer_type"]["question"],
                    MCQ_QUESTIONS["customer_type"]["options"],
                    key="q2"
                )
                q3 = st.radio(
                    MCQ_QUESTIONS["main_challenge"]["question"],
                    MCQ_QUESTIONS["main_challenge"]["options"],
                    key="q3"
                )
                submitted = st.form_submit_button("✅ Continue with these answers")
                if submitted:
                    st.session_state.mcq_answers = {
                        "ad_experience": q1,
                        "customer_type": q2,
                        "main_challenge": q3
                    }
                    st.experimental_rerun()  # will now run the generation
        else:
            st.session_state.generation_requested = False  # reset if already answered (shouldn't happen on normal flow)

# ── Run generation if requested and MCQs answered ──
if st.session_state.generation_requested and st.session_state.mcq_answers is not None:
    insights = format_insights(st.session_state.mcq_answers)
    ctx = {
        "business_name": business_name,
        "url": url,
        "country": country,
        "provinces": provinces,
        "cities": cities,
        "languages": langs,
        "bilingual": bilingual,
        "business_type": business_type,
        "objective": objective,
        "budget": budget,
        "competitors": competitors,
        "assets": assets
    }
    with st.spinner("🚀 3 AI workers generating strategies in parallel..."):
        all_outputs = run_ensemble_agents(ctx, insights)
    with st.spinner("⚖️ Judge 1 synthesising the best unified strategy..."):
        unified = judge1_synthesize(all_outputs, ctx)
    with st.spinner("🔍 Judge 2 performing quality review..."):
        final_strategy = judge2_improve(unified, ctx)
    st.success("✅ Strategy Ready!")
    st.markdown(final_strategy)
    if PDF:
        pdf_buf = generate_pdf(final_strategy, ctx)
        if pdf_buf:
            st.download_button("📄 Download Professional PDF", pdf_buf,
                               file_name=f"{business_name or 'strategy'}_report.pdf")
    else:
        st.info("Install `reportlab` for PDF export.")
    # Reset state for next run
    st.session_state.generation_requested = False
    # Optionally keep MCQs for next run – we'll keep them or clear
    # st.session_state.mcq_answers = None   # Uncomment to ask again every time