import streamlit as st
import re, time
from groq import Groq

# ── Initialize Groq client from Streamlit secrets ──────────
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ── Agent prompts (condensed versions based on the original repo) ──
PROMPTS = {
    "audience": """You are an expert audience researcher. Analyze this business: {url}.
Build 2‑4 detailed audience personas. For each persona include:
- Demographics (age, income, location)
- Psychographics (motivations, pain points, goals)
- Platform behavior (where they spend time, peak activity)
- Targeting parameters for Meta, Google, LinkedIn, TikTok
- Primary messaging hooks.
Output as plain text. End with SCORE: xx (0‑100) rating the clarity of audience definition.""",

    "creative": """You are an expert ad creative strategist. Analyze this business: {url}.
Generate:
A) 10 scroll‑stopping hooks (pattern interrupts, curiosity gaps, bold claims)
B) Platform‑specific ad copy for Google Search, Meta, LinkedIn, TikTok
C) A 30‑second video ad script with shot‑by‑shot direction
D) Creative direction brief with visual style and format recommendations.
Output as plain text. End with SCORE: xx (0‑100) rating creative quality.""",

    "funnel": """You are an expert campaign funnel architect. Analyze this business: {url}.
Design a full advertising funnel:
- TOFU (40% budget): awareness campaigns, broad targeting, KPIs (CPM, CTR)
- MOFU (30%): retargeting, consideration content, KPIs (CPC, CPL)
- BOFU (20%): conversion campaigns, high‑intent audiences, KPIs (CPA, ROAS)
- Retargeting layer (10%): dynamic ads, frequency cap.
Provide campaign naming conventions.
Output as plain text. End with SCORE: xx (0‑100) rating funnel completeness.""",

    "competitive": """You are an expert competitive analyst. Analyze this business: {url}.
Identify 3‑5 competitors. For each describe their ad strategy, hooks, platforms, estimated spend.
Then provide:
- Gaps to exploit (audience, message, platform, creative)
- Counter‑positioning strategy
- Competitive SWOT.
Output as plain text. End with SCORE: xx (0‑100) rating competitive insight.""",

    "budget": """You are an expert budget strategist. Analyze this business: {url} with a monthly budget of ${budget}.
Allocate across Google Ads, Meta, LinkedIn, TikTok, YouTube, Pinterest.
Provide percentage splits, dollar amounts, projected CPM, CPC, CPA, and ROAS.
Include a 3‑month scaling plan.
Output as plain text. End with SCORE: xx (0‑100) rating budget efficiency.""",

    "quick": """You are an advertising auditor. Give a 60‑second ad readiness snapshot for {url}.
Analyze: value proposition clarity, offer strength, CTA quality, social proof, best platform to start, estimated starting budget.
Output as plain text. End with SCORE: xx (0‑100).""",

    "keywords": """You are a Google Ads keyword strategist. Build a keyword strategy for {url}.
Include: high‑intent keywords, commercial investigation keywords, negative keywords, match type recommendations, bid suggestions.
Output as plain text.""" ,

    "copy": """Generate platform‑specific ad copy for {url} on {platform}.
Include headlines, primary text, descriptions, CTAs. Follow platform best practices.
Output as plain text.""" ,

    "hooks": """Generate 20 scroll‑stopping hooks for ads for {url}.
Use these categories: pattern interrupts, curiosity gaps, bold claims, relatable pain points.
Output as plain text.""" ,

    "creative_brief": """Create a creative brief for designers and editors for {url}.
Include visual style, color palette, format specs for Meta/Google/TikTok, do's and don'ts.
Output as plain text.""" ,

    "video_script": """Create a 30‑second video ad script for {url}.
Time | Visual | Audio/Text Overlay. Include hook, body, CTA.
Output as plain text.""" ,

    "funnel_only": """Design a full ads funnel architecture for {url}.
TOFU/MOFU/BOFU/Retargeting with campaign structure, audiences, KPIs.
Output as plain text.""" ,

    "testing": """Create an A/B testing plan for a campaign of {url}.
Include variables to test, sample sizes, duration, success criteria.
Output as plain text.""" ,

    "landing_audit": """Audit the landing page at {url} for conversion optimization.
Evaluate headline clarity, CTA, trust signals, mobile experience, copy.
Output as plain text.""" ,

    "ad_audit": """Audit the existing ad performance for {url}.
Identify wasted spend, underperforming campaigns, optimization opportunities.
Output as plain text."""
}

# ── Weighted scoring for full strategy ──
WEIGHTS = {"audience":25, "creative":20, "funnel":20, "competitive":15, "budget":20}

def grade(score):
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

def call_groq(prompt, max_tokens=4096):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content

