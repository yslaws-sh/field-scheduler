import streamlit as st
import pandas as pd
import requests
import os
import io
from datetime import datetime, timedelta

# הגדרות אפליקציה רשמית
st.set_page_config(page_title="הפועל הרצליה - מערכת ניהול", page_icon="⚽", layout="wide")

# עיצוב RTL
st.markdown("""
    <style>
    .main { direction: rtl; text-align: right; background-color: #f8f9fa; }
    body { direction: rtl; }
    .main-header { background-color: #e31e24; padding: 20px; border-radius: 0 0 20px 20px; color: white; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #e31e24 !important; color: white !important; border-radius: 12px; font-weight: bold; }
    th, td { text-align: center !important; border: 1px solid #dee2e6 !important; padding: 8px !important; }
    </style>
    <div class="main-header">
        <h1 style='margin:0; font-size: 24px;'>מועדון כדורגל הפועל הרצליה</h1>
        <p style='margin:0; font-size: 16px;'>מערכת ניהול ושיבוץ חכמה</p>
    </div>
    """, unsafe_allow_html=True)

# קישור לגיליון הנתונים (מה ששלחת לי)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR8In1pn4dPWFvpIrxj1eLufbA7KQ6_wupxQiDbfxsAmvjsHrsO8ehPc3f5fT0TbenxVaLr8Tet6h5u/pub?output=tsv"

# פונקציה למשיכת נתונים מהגיליון
def load_external_data():
    try:
        response = requests.get(SHEET_URL)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text), sep='\t')
            # כאן אנחנו ממירים את הנתונים מהגיליון לפורמט שהאפליקציה מבינה
            # (בהנחה שבגיליון יש עמודות כמו 'קבוצה', 'יום', 'משמרת')
            return df
    except:
        return pd.DataFrame()
    return pd.DataFrame()

# --- הגדרות קבועות ---
ALL_FIELD_OPTIONS = ['קאנטרי קדמי 1', 'קאנטרי קדמי 2', 'קאנטרי אחורי 1', 'קאנטרי אחורי 2', 'משק קדמי 1', 'משק קדמי 2', 'משק אחורי 1', 'משק אחורי 2', 'סינטטי קטן']
if 'active_fields' not in st.session_state: st.session_state.active_fields = ALL_FIELD_OPTIONS
if 'active_slots' not in st.session_state: st.session_state.active_slots = ['16:30-18:00', '18:00-19:30', '19:30-21:00']

start_date = datetime(2026, 3, 22)
days_list = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי']
day_labels = [(start_date + timedelta(days=i)).strftime(f"יום {days_list[i]} %d/%m") for i in range(5)]

if 'admin_access' not in st.session_state: st.session_state.admin_access = False

# טעינת קובץ המאמנים מ-GitHub
file_path = 'טבלת מאמנים.csv'
if os.path.exists(file_path):
    df_info = pd.read_csv(file_path)
    df_info['full_id'] = df_info['שם הקבוצה'] + " (" + df_info['מאמן'] + ")"
    
    # טעינת הבחירות הקיימות מהגיליון של גוגל
    external_data = load_external_data()
    
    tabs = ["📝 הזנת העדפות", "⚙️ ניהול מגרשים ושיבוץ"]
    active_tabs = st.tabs(tabs)
    
    with active_tabs[0]:
        selected_team_id = st.selectbox("בחר קבוצה:", ["לחץ לבחירה..."] + df_info['full_id'].tolist())
        if selected_team_id != "לחץ לבחירה...":
            row = df_info[df_info['full_id'] == selected_team_id].iloc[0]
            st.info(f"💡 **הודעה לקבוצת {row['שם הקבוצה']}:** עליך לסמן לפחות 4 ימים שונים.")

            # (כאן המאמן מסמן צ'קבוקסים - נשאר אותו דבר)
            # בשלב הבא נחבר את כפתור ה'שמור' לשליחה ל-Google Form
            if st.button("שמור העדפות 🚀"):
                st.success("הנתונים נשמרים בגיליון המרכזי...")
                # כאן תבוא פונקציית השליחה לטופס ברגע שתשלח לי את הלינק שלו

    # --- טאב מנהל ---
    with active_tabs[1]:
        admin_key = st.text_input("סיסמת מנהל:", type="password")
        if admin_key == "1906":
            st.session_state.admin_access = True
            
            # הצגת הנתונים הגולמיים מהגיליון כדי לוודא שזה עובד
            if not external_data.empty:
                st.write("### ✅ נתונים שהתקבלו מהמאמנים (מתוך גוגל שיטס):")
                st.dataframe(external_data)
                
                # כאן תרוץ לוגיקת השיבוץ על בסיס הנתונים האלו
            else:
                st.warning("טרם התקבלו נתונים מהגיליון. וודא שמאמנים מילאו את הטופס.")

else:
    st.error("קובץ המאמנים חסר ב-GitHub")
