import streamlit as st
from google import genai
from google.genai import types
import sqlite3
from PIL import Image
from datetime import datetime
import re

# ==========================================
# 1. THE CREATIVE BENTO-GRID DESIGN SYSTEM
# ==========================================
st.set_page_config(page_title="SilverCare AI", page_icon="✨", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght=300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        background-color: #FAFAFE !important;
        color: #0F172A; 
    }
    .stApp { background-color: #FAFAFE !important; }
    
    section[data-testid="stSidebar"] { display: none; }
    
    .premium-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 0px;
        margin-bottom: 20px;
        border-bottom: 1px solid rgba(0, 0, 0, 0.04);
    }
    .brand-logo { font-size: 1.4rem; font-weight: 700; color: #1E1B4B; letter-spacing: -0.5px; }
    .brand-status { font-size: 0.85rem; font-weight: 600; color: #6366F1; background: rgba(99, 102, 241, 0.08); padding: 6px 16px; border-radius: 100px; }

    /* Native Streamlit Container Override for Perfect Bento Style */
    div[data-testid="stContainer"] {
        background: #FFFFFF !important;
        border: 1px solid rgba(0, 0, 0, 0.05) !important;
        border-radius: 24px !important;
        padding: 35px !important;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.01) !important;
        margin-bottom: 25px !important;
    }
    
    .bento-card {
        background: #FFFFFF;
        border: 1px solid rgba(0, 0, 0, 0.05);
        border-radius: 24px;
        padding: 35px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.01);
        margin-bottom: 25px;
    }
    .bento-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: #6366F1;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 15px;
    }
    
    .creative-hero {
        font-size: 3.6rem !important;
        font-weight: 800 !important;
        color: #0F172A;
        letter-spacing: -1.5px;
        line-height: 1.1;
        margin-bottom: 15px;
    }
    .creative-sub {
        font-size: 1.25rem;
        color: #64748B;
        font-weight: 400;
        margin-bottom: 50px;
    }

    .stTextArea textarea, .stTextInput input {
        border-radius: 14px !important;
        border: 1px solid #E2E8F0 !important;
        background-color: #FAFAFE !important;
        padding: 12px 15px !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #6366F1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }

    .stButton>button {
        background: #0F172A !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 14px !important;
        padding: 14px 30px !important;
        border: none !important;
        transition: all 0.2s ease;
        width: 100%;
    }
    .stButton>button:hover { 
        background: #1E293B !important;
        transform: translateY(-1px);
    }
    
    mark {
        background-color: rgba(99, 102, 241, 0.08) !important;
        color: #4F46E5 !important;
        padding: 4px 8px !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }

    /* Tab bar clean up */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 30px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 100px;
        padding: 8px 20px;
        font-weight: 600;
        color: #64748B;
        border: 1px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #0F172A;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize Database with safe contextual management
def init_db():
    with sqlite3.connect('silvercare_records.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                patient_name TEXT, 
                report_date TEXT, 
                content TEXT
            )
        ''')
        conn.commit()

def get_history():
    with sqlite3.connect('silvercare_records.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, patient_name, report_date, content FROM reports ORDER BY id DESC")
        return cursor.fetchall()

init_db()

if 'analysis_result' not in st.session_state: 
    st.session_state.analysis_result = None

# ==========================================
# EXTRA-SMART MEDICAL INTELLIGENCE PROMPT
# ==========================================
SILVERCARE_SYSTEM_INSTRUCTION = """
You are SilverCare AI, an elite clinical intelligence analyst specializing in translating lab work into simple, clear, actionable caregiver insights.

Your primary directive is to look at the COMPLETE profile rather than reporting individual numbers in isolation. Even if a core metric (like Hemoglobin) is technically inside a 'safe standard reference range', you must investigate secondary or supporting indices (like MCV, MCH, MCHC, or RDW) to see if they collectively signal early trends, hidden anomalies, or structural changes (such as cell size shrinkage/Microcytosis or color concentration alterations).

FORMATTING REQUIREMENTS:
- Use simple, reassuring, conversational language that a family caregiver can easily understand.
- Absolutely split your output into distinct data blocks using explicit [EXPLANATION], [SUGGESTIONS], and [SUMMARY] tags.
- Break content up into clean, scannable, well-spaced bullet points. Do not write long blocks or clump multiple metrics together on one line.
- CRITICAL HIGHLIGHTING RULE: Wrap key findings, specific abnormal biomarkers, or critical directional trends inside this exact tag: <mark>TEXT</mark>.

Structure your segments exactly as follows:

[EXPLANATION]
### 🩸 Vital Biomarkers Breakdown
(Provide clean, individual bullet points for each notable test group. Explain clearly what the metric means for the patient and how it connects to hidden cross-metric patterns.)

[SUGGESTIONS]
- Provide 3-4 simple, bulleted everyday health adjustments or dietary support plans.

[SUMMARY]
(Provide a brief, professional summary phrase that a family can easily pass on directly to their primary care physician.)
"""

# Hardcoded API key configuration for seamless local testing
API_KEY = "AIzaSyDm73rTZrKQ5zFknQDDnk3Z3_a_obJsh6Y"
client = genai.Client(api_key=API_KEY)

# --- CLEAN TOP BAR BAR ---
top_left, top_right = st.columns([4, 1], vertical_alignment="center")

with top_left:
    st.markdown("<div class='brand-logo' style='margin-bottom: 10px;'>SilverCare — Engine 2.5</div>", unsafe_allow_html=True)

with top_right:
    st.markdown("<div style='display: flex; justify-content: flex-end; margin-bottom: 10px;'><span class='brand-status'>● System Active</span></div>", unsafe_allow_html=True)

# Injecting clean tabs for primary navigation
tab_active, tab_history = st.tabs(["✨ Analysis Suite", "🗄️ Patient Archives"])
st.markdown("<div style='border-bottom: 1px solid rgba(0, 0, 0, 0.04); margin-bottom: 30px; margin-top: -15px;'></div>", unsafe_allow_html=True)

# Helper function to parse sections safely using Regex
def parse_section(text, section_name, next_section_name=None):
    try:
        pattern = rf"\[{section_name}\](.*?)(?=\[{next_section_name}\]|$)" if next_section_name else rf"\[{section_name}\](.*)"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""
    except Exception:
        return ""

# ==========================================
# TAB 1: RUNTIME ANALYSIS SUITE
# ==========================================
with tab_active:
    if st.session_state.analysis_result is None:
        # --- STATE A: THE CONTROL GRID ---
        col_hero_left, col_hero_right = st.columns([1.1, 0.9])
        
        with col_hero_left:
            st.markdown("<div class='creative-hero'>Clear insights,<br>built for families.</div>", unsafe_allow_html=True)
            st.markdown("<div class='creative-sub'>Drop your complex laboratory documents below. Our intelligence layer instantly translates medical terminology into simple, actionable lifelines.</div>", unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader("Drop document scan here", type=["png", "jpg", "jpeg", "pdf"], label_visibility="collapsed")
            
        with col_hero_right:
            with st.container():
                st.markdown("<div class='bento-title'>Patient Context</div>", unsafe_allow_html=True)
                p_name = st.text_input("Patient Identity", value="Grandfather", placeholder="e.g., Grandfather")
                p_age = st.text_input("Age Group", value="72", placeholder="e.g., 72")
                p_notes = st.text_area("Observations & Background", placeholder="e.g., Experiences mild fatigue in the early mornings...", height=100)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Begin Deep Analysis"):
                    if uploaded_file:
                        with st.spinner("Decoding laboratory markers..."):
                            img_to_send = Image.open(uploaded_file)
                            analysis_prompt = f"Analyze for {p_name} (Age: {p_age}). Focus context: {p_notes}. Split by [EXPLANATION], [SUGGESTIONS], and [SUMMARY]."
                            
                            try:
                                response = client.models.generate_content(
                                    model='gemini-2.5-flash',
                                    contents=[img_to_send, analysis_prompt],
                                    config=types.GenerateContentConfig(system_instruction=SILVERCARE_SYSTEM_INSTRUCTION)
                                )
                                st.session_state.analysis_result = response.text
                                
                            except Exception as first_error:
                                if "503" in str(first_error) or "UNAVAILABLE" in str(first_error).upper():
                                    st.toast("⚠️ Primary engine busy. Activating secondary AI lane...", icon="⚡")
                                    try:
                                        response = client.models.generate_content(
                                            model='gemini-2.0-flash',
                                            contents=[img_to_send, analysis_prompt],
                                            config=types.GenerateContentConfig(system_instruction=SILVERCARE_SYSTEM_INSTRUCTION)
                                        )
                                        st.session_state.analysis_result = response.text
                                    except Exception as second_error:
                                        st.error(f"Both AI processing lanes are timing out: {second_error}")
                                        st.stop()
                                else:
                                    st.error(f"Analysis interrupted: {first_error}")
                                    st.stop()

                            if st.session_state.analysis_result:
                                current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                                with sqlite3.connect('silvercare_records.db') as conn:
                                    cursor = conn.cursor()
                                    cursor.execute("INSERT INTO reports (patient_name, report_date, content) VALUES (?, ?, ?)", 
                                                   (p_name, current_timestamp, st.session_state.analysis_result))
                                    conn.commit()
                                st.rerun()
                    else:
                        st.warning("Please upload a medical document scan to proceed.")

    else:
        # --- STATE B: THE INSIGHTS CANVAS ---
        raw_data = st.session_state.analysis_result
        
        explanation_part = parse_section(raw_data, "EXPLANATION", "SUGGESTIONS")
        suggestions_part = parse_section(raw_data, "SUGGESTIONS", "SUMMARY")
        summary_part = parse_section(raw_data, "SUMMARY")

        if not explanation_part:
            explanation_part = raw_data

        col_back, col_empty = st.columns([1, 7])
        with col_back:
            if st.button("← New Analysis"):
                st.session_state.analysis_result = None
                st.rerun()
                
        st.markdown("<br>", unsafe_allow_html=True)
        col_out_left, col_out_right = st.columns([1.2, 0.8])
        
        with col_out_left:
            with st.container():
                st.markdown("<div class='bento-title'>📄 Translated Health Record</div>", unsafe_allow_html=True)
                st.markdown(explanation_part, unsafe_allow_html=True)
            
        with col_out_right:
            if summary_part:
                with st.container():
                    st.markdown("<div class='bento-title'>🩺 Doctor Consultation Brief</div>", unsafe_allow_html=True)
                    st.markdown(summary_part, unsafe_allow_html=True)

            if suggestions_part:
                with st.container():
                    st.markdown("<div class='bento-title'>🥣 Actionable Caregiver Steps</div>", unsafe_allow_html=True)
                    st.markdown(suggestions_part, unsafe_allow_html=True)

# ==========================================
# TAB 2: INTERACTIVE HISTORICAL ARCHIVES
# ==========================================
with tab_history:
    records = get_history()
    
    if not records:
        st.info("No historical records found. Run an evaluation inside the Analysis Suite first.")
    else:
        st.markdown("<p style='color: #64748B; margin-bottom: 20px;'>Select a previous session below to re-render the patient profile and comparative analytics metrics.</p>", unsafe_allow_html=True)
        
        options = [f"📂 {rec[1]} — Checked on {rec[2]} (ID: #{rec[0]})" for rec in records]
        selected_option = st.selectbox("Historical Archive Registry", options, label_visibility="collapsed")
        
        chosen_idx = options.index(selected_option)
        chosen_record = records[chosen_idx]
        hist_raw_data = chosen_record[3]
        
        hist_explanation = parse_section(hist_raw_data, "EXPLANATION", "SUGGESTIONS")
        hist_suggestions = parse_section(hist_raw_data, "SUGGESTIONS", "SUMMARY")
        hist_summary = parse_section(hist_raw_data, "SUMMARY")
        
        if not hist_explanation:
            hist_explanation = hist_raw_data
            
        st.markdown("<hr style='opacity: 0.1; margin: 20px 0;'>", unsafe_allow_html=True)
        
        col_hist_left, col_hist_right = st.columns([1.2, 0.8])
        
        with col_hist_left:
            with st.container():
                st.markdown(f"<div class='bento-title'>📄 Archived Record: {chosen_record[1]}</div>", unsafe_allow_html=True)
                st.markdown(hist_explanation, unsafe_allow_html=True)
            
        with col_hist_right:
            if hist_summary:
                with st.container():
                    st.markdown("<div class='bento-title'>🩺 Doctor Consultation Brief</div>", unsafe_allow_html=True)
                    st.markdown(hist_summary, unsafe_allow_html=True)

            if hist_suggestions:
                with st.container():
                    st.markdown("<div class='bento-title'>🥣 Actionable Caregiver Steps</div>", unsafe_allow_html=True)
                    st.markdown(hist_suggestions, unsafe_allow_html=True)