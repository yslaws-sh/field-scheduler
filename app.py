import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# חיבור ל-Google Sheets (חובה שהגדרת ב-Secrets את gsheet_url)
conn = st.connection("gsheets", type=GSheetsConnection)

# הגדרות שבוע
start_date = datetime(2026, 3, 22)
days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
shifts = ['מוקדם (16:30-19:30)', 'מאוחר (18:00-21:00)']
field_parts = [('מגרש 1', 'חצי קדמי'), ('מגרש 1', 'חצי אחורי'), ('מגרש 2', 'חצי קדמי'), ('מגרש 2', 'חצי אחורי')]

def handle_coach_change():
    for key in list(st.session_state.keys()):
        if key.startswith("cb_"): del st.session_state[key]

# קריאת נתונים קיימים מהגוגל שיטס
try:
    existing_db = conn.read(spreadsheet=st.secrets["gsheet_url"])
except:
    existing_db = pd.DataFrame(columns=["Coach", "Day", "Shift", "Unique_Key"])

file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    coaches = pd.read_csv(file_path)['מאמן'].unique()
    tab1, tab2 = st.tabs(["📋 הזנת העדפות מאמנים", "📅 לוח שיבוץ מעוצב"])
    
    with tab1:
        current_coach = st.selectbox("בחר שם מאמן:", ["בחר מאמן"] + list(coaches), on_change=handle_coach_change)
        
        if current_coach != "בחר מאמן":
            # טעינת בחירות מהגוגל שיטס
            saved_for_coach = existing_db[existing_db['Coach'] == current_coach]['Unique_Key'].tolist()
            st.write(f"שלום **{current_coach}**, סמן 4 ימים שונים:")
            
            new_selections = []
            for day in days:
                st.write(f"---")
                cols = st.columns(2)
                for j, shift in enumerate(shifts):
                    u_key = f"{day}_{shift}"
                    cb_key = f"cb_{u_key}"
                    if cb_key not in st.session_state:
                        st.session_state[cb_key] = u_key in saved_for_coach
                    
                    if cols[j].checkbox(shift, key=cb_key):
                        new_selections.append({"Coach": current_coach, "Day": day, "Shift": shift, "Unique_Key": u_key})
            
            if st.button("שמור ב-Google Sheets"):
                if len(set([x['Day'] for x in new_selections])) < 4:
                    st.error("חובה לסמן לפחות 4 ימים שונים.")
                else:
                    # עדכון הגיליון: מסירים ישן ומוסיפים חדש
                    other_coaches = existing_db[existing_db['Coach'] != current_coach]
                    final_df = pd.concat([other_coaches, pd.DataFrame(new_selections)], ignore_index=True)
                    conn.update(spreadsheet=st.secrets["gsheet_url"], data=final_df)
                    st.success("הנתונים נשמרו בגיליון!")
                    st.balloons()

    with tab2:
        st.subheader("לוח שיבוץ שבועי (הצבה אוטומטית)")
        # בניית הלוח הוויזואלי
        schedule = []
        for day in days:
            for shift in shifts:
                for field, part in field_parts:
                    schedule.append({"יום": day, "סבב": shift, "מגרש": field, "מיקום": part, "מאמן": ""})
        df_viz = pd.DataFrame(schedule)

        # הצבת המאמנים מהגיליון ללוח
        for _, row in existing_db.iterrows():
            mask = (df_viz['יום'] == row['Day']) & (df_viz['סבב'] == row['Shift']) & (df_viz['מאמן'] == "")
            idx = df_viz[mask].index
            if len(idx) > 0: df_viz.at[idx[0], 'מאמן'] = row['Coach']

        # תצוגה יפה כטבלה רחבה (Pivot)
        pivot_df = df_viz.pivot_table(index=['סבב', 'מגרש', 'מיקום'], columns='יום', values='מאמן', aggfunc=lambda x: ' '.join(x))
        pivot_df = pivot_df.reindex(columns=days)
        st.dataframe(pivot_df, use_container_width=True, height=500)
        
        if st.button("רענן לוח"): st.rerun()
else:
    st.error("קובץ המאמנים חסר.")
