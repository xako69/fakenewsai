import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from datetime import datetime
import time
import os
import warnings
import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import urllib.parse

warnings.filterwarnings("ignore", category=UserWarning)

# ---------------- ORIGINAL IMPORTS ----------------
from utils.semantic_verifier import semantic_verify
from utils.url_extract import extract_title_from_url
from utils.ocr_extract import extract_text_from_image
from utils.ml_model import predict_ml

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Fake News AI Platform", page_icon="🧿", layout="wide")

# -------------------------------------------------
# 🚀 ULTRA-MODERN UI & ANIMATIONS
# -------------------------------------------------
st.markdown("""
<style>
/* Animated Deep Space Background */
.stApp {
    background: radial-gradient(circle at 15% 50%, #0f172a, #1e1b4b, #020617);
    background-size: 200% 200%;
    animation: cyber-glow 15s ease infinite;
    color: #f8fafc;
}
@keyframes cyber-glow { 
    0% {background-position: 0% 50%} 
    50% {background-position: 100% 50%} 
    100% {background-position: 0% 50%} 
}

/* Glassmorphism Header */
.header {
    padding: 40px;
    border-radius: 20px;
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    text-align: center;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.5);
    margin-bottom: 40px;
    animation: floatDown 1s cubic-bezier(0.25, 0.8, 0.25, 1) forwards;
}

@keyframes floatDown {
    from { opacity: 0; transform: translateY(-30px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Sweeping Gradient Text */
.header h1 {
    font-size: 3.5rem;
    font-weight: 900;
    margin: 0;
    background: linear-gradient(to right, #00f2fe, #4facfe, #00f2fe);
    background-size: 200% auto;
    color: #fff;
    background-clip: text;
    text-fill-color: transparent;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 3s linear infinite;
}
@keyframes shine { to { background-position: 200% center; } }

/* Neon Hover Cards */
.card {
    background: rgba(255, 255, 255, 0.03);
    backdrop-filter: blur(10px);
    padding: 25px;
    border-radius: 15px;
    margin: 15px 0;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    border-left: 4px solid #4facfe;
}
.card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 15px 30px rgba(79, 172, 254, 0.2);
    background: rgba(255, 255, 255, 0.07);
    border-left: 4px solid #00f2fe;
}
.card a {
    color: #00f2fe;
    text-decoration: none;
    font-weight: 700;
    letter-spacing: 1px;
    transition: 0.3s;
}
.card a:hover {
    color: #fff;
    text-shadow: 0 0 10px #00f2fe;
}

/* Futuristic KPI Boxes */
.kpi {
    background: linear-gradient(145deg, rgba(0,0,0,0.6), rgba(20,20,20,0.8));
    padding: 25px;
    border-radius: 20px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.05);
    transition: 0.4s ease;
    box-shadow: inset 0 0 20px rgba(0,0,0,0.5);
}
.kpi:hover {
    transform: translateY(-5px);
    border-color: #4facfe;
    box-shadow: 0 10px 20px rgba(0,0,0,0.4), inset 0 0 15px rgba(79, 172, 254, 0.2);
}
.kpi h2 { margin: 0; color: #00f2fe; font-size: 3rem; font-weight: 900; text-shadow: 0 0 15px rgba(0, 242, 254, 0.4); }
.kpi p { margin: 0; color: #94a3b8; font-size: 1.1rem; text-transform: uppercase; letter-spacing: 2px; margin-top: 5px;}

/* Status Pulse Animations */
.pulse-real {
    font-size: 32px; font-weight: 900; color: #4ade80; text-align: center; margin: 30px 0; letter-spacing: 3px;
    animation: pulse-g 2s infinite; text-transform: uppercase;
}
.pulse-partial {
    font-size: 32px; font-weight: 900; color: #facc15; text-align: center; margin: 30px 0; letter-spacing: 3px;
    animation: pulse-y 2s infinite; text-transform: uppercase;
}
.pulse-fake {
    font-size: 32px; font-weight: 900; color: #f87171; text-align: center; margin: 30px 0; letter-spacing: 3px;
    animation: pulse-r 1.5s infinite; text-transform: uppercase;
}
@keyframes pulse-g { 0% {transform: scale(1); text-shadow: 0 0 10px rgba(74,222,128,0.5);} 50% {transform: scale(1.05); text-shadow: 0 0 25px rgba(74,222,128,0.9);} 100% {transform: scale(1); text-shadow: 0 0 10px rgba(74,222,128,0.5);} }
@keyframes pulse-y { 0% {transform: scale(1); text-shadow: 0 0 10px rgba(250,204,21,0.5);} 50% {transform: scale(1.05); text-shadow: 0 0 25px rgba(250,204,21,0.9);} 100% {transform: scale(1); text-shadow: 0 0 10px rgba(250,204,21,0.5);} }
@keyframes pulse-r { 0% {transform: scale(1); text-shadow: 0 0 10px rgba(248,113,113,0.5);} 50% {transform: scale(1.08); text-shadow: 0 0 30px rgba(248,113,113,1);} 100% {transform: scale(1); text-shadow: 0 0 10px rgba(248,113,113,0.5);} }

/* Cyberpunk Buttons */
div.stButton > button {
    background: linear-gradient(135deg, #00c6ff, #0072ff);
    color: white;
    border: none;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    border-radius: 8px;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    padding: 10px 24px;
}
div.stButton > button:hover {
    transform: translateY(-3px) scale(1.02);
    box-shadow: 0 10px 20px rgba(0, 198, 255, 0.5);
    color: white;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# HEADER
# -------------------------------------------------
st.markdown("""
<div class="header">
    <h1>🌐 Project Sentinel: Fake News AI</h1>
    <p style="margin-top:10px; font-size:1.3rem; color:#cbd5e1; font-weight:300;">Multilingual Semantic Verification Engine</p>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------
# 🔥 TRANSLATOR
# -------------------------------------------------
def translate_text(text):
    try:
        return GoogleTranslator(source='auto', target='en').translate(text[:4000])
    except:
        return text

# -------------------------------------------------
# 🔥 SCRAPER
# -------------------------------------------------
def scrape_article_title(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        og = soup.find("meta", property="og:title")
        if og: return og.get("content")
        if soup.title: return soup.title.text.strip()
        return ""
    except:
        return ""

# -------------------------------------------------
# LOGGING
# -------------------------------------------------
LOG_FILE = "logs/log.csv"
os.makedirs("logs", exist_ok=True)

def log_result(query, decision, matches):
    ts = datetime.now()
    rows = [{
        "time": ts,
        "query": query,
        "publisher": m["publisher"],
        "score": m["score"],
        "decision": decision
    } for m in matches]
    if rows:
        pd.DataFrame(rows).to_csv(LOG_FILE, mode="a", header=not os.path.exists(LOG_FILE), index=False)

# -------------------------------------------------
# GAUGE (PLOTLY)
# -------------------------------------------------
def gauge(score):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Global Truth Index", 'font': {'size': 20, 'color': '#e2e8f0'}},
        number={'suffix': "%", 'font': {'size': 40, 'color': '#fff'}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 2, 'tickcolor': "white"},
            'bar': {'color': "rgba(255,255,255,0.8)", 'thickness': 0.1},
            'bgcolor': "rgba(0,0,0,0)",
            'borderwidth': 0,
            'steps': [
                {'range': [0, 72], 'color': "rgba(239, 68, 68, 0.8)"},     # RED (<72)
                {'range': [72, 80], 'color': "rgba(234, 179, 8, 0.8)"},    # YELLOW (72-80)
                {'range': [80, 100], 'color': "rgba(34, 197, 94, 0.8)"}],  # GREEN (80+)
        }
    ))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font={'color': "white"}, height=350, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, width='stretch')

# -------------------------------------------------
# 📊 NEW: EVIDENCE STRENGTH CHART
# -------------------------------------------------
def plot_source_match(df):
    if df.empty:
        return
        
    # Take the top 6 sources for visual clarity
    plot_df = df.head(6).copy()
    plot_df['Publisher'] = plot_df['publisher'].str.upper()
    
    # Create an impressive bar chart showing semantic scores
    fig = px.bar(
        plot_df, 
        x='score', 
        y='Publisher', 
        orientation='h', 
        title="AI Evidence Score by Publisher", 
        color='score', 
        color_continuous_scale='teal',
        text='score'
    )
    
    # Format the layout to match the dark cyberpunk theme
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(
        xaxis_title="Semantic Similarity (%)",
        yaxis_title="",
        yaxis={'categoryorder':'total ascending'},
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)", 
        font=dict(color="#e2e8f0"), 
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(range=[0, 110]) # Gives room for the text label
    )
    st.plotly_chart(fig, width='stretch')

# -------------------------------------------------
# RESULTS
# -------------------------------------------------
def show_results(matches, query, semantic_decision):
    if not matches:
        st.error("🚨 CRITICAL ALERT: No trusted sources found. This claim is completely unverified.")
        return

    df = pd.DataFrame(matches).sort_values(by="score", ascending=False)
    ml_label, ml_conf = predict_ml(query)
    # 70% weight to the hard evidence (Peak Match), 30% to grammatical ML
    final_conf = round((ml_conf * 0.3) + (df["score"].iloc[0] * 0.7), 2)

    # Animated KPI Row
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi'><h2>{len(df)}</h2><p>Trusted Sources</p></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi'><h2>{df['score'].iloc[0]}%</h2><p>Peak Match</p></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi'><h2>{round(df['score'].mean(),1)}%</h2><p>Avg Match</p></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi'><h2>{ml_conf}%</h2><p>ML Confidence</p></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 🔥 DYNAMIC 80 / 72 THRESHOLD LOGIC 🔥
    if final_conf >= 80:
        st.markdown(f"<div class='pulse-real'>✅ {semantic_decision}</div>", unsafe_allow_html=True)
        st.success("STATUS: FULLY VERIFIED. This news is heavily corroborated by multiple trusted global and regional networks.")
        st.balloons()
    elif final_conf >= 72:
        st.markdown(f"<div class='pulse-partial'>⚠️ {semantic_decision}</div>", unsafe_allow_html=True)
        st.warning("STATUS: PARTIALLY REAL. Some elements of this story match the database, but full context may be missing or skewed.")
    else:
        st.markdown(f"<div class='pulse-fake'>🚨 {semantic_decision}</div>", unsafe_allow_html=True)
        st.error("STATUS: HIGH RISK / FAKE. This content exhibits signs of severe manipulation or lacks any credible corroboration.")

    # Charts
    col1, col2 = st.columns([1, 1])
    with col1:
        gauge(final_conf)
    with col2:
        # 🔥 CALLED THE NEW CHART HERE INSTEAD OF KEYWORDS
        plot_source_match(df)

    # Animated Cards
    with st.expander("📡 VIEW LIVE NETWORK MATCHES", expanded=True):
        for m in df.head(8).to_dict("records"):
            st.markdown(f"""
            <div class="card">
                <h4 style="margin:0; color:#f8fafc; font-size:1.1rem;">{m['title']}</h4>
                <p style="margin:8px 0; color:#94a3b8; font-size:0.9rem;">
                    <strong style="color:#4facfe;">{m['publisher'].upper()}</strong> &nbsp;|&nbsp; 🎯 {m['score']}% AI Match
                </p>
                <a href="{m['link']}" target="_blank">🔗 Access Original Source</a>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------------------------
# TABS
# -------------------------------------------------
tabs = st.tabs(["📝 Text Engine", "🖼 Image Forensics", "🔗 URL Scanner", "📈 Global Analytics"])

# ---------------- TEXT ----------------
with tabs[0]:
    st.markdown("### 📝 Text Verification Engine")
    text = st.text_area("Input controversial headline, WhatsApp forward, or claim:", height=120, placeholder="E.g., Violence erupts in Mexico after drug lord El Mencho killed...")
    
    if st.button("🚀 INITIATE AI SCAN", width='stretch'):
        if text:
            with st.spinner("⚡ Initializing Neural Network... Scanning Global News Nodes..."):
                time.sleep(0.5)
                decision, count, matches = semantic_verify(text)
                log_result(text, decision, matches)
                show_results(matches, text, decision)
        else:
            st.warning("Please enter text into the engine.")

# ---------------- IMAGE ----------------
with tabs[1]:
    st.markdown("### 🖼 Image-Based Forensics (Screenshots / Memes)")
    img = st.file_uploader("Upload suspected image artifact:", type=["png", "jpg", "jpeg"])

    if img:
        image = Image.open(img)
        st.image(image, width='stretch')

        if st.button("🔍 EXTRACT & VERIFY", width='stretch'):
            with st.spinner("👁️ Running Optical Character Recognition (OCR)..."):
                txt, _ = extract_text_from_image(image)
            st.toast("✅ Artifact Text Decoded!")
            st.info(f"**Extracted Data:** {txt}")
            
            with st.spinner("⚡ Cross-referencing extracted data..."):
                decision, count, matches = semantic_verify(txt)
                log_result(txt, decision, matches)
                show_results(matches, txt, decision)

# ---------------- URL ----------------
with tabs[2]:
    st.markdown("### 🔗 Direct URL Scanner")
    url = st.text_input("Paste suspected article URL:")

    if st.button("🌐 SCRAPE DOMAIN & VERIFY", width='stretch'):
        if url:
            with st.spinner("🕷️ Bypassing domain... Extracting core metadata..."):
                domain = urllib.parse.urlparse(url).netloc
                title = extract_title_from_url(url)
                if not title:
                    title = scrape_article_title(url)
            
            st.toast("✅ Payload secured!")
            st.info(f"**Extracted Headline:** {title}")

            with st.spinner("⚡ Analyzing semantic structure..."):
                decision, count, matches = semantic_verify(title, source_domain=domain)
                log_result(title, decision, matches)
                show_results(matches, title, decision)
        else:
            st.warning("Please provide a valid URL string.")

# ---------------- DASHBOARD ----------------
with tabs[3]:
    st.markdown("### 📈 Live Analytics Command Center")
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE, parse_dates=["time"])
        d_col1, d_col2 = st.columns(2)
        
        with d_col1:
            time_df = df.groupby(df["time"].dt.date).size().reset_index(name='Count')
            fig_line = px.line(time_df, x='time', y='Count', title="System Traffic Over Time", markers=True)
            fig_line.update_traces(line_color="#00f2fe")
            fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
            st.plotly_chart(fig_line, width='stretch')

        with d_col2:
            dec_df = df["decision"].value_counts().reset_index()
            dec_df.columns = ['Decision', 'Count']
            fig_bar = px.bar(dec_df, x='Decision', y='Count', title="Verification Outcomes", color='Decision', color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_bar.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
            st.plotly_chart(fig_bar, width='stretch')
            
        st.markdown("---")
        
        pub_df = df["publisher"].value_counts().head(10).reset_index()
        pub_df.columns = ['Publisher', 'Count']
        fig_pub = px.bar(pub_df, x='Count', y='Publisher', orientation='h', title="Top Trusted Nodes Pinged", color='Count', color_continuous_scale='blues')
        fig_pub.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#e2e8f0"))
        st.plotly_chart(fig_pub, width='stretch')

        st.download_button("📥 DOWNLOAD ENCRYPTED LOG DATA (CSV)", df.to_csv(index=False), file_name="sentinel_logs.csv", width='stretch')
    else:
        st.warning("No telemetric data logged yet. Initiate scans to populate the command center.")
