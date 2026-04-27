"""
AI Ads Strategist — Full Visual Redesign (April 2026)
─────────────────────────────────────────────────────
• All 15 commands preserved & enhanced
• Plotly interactive gauge charts, horizontal bar charts, metric cards
• Pakistan market intelligence baked in
• Geography-aware language suggestions
• Business type, campaign objective, competitor URL inputs
• Enhanced PDF generation with ReportLab charts
• Free Groq API backend
"""

import streamlit as st
import re, time, json, os, io
from datetime import datetime
from groq import Groq

# ── Optional: PDF generation ──
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.units import inch, mm
    from reportlab.lib.colors import HexColor, white, black, Color
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        PageBreak, Image, HRFlowable, KeepTogether
    )
    from reportlab.graphics.shapes import Drawing, Rect, Circle, String, Line, Wedge
    from reportlab.graphics.charts.barcharts import HorizontalBarChart
    from reportlab.graphics.charts.legends import Legend
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# ── Optional: Plotly for interactive charts ──
try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════
# PAGE CONFIG & GLOBAL STYLING
# ═══════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AI Ads Strategist — Pakistan Optimized",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Root variables ── */
    :root {
        --navy: #1E3A5F;
        --blue: #2563EB;
        --green: #10B981;
        --amber: #F59E0B;
        --red: #EF4444;
        --light: #F8FAFC;
        --white: #FFFFFF;
        --border: #E2E8F0;
        --text: #1E293B;
        --muted: #64748B;
        --radius: 14px;
    }
    
    /* ── Hide Streamlit defaults ── */
    header[data-testid="stHeader"] {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ── Main background ── */
    .stApp {
        background: linear-gradient(135deg, #f0f4ff 0%, #f8fafc 50%, #f0fdf4 100%);
    }
    
    /* ── Hero header ── */
    .hero-header {
        background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 100%);
        color: white;
        padding: 2rem 2.5rem;
        border-radius: var(--radius);
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(37,99,235,0.3);
    }
    .hero-header h1 { font-size: 2.4rem; margin: 0; font-weight: 800; letter-spacing: -0.5px; }
    .hero-header p { opacity: 0.9; margin-top: 0.5rem; font-size: 1.05rem; }
    
    /* ── Metric cards ── */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1.5rem 0;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #E2E8F0;
        text-align: center;
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .metric-card .metric-value { font-size: 2.2rem; font-weight: 700; margin: 0.3rem 0; }
    .metric-card .metric-label { font-size: 0.85rem; color: #64748B; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-card .metric-icon { font-size: 1.8rem; }
    
    /* ── Section cards ── */
    .section-card {
        background: white;
        border-radius: var(--radius);
        padding: 1.5rem 2rem;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        border: 1px solid #E2E8F0;
    }
    .section-card h3 { color: #1E3A5F; border-bottom: 2px solid #E2E8F0; padding-bottom: 0.6rem; margin-bottom: 1rem; }
    
    /* ── Score display ── */
    .score-hero {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 2rem;
        flex-wrap: wrap;
        margin: 1.5rem 0;
    }
    
    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #2563EB, #1D4ED8);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.2s;
        box-shadow: 0 3px 12px rgba(37,99,235,0.3);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(37,99,235,0.4);
    }
    
    /* ── Expander styling ── */
    .streamlit-expanderHeader {
        background: #F8FAFC;
        border-radius: 10px;
        font-weight: 600;
    }
    
    /* ── Select box ── */
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stMultiselect label {
        font-weight: 600;
        color: #1E293B;
    }
    
    /* ── Download buttons ── */
    .stDownloadButton > button {
        border-radius: 10px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# DATA: GEOGRAPHY, LANGUAGES, MARKET INTELLIGENCE
# ═══════════════════════════════════════════════════════════════

COUNTRIES = [
    "Pakistan", "India", "United States", "United Kingdom", "Canada",
    "United Arab Emirates", "Saudi Arabia", "Australia", "Bangladesh",
    "Malaysia", "Indonesia", "Singapore", "Other"
]

PROVINCES_BY_COUNTRY = {
    "Pakistan": [
        "Punjab", "Sindh", "Khyber Pakhtunkhwa", "Balochistan",
        "Islamabad Capital Territory", "Gilgit-Baltistan",
        "Azad Jammu & Kashmir", "All Provinces"
    ],
    "India": [
        "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Gujarat",
        "Uttar Pradesh", "West Bengal", "Rajasthan", "All States"
    ],
    "United States": [
        "California", "New York", "Texas", "Florida", "Illinois",
        "Pennsylvania", "Ohio", "Georgia", "All States"
    ],
    "United Kingdom": ["England", "Scotland", "Wales", "Northern Ireland", "All UK"],
    "Canada": ["Ontario", "Quebec", "British Columbia", "Alberta", "All Provinces"],
    "United Arab Emirates": ["Dubai", "Abu Dhabi", "Sharjah", "All Emirates"],
    "Saudi Arabia": ["Riyadh", "Jeddah", "Makkah", "Dammam", "All Regions"],
}

LANGUAGES_BY_COUNTRY = {
    "Pakistan": ["Urdu", "English", "Punjabi", "Sindhi", "Pashto", "Balochi", "Saraiki"],
    "India": ["Hindi", "English", "Bengali", "Telugu", "Marathi", "Tamil", "Gujarati", "Kannada", "Malayalam", "Punjabi"],
    "United States": ["English", "Spanish"],
    "United Kingdom": ["English"],
    "Canada": ["English", "French"],
    "United Arab Emirates": ["Arabic", "English", "Urdu", "Hindi"],
    "Saudi Arabia": ["Arabic", "English"],
    "Australia": ["English"],
    "Bangladesh": ["Bengali", "English"],
    "Malaysia": ["Malay", "English", "Chinese", "Tamil"],
    "Indonesia": ["Indonesian", "English"],
    "Singapore": ["English", "Chinese", "Malay", "Tamil"],
}

PAKISTAN_MARKET_CONTEXT = """
## Pakistan Market Intelligence (2026)

**Platform Reality:**
- Facebook: 101M users — #1 platform for all age groups. Best for broad reach, retargeting, community building.
- Instagram: 49.9M users — Essential for urban audiences (18-35). Best for fashion, food, lifestyle, e-commerce.
- TikTok: 66.9M adults, +23% YoY growth. Self-serve ads now available in Pakistan. Best for youth brands, viral content.
- YouTube: 96.6M users — Best for long-form product demos, tutorials, pre-roll ads.
- WhatsApp: 91.7M users — Essential for customer communication, order confirmations, cart recovery.
- Google Search: Higher intent but limited reach. CPC higher than Meta. Best for B2B, high-ticket, local services.
- LinkedIn: Niche only — B2B and professional services.

**Cost Benchmarks (Actual Pakistani Market):**
- Meta CPM: PKR 120-480 (~$0.42-$1.70), CPC: PKR 5-20 (~$0.02-$0.07)
- TikTok CPM: PKR 80-300 (~$0.28-$1.05), CPC: PKR 3-15 (~$0.01-$0.05)
- Google CPC: PKR 25-100 (~$0.09-$0.35)
- Short-form vertical video (9:16) drives ~80% of digital traffic growth.

**Creative Best Practices:**
- Bilingual Urdu+English ads see 20-30% higher CTR than English-only.
- Authentic UGC-style content + real faces outperform polished production by 40-50% in hook rate.
- Pakistani audiences decide in 2-3 seconds — hook must be immediate and culturally relevant.
- Carousel ads work well for e-commerce (fashion, electronics).
- TikTok Spark Ads (boosting organic content) often deliver better engagement than traditional in-feed ads.

**Cultural Calendar:**
- Ramadan, Eid-ul-Fitr, Eid-ul-Azha — massive spending spikes on fashion, gifts, food.
- Independence Day (Aug 14) — patriotic branding opportunity.
- Wedding season (Oct-Mar) — fashion, jewellery, photography, event services.
- Back-to-school (Mar-Apr) — education, supplies, tutoring.
"""

BUSINESS_TYPES = [
    "E-commerce / Online Store",
    "Local Service / Brick & Mortar",
    "SaaS / Software",
    "Agency / Consulting",
    "Restaurant / Food Business",
    "Creator / Course / Coaching",
    "Real Estate",
    "Healthcare / Wellness",
    "Education / Training",
    "Other"
]

CAMPAIGN_OBJECTIVES = [
    "Brand Awareness / Reach",
    "Website Traffic",
    "Lead Generation",
    "Sales / Conversions",
    "App Installs",
    "Engagement / Community Building",
]

CREATIVE_ASSETS = [
    "Product photos",
    "Customer testimonial videos",
    "UGC / influencer content",
    "Before/after images",
    "Professional brand video",
    "Nothing yet — need full guidance",
]


# ═══════════════════════════════════════════════════════════════
# GROQ CLIENT INITIALIZATION
# ═══════════════════════════════════════════════════════════════

@st.cache_resource
def get_groq_client():
    return Groq(api_key=st.secrets["GROQ_API_KEY"])

try:
    client = get_groq_client()
except KeyError:
    st.error("🔑 Groq API key not found. Add `GROQ_API_KEY = \"gsk_...\"` to your Streamlit secrets.")
    st.stop()


# ═══════════════════════════════════════════════════════════════
# AGENT PROMPTS (Enhanced with location, language, context)
# ═══════════════════════════════════════════════════════════════

def build_prompt(agent_name, **kwargs):
    """Build a prompt for a given agent, injecting all user context."""
    
    url = kwargs.get("url", "")
    country = kwargs.get("country", "")
    provinces = kwargs.get("provinces", [])
    cities = kwargs.get("cities", "")
    languages = kwargs.get("languages", ["English"])
    bilingual = kwargs.get("bilingual", False)
    business_type = kwargs.get("business_type", "")
    objective = kwargs.get("objective", "")
    budget = kwargs.get("budget", 3000)
    competitor_urls = kwargs.get("competitor_urls", "")
    creative_assets = kwargs.get("creative_assets", [])
    platform = kwargs.get("platform", "Meta (Facebook/Instagram)")
    
    # Language instruction
    lang_str = ", ".join(languages)
    if bilingual and len(languages) >= 2:
        lang_instruction = f"Create ad content in a natural bilingual mix of {lang_str} (code-switching, as Pakistani audiences prefer in real life). Use {languages[0]} for headlines/hooks and blend {languages[1]} naturally in the body."
    else:
        lang_instruction = f"Create all ad content in {lang_str}."
    
    # Location context
    location_str = f"{country}"
    if provinces and "All" not in provinces[0]:
        location_str += f", specifically targeting these regions: {', '.join(provinces)}"
    if cities:
        location_str += f". Cities/areas: {cities}"
    
    # Market intelligence (inject for Pakistan)
    market_context = ""
    if country == "Pakistan":
        market_context = PAKISTAN_MARKET_CONTEXT
    
    # Business context
    biz_context = f"Business type: {business_type}." if business_type else ""
    obj_context = f"Campaign objective: {objective}." if objective else ""
    comp_context = f"Specific competitors to analyze: {competitor_urls}." if competitor_urls else ""
    asset_context = f"Available creative assets: {', '.join(creative_assets)}." if creative_assets else ""
    
    base_context = f"""
BUSINESS URL: {url}
TARGET LOCATION: {location_str}
LANGUAGE: {lang_instruction}
{biz_context}
{obj_context}
{comp_context}
{asset_context}

{market_context}
"""
    
    prompts = {
        "audience": f"""{base_context}
You are an expert audience researcher. Analyze this business and build 2-4 detailed audience personas tailored to {location_str}.
For each persona include:
- Demographics (age, income, location specific to {location_str})
- Psychographics (motivations, pain points, goals, cultural nuances)
- Platform behavior (where they spend time in {country}, peak activity)
- Targeting parameters for Meta, Google, TikTok (using {country}-specific options)
- Primary messaging hooks in {lang_str} that resonate culturally.
Output as well-structured plain text with clear sections.
End with SCORE: XX (0-100) rating audience clarity.""",

        "creative": f"""{base_context}
You are an expert ad creative strategist. Generate for this business targeting {location_str}:
A) 10 scroll-stopping hooks (use pattern interrupts, curiosity gaps, bold claims, relatable pain points) — make them culturally relevant to {country}
B) Platform-specific ad copy in {lang_str} for Meta (Facebook/Instagram), TikTok, and Google
C) A 30-second vertical video ad script (9:16) with shot-by-shot direction — use authentic, relatable visuals, real faces, not polished production
D) Creative direction brief with visual style, color palette, format recommendations.
Output as well-structured plain text with clear sections.
End with SCORE: XX (0-100) rating creative quality.""",

        "funnel": f"""{base_context}
You are an expert campaign funnel architect. Design a complete advertising funnel for this business in {location_str}.
- TOFU (40% budget): awareness campaigns, broad targeting on Meta/TikTok, KPIs (CPM, CTR)
- MOFU (30%): retargeting site visitors, consideration content, KPIs (CPC, CPL)
- BOFU (20%): conversion campaigns, high-intent audiences, KPIs (CPA, ROAS)
- Retargeting layer (10%): dynamic ads, WhatsApp follow-up (if Pakistan), frequency cap
Use {country}-specific platform recommendations and cost benchmarks.
Provide campaign naming conventions.
Output as well-structured plain text.
End with SCORE: XX (0-100) rating funnel completeness.""",

        "competitive": f"""{base_context}
You are an expert competitive analyst for {country}'s market.
Identify 3-5 competitors in {location_str}. For each describe their ad strategy, hooks, platforms, estimated spend in local context.
Then provide:
- Gaps to exploit (audience, message, platform, creative)
- Counter-positioning strategy relevant to {country} consumers
- Competitive SWOT tailored to {location_str}.
Output as well-structured plain text.
End with SCORE: XX (0-100) rating competitive insight.""",

        "budget": f"""{base_context}
You are an expert budget strategist for the {country} market.
Allocate ${budget}/month across platforms appropriate for {country} (Meta, TikTok, Google, YouTube, LinkedIn, Pinterest).
Use {country}-specific CPM, CPC, CPA benchmarks (NOT international averages).
Provide percentage splits, dollar amounts, projected impressions, clicks, conversions, and ROAS.
Include a 3-month scaling plan with budget increases tied to performance.
Output as well-structured plain text.
End with SCORE: XX (0-100) rating budget efficiency.""",

        "quick": f"""{base_context}
Give a 60-second ad readiness snapshot for this business in {location_str}.
Analyze: value proposition clarity, offer strength, CTA quality, social proof, best platform to start (considering {country} market), estimated starting budget in local context.
Output as compact plain text.
End with SCORE: XX (0-100).""",

        "keywords": f"""{base_context}
You are a Google Ads keyword strategist for the {country} market.
Build a keyword strategy: high-intent keywords, commercial investigation keywords, negative keywords, match type recommendations, bid suggestions in {country} context.
Output as well-structured plain text.""",

        "copy": f"""{base_context}
Generate platform-specific ad copy for {platform} targeting {location_str}.
Language: {lang_instruction}
Include headlines, primary text, descriptions, CTAs. Follow {platform} best practices and {country}-specific audience preferences.
Output as well-structured plain text.""",

        "hooks": f"""{base_context}
Generate 20 scroll-stopping hooks for ads targeting {location_str}.
Language: {lang_instruction}
Use these categories: pattern interrupts, curiosity gaps, bold claims, relatable pain points.
Make hooks culturally relevant to {country} audiences.
Output as well-structured plain text.""",

        "creative_brief": f"""{base_context}
Create a creative brief for designers and editors targeting {location_str}.
Include visual style (authentic vs polished, considering {country} preferences), color palette, format specs for Meta/TikTok/Google, do's and don'ts.
Available assets: {asset_context}
Output as well-structured plain text.""",

        "video_script": f"""{base_context}
Create a 30-second vertical video ad script (9:16) targeting {location_str}.
Language: {lang_instruction}
Format: Time | Visual Scene | Audio/Voiceover | Text Overlay
Use authentic, relatable visuals for {country} audiences. Real faces, real settings.
Include hook (0-3s), problem (3-8s), solution (8-20s), social proof (20-25s), CTA (25-30s).
Output as well-structured plain text.""",

        "funnel_only": f"""{base_context}
Design a full ads funnel architecture for this business targeting {location_str}.
TOFU/MOFU/BOFU/Retargeting with campaign structure, audiences, KPIs specific to {country}.
Output as well-structured plain text.""",

        "testing": f"""{base_context}
Create an A/B testing plan for a campaign targeting {location_str}.
Include variables to test, sample sizes relevant to {country} audience sizes, duration, success criteria.
Output as well-structured plain text.""",

        "landing_audit": f"""{base_context}
Audit the landing page at {url} for conversion optimization in {country}'s market.
Evaluate headline clarity, CTA, trust signals, mobile experience, copy quality.
Recommend specific rewrites optimized for {country} consumers.
Output as well-structured plain text.""",

        "ad_audit": f"""{base_context}
Audit existing ad performance for this business in {country}.
Identify wasted spend, underperforming campaigns, optimization opportunities using {country} benchmarks.
Output as well-structured plain text.""",
    }
    
    return prompts.get(agent_name, prompts["quick"])


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def call_groq(prompt, max_tokens=4096):
    """Call Groq API and return text response."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

def extract_score(text):
    """Extract SCORE: XX from agent output."""
    m = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 65

def grade_from_score(score):
    """Convert numeric score to letter grade."""
    if score >= 95: return "A+"
    if score >= 90: return "A"
    if score >= 85: return "A-"
    if score >= 80: return "B+"
    if score >= 75: return "B"
    if score >= 70: return "B-"
    if score >= 65: return "C+"
    if score >= 60: return "C"
    if score >= 55: return "C-"
    if score >= 50: return "D+"
    if score >= 45: return "D"
    if score >= 40: return "D-"
    return "F"

def score_color(score):
    """Return hex color for score."""
    if score >= 80: return "#10B981"
    elif score >= 65: return "#3B82F6"
    elif score >= 50: return "#F59E0B"
    return "#EF4444"

def status_label(score):
    """Return status text."""
    if score >= 80: return "✅ Strong"
    elif score >= 65: return "⚠️ Needs Work"
    return "🔴 Critical"

# ── Visualization helpers ──────────────────────────────────

def build_gauge_chart(score, title="Ad Readiness Score"):
    """Build a Plotly gauge chart."""
    if not PLOTLY_AVAILABLE:
        return None
    
    color = score_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": title, "font": {"size": 20, "color": "#1E293B"}},
        number={"font": {"size": 48, "color": color, "family": "Inter"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#1E293B"},
            "bar": {"color": color, "thickness": 0.2},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "#E2E8F0",
            "steps": [
                {"range": [0, 40], "color": "#FEE2E2"},
                {"range": [40, 55], "color": "#FEF3C7"},
                {"range": [55, 70], "color": "#DBEAFE"},
                {"range": [70, 85], "color": "#D1FAE5"},
                {"range": [85, 100], "color": "#A7F3D0"},
            ],
            "threshold": {
                "line": {"color": color, "width": 4},
                "thickness": 0.75,
                "value": score
            }
        }
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=30, r=30, t=50, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, system-ui, sans-serif"}
    )
    return fig

def build_breakdown_chart(scores, weights):
    """Build a horizontal bar chart for category scores."""
    if not PLOTLY_AVAILABLE:
        return None
    
    categories = ["Audience Clarity", "Creative Quality", "Funnel Architecture", "Competitive Position", "Budget Efficiency"]
    values = [scores.get("audience", 65), scores.get("creative", 65), scores.get("funnel", 65), scores.get("competitive", 65), scores.get("budget", 65)]
    weight_labels = [f"{w}%" for w in [25, 20, 20, 15, 20]]
    
    colors_list = [score_color(v) for v in values]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=categories,
        x=values,
        orientation='h',
        marker=dict(color=colors_list, cornerradius=6),
        text=[f"{v}  ({w})" for v, w in zip(values, weight_labels)],
        textposition='outside',
        textfont=dict(color="#1E293B", size=13),
        hovertemplate='%{y}: %{x}/100<br>Weight: %{text}<extra></extra>'
    ))
    fig.update_layout(
        height=280,
        xaxis=dict(range=[0, 100], showgrid=True, gridcolor="#E2E8F0", title=None),
        yaxis=dict(autorange="reversed", title=None),
        margin=dict(l=10, r=60, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, system-ui, sans-serif"},
        showlegend=False
    )
    return fig

def build_pdf_report(data, output_path):
    """Generate enhanced PDF with charts and infographics."""
    if not PDF_AVAILABLE:
        return None
    
    COLORS_PDF = {
        "navy": HexColor("#1E3A5F"),
        "blue": HexColor("#2563EB"),
        "green": HexColor("#10B981"),
        "amber": HexColor("#F59E0B"),
        "red": HexColor("#EF4444"),
        "light": HexColor("#F8FAFC"),
        "white": white,
        "border": HexColor("#E2E8F0"),
        "text": HexColor("#1E293B"),
        "muted": HexColor("#64748B"),
    }
    
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.6*inch, bottomMargin=0.6*inch)
    styles = getSampleStyleSheet()
    
    # Custom styles
    styles.add(ParagraphStyle("CoverTitle", parent=styles["Title"], fontSize=26, textColor=COLORS_PDF["navy"], alignment=TA_CENTER, spaceAfter=12))
    styles.add(ParagraphStyle("SectionHead", parent=styles["Heading2"], fontSize=15, textColor=COLORS_PDF["navy"], spaceBefore=18, spaceAfter=8))
    styles.add(ParagraphStyle("BodyText2", parent=styles["Normal"], fontSize=9.5, leading=14, textColor=COLORS_PDF["text"]))
    
    story = []
    
    # ── Page 1: Cover ──
    story.append(Spacer(1, 1.5*inch))
    story.append(Paragraph("AI Advertising Strategy Report", styles["CoverTitle"]))
    story.append(Spacer(1, 0.2*inch))
    url_clean = data.get("url", "").replace("https://", "").replace("http://", "")
    story.append(Paragraph(f"<font size='14' color='#64748B'>{url_clean}</font>", ParagraphStyle("Center", alignment=TA_CENTER)))
    story.append(Spacer(1, 0.15*inch))
    location = data.get("country", "")
    if data.get("cities"):
        location += f" — {data.get('cities', '')}"
    story.append(Paragraph(f"<font size='11' color='#94A3B8'>Target Market: {location}</font>", ParagraphStyle("Center2", alignment=TA_CENTER)))
    story.append(Spacer(1, 0.4*inch))
    
    # Score gauge (drawn with ReportLab graphics)
    score = data.get("total", 65)
    grade = data.get("grade", "C+")
    sc = score_color(score)
    gauge_d = Drawing(250, 140)
    # Background arc
    for i in range(0, 100, 5):
        angle_start = 180 + (i * 180 / 100)
        angle_end = 180 + ((i + 5) * 180 / 100)
        seg_color = HexColor("#10B981") if i >= 80 else HexColor("#3B82F6") if i >= 60 else HexColor("#F59E0B") if i >= 40 else HexColor("#EF4444")
        if i <= score:  # fill up to score
            gauge_d.add(Wedge(125, 80, 80, angle_start, min(angle_end, 180 + score * 180 / 100), fillColor=seg_color, strokeColor=None))
    # Center
    gauge_d.add(Circle(125, 80, 55, fillColor=COLORS_PDF["white"], strokeColor=COLORS_PDF["border"], strokeWidth=1))
    gauge_d.add(String(125, 90, str(int(score)), fontSize=32, fillColor=HexColor(sc), textAnchor="middle", fontName="Helvetica-Bold"))
    gauge_d.add(String(125, 68, f"/ 100  |  Grade: {grade}", fontSize=10, fillColor=COLORS_PDF["muted"], textAnchor="middle"))
    story.append(gauge_d)
    
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(f"<font size='12' color='#1E293B'>Report Generated: {datetime.now().strftime('%B %d, %Y')}</font>", ParagraphStyle("Center3", alignment=TA_CENTER)))
    story.append(PageBreak())
    
    # ── Page 2: Score Breakdown ──
    story.append(Paragraph("📊 Score Breakdown", styles["SectionHead"]))
    story.append(Spacer(1, 0.15*inch))
    
    # Horizontal bar chart using ReportLab
    scores = data.get("scores", {})
    weights_dict = {"audience": 25, "creative": 20, "funnel": 20, "competitive": 15, "budget": 20}
    cats = ["Audience", "Creative", "Funnel", "Competitive", "Budget"]
    vals = [scores.get(k, 65) for k in ["audience", "creative", "funnel", "competitive", "budget"]]
    wts = [25, 20, 20, 15, 20]
    
    chart_d = Drawing(400, 160)
    bc = HorizontalBarChart()
    bc.x = 80
    bc.y = 20
    bc.width = 280
    bc.height = 120
    bc.data = [vals]
    bc.categoryAxis.categoryNames = cats
    bc.categoryAxis.labels.fontSize = 9
    bc.categoryAxis.labels.fillColor = COLORS_PDF["text"]
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100
    bc.valueAxis.valueStep = 20
    bc.bars[0].fillColor = COLORS_PDF["blue"]
    bc.bars.strokeColor = None
    chart_d.add(bc)
    story.append(chart_d)
    
    # Weight table
    table_data = [["Category", "Score", "Weight", "Status"]]
    for i, cat in enumerate(cats):
        sc_val = vals[i]
        status = "✅ Strong" if sc_val >= 80 else "⚠️ Needs Work" if sc_val >= 65 else "🔴 Critical"
        table_data.append([cat, str(sc_val), f"{wts[i]}%", status])
    
    tbl = Table(table_data, colWidths=[1.6*inch, 0.9*inch, 0.9*inch, 1.2*inch])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLORS_PDF["navy"]),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, COLORS_PDF["border"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, COLORS_PDF["light"]]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(Spacer(1, 0.2*inch))
    story.append(tbl)
    story.append(PageBreak())
    
    # ── Pages 3-7: Agent outputs ──
    agent_names = {"audience": "🎯 Audience Personas", "creative": "✍️ Ad Creative & Copy", 
                   "funnel": "🔽 Campaign Funnel", "competitive": "🔍 Competitive Intelligence", 
                   "budget": "💰 Budget Allocation & Projections"}
    
    for key, title in agent_names.items():
        text = data.get("results", {}).get(key, "")
        if text:
            story.append(Paragraph(title, styles["SectionHead"]))
            story.append(Spacer(1, 0.1*inch))
            # Clean text for PDF
            clean = text.replace("\n", "<br/>").replace("#", "")
            story.append(Paragraph(clean, styles["BodyText2"]))
            story.append(PageBreak())
    
    # ── Final page: Action Plan ──
    story.append(Paragraph("📋 Action Plan & Next Steps", styles["SectionHead"]))
    story.append(Spacer(1, 0.15*inch))
    action_items = [
        "✅ Week 1: Verify tracking pixels are installed correctly. Launch initial test campaigns with 3 creative variants.",
        "✅ Week 2: Analyze early data. Kill underperformers. Scale winning creatives. Build retargeting audiences.",
        "✅ Week 3: Introduce MOFU content (testimonials, case studies). Launch lookalike audiences from converters.",
        "✅ Week 4: Full-funnel optimization. Prepare Month 2 scaling plan.",
        "📅 Month 2: Increase budget 30-50% on proven channels. Expand to secondary platform.",
        "📅 Month 3: International/regional expansion if applicable. Advanced bid strategies (tCPA, tROAS)."
    ]
    for item in action_items:
        story.append(Paragraph(item, styles["BodyText2"]))
        story.append(Spacer(1, 0.08*inch))
    
    doc.build(story)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════
# UI: HERO HEADER
# ═══════════════════════════════════════════════════════════════

st.markdown("""
<div class="hero-header">
    <h1>🎯 AI Ads Strategist</h1>
    <p>15 advertising skills · 6 platforms · Pakistan optimized · Zero login</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
# UI: COMMAND SELECTOR (Main)
# ═══════════════════════════════════════════════════════════════

col_cmd, col_url = st.columns([1, 2])

with col_cmd:
    command = st.selectbox("🎛️ Choose a service:", [
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

with col_url:
    url = st.text_input("🌐 Business Website URL:", "https://example.com", 
                        placeholder="https://your-business.com")


# ═══════════════════════════════════════════════════════════════
# UI: TARGET MARKET SETTINGS (Collapsible)
# ═══════════════════════════════════════════════════════════════

with st.expander("🌍 Target Market & Strategy Settings", expanded=True):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        country = st.selectbox("Country:", COUNTRIES, index=0, key="country_select")
        provinces_available = PROVINCES_BY_COUNTRY.get(country, ["All Regions"])
        provinces = st.multiselect("Provinces/Regions (optional):", provinces_available, 
                                   default=["All Provinces"] if "All" in provinces_available[0] else [provinces_available[0]],
                                   key="provinces_select")
    
    with col2:
        cities = st.text_input("Cities/Areas (optional):", "", placeholder="Karachi, Lahore, Islamabad")
        languages_available = LANGUAGES_BY_COUNTRY.get(country, ["English"])
        # Smart default: for Pakistan, default to ["Urdu", "English"]
        default_langs = ["Urdu", "English"] if country == "Pakistan" else [languages_available[0]]
        languages = st.multiselect("Ad Languages:", languages_available, default=default_langs, key="lang_select")
    
    with col3:
        business_type = st.selectbox("Business Type:", [""] + BUSINESS_TYPES, key="biz_type")
        campaign_objective = st.selectbox("Campaign Objective:", [""] + CAMPAIGN_OBJECTIVES, key="obj_select")
        bilingual = st.checkbox("Generate bilingual copy (mix selected languages)", 
                                value=(country == "Pakistan" and len(languages) >= 2),
                                key="bilingual_check")

with st.expander("🎯 Advanced Options (optional)", expanded=False):
    col_adv1, col_adv2 = st.columns(2)
    with col_adv1:
        competitor_urls = st.text_area("Competitor URLs or names:", "", 
                                       placeholder="competitor1.com, competitor2.com",
                                       height=80)
        budget_amount = st.number_input("Monthly Budget ($):", min_value=100, value=3000, step=500, key="budget_input")
    
    with col_adv2:
        creative_assets = st.multiselect("Available creative assets:", CREATIVE_ASSETS, key="creative_assets")
        extra_notes = st.text_area("Additional context for AI:", "", 
                                   placeholder="Any extra details about your business, target audience, or current ad situation...",
                                   height=100)


# ═══════════════════════════════════════════════════════════════
# GENERATE BUTTON
# ═══════════════════════════════════════════════════════════════

gen_col1, gen_col2, gen_col3 = st.columns([1, 2, 1])
with gen_col2:
    generate_clicked = st.button("🚀 Generate Strategy Report", type="primary", use_container_width=True)


# ═══════════════════════════════════════════════════════════════
# PROCESS & DISPLAY RESULTS
# ═══════════════════════════════════════════════════════════════

if generate_clicked:
    if not url.startswith("http"):
        st.warning("⚠️ Please enter a valid URL starting with http:// or https://")
    else:
        # Build context kwargs
        ctx = {
            "url": url,
            "country": country,
            "provinces": provinces,
            "cities": cities,
            "languages": languages,
            "bilingual": bilingual,
            "business_type": business_type,
            "objective": campaign_objective,
            "budget": budget_amount,
            "competitor_urls": competitor_urls,
            "creative_assets": creative_assets,
        }
        
        if command == "📊 Full Strategy (all 5 agents)":
            results = {}
            scores = {}
            agents = ["audience", "creative", "funnel", "competitive", "budget"]
            weights = {"audience": 25, "creative": 20, "funnel": 20, "competitive": 15, "budget": 20}
            
            progress_bar = st.progress(0, text="Starting analysis...")
            
            for i, agent in enumerate(agents):
                progress_bar.progress((i) / len(agents), text=f"Running {agent} agent...")
                prompt = build_prompt(agent, **ctx)
                output = call_groq(prompt)
                results[agent] = output
                scores[agent] = extract_score(output)
                time.sleep(0.5)
            
            progress_bar.progress(1.0, text="Complete! Building report...")
            
            # Compute total
            total_score = sum(scores.get(a, 65) * weights[a] / 100 for a in agents)
            grade = grade_from_score(total_score)
            
            # ── DISPLAY: Score Dashboard ──
            st.markdown("---")
            st.markdown("## 📊 Ad Readiness Score Dashboard")
            
            # Metric cards row
            metric_cols = st.columns(5)
            metric_data = [
                ("🎯", f"{scores.get('audience',65)}", "Audience"),
                ("✍️", f"{scores.get('creative',65)}", "Creative"),
                ("🔽", f"{scores.get('funnel',65)}", "Funnel"),
                ("🔍", f"{scores.get('competitive',65)}", "Competitive"),
                ("💰", f"{scores.get('budget',65)}", "Budget"),
            ]
            for idx, (icon, val, label) in enumerate(metric_data):
                with metric_cols[idx]:
                    sc = int(val)
                    color = score_color(sc)
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="metric-icon">{icon}</div>
                        <div class="metric-value" style="color:{color}">{val}</div>
                        <div class="metric-label">{label}</div>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Gauge + Bar chart
            chart_col1, chart_col2 = st.columns([1, 1])
            with chart_col1:
                if PLOTLY_AVAILABLE:
                    gauge = build_gauge_chart(total_score)
                    st.plotly_chart(gauge, use_container_width=True)
                else:
                    st.markdown(f"""
                    <div style="text-align:center; margin:2rem 0;">
                        <div style="width:150px;height:150px;border-radius:50%;background:{score_color(total_score)};margin:0 auto;display:flex;align-items:center;justify-content:center;flex-direction:column;color:white;">
                            <span style="font-size:3rem;font-weight:700;">{total_score:.0f}</span>
                            <span style="font-size:1.3rem;">/100</span>
                        </div>
                        <p style="font-size:1.5rem;font-weight:700;margin-top:0.5rem;">Grade: {grade}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            with chart_col2:
                if PLOTLY_AVAILABLE:
                    bar_chart = build_breakdown_chart(scores, weights)
                    st.plotly_chart(bar_chart, use_container_width=True)
            
            # ── DISPLAY: Report Sections ──
            st.markdown("---")
            st.markdown("## 📋 Full Strategy Report")
            
            section_icons = {
                "audience": "🎯", "creative": "✍️", "funnel": "🔽",
                "competitive": "🔍", "budget": "💰"
            }
            
            for agent in agents:
                with st.expander(f"{section_icons[agent]} {agent.title()} Analysis", expanded=(agent == "audience")):
                    st.markdown(results[agent])
            
            # ── Download buttons ──
            st.markdown("---")
            dl_col1, dl_col2, dl_col3 = st.columns(3)
            
            # Save complete report as markdown
            report_md = f"""# AI ADS STRATEGY REPORT
**Business:** {url}
**Target Market:** {country} {f'- {cities}' if cities else ''}
**Date:** {datetime.now().strftime('%B %d, %Y')}

## Ad Readiness Score: {total_score:.0f}/100 (Grade: {grade})

| Category | Score | Weight | Status |
|----------|-------|--------|--------|
"""
            for a in agents:
                s = scores.get(a, 65)
                status = "✅ Strong" if s >= 80 else "⚠️ Needs Work" if s >= 65 else "🔴 Critical"
                report_md += f"| {a.title()} | {s} | {weights[a]}% | {status} |\n"
            
            for a in agents:
                report_md += f"\n## {a.title()}\n\n{results[a]}\n"
            
            with dl_col1:
                st.download_button("⬇ Download Report (.md)", report_md, 
                                   file_name=f"ADS-STRATEGY-{url.replace('https://','').replace('http://','').split('/')[0]}.md",
                                   mime="text/markdown")
            
            # PDF
            with dl_col2:
                if PDF_AVAILABLE:
                    pdf_data = {
                        "url": url, "country": country, "cities": cities,
                        "total": total_score, "grade": grade,
                        "scores": scores, "results": results
                    }
                    pdf_buf = build_pdf_report(pdf_data, "")
                    if pdf_buf:
                        st.download_button("📄 Download PDF Report", pdf_buf,
                                           file_name=f"ADS-Report-{url.replace('https://','').replace('http://','').split('/')[0]}.pdf",
                                           mime="application/pdf")
                else:
                    st.info("📄 PDF requires `reportlab`. Add to requirements.txt for PDF export.")
            
            # Store for later PDF command
            st.session_state["last_strategy"] = {
                "url": url, "country": country, "cities": cities,
                "total": total_score, "grade": grade,
                "scores": scores, "results": results,
                "context": ctx
            }
            
            st.success(f"✅ Full strategy complete! Score: {total_score:.0f}/100 ({grade})")
            progress_bar.empty()
        
        elif command == "📑 Generate PDF Report (from last strategy)":
            if "last_strategy" not in st.session_state:
                st.warning("⚠️ No strategy has been generated yet. Run 'Full Strategy' first.")
            elif PDF_AVAILABLE:
                data = st.session_state["last_strategy"]
                pdf_buf = build_pdf_report(data, "")
                if pdf_buf:
                    st.download_button("📄 Download PDF Report", pdf_buf,
                                       file_name=f"ADS-Report-{data.get('url','report').replace('https://','').replace('http://','').split('/')[0]}.pdf",
                                       mime="application/pdf")
                st.success("✅ PDF ready for download!")
            else:
                st.error("PDF generation requires `reportlab`. Add 'reportlab' to your requirements.txt.")
        
        else:
            # ── All other single-agent commands ──
            with st.spinner(f"Running {command}..."):
                agent_map = {
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
                
                agent_key = agent_map.get(command, "quick")
                
                # Get platform for copy command
                if command == "✍️ Ad Copy Generator":
                    platform_choice = st.selectbox("Select platform:", ["Meta (Facebook/Instagram)", "Google Ads", "TikTok", "YouTube", "LinkedIn", "Pinterest"])
                    ctx["platform"] = platform_choice
                
                prompt = build_prompt(agent_key, **ctx)
                result = call_groq(prompt)
                sc = extract_score(result)
                
                # Display in styled card
                st.markdown("---")
                st.markdown(f"## {command}")
                
                if sc:
                    st.markdown(f"""
                    <div style="text-align:center; margin:1rem 0;">
                        <span style="font-size:1.2rem;font-weight:600;color:{score_color(sc)};">Quality Score: {sc}/100</span>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="section-card">
                    <pre style="white-space:pre-wrap;font-family:inherit;font-size:0.95rem;line-height:1.6;">{result}</pre>
                </div>
                """, unsafe_allow_html=True)
                
                # Download
                st.download_button("⬇ Download Result (.md)", f"# {command}\n\n{result}",
                                   file_name=f"ADS-{agent_key}.md", mime="text/markdown")
                
                st.success("✅ Analysis complete!")


# ═══════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════

st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#94A3B8; font-size:0.85rem; padding:1rem 0;">
    Powered by Groq · 100% Free · No Login Required · Pakistan Market Optimized<br/>
    Built with Streamlit + Plotly · Enhanced PDF Reports
</div>
""", unsafe_allow_html=True)