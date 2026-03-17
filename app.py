import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import os

st.set_page_config(page_title="ניהול מגרשים - סנכרון נתונים", layout="wide")

st.title("⚽ מערכת שיבוץ מגרשים - סנכרון Google Sheets")

# חיבור ל-Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# פונקציה לניקוי בחירות
if 'last_coach' not in st.session_state:
    st.session_state.last_coach = "בחר מאמן"

def reset_selections():
    for key in st.session_state.keys():
        if "day_" in key:
            st.session_state[key] = False

# טעינת קובץ המאמנים מה-GitHub
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_coaches = pd.read_csv(file_path)
    coaches_list = df_coaches['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📝 מילוי דרישות", "📊 לוח שיבוץ מסונכרן"])
    
    with tab1:
        selected_coach = st.selectbox("בחר את שמך:", ["בחר מאמן"] + list(coaches_list))
        
        if selected_coach != st.session_state.last_coach:
            st.session_state.last_coach = selected_coach
            reset_selections()
            st.rerun()

        if selected_coach != "בחר מאמן":
            days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
            selected_slots = []
            
            for day in days:
                st.write(f"---")
                col1, col2 = st.columns(2)
                with col1:
                    key_early = f"day_{day}_early"
                    if st.checkbox(f"יום {day} - מוקדם", key=key_early):
                        selected_slots.append(f"{day} מוקדם")
                with col2:
                    key_late = f"day_{day}_late"
                    if st.checkbox(f"יום {day} - מאוחר", key=key_late):
                        selected_slots.append(f"{day} מאוחר")

            if st.button("שלח העדפות לגיליון"):
                if len(set([s.split(' ')[0] for s in selected_slots])) < 4:
                    st.error("חובה לסמן לפחות 4 ימים שונים.")
                else:
                    # יצירת שורה חדשה לשמירה
                    new_data = pd.DataFrame([{
                        "Timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
                        "Coach": selected_coach,
                        "Selections": ", ".join(selected_slots)
                    }])
                    
                    # קריאת נתונים קיימים ושמירה
                    existing_data = conn.read(spreadsheet=st.secrets["gsheet_url"])
                    updated_df = pd.concat([existing_data, new_data], ignore_index=True)
                    conn.update(spreadsheet=st.secrets["gsheet_url"], data=updated_df)
                    
                    st.success(f"הנתונים של {selected_coach} נשמרו ב-Google Sheets!")

    with tab2:
        st.subheader("נתונים שנשאבו מהגיליון")
        # קריאה והצגה של הנתונים הגולמיים מהגיליון
        data = conn.read(spreadsheet=st.secrets["gsheet_url"])
        st.dataframe(data, use_container_width=True)
        
        if st.button("רענן נתונים"):
            st.rerun()

else:
    st.error("קובץ המאמנים לא נמצא ב-GitHub.")
