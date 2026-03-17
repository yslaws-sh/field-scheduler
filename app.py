import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

st.markdown("<h1 style='text-align: center; color: red;'>⚽ הפועל הרצליה - מערכת שיבוץ חכמה</h1>", unsafe_allow_html=True)

# חישוב תאריכים
start_date = datetime(2026, 3, 22)
days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
days_with_dates = [(start_date + timedelta(days=i)).strftime("%d/%m") for i in range(5)]
day_labels = [f"יום {d} ({date})" for d, date in zip(days, days_with_dates)]

shifts = ['מוקדם (16:30-19:30)', 'מאוחר (18:00-21:00)']
field_parts = [
    ('מגרש 1', 'חצי קדמי'), ('מגרש 1', 'חצי אחורי'),
    ('מגרש 2', 'חצי קדמי'), ('מגרש 2', 'חצי אחורי')
]

# ניהול נתונים (State)
if 'db' not in st.session_state:
    st.session_state.db = []

# פונקציה קריטית: ניקוי התיבות בזמן החלפת מאמן
def handle_coach_change():
    for key in st.session_state.keys():
        if key.startswith("cb_"):
            del st.session_state[key]

# טעינת מאמנים
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    coaches = pd.read_csv(file_path)['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📋 הזנת העדפות מאמנים", "📅 לוח שיבוץ שבועי"])
    
    with tab1:
        # הוספנו on_change כדי לנקות את התיבות ברגע שבוחרים מאמן אחר
        current_coach = st.selectbox("בחר שם מאמן:", ["בחר מאמן"] + list(coaches), on_change=handle_coach_change)
        
        if current_coach != "בחר מאמן":
            # שליפת בחירות קיימות של המאמן
            saved_choices = [row['סבב_יום'] for row in st.session_state.db if row['מאמן'] == current_coach]
            
            st.write(f"שלום **{current_coach}**, סמן 4 ימים שונים:")
            
            current_selections = []
            for i, day_name in enumerate(days):
                st.write(f"---")
                st.write(f"**{day_labels[i]}**")
                cols = st.columns(2)
                for j, shift in enumerate(shifts):
                    unique_key = f"{day_name}_{shift}"
                    # מפתח ייחודי לצ'קבוקס ב-session_state
                    cb_key = f"cb_{unique_key}"
                    
                    # אם המאמן כבר בחר את זה בעבר, נסמן לו מראש
                    if cb_key not in st.session_state:
                        st.session_state[cb_key] = unique_key in saved_choices
                    
                    if cols[j].checkbox(shift, key=cb_key):
                        current_selections.append({
                            "יום": day_name, 
                            "סבב": shift, 
                            "סבב_יום": unique_key, 
                            "מאמן": current_coach
                        })
            
            if st.button("שמור ועדכן שיבוץ"):
                unique_days_count = len(set([x['יום'] for x in current_selections]))
                if unique_days_count < 4:
                    st.error(f"בחרת רק {unique_days_count} ימים. חובה לסמן לפחות 4 ימים שונים.")
                else:
                    # עדכון בסיס הנתונים: מחיקת ישן והכנסת חדש
                    st.session_state.db = [row for row in st.session_state.db if row['מאמן'] != current_coach]
                    st.session_state.db.extend(current_selections)
                    st.success(f"העדפות של {current_coach} נשמרו בהצלחה!")
                    st.balloons()

    with tab2:
        st.subheader(f"לוח שיבוץ סופי (שבוע ה-{days_with_dates[0]})")
        
        # יצירת לוח ריק
        schedule = []
        for day in days:
            for shift in shifts:
                for field, part in field_parts:
                    schedule.append({"יום": day, "סבב": shift, "מגרש": field, "מיקום": part, "מאמן משובץ": ""})
        df_schedule = pd.DataFrame(schedule)

        # שיבוץ אוטומטי לתוך החצאים
        for record in st.session_state.db:
            mask = (df_schedule['יום'] == record['יום']) & \
                   (df_schedule['סבב'] == record['סבב']) & \
                   (df_schedule['מאמן משובץ'] == "")
            
            indices = df_schedule[mask].index
            if len(indices) > 0:
                df_schedule.at[indices[0], 'מאמן משובץ'] = record['מאמן']

        st.table(df_schedule)

else:
    st.error("קובץ המאמנים לא נמצא ב-GitHub.")
