import streamlit as st
from auth import AuthManager
from ocr_processor import OCRProcessor
from data_manager import DataManager
from visualizer import Visualizer
from config import NORMAL_RANGES, REPORT_TYPES, TEST_PARAMETERS
import pandas as pd
import os
from datetime import datetime

# ----------------------------------
# PAGE CONFIG
# ----------------------------------
st.set_page_config(
    page_title="MedAssist – Health Suite",
    page_icon="🏥",
    layout="wide"
)

# ----------------------------------
# SESSION STATE INIT
# ----------------------------------
defaults = {
    "logged_in": False,
    "username": None,
    "selected_patient": None,
    "selected_family_member": None,
    "family_members": {},
    "current_report": None,
    "manual_report": None,
    "editing_report": False,
    "selected_test_type": None,
    "extracted_text": None,
    "report_saved": False,
    "show_all_reports_in_upload": False,
    "active_page": "home",          # home | report_analysis | med_chatbot | dashboard | all_reports | family_profiles | settings
    "chat_history": [],
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

auth_manager = AuthManager()

# ----------------------------------
# LOGOUT
# ----------------------------------
def logout():
    for k in list(defaults.keys()):
        st.session_state[k] = defaults[k]
    st.rerun()

# ----------------------------------
# LOGIN PAGE
# ----------------------------------
def login_page():
    st.markdown("""
    <style>
    .login-header { text-align:center; padding: 2rem 0 1rem; }
    .login-header h1 { font-size: 2.8rem; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-header"><h1>🏥 MedAssist System</h1><p>Your complete medical companion — report analysis & AI chatbot in one place</p></div>', unsafe_allow_html=True)
    st.markdown("---")

    col_left, col_center, col_right = st.columns([1, 2, 1])
    with col_center:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

        with tab1:
            st.subheader("Login to Your Account")
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", type="primary", key="login_button", use_container_width=True):
                if username and password:
                    success, msg = auth_manager.login(username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.family_members = auth_manager.get_family_members(username)
                        st.session_state.active_page = "home"
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Please enter both username & password")

        with tab2:
            st.subheader("Create Account")
            username = st.text_input("New Username", key="signup_username")
            email = st.text_input("Email", key="signup_email")
            pwd = st.text_input("Password", type="password", key="signup_password")
            confirm = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
            if st.button("Sign Up", type="primary", key="signup_button", use_container_width=True):
                if not username or not email or not pwd:
                    st.warning("Fill all fields")
                elif pwd != confirm:
                    st.error("Passwords do not match")
                elif len(pwd) < 6:
                    st.error("Password must be 6+ chars")
                else:
                    success, msg = auth_manager.signup(username, pwd, email)
                    if success:
                        st.success(msg)
                        st.info("Login with your credentials")
                    else:
                        st.error(msg)

# ----------------------------------
# SIDEBAR
# ----------------------------------
def render_sidebar():
    with st.sidebar:
        current_patient = st.session_state.selected_family_member or st.session_state.username
        st.title("🏥 MedAssist")
        st.caption(f"👤 {st.session_state.username}")
        st.markdown("---")

        st.subheader("📌 Navigation")

        nav_items = [
            ("🏠 Home", "home"),
            ("📊 Report Analysis", "report_analysis"),
            ("🤖 Med Chatbot", "med_chatbot"),
            ("📈 Dashboard", "dashboard"),
            ("📋 All Reports", "all_reports"),
            ("👨‍👩‍👧‍👦 Family Profiles", "family_profiles"),
            ("⚙️ Settings", "settings"),
        ]

        for label, key in nav_items:
            is_active = st.session_state.active_page == key
            btn_type = "primary" if is_active else "secondary"
            if st.button(label, key=f"nav_{key}", type=btn_type, use_container_width=True):
                st.session_state.active_page = key
                # reset report editing state when navigating away
                if key not in ("report_analysis",):
                    st.session_state.editing_report = False
                    st.session_state.report_saved = False
                st.rerun()

        st.markdown("---")
        st.subheader("👤 Current Profile")
        st.info(f"**{current_patient}**")

        st.subheader("🔀 Switch Profile")
        profiles = [f"👤 {st.session_state.username} (You)"]
        if st.session_state.family_members:
            for _, m in st.session_state.family_members.items():
                emoji = "👨" if m.get("gender", "").lower() == "male" else "👩" if m.get("gender", "").lower() == "female" else "👤"
                profiles.append(f"{emoji} {m['name']} ({m['relationship']})")
        profiles.append("➕ Add New Family Member")

        selected = st.selectbox("Select Profile", profiles, key="profile_selector")
        if selected.startswith("➕"):
            st.session_state.selected_patient = "new_member"
            st.session_state.selected_family_member = None
        elif selected.startswith("👤 " + st.session_state.username):
            st.session_state.selected_patient = st.session_state.username
            st.session_state.selected_family_member = None
        else:
            name = selected.split(" ", 1)[1].split(" (")[0]
            st.session_state.selected_patient = name
            st.session_state.selected_family_member = name

        st.markdown("---")
        if st.button("🚪 Logout", type="primary", key="logout_button", use_container_width=True):
            logout()

# ----------------------------------
# HOME PAGE
# ----------------------------------
def home_page():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    .home-header {
        padding: 2rem 0 3rem;
        text-align: center;
    }
    .home-header h1 {
        font-size: 3.5rem;
        font-weight: 800;
        letter-spacing: -2px;
        background: linear-gradient(180deg, #FFFFFF 0%, #717171 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .home-header p {
        font-size: 1.25rem;
        color: #888;
        max-width: 600px;
        margin: 0 auto;
    }
    
    .bento-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1.5rem;
        margin-bottom: 3rem;
    }
    
    .bento-item {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 32px;
        padding: 3rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
        transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        text-align: left;
        position: relative;
        overflow: hidden;
    }
    
    .bento-item::before {
        content: "";
        position: absolute;
        width: 150px;
        height: 150px;
        border-radius: 50%;
        filter: blur(60px);
        opacity: 0.15;
        z-index: 0;
        transition: all 0.5s ease;
    }
    
    .item-report::before { background: #6366F1; top: -20px; right: -20px; }
    .item-chat::before { background: #10B981; top: -20px; right: -20px; }
    
    .bento-item:hover {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.15);
        transform: translateY(-8px);
    }
    
    .bento-item:hover::before {
        opacity: 0.3;
        transform: scale(1.5);
    }
    
    .icon-box {
        width: 64px;
        height: 64px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 18px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        z-index: 1;
    }
    
    .bento-item h2 {
        font-size: 2rem;
        font-weight: 700;
        color: white;
        margin-bottom: 1rem;
        z-index: 1;
    }
    
    .bento-item p {
        color: #999;
        font-size: 1.1rem;
        line-height: 1.6;
        margin-bottom: 2rem;
        z-index: 1;
    }
    
    .stats-footer {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 24px;
        padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-top: 2rem;
    }
    
    /* Button Overrides */
    .stButton > button {
        border-radius: 12px !important;
        padding: 0.8rem 2rem !important;
        font-weight: 600 !important;
        text-transform: none !important;
        letter-spacing: 0px !important;
        transition: all 0.3s ease !important;
    }
    </style>
    """, unsafe_allow_html=True)

    username = st.session_state.username
    st.markdown(f"""
    <div class="home-header">
        <h1>Health Dashboard</h1>
        <p>Good morning, {username}. How can MedAssist help you today?</p>
    </div>
    """, unsafe_allow_html=True)

    # We use columns as the container for our bento-grid
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="bento-item item-report">
            <div class="icon-box">📊</div>
            <h2>Report Engine</h2>
            <p>Advanced diagnostic processing. Analyze bloodwork, vitals, and imaging with automated range verification.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Access Reports", type="primary", use_container_width=True, key="home_report_btn"):
            st.session_state.active_page = "report_analysis"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="bento-item item-chat">
            <div class="icon-box">🧠</div>
            <h2>Clinical AI</h2>
            <p>Specialized medical intelligence. Consult with our RAG-enhanced model for symptom analysis and health guidance.</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("Consult AI", type="primary", use_container_width=True, key="home_chatbot_btn"):
            st.session_state.active_page = "med_chatbot"
            st.rerun()

    # Footer Stats
    st.markdown('<div class="stats-footer">', unsafe_allow_html=True)
    st.markdown('<p style="color: #666; font-size: 0.9rem; margin-bottom: 1rem; font-weight: 600; text-transform: uppercase;">Overview</p>', unsafe_allow_html=True)
    data_manager = DataManager(st.session_state.username)
    df = data_manager.get_all_reports()
    
    s1, s2, s3 = st.columns(3)
    with s1:
        st.metric("Processed Files", len(df))
    with s2:
        st.metric("Managed Profiles", len(st.session_state.family_members) + 1)
    with s3:
        if not df.empty and "Date" in df.columns:
            try:
                latest = df["Date"].max()
                st.metric("Last Engagement", str(latest)[:10])
            except:
                st.metric("Last Engagement", "—")
        else:
            st.metric("Last Engagement", "N/A")
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------
# REPORT ANALYSIS (Upload) PAGE
# ----------------------------------
def report_analysis_page(data_manager, ocr):
    if st.session_state.show_all_reports_in_upload:
        st.session_state.show_all_reports_in_upload = False
        all_reports_page(data_manager)
        return

    st.title("📊 Report Analysis")

    if st.session_state.get("report_saved"):
        st.success("✅ Report saved successfully!")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("📤 Upload Another Report"):
                st.session_state.report_saved = False
                st.session_state.editing_report = False
                st.rerun()
        with c2:
            if st.button("📋 View All Reports"):
                st.session_state.report_saved = False
                st.session_state.editing_report = False
                st.session_state.active_page = "all_reports"
                st.rerun()
        return

    if st.session_state.editing_report:
        edit_report_page(data_manager, ocr)
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Option 1: Upload PDF")
        uploaded = st.file_uploader("Upload PDF Report", type=["pdf"], key="pdf_upload")
        if uploaded:
            test_options = ["Auto Detect", "Blood Test", "Vitals Check", "General Checkup",
                            "Liver Function Test (LFT)", "Complete Blood Picture (CBP)",
                            "Thyroid Test", "Comprehensive Health Check", "Ultrasound Report"]
            selected_test = st.selectbox("Choose test type:", test_options, key="test_type_select")
            if selected_test == "Auto Detect":
                selected_test = None
            if st.button("🚀 Process PDF", type="primary", key="process_pdf"):
                with st.spinner("Processing OCR..."):
                    try:
                        pdf_bytes = uploaded.read()
                        parsed, text = ocr.process_pdf_report(pdf_bytes, selected_test)
                        st.success("✅ OCR Successful!")
                        st.session_state.extracted_text = text
                        st.session_state.current_report = parsed
                        st.session_state.editing_report = True
                        st.session_state.selected_test_type = selected_test
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.info("Ensure Tesseract & Poppler are installed correctly")

    with col2:
        st.subheader("✍️ Option 2: Manual Entry")
        manual_report_type = st.selectbox(
            "Select Report Type",
            ["Blood Test", "Vitals Check", "General Checkup", "Liver Function Test (LFT)",
             "Complete Blood Picture (CBP)", "Thyroid Test", "Comprehensive Health Check", "Ultrasound Report"],
            key="manual_report_type"
        )
        if st.button("📝 Create Manual Report", key="create_manual", type="primary"):
            patient_info = {}
            if st.session_state.selected_family_member:
                patient_info["Patient Name"] = st.session_state.selected_family_member
                for member_id, member in st.session_state.family_members.items():
                    if member["name"] == st.session_state.selected_family_member:
                        patient_info["Patient Age"] = member.get("age", "")
                        patient_info["Patient Gender"] = member.get("gender", "")
                        break
            else:
                patient_info["Patient Name"] = st.session_state.username
            manual_report = ocr.create_manual_report(manual_report_type, patient_info)
            st.session_state.manual_report = manual_report
            st.session_state.editing_report = True
            st.rerun()

# ----------------------------------
# EDIT REPORT PAGE
# ----------------------------------
def edit_report_page(data_manager, ocr):
    st.title("📝 Review & Save Report")

    report = st.session_state.current_report or st.session_state.manual_report
    if not report:
        st.error("No report to edit")
        if st.button("Go Back"):
            st.session_state.editing_report = False
            st.rerun()
        return

    if st.session_state.get("extracted_text"):
        st.subheader("🔄 Change Test Type & Re-parse")
        c1, c2, c3 = st.columns([3, 2, 1])
        with c1:
            new_test_type = st.selectbox(
                "Select new test type to re-parse:",
                ["Blood Test", "Vitals Check", "General Checkup", "Liver Function Test (LFT)",
                 "Complete Blood Picture (CBP)", "Thyroid Test", "Comprehensive Health Check", "Ultrasound Report"],
                key="reparse_test_type"
            )
        with c2:
            if st.button("🔄 Apply & Re-parse", type="secondary", key="apply_changes"):
                try:
                    new_parsed = ocr.parse_medical_report(st.session_state.extracted_text, new_test_type)
                    for field in ["Patient Name", "Patient Age", "Patient Gender"]:
                        if report.get(field):
                            new_parsed[field] = report[field]
                    for key in new_parsed:
                        report[key] = new_parsed[key]
                    st.session_state.current_report = report
                    st.session_state.selected_test_type = new_test_type
                    st.success(f"✅ Re-parsed as {new_test_type}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error re-parsing: {str(e)}")
        with c3:
            if st.button("📄 OCR Text", key="view_ocr"):
                with st.expander("OCR Extracted Text"):
                    st.text_area("Text", st.session_state.extracted_text, height=300)

    detected_params = [k for k, v in report.items() if v is not None and k not in
                       ["Date", "Report Type", "Patient Name", "Patient Age",
                        "Patient Gender", "Notes", "Ultrasound Findings", "Ultrasound Impression"]]
    if detected_params:
        st.info(f"📊 Detected {len(detected_params)} parameters")

    with st.form("edit_report_form"):
        st.subheader("Basic Information")
        c1, c2, c3 = st.columns(3)
        with c1:
            current_date = report.get("Date", datetime.now().strftime("%Y-%m-%d"))
            try:
                date_value = datetime.strptime(str(current_date), "%Y-%m-%d")
            except:
                date_value = datetime.now()
            date_input = st.date_input("Date", value=date_value)
        with c2:
            rto = ["Blood Test", "Vitals Check", "General Checkup", "Liver Function Test (LFT)",
                   "Complete Blood Picture (CBP)", "Thyroid Test", "Comprehensive Health Check", "Ultrasound Report"]
            current_type = report.get("Report Type", "Blood Test")
            ci = rto.index(current_type) if current_type in rto else 0
            report_type = st.selectbox("Report Type", rto, index=ci)
        with c3:
            default_name = st.session_state.selected_family_member or st.session_state.username
            patient_name = st.text_input("Patient Name", value=report.get("Patient Name", default_name))

        c4, c5 = st.columns(2)
        with c4:
            patient_age = st.text_input("Age", value=report.get("Patient Age", ""))
        with c5:
            go = ["Male", "Female", "Other"]
            cg = report.get("Patient Gender", "")
            patient_gender = st.selectbox("Gender", options=[""] + go,
                                          index=0 if cg not in go else go.index(cg) + 1)

        notes = st.text_area("Notes", value=report.get("Notes", ""))
        st.divider()

        st.subheader("Medical Parameters")
        relevant_params = []
        for test_type, params in TEST_PARAMETERS.items():
            if test_type in report_type:
                relevant_params = params
                break
        if not relevant_params:
            relevant_params = ["Hemoglobin", "RBC", "WBC", "Platelets", "Glucose", "Cholesterol",
                                "Blood Pressure Systolic", "Blood Pressure Diastolic", "Heart Rate", "Temperature"]
        if report_type == "Ultrasound Report":
            relevant_params = ["Liver Size", "Gall Bladder Status", "Spleen Size",
                                "Pancreas Status", "Right Kidney Size", "Left Kidney Size", "Urinary Bladder Status"]

        cols = st.columns(3)
        updated_values = {}
        for idx, param in enumerate(relevant_params):
            with cols[idx % 3]:
                cur = report.get(param)
                display = "" if cur is None else str(cur)
                unit = NORMAL_RANGES.get(param, {}).get("unit", "")
                label = f"{param} ({unit})" if unit else param
                updated_values[param] = st.text_input(label, value=display, key=f"edit_{param}_{idx}")

        ultrasound_findings = ""
        ultrasound_impression = ""
        if report_type == "Ultrasound Report":
            st.subheader("Ultrasound Details")
            c1, c2 = st.columns(2)
            with c1:
                ultrasound_findings = st.text_area("Findings", value=report.get("Ultrasound Findings", ""), height=100, key="us_findings")
            with c2:
                ultrasound_impression = st.text_area("Impression", value=report.get("Ultrasound Impression", ""), height=100, key="us_impression")

        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1:
            save_button = st.form_submit_button("💾 Save Report", type="primary")
        with c2:
            cancel_button = st.form_submit_button("❌ Cancel")
        with c3:
            clear_button = st.form_submit_button("🗑️ Clear Values")

    if save_button:
        report["Date"] = date_input.strftime("%Y-%m-%d")
        report["Report Type"] = report_type
        report["Patient Name"] = patient_name
        report["Patient Age"] = patient_age
        report["Patient Gender"] = patient_gender if patient_gender else None
        report["Notes"] = notes
        for param, value in updated_values.items():
            if value:
                try:
                    report[param] = float(value)
                except ValueError:
                    report[param] = value
            else:
                report[param] = None
        if report_type == "Ultrasound Report":
            report["Ultrasound Findings"] = ultrasound_findings
            report["Ultrasound Impression"] = ultrasound_impression

        if not report.get("Patient Name"):
            st.error("Patient Name is required")
        else:
            success, msg = data_manager.add_report(report)
            if success:
                st.session_state.report_saved = True
                st.session_state.current_report = None
                st.session_state.manual_report = None
                st.session_state.editing_report = False
                st.session_state.selected_test_type = None
                st.session_state.extracted_text = None
                st.rerun()
            else:
                st.error(f"❌ Error saving report: {msg}")

    if cancel_button:
        st.session_state.current_report = None
        st.session_state.manual_report = None
        st.session_state.editing_report = False
        st.session_state.selected_test_type = None
        st.session_state.extracted_text = None
        st.rerun()

    if clear_button:
        for key in list(report.keys()):
            if key not in ["Date", "Report Type", "Patient Name", "Patient Age",
                           "Patient Gender", "Notes", "Ultrasound Findings", "Ultrasound Impression"]:
                report[key] = None
        st.rerun()

    st.divider()
    if st.button("⬅️ Back"):
        st.session_state.editing_report = False
        st.rerun()

# ----------------------------------
# MED CHATBOT PAGE
# ----------------------------------
def med_chatbot_page():
    st.title("🤖 Med Chatbot")
    st.caption("AI-powered medical assistant. Not a substitute for professional medical advice.")

    # Lazy import to avoid errors if packages not installed
    try:
        from gemini_engine import ask_gemini
        from rag_engine import search_pdf
        from csv_engine import search_csv
        from txt_engine import search_txt
        chatbot_available = True
    except Exception as e:
        chatbot_available = False
        st.warning(f"⚠️ Chatbot dependencies not fully loaded: {str(e)[:120]}")
        st.info("Please ensure all requirements are installed and GEMINI_API_KEY is set.")

    # Display history
    for role, msg in st.session_state.chat_history:
        with st.chat_message(role):
            st.markdown(msg, unsafe_allow_html=True)

    # Clear chat button
    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    query = st.chat_input("Describe your symptoms or ask a medical question...")

    if query and chatbot_available:
        st.session_state.chat_history.append(("user", query))

        with st.chat_message("user"):
            st.markdown(query)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # 1. Search CSV (Exact/Keyword match)
                    context, score = search_csv(query)
                    if score:
                        source_label = "Medical Q&A Database (CSV)"
                    else:
                        # 2. Search TXT (Fact matching)
                        context, score = search_txt(query)
                        if score:
                            source_label = "Medical Information File (TXT)"
                        else:
                            # 3. Search PDF (Vector similarity)
                            context, score, pg_info = search_pdf(query)
                            if score > 20: # Stricter threshold for PDF
                                source_label = f"Medical Knowledge Base (PDF){pg_info}"
                            else:
                                source_label = "General medical knowledge"
                                context = "General medical knowledge"

                    if not context:
                        context = "General medical knowledge"

                    answer = ask_gemini(query, context)
                    
                    # Append source footer
                    if source_label:
                        answer += f"\n\n---\n<p style='font-size: 0.75rem; color: #888888; margin-top: 10px;'>Source: {source_label}</p>"

                except Exception as e:
                    answer = f"⚠️ Error: {str(e)[:200]}. Please try again or consult a doctor."

            st.markdown(answer, unsafe_allow_html=True)
            st.session_state.chat_history.append(("assistant", answer))

    elif query and not chatbot_available:
        st.error("Chatbot is not available. Please check your installation.")

    st.markdown("---")
    st.caption("⚠️ This is not medical advice. Always consult a qualified doctor.")

# ----------------------------------
# DASHBOARD
# ----------------------------------
def dashboard_page(data_manager, visualizer):
    st.title("📈 Dashboard")
    df = data_manager.get_all_reports()

    if df.empty:
        st.info("No reports yet. Upload one from Report Analysis.")
        return

    st.subheader("Latest Report")
    latest = df.iloc[-1] if not df.empty else None

    if latest is not None:
        try:
            latest_date = latest.get('Date', 'Unknown') if hasattr(latest, 'get') else latest['Date']
            report_type = latest.get('Report Type', 'Unknown') if hasattr(latest, 'get') else latest['Report Type']
            patient_name = latest.get('Patient Name', 'Unknown') if hasattr(latest, 'get') else latest['Patient Name']
        except:
            latest_date = report_type = patient_name = 'Unknown'

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Date", str(latest_date)[:10] if isinstance(latest_date, pd.Timestamp) else str(latest_date))
        with c2:
            st.metric("Report Type", report_type)
        with c3:
            st.metric("Patient", patient_name)

    st.subheader("Trend Charts")
    numeric_params = []
    for col in df.columns:
        if col not in ["Date", "Report Type", "Patient Name", "Notes", "Patient Age", "Patient Gender",
                       "Ultrasound Findings", "Ultrasound Impression", "Gall Bladder Status",
                       "Pancreas Status", "Urinary Bladder Status"]:
            try:
                ns = pd.to_numeric(df[col], errors='coerce')
                if ns.notna().any():
                    numeric_params.append(col)
            except:
                continue

    display_params = numeric_params[:6]
    if not display_params:
        st.info("No numeric parameters found for trend charts.")
        return

    report_type_val = None
    if latest is not None:
        try:
            report_type_val = latest.get("Report Type") if hasattr(latest, 'get') else latest['Report Type']
        except:
            pass

    for param in display_params:
        data_points = pd.to_numeric(df[param], errors='coerce').dropna().count()
        if data_points < 2:
            st.info(f"Need ≥2 data points for {param} trend.")
            continue
        try:
            fig = visualizer.create_multi_test_trend_chart(df, param, report_type_val)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Chart error for {param}: {str(e)}")

# ----------------------------------
# ALL REPORTS PAGE  (with permanent delete)
# ----------------------------------
def all_reports_page(data_manager):
    st.title("📋 All Reports")

    df = data_manager.get_all_reports()

    if df.empty:
        st.info("No reports yet. Upload one from Report Analysis.")
        return

    st.dataframe(df, use_container_width=True)

    # Action bar
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔄 Refresh", key="refresh_reports"):
            st.rerun()
    with c2:
        if os.path.exists(data_manager.excel_file):
            with open(data_manager.excel_file, "rb") as f:
                st.download_button(
                    "📥 Download Excel",
                    f,
                    file_name=f"medical_reports_{st.session_state.username}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_excel"
                )

    st.divider()
    st.subheader("🗑️ Delete Report")
    st.caption("Select and permanently delete a report. This action cannot be undone.")

    if not df.empty:
        report_options = {}
        for idx, row in df.iterrows():
            date_str = str(row.get("Date", "Unknown"))[:10]
            rt = row.get("Report Type", "Unknown")
            patient = row.get("Patient Name", "Unknown")
            label = f"#{idx + 1}: {date_str} — {rt} — {patient}"
            report_options[label] = idx

        selected_label = st.selectbox("Select report to delete:", list(report_options.keys()), key="delete_report_select")

        col_del, col_info = st.columns([1, 3])
        with col_del:
            if st.button("🗑️ Delete Permanently", type="primary", key="delete_confirm_btn"):
                actual_idx = report_options[selected_label]
                success, msg = data_manager.delete_report(actual_idx)
                if success:
                    st.success("✅ Report deleted successfully!")
                    st.rerun()   # <-- immediately refreshes so deleted report is gone from UI
                else:
                    st.error(f"❌ Error: {msg}")
        with col_info:
            st.info(f"Selected: **{selected_label}**")

# ----------------------------------
# FAMILY PROFILES
# ----------------------------------
def family_profiles_page(auth_manager):
    st.title("👨‍👩‍👧‍👦 Family Profiles")

    with st.expander("➕ Add New Family Member", expanded=False):
        with st.form("add_family_member"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Full Name", key="family_name")
                age = st.number_input("Age", min_value=0, max_value=150, value=30, key="family_age")
            with c2:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="family_gender")
                relationship = st.selectbox("Relationship",
                                            ["Spouse", "Child", "Parent", "Sibling", "Grandparent", "Other"],
                                            key="family_relationship")
            if st.form_submit_button("Add Family Member", type="primary"):
                if name:
                    success, msg = auth_manager.add_family_member(st.session_state.username, name, age, gender, relationship)
                    if success:
                        st.success(f"✅ {msg}")
                        st.session_state.family_members = auth_manager.get_family_members(st.session_state.username)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                else:
                    st.warning("Please enter a name")

    st.subheader("Family Members")
    members = auth_manager.get_family_members(st.session_state.username)

    if not members:
        st.info("No family members added yet.")
    else:
        for member_id, member in members.items():
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 1])
                with c1:
                    st.write(f"**{member['name']}**")
                with c2:
                    st.write(f"Age: {member['age']}")
                with c3:
                    st.write(f"Gender: {member['gender']}")
                with c4:
                    st.write(f"Relationship: {member['relationship']}")
                with c5:
                    if st.button("🗑️", key=f"delete_{member_id}"):
                        success, msg = auth_manager.delete_family_member(st.session_state.username, member_id)
                        if success:
                            st.success(f"✅ {msg}")
                            st.session_state.family_members = auth_manager.get_family_members(st.session_state.username)
                            st.rerun()
                        else:
                            st.error(f"❌ {msg}")
                st.divider()

