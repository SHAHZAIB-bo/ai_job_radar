import streamlit as st
import time
import os
import sys
import subprocess
import pandas as pd
from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Helper function to strip ALL leading spaces from HTML lines
def clean_html(html_str):
    return "\n".join(line.strip() for line in html_str.splitlines())

# 1. Page Configuration
st.set_page_config(
    page_title="CYBER MATCH // AI Job Radar",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session Storage
if 'saved_jobs' not in st.session_state:
    st.session_state['saved_jobs'] = []
if 'applied_jobs' not in st.session_state:
    st.session_state['applied_jobs'] = []
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'radar'

# 2. Tactical HUD CSS Style
TACTICAL_HUD_CSS = clean_html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&display=swap');

.stApp {
    background: #02050c;
    color: #00f0ff;
    font-family: 'Rajdhani', sans-serif;
}

h1, h2, h3, .stTitle {
    font-family: 'Orbitron', sans-serif !important;
    color: #00f0ff !important;
    text-shadow: 0 0 10px #00f0ff, 0 0 20px rgba(0, 240, 255, 0.5);
}

.hud-display {
    display: grid;
    grid-template-columns: 360px 1fr;
    gap: 15px;
    background: #020813;
    border: 2px solid #00f0ff;
    border-radius: 6px;
    padding: 15px;
    box-shadow: 0 0 30px rgba(0, 240, 255, 0.25), inset 0 0 30px rgba(0, 240, 255, 0.08);
    margin-bottom: 20px;
}

.left-panel {
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.top-left-row {
    display: grid;
    grid-template-columns: 90px 1fr;
    gap: 10px;
}

.panel-box {
    border: 1px solid rgba(0, 240, 255, 0.4);
    background: rgba(4, 14, 28, 0.85);
    padding: 8px;
    border-radius: 4px;
}

.panel-header {
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    color: #8899ac;
    text-transform: uppercase;
    margin-bottom: 4px;
    letter-spacing: 1px;
}

.globe-container {
    width: 85px;
    height: 85px;
    border-radius: 50%;
    border: 1px solid #00f0ff;
    background: radial-gradient(circle, rgba(0,240,255,0.2) 0%, transparent 70%);
    box-shadow: 0 0 12px rgba(0, 240, 255, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
}

.arc-dial {
    position: relative;
    width: 100px;
    height: 100px;
    margin: 0 auto;
    border-radius: 50%;
    border: 2px dashed #00f0ff;
    animation: spin-reverse 8s linear infinite;
    display: flex;
    align-items: center;
    justify-content: center;
}

.arc-dial-text {
    position: absolute;
    font-family: 'Orbitron', sans-serif;
    font-size: 9px;
    color: #00f0ff;
    letter-spacing: 1px;
    animation: pulse-text 1.5s ease-in-out infinite alternate;
}

.target-table {
    width: 100%;
    border-collapse: collapse;
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
}

.target-table td {
    border: 1px solid rgba(0, 240, 255, 0.25);
    padding: 2px 6px;
    color: #00f0ff;
}

.bar-chart {
    display: flex;
    align-items: flex-end;
    gap: 3px;
    height: 38px;
}

.bar {
    flex: 1;
    background: #00f0ff;
    box-shadow: 0 0 6px #00f0ff;
    animation: bar-height 1.2s ease-in-out infinite alternate;
}

.wireframe-surface {
    width: 100%;
    height: 80px;
    background: radial-gradient(circle, rgba(0,240,255,0.2) 0%, transparent 80%),
                linear-gradient(0deg, transparent 24%, rgba(0, 240, 255, .3) 25%, rgba(0, 240, 255, .3) 26%, transparent 27%, transparent 74%, rgba(0, 240, 255, .3) 75%, rgba(0, 240, 255, .3) 76%, transparent 77%),
                linear-gradient(90deg, transparent 24%, rgba(0, 240, 255, .3) 25%, rgba(0, 240, 255, .3) 26%, transparent 27%, transparent 74%, rgba(0, 240, 255, .3) 75%, rgba(0, 240, 255, .3) 76%, transparent 77%);
    background-size: 16px 16px;
    transform: perspective(220px) rotateX(60deg);
    border: 1px solid #00f0ff;
}

.radar-display-right {
    position: relative;
    width: 100%;
    min-height: 440px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(0, 240, 255, 0.4);
    border-radius: 6px;
    background: radial-gradient(circle, rgba(0,240,255,0.1) 0%, rgba(2,8,19,0.95) 80%);
    overflow: hidden;
}

.radar-degree-ring {
    position: relative;
    width: 380px;
    height: 380px;
    border-radius: 50%;
    border: 2px solid #00f0ff;
    box-shadow: 0 0 25px rgba(0, 240, 255, 0.4), inset 0 0 25px rgba(0, 240, 255, 0.2);
}

.degree-label {
    position: absolute;
    font-family: 'Orbitron', sans-serif;
    font-size: 9px;
    color: #00f0ff;
}

.radar-inner-ring-1 {
    position: absolute; top: 15%; left: 15%; width: 70%; height: 70%;
    border-radius: 50%; border: 1px solid rgba(0, 240, 255, 0.4);
}
.radar-inner-ring-2 {
    position: absolute; top: 32%; left: 32%; width: 36%; height: 36%;
    border-radius: 50%; border: 1px dashed rgba(0, 240, 255, 0.5);
}

.radar-cross-h { position: absolute; top: 50%; left: 0; width: 100%; height: 1px; background: rgba(0, 240, 255, 0.5); }
.radar-cross-v { position: absolute; top: 0; left: 50%; width: 1px; height: 100%; background: rgba(0, 240, 255, 0.5); }

.radar-sweep-fan {
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    border-radius: 50%;
    background: conic-gradient(from 0deg, rgba(0, 240, 255, 0.55) 0deg, rgba(0, 240, 255, 0.05) 60deg, transparent 61deg);
    animation: radar-rotate 2.5s linear infinite;
}

.blip {
    position: absolute;
    width: 8px; height: 8px;
    background: #00f0ff;
    border-radius: 50%;
    box-shadow: 0 0 10px #00f0ff, 0 0 20px #00f0ff;
    animation: blip-pulse 1s infinite alternate;
}

.job-card {
    background: rgba(10, 20, 38, 0.85);
    border: 1px solid #00f0ff;
    border-radius: 8px;
    padding: 18px;
    margin-bottom: 16px;
    box-shadow: 0 0 15px rgba(0, 240, 255, 0.15);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.apply-btn {
    background: linear-gradient(90deg, #ff0055 0%, #ff5500 100%);
    color: white !important;
    padding: 8px 16px;
    border-radius: 6px;
    text-decoration: none;
    font-family: 'Orbitron', sans-serif;
    font-weight: bold;
}

@keyframes radar-rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes spin-reverse { from { transform: rotate(360deg); } to { transform: rotate(0deg); } }
@keyframes pulse-text { from { opacity: 0.4; } to { opacity: 1; } }
@keyframes blip-pulse { from { transform: scale(0.8); opacity: 0.5; } to { transform: scale(1.4); opacity: 1; } }
@keyframes bar-height { 0% { height: 15%; } 50% { height: 90%; } 100% { height: 35%; } }
</style>
""")
st.markdown(TACTICAL_HUD_CSS, unsafe_allow_html=True)

# 3. Helper Functions
def extract_text_from_file(uploaded_file):
    if uploaded_file.name.endswith(".pdf"):
        reader = PdfReader(uploaded_file)
        text = " ".join([page.extract_text() or "" for page in reader.pages])
    elif uploaded_file.name.endswith(".docx"):
        doc = Document(uploaded_file)
        text = " ".join([para.text for para in doc.paragraphs])
    else:
        text = ""
    return text.strip()

def calculate_matches(cv_text, job_descriptions):
    if not cv_text or not job_descriptions:
        return [0.0] * len(job_descriptions)
    corpus = [cv_text] + job_descriptions
    vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    matrix = vectorizer.fit_transform(corpus)
    scores = cosine_similarity(matrix[0:1], matrix[1:]).flatten()
    return [round(s * 100, 1) for s in scores]

def play_radar_completion_beep():
    beep_js = """
    <script>
    (function() {
        try {
            var AudioContext = window.AudioContext || window.webkitAudioContext;
            var ctx = new AudioContext();
            var osc1 = ctx.createOscillator();
            var gain1 = ctx.createGain();
            osc1.type = 'sine';
            osc1.frequency.setValueAtTime(880, ctx.currentTime);
            gain1.gain.setValueAtTime(0.3, ctx.currentTime);
            gain1.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.18);
            osc1.connect(gain1);
            gain1.connect(ctx.destination);
            osc1.start(ctx.currentTime);
            osc1.stop(ctx.currentTime + 0.18);

            var osc2 = ctx.createOscillator();
            var gain2 = ctx.createGain();
            osc2.type = 'triangle';
            osc2.frequency.setValueAtTime(1760, ctx.currentTime + 0.20);
            gain2.gain.setValueAtTime(0.35, ctx.currentTime + 0.20);
            gain2.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.45);
            osc2.connect(gain2);
            gain2.connect(ctx.destination);
            osc2.start(ctx.currentTime + 0.20);
            osc2.stop(ctx.currentTime + 0.45);
        } catch(e) {}
    })();
    </script>
    """
    st.components.v1.html(beep_js, height=0, width=0)

# 4. Control Sidebar Panel
st.sidebar.title("🎛️ CONTROL CONSOLE")
st.sidebar.markdown("---")

uploaded_cv = st.sidebar.file_uploader("📂 UPLOAD CV (PDF/DOCX)", type=["pdf", "docx"])
search_term = st.sidebar.text_input("🎯 TARGET JOB TITLE", value="Software Engineer")
target_company = st.sidebar.text_input("🏢 TARGET COMPANY (Optional)", value="", placeholder="e.g. Interloop, MTM, Sapphire")
location = st.sidebar.text_input("📍 LOCATION", value="Pakistan")

# RESTRICTED TO SINGLE SELECTION TO PREVENT CRASHES AND BOT BLOCKS
selected_platform = st.sidebar.selectbox(
    "🌐 TARGET PLATFORM (Single Target Mode)",
    options=["indeed", "linkedin", "google", "glassdoor"],
    index=0
)

results_wanted = st.sidebar.slider("📊 NUMBER OF JOBS TO RADAR", min_value=5, max_value=20, value=5)
initiate_btn = st.sidebar.button("🚀 INITIATE RADAR SEARCH")

# 5. Dashboard Top Navigation Tabs
st.title("⚡ AI JOB RADAR // SCANNER HUD")

col_nav1, col_nav2, col_nav3 = st.columns([1, 1, 1])
with col_nav1:
    if st.button("📡 LIVE RADAR SCANNER", use_container_width=True):
        st.session_state['current_view'] = 'radar'
with col_nav2:
    if st.button(f"🔖 SAVED JOBS ({len(st.session_state['saved_jobs'])})", use_container_width=True):
        st.session_state['current_view'] = 'saved'
with col_nav3:
    if st.button(f"✅ APPLIED JOBS ({len(st.session_state['applied_jobs'])})", use_container_width=True):
        st.session_state['current_view'] = 'applied'

st.markdown("---")

# 6. PERMANENT TACTICAL HUD VIEW AT TOP
PERMANENT_HUD_HTML = clean_html("""
<div class="hud-display">
    <div class="left-panel">
        <div class="top-left-row">
            <div class="globe-container">
                <svg width="80" height="80" style="stroke: #00f0ff; fill: none; stroke-width: 1;">
                    <circle cx="40" cy="40" r="35"/>
                    <ellipse cx="40" cy="40" rx="35" ry="12"/>
                    <ellipse cx="40" cy="40" rx="12" ry="35"/>
                    <line x1="5" y1="40" x2="75" y2="40"/>
                    <line x1="40" y1="5" x2="40" y2="75"/>
                </svg>
            </div>
            <div class="panel-box">
                <div class="panel-header">Spectrum Analyzer</div>
                <svg width="100%" height="30" style="stroke: #00f0ff; fill: none; stroke-width: 1.5;">
                    <path d="M0,15 Q15,5 30,15 T60,15 T90,5 T120,25 T150,15 T180,15 T210,5 T240,20 T270,15 T300,15"/>
                </svg>
            </div>
        </div>

        <div class="panel-box" style="text-align: center;">
            <div class="arc-dial">
                <div class="arc-dial-text">PROCESSING...</div>
            </div>
        </div>

        <div class="panel-box">
            <div class="panel-header">Target Speed Metrics</div>
            <table class="target-table">
                <tr><td>TRGT 001</td><td>268</td><td>TRGT 004</td><td>645</td></tr>
                <tr><td>TRGT 002</td><td>923</td><td>TRGT 005</td><td>917</td></tr>
                <tr><td>TRGT 003</td><td>184</td><td>TRGT 006</td><td>836</td></tr>
            </table>
        </div>

        <div class="panel-box">
            <div class="panel-header">Activity Diagnostics</div>
            <div class="bar-chart">
                <div class="bar" style="animation-delay: 0.1s;"></div>
                <div class="bar" style="animation-delay: 0.3s;"></div>
                <div class="bar" style="animation-delay: 0.2s;"></div>
                <div class="bar" style="animation-delay: 0.5s;"></div>
                <div class="bar" style="animation-delay: 0.4s;"></div>
                <div class="bar" style="animation-delay: 0.7s;"></div>
                <div class="bar" style="animation-delay: 0.6s;"></div>
            </div>
        </div>

        <div class="panel-box">
            <div class="panel-header">Modeling Surface ...</div>
            <div class="wireframe-surface"></div>
        </div>
    </div>

    <div class="radar-display-right">
        <div class="radar-degree-ring">
            <div class="degree-label" style="top: -18px; left: 46%;">0°</div>
            <div class="degree-label" style="top: 8%; right: 12%;">40°</div>
            <div class="degree-label" style="top: 47%; right: -22px;">90°</div>
            <div class="degree-label" style="bottom: 8%; right: 12%;">140°</div>
            <div class="degree-label" style="bottom: -18px; left: 45%;">180°</div>
            <div class="degree-label" style="bottom: 8%; left: 10%;">230°</div>
            <div class="degree-label" style="top: 47%; left: -28px;">270°</div>
            <div class="degree-label" style="top: 8%; left: 10%;">320°</div>

            <div class="radar-cross-h"></div>
            <div class="radar-cross-v"></div>
            <div class="radar-inner-ring-1"></div>
            <div class="radar-inner-ring-2"></div>

            <svg width="100%" height="100%" style="position: absolute; top:0; left:0; opacity: 0.35; fill: none; stroke: #00f0ff; stroke-width: 1;">
                <path d="M 110 160 Q 150 140 190 170 T 260 160 T 310 200"/>
                <path d="M 80 220 Q 140 250 180 230 T 240 280"/>
            </svg>

            <div class="radar-sweep-fan"></div>

            <div class="blip" style="top: 30%; left: 45%;"></div>
            <div class="blip" style="top: 65%; left: 70%;"></div>
            <div class="blip" style="top: 50%; left: 25%;"></div>
            <div class="blip" style="top: 20%; left: 75%;"></div>
        </div>
    </div>
</div>
""")
st.markdown(PERMANENT_HUD_HTML, unsafe_allow_html=True)

# 7. Page Content Rendering
if st.session_state['current_view'] == 'saved':
    st.subheader(f"🔖 SAVED JOBS ({len(st.session_state['saved_jobs'])})")
    if not st.session_state['saved_jobs']:
        st.info("No saved jobs yet. Click '🔖 Save Job' on any target match.")
    else:
        for idx, job in enumerate(st.session_state['saved_jobs']):
            st.markdown(f"**{job['title']}** | 🏢 {job['company']} | 📍 {job['location']} | [Apply Link]({job.get('job_url','#')})")

elif st.session_state['current_view'] == 'applied':
    st.subheader(f"✅ APPLIED JOBS ({len(st.session_state['applied_jobs'])})")
    if not st.session_state['applied_jobs']:
        st.info("No applied jobs tracked yet. Click '✅ Mark Applied' on any job card.")
    else:
        for idx, job in enumerate(st.session_state['applied_jobs']):
            st.markdown(f"**{job['title']}** | 🏢 {job['company']} | 📍 {job['location']} | [Apply Link]({job.get('job_url','#')})")

else:
    if not initiate_btn:
        st.info("👈 Upload your CV (or specify a Target Company) and click **INITIATE RADAR SEARCH** to scan.")
    else:
        company_query = target_company.strip()
        
        # Check if user has neither uploaded a CV nor specified a company
        if not uploaded_cv and not company_query:
            st.error("⚠️ PLEASE EITHER UPLOAD A CV OR ENTER A TARGET COMPANY NAME BEFORE SCANNING.")
        else:
            with st.spinner("📡 SCANNING LIVE JOB NETWORKS..."):
                cv_text = extract_text_from_file(uploaded_cv) if uploaded_cv else ""

                json_file = "jobs_temp.json"
                if os.path.exists(json_file):
                    os.remove(json_file)

                # Combine title and company if target company is supplied
                final_search_query = f"{search_term} {company_query}".strip() if company_query else search_term

                scraper_path = os.path.join(os.path.dirname(__file__), "scraper.py")
                cmd = [sys.executable, scraper_path, final_search_query, location, str(results_wanted), selected_platform]
                
                subprocess.run(cmd, capture_output=True, text=True)

            play_radar_completion_beep()

            jobs_df = None
            if os.path.exists(json_file):
                try:
                    jobs_df = pd.read_json(json_file)
                except Exception:
                    jobs_df = None

            if jobs_df is None or jobs_df.empty:
                st.warning("NO TARGETS FOUND OR CAPTCHA DETECTED. TRY AGAIN OR SWITCH TARGET PLATFORM.")
            else:
                jobs_df['description'] = jobs_df['description'].fillna(jobs_df['title'])

                # IF TARGET COMPANY IS ENTERED: Soft filter to keep matching firm results
                if company_query:
                    company_matches = jobs_df[
                        jobs_df['company'].str.contains(company_query, case=False, na=False) |
                        jobs_df['title'].str.contains(company_query, case=False, na=False)
                    ]
                    if not company_matches.empty:
                        jobs_df = company_matches

                # CALCULATE CV MATCH SCORES (IF CV IS AVAILABLE)
                if cv_text:
                    scores = calculate_matches(cv_text, jobs_df['description'].tolist())
                    jobs_df['match_score'] = scores
                else:
                    # Default score display if search was performed without a CV
                    jobs_df['match_score'] = 100.0

                # SORT RESULTS (Showing all found postings for target firm directly)
                ranked_df = jobs_df.sort_values(by="match_score", ascending=False)
                
                if company_query:
                    st.markdown(f"<h2 style='color:#00f0ff;'>🏢 DIRECT COMPANY OFFERS FOUND FOR '{company_query.upper()}': {len(ranked_df)}</h2>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<h2 style='color:#00f0ff;'>🎯 TARGET MATCHES FOUND: {len(ranked_df)}</h2>", unsafe_allow_html=True)

                for idx, row in ranked_df.iterrows():
                    match = row['match_score']
                    dash_array = 283
                    dash_offset = dash_array - (dash_array * match / 100)
                    color = "#00f0ff" if match > 60 else ("#ffaa00" if match > 40 else "#ff0055")

                    col_card, col_act = st.columns([4, 1])
                    with col_card:
                        card_html = clean_html(f"""
                        <div class="job-card">
                            <div>
                                <span style="background: {color}; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; font-family: Orbitron;">
                                    {str(row.get('site', selected_platform)).upper()}
                                </span>
                                <h2 style="margin: 8px 0 4px 0; color: #ffffff; font-size: 20px;">{row['title']}</h2>
                                <p style="margin: 0; color: #8899ac; font-size: 15px;">🏢 <b>{row['company']}</b> | 📍 {row['location']}</p>
                            </div>
                            <div style="display: flex; align-items: center; gap: 20px;">
                                <div style="position: relative; width: 75px; height: 75px; display: flex; align-items: center; justify-content: center;">
                                    <svg width="75" height="75">
                                        <circle cx="37.5" cy="37.5" r="32" stroke="#101a2d" stroke-width="6" fill="transparent"/>
                                        <circle cx="37.5" cy="37.5" r="32" stroke="{color}" stroke-width="6" fill="transparent"
                                                stroke-dasharray="{dash_array}" stroke-dashoffset="{dash_offset}"
                                                stroke-linecap="round" transform="rotate(-90 37.5 37.5)"/>
                                    </svg>
                                    <div style="position: absolute; font-family: 'Orbitron', sans-serif; font-size: 14px; font-weight: bold; color: {color};">
                                        {int(match) if match == 100.0 and not cv_text else f'{match}%'}
                                    </div>
                                </div>
                                <a class="apply-btn" href="{row.get('job_url', '#')}" target="_blank">APPLY NOW ↗</a>
                            </div>
                        </div>
                        """)
                        st.markdown(card_html, unsafe_allow_html=True)

                    with col_act:
                        job_dict = row.to_dict()
                        if st.button(f"🔖 Save Job", key=f"save_{idx}"):
                            if job_dict not in st.session_state['saved_jobs']:
                                st.session_state['saved_jobs'].append(job_dict)
                                st.success("Saved!")
                        if st.button(f"✅ Mark Applied", key=f"apply_{idx}"):
                            if job_dict not in st.session_state['applied_jobs']:
                                st.session_state['applied_jobs'].append(job_dict)
                                st.success("Applied!")