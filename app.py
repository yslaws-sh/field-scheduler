import streamlit as st
import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

# הגדרות אפליקציה
st.set_page_config(page_title="הפועל הרצליה - מערכת שיבוץ", page_icon="⚽", layout="wide")

# עיצוב RTL ויישור
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; background-color: #f8f9fa; }
    body { direction: rtl; }
    .main-header { background-color: #e31e24; padding: 20px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #e31e24 !important; color: white !important; border-radius: 12px; font-weight: bold; }
    th, td { text-align: center !important; border: 1px solid #dee2e6 !important; }
    </style>
    <div class="main-header">
        <h1 style='margin:0; font-size: 24px;'>מועדון כדורגל הפועל הרצליה</h1>
        <p style='margin:0; font-size: 16px;'>מערכת שיבוץ מגרשים חכמה</p>
    </div>
    """, unsafe_allow_html=True)

# --- תאריכים ---
start_date = datetime(2026, 3, 22)
days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

# --- הגדרות ---
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}
SLOTS = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
FIELDS = ['קאנטרי (קדמי)', 'קאנטרי (אחורי)', 'משק (קדמי)', 'משק (אחורי)']

if 'db' not in st.session_state: st.session_state.db = []
if 'admin_access' not in st.session_state: st.session_state.admin_access = False

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    tabs = ["📝 הזנת העדפות"]
    if st.session_state.admin_access: tabs.append("📊 לוח שיבוץ (מנהל)")
    active_tabs = st.tabs(tabs)
    
    with active_tabs[0]:
        selected_team_id = st.selectbox("בחר קבוצה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        if selected_team_id != "לחץ לבחירה...":
            row = df_info[df_info['full_id'] == selected_team_id].iloc[0]
            st.info(f"💡 קבוצת {row['שם הקבוצה']} צריכה {row['מספר אימונים']} אימונים. סמנו לפחות 4 ימים שונים לגמישות!")
            
            saved = [r['Unique'] for r in st.session_state.db if r['TeamID'] == selected_team_id]
            new_selections = []
            for d_label in day_labels:
                with st.expander(f"📅 {d_label}", expanded=True):
                    col1, col2 = st.columns(2)
                    u_early, u_late = f"{d_label}_מוקדם", f"{d_label}_מאוחר"
                    if col1.checkbox("☀️ מוקדם", key=f"cb_{selected_team_id}_{u_early}", value=u_early in saved):
                        new_selections.append({"TeamID": selected_team_id, "Coach": row['מאמן'], "Day": d_label, "Shift": "מוקדם", "Unique": u_early})
                    if col2.checkbox("🌙 מאוחר", key=f"cb_{selected_team_id}_{u_late}", value=u_late in saved):
                        new_selections.append({"TeamID": selected_team_id, "Coach": row['מאמן'], "Day": d_label, "Shift": "מאוחר", "Unique": u_late})

            if st.button("שמור העדפות 🚀"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("❌ חובה לסמן לפחות 4 ימים שונים.")
                else:
                    st.session_state.db = [r for r in st.session_state.db if r['TeamID'] != selected_team_id]
                    st.session_state.db.extend(new_selections)
                    for sel in