# ----------------------------------
# SETTINGS
# ----------------------------------
def settings_page():
    st.title("⚙️ Settings")
    c1, c2 = st.columns(2)

    data_manager = DataManager(st.session_state.username)
    df = data_manager.get_all_reports()

    with c1:
        st.subheader("Account Information")
        st.info(f"**Username:** {st.session_state.username}")
        st.metric("Total Reports", len(df))
        st.metric("Family Members", len(st.session_state.family_members))
        if not df.empty:
            try:
                st.metric("Latest Report", str(df['Date'].max())[:10])
            except:
                pass

    with c2:
        st.subheader("Data Management")
        if os.path.exists(data_manager.excel_file):
            with open(data_manager.excel_file, "rb") as f:
                st.download_button("📥 Download Complete History", f,
                                   file_name=f"{st.session_state.username}_history.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="download_complete")

        st.divider()
        st.warning("⚠️ Danger Zone")
        if st.button("🗑️ Clear All Reports", type="secondary", key="clear_all"):
            try:
                from config import EXCEL_COLUMNS
                empty_df = pd.DataFrame(columns=EXCEL_COLUMNS)
                empty_df.to_excel(data_manager.excel_file, index=False)
                st.success("✅ All reports cleared!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

    st.divider()
    st.subheader("System Information")
    st.info(f"Data Directory: {os.path.abspath('data')}")
    if os.path.exists("data/users.json"):
        st.write(f"Users DB: {os.path.getsize('data/users.json') / 1024:.2f} KB")
    if os.path.exists(data_manager.excel_file):
        st.write(f"Your Reports: {os.path.getsize(data_manager.excel_file) / (1024*1024):.3f} MB")

# ----------------------------------
# MAIN APP
# ----------------------------------
def main_app():
    render_sidebar()

    data_manager = DataManager(st.session_state.username)
    ocr = OCRProcessor()
    visualizer = Visualizer()

    page = st.session_state.active_page

    if page == "home":
        home_page()
    elif page == "report_analysis":
        report_analysis_page(data_manager, ocr)
    elif page == "med_chatbot":
        med_chatbot_page()
    elif page == "dashboard":
        try:
            dashboard_page(data_manager, visualizer)
        except Exception as e:
            st.error(f"Error loading dashboard: {str(e)}")
            import traceback
            with st.expander("Error Details"):
                st.code(traceback.format_exc())
    elif page == "all_reports":
        all_reports_page(data_manager)
    elif page == "family_profiles":
        family_profiles_page(auth_manager)
    elif page == "settings":
        settings_page()

# ----------------------------------
# ENTRY POINT
# ----------------------------------
if __name__ == "__main__":
    if not st.session_state.logged_in:
        login_page()
    else:
        main_app()
