import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ניהול מגרשים - הפועל הרצליה", layout="wide")

# עיצוב כותרת בסגנון המועדון
st.markdown("<h1 style='text-align: center; color: red;'>מועדון הכדורגל הפועל הרצליה - מחלקת הנוער</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>מערכת שיבוץ מגרשים 2025/2026</h3>", unsafe_allow_html=True)

# מבנה המגרשים והחלקים
parts = ['מגרש 1 - חצי קדמי', 'מגרש 1 - חצי אחורי', 'מגרש 2 - חצי קדמי', 'מגרש 2 - חצי אחורי']
days = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
times = ['16:30-18:00', '18:00-19:30', '19:30-21:00']

# ניהול נתונים בזיכרון האפליקציה (כדי שזה יופיע בטבלה מיד)
if 'schedule_data' not in st.session_state:
    st.session_state.schedule_data = []

# טעינת רשימת מאמנים
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_coaches = pd.read_csv(file_path)
    coaches_list = df_coaches['מאמן'].unique()
    
    tab1, tab2 = st.tabs(["📋 מילוי דרישות מאמנים", "📅 לוח שיבוץ שבועי"])
    
    with tab1:
        col_a, col_b = st.columns([1, 2])
        with col_a:
            selected_coach = st.selectbox("בחר שם מאמן:", ["בחר מאמן"] + list(coaches_list))
        
        if selected_coach != "בחר מאמן":
            st.write(f"שלום **{selected_coach}**, סמן את המשמרות המועדפות עליך (חובה 4):")
            
            selections = []
            for day in days:
                with st.expander(f"יום {day}"):
                    c1, c2, c3 = st.columns(3)
                    with c1: 
                        if st.checkbox("16:30-18:00", key=f"{day}_1"): selections.append((day, "16:30-18:00"))
                    with c2: 
                        if st.checkbox("18:00-19:30", key=f"{day}_2"): selections.append((day, "18:00-19:30"))
                    with c3: 
                        if st.checkbox("19:30-21:00", key=f"{day}_3"): selections.append((day, "19:30-21:00"))

            if st.button("שמור שיבוץ במערכת"):
                unique_days = len(set([x[0] for x in selections]))
                if unique_days < 4:
                    st.error(f"סימנת רק {unique_days} ימים. דרושים 4 לפחות.")
                else:
                    # הוספה לרשימת השיבוץ
                    for s in selections:
                        st.session_state.schedule_data.append({
                            "יום": s[0], "שעה": s[1], "מאמן": selected_coach
                        })
                    st.success("הנתונים נקלטו! עבור ללשונית לוח שיבוץ.")
                    st.balloons()

    with tab2:
        st.subheader("לוח שיבוץ מגרשים - מבט על")
        
        # יצירת הטבלה הויזואלית (Pivot)
        if st.session_state.schedule_data:
            df_final = pd.DataFrame(st.session_state.schedule_data)
            # סיכום המאמנים לכל משבצת
            summary = df_final.groupby(['שעה', 'יום'])['מאמן'].apply(lambda x: ", ".join(list(set(x)))).unstack()
            # סידור עמודות לפי ימים
            summary = summary.reindex(columns=days, fill_value="")
            summary = summary.reindex(times)
            
            st.table(summary) # טבלה נקייה וברורה
        else:
            st.info("עדיין לא מולאו נתונים על ידי המאמנים.")
            
        # הצגת המבנה הריק של המגרשים
        st.write("---")
        st.write("**מקרא חלוקת מגרשים לכל משבצת:**")
        st.json({"מגרש 1": ["חצי קדמי", "חצי אחורי"], "מגרש 2": ["חצי קדמי", "חצי אחורי"]})

else:
    st.error("קובץ המאמנים לא נמצא.")
