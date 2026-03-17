import streamlit as st
import pandas as pd
import requests
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# --- הגדרות חיבור לגוגל פורמס (IDs מעודכנים) ---
FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSd-HaGeFh0P_zU7xs1kiFjLnM5i2mjZhiaRTcUD4h_L0ETksA/formResponse"
ENTRY_COACH = "entry.1199305397"
ENTRY_DAY = "entry.1231450869"
ENTRY_SHIFT = "entry.1001387245"

# --- הגדרות זמן ---
start_date = datetime(2026, 3, 22)
days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days[i]} (%d/%m)") for i in range(5)]
shifts = ['מוקדם (16:30-19:30)', 'מאוחר (18:00-21:00)']
field_parts = [('מגרש 1', 'חצי קדמי'), ('מגרש 1', 'חצי אחורי'), ('מגרש 2', 'חצי קדמי'), ('מגרש 2', 'חצי אחורי')]

# זיכרון מקומי לתצוגה בלוח
if 'db' not in st.session_state:
    st.session_state.db = []

# פונקציית ניקוי כשהמאמן מתחלף
def clear_form():
    for key in list(st.session_state.keys()):
        if key.startswith("cb_"):
            st.session_state[key] = False

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    coaches = pd.read_csv(file_path)['מאמן'].unique()
    tab1, tab2 = st.tabs(["📋 הזנת העדפות", "📅 לוח שיבוץ מעוצב"])
    
    with tab1:
        current_coach = st.selectbox("בחר שם מאמן:", ["בחר מאמן"] + list(coaches), on_change=clear_form)
        
        if current_coach != "בחר מאמן":
            st.info(f"שלום {current_coach}, בחר 4 ימים לשבוע הקרוב:")
            selections = []
            for i, day_name in enumerate(days):
                st.markdown(f"#### {day_labels[i]}")
                cols = st.columns(2)
                for j, shift in enumerate(shifts):
                    # מפתח ייחודי למאמן וליום כדי למנוע ערבוב
                    cb_key = f"cb_{current_coach}_{day_name}_{shift}"
                    if cols[j].checkbox(shift, key=cb_key):
                        selections.append({"Coach": current_coach, "Day": day_name, "Shift": shift})

            if st.button("שמור שיבוץ ועדכן גיליון"):
                unique_days = len(set([x['Day'] for x in selections]))
                if unique_days < 4:
                    st.error("חובה לסמן לפחות 4 ימים שונים!")
                else:
                    # שליחה לגוגל
                    success = True
                    for sel in selections:
                        payload = {ENTRY_COACH: sel['Coach'], ENTRY_DAY: sel['Day'], ENTRY_SHIFT: sel['Shift']}
                        try:
                            requests.post(FORM_URL, data=payload)
                        except:
                            success = False
                    
                    if success:
                        st.session_state.db = [r for r in st.session_state.db if r['Coach'] != current_coach]
                        st.session_state.db.extend(selections)
                        st.success("הנתונים נשלחו ונקלטו בגוגל שיטס!")
                        st.balloons()
                    else:
                        st.error("שגיאה בשליחה. וודא חיבור לאינטרנט.")

    with tab2:
        st.subheader("לוח שיבוץ שבועי")
        # יצירת לוח ריק
        grid = []
        for day in days:
            for shift in shifts:
                for field, part in field_parts:
                    grid.append({"יום": day, "סבב": shift, "מגרש": field, "מיקום": part, "מאמן": ""})
        df_viz = pd.DataFrame(grid)

        # הצבה בלוח
        for row in st.session_state.db:
            mask = (df_viz['יום'] == row['Day']) & (df_viz['סבב'] == row['Shift']) & (df_viz['מאמן'] == "")
            idx = df_viz[mask].index
            if len(idx) > 0: df_viz.at[idx[0], 'מאמן'] = row['Coach']

        # עיצוב טבלה רחבה
        df_viz['מגרש_וחלק'] = df_viz['מגרש'] + " (" + df_viz['מיקום'] + ")"
        pivot = df_viz.pivot_table(index=['סבב', 'מגרש_וחלק'], columns='יום', values='מאמן', aggfunc='first')
        pivot = pivot.reindex(columns=days)
        pivot.columns = day_labels
        st.table(pivot)

else:
    st.error("קובץ המאמנים חסר.")
