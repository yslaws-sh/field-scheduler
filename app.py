import streamlit as st
import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# --- חישוב תאריכים אוטומטי (יום ראשון הקרוב) ---
today = datetime.now()
days_until_sunday = (6 - today.weekday()) % 7
if days_until_sunday == 0 and today.weekday() == 6: # אם היום ראשון, מציג את השבוע הנוכחי
    next_sunday = today
else:
    next_sunday = today + timedelta(days=days_until_sunday if days_until_sunday > 0 else 7)

days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(next_sunday + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

# --- הגדרות קבועות ---
FORM_SUBMIT_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
IDS = {"coach": "entry.1199305397", "day": "entry.1231450869", "shift": "entry.1001387245"}
SLOTS = ['16:30-18:00', '18:00-19:30', '19:30-21:00']
FIELDS = ['מגרש 1 (קדמי)', 'מגרש 1 (אחורי)', 'מגרש 2 (קדמי)', 'מגרש 2 (אחורי)']

if 'db' not in st.session_state: st.session_state.db = []

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    tab1, tab2 = st.tabs(["📋 הזנת העדפות", "📅 לוח שיבוץ סופי להורדה"])
    
    with tab1:
        selected_team_id = st.selectbox("בחר קבוצה:", ["בחר קבוצה"] + df_info['full_id'].tolist())
        if selected_team_id != "בחר קבוצה":
            row = df_info[df_info['full_id'] == selected_team_id].iloc[0]
            st.success(f"קבוצת **{row['שם הקבוצה']}** צריכה **{row['מספר אימונים']}** אימונים. סמן את כל האפשרויות הנוחות!")
            
            saved = [r['Unique'] for r in st.session_state.db if r['TeamID'] == selected_team_id]
            new_selections = []
            for day_label in day_labels:
                st.markdown(f"#### {day_label}")
                col1, col2 = st.columns(2)
                u_early, u_late = f"{day_label}_מוקדם", f"{day_label}_מאוחר"
                if col1.checkbox("מוקדם (16:30-19:30)", key=f"cb_{selected_team_id}_{u_early}", value=u_