def extract_score(text):
    m = re.search(r"SCORE:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else 65

# ── Streamlit UI ──────────────────────────────────────────
st.set_page_config(page_title="AI Ads Strategist", layout="wide")
st.title("🎯 AI Ads Strategist")
st.caption("15 advertising skills · 6 platforms · No login required")

command = st.selectbox("Choose a service:", [
    "📊 Full Strategy (all 5 agents)",
    "⚡ 60‑Second Snapshot",
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

url = st.text_input("Enter business website URL:", "https://example.com")

# Dynamic extra inputs
extra_inputs = {}
if command == "✍️ Ad Copy Generator":
    extra_inputs["platform"] = st.selectbox("Platform:", ["Meta (Facebook/Instagram)", "Google Ads", "LinkedIn", "TikTok", "YouTube", "Pinterest"])
elif command == "💰 Budget Allocation":
    extra_inputs["budget"] = st.number_input("Monthly budget ($):", min_value=100, value=3000, step=500)

if st.button("Generate", type="primary"):
    if not url.startswith("http"):
        st.warning("Please enter a valid URL starting with http:// or https://")
    else:
        # ── Route to appropriate handler ──
        with st.spinner("Running AI agents…"):
            if command == "📊 Full Strategy (all 5 agents)":
                results = {}
                scores = {}
                progress = st.progress(0)
                agents = ["audience", "creative", "funnel", "competitive", "budget"]
                for i, agent in enumerate(agents):
                    prompt = PROMPTS[agent].format(url=url, budget=3000)  # default budget
                    output = call_groq(prompt)
                    results[agent] = output
                    scores[agent] = extract_score(output)
                    progress.progress((i+1)/len(agents))
                    time.sleep(0.5)

                total = sum(scores.get(a,65) * WEIGHTS[a]/100 for a in agents)
                g = grade(total)
                color = "#10B981" if total>=80 else "#3B82F6" if total>=65 else "#F59E0B" if total>=50 else "#EF4444"

                # Report
                st.markdown(f"## Ad Readiness Score: {total:.0f}/100 ({g})")
                st.markdown(f"<div style='background:{color};width:120px;height:120px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:white;font-size:3rem;font-weight:bold;margin:0 auto;'>{total:.0f}</div>", unsafe_allow_html=True)

                # Table
                table = "| Category | Score | Weight | Status |\n|---|---|---|---|\n"
                for a in agents:
                    s = scores.get(a,65)
                    status = "✅ Strong" if s>=80 else "⚠️ Needs Work" if s>=65 else "🔴 Critical"
                    table += f"| {a.title()} | {s} | {WEIGHTS[a]}% | {status} |\n"
                st.markdown(table)

                for a in agents:
                    st.subheader(a.title())
                    st.text(results[a])

                # Store for PDF
                st.session_state["last_strategy"] = {
                    "results": results, "scores": scores, "total": total, "grade": g, "url": url
                }
                st.success("Full strategy saved. You can now generate a PDF report.")

            elif command == "⚡ 60‑Second Snapshot":
                prompt = PROMPTS["quick"].format(url=url)
                res = call_groq(prompt, 1024)
                sc = extract_score(res)
                st.subheader(f"Snapshot Score: {sc}/100")
                st.text(res)

            elif command == "🎯 Audience Personas":
                res = call_groq(PROMPTS["audience"].format(url=url))
                st.text(res)

            elif command == "🔍 Competitor Analysis":
                res = call_groq(PROMPTS["competitive"].format(url=url))
                st.text(res)

            elif command == "🔑 Keyword Strategy":
                res = call_groq(PROMPTS["keywords"].format(url=url))
                st.text(res)

            elif command == "✍️ Ad Copy Generator":
                platform = extra_inputs["platform"]
                prompt = PROMPTS["copy"].format(url=url, platform=platform)
                res = call_groq(prompt)
                st.text(res)

            elif command == "🪝 Hook Generator (20 hooks)":
                res = call_groq(PROMPTS["hooks"].format(url=url))
                st.text(res)

            elif command == "🎨 Creative Brief":
                res = call_groq(PROMPTS["creative_brief"].format(url=url))
                st.text(res)

            elif command == "🎬 Video Ad Script":
                res = call_groq(PROMPTS["video_script"].format(url=url))
                st.text(res)

            elif command == "🔽 Funnel Architecture":
                res = call_groq(PROMPTS["funnel_only"].format(url=url))
                st.text(res)

            elif command == "💰 Budget Allocation":
                budget = extra_inputs["budget"]
                prompt = PROMPTS["budget"].format(url=url, budget=budget)
                res = call_groq(prompt)
                st.text(res)

            elif command == "🧪 A/B Testing Plan":
                res = call_groq(PROMPTS["testing"].format(url=url))
                st.text(res)

            elif command == "📄 Landing Page Audit":
                res = call_groq(PROMPTS["landing_audit"].format(url=url))
                st.text(res)

            elif command == "📊 Ad Performance Audit":
                res = call_groq(PROMPTS["ad_audit"].format(url=url))
                st.text(res)

            elif command == "📑 Generate PDF Report (from last strategy)":
                if "last_strategy" not in st.session_state:
                    st.warning("No strategy has been generated yet. Run 'Full Strategy' first.")
                else:
                    # Generate PDF using reportlab (must be installed)
                    try:
                        from reportlab.lib.pagesizes import letter
                        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                        from reportlab.lib import colors
                        import io, datetime

                        data = st.session_state["last_strategy"]
                        buf = io.BytesIO()
                        doc = SimpleDocTemplate(buf, pagesize=letter)
                        story = []
                        styles = getSampleStyleSheet()
                        story.append(Paragraph(f"AI Ads Strategy Report – {data['url']}", styles["Title"]))
                        story.append(Paragraph(f"Score: {data['total']:.0f}/100 ({data['grade']})", styles["Heading2"]))
                        # Add each agent text
                        for agent in ["audience","creative","funnel","competitive","budget"]:
                            story.append(Paragraph(agent.title(), styles["Heading3"]))
                            story.append(Paragraph(data["results"][agent].replace("\n","<br/>"), styles["Normal"]))
                            story.append(Spacer(1,12))
                        doc.build(story)
                        buf.seek(0)
                        st.download_button("Download PDF", buf, file_name="ads_strategy_report.pdf", mime="application/pdf")
                    except ImportError:
                        st.error("PDF generation requires reportlab. Add 'reportlab' to requirements.txt.")