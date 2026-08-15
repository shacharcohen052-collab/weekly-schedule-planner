from __future__ import annotations

from datetime import date, datetime, time, timedelta
from io import BytesIO
from typing import Any

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="מתכנן שבוע — 75 Hard",
    page_icon="📅",
    layout="wide",
)

st.markdown(
    """
    <style>
      html, body, [class*="css"] { direction: rtl; text-align: right; }
      .stTextArea textarea, .stCodeBlock { direction: rtl; text-align: right; }
      [data-testid="stDataFrame"] { direction: rtl; }
      .block-container { max-width: 1220px; padding-top: 2rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

DAYS = ["ראשון", "שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת"]
CLASS_OPTIONS = ["ללא שיעור", "02:30", "03:30", "04:00"]
REQUIRED_COLUMNS = ["יום", "תחילת צבא", "סיום צבא", "נסיעות (דקות)", "שיעור קבלה"]


def build_default_week(monday: date) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for index, day_name in enumerate(DAYS):
        current = monday + timedelta(days=index)
        rows.append(
            {
                "יום": f"{day_name} {current.strftime('%d/%m')}",
                "תחילת צבא": "",
                "סיום צבא": "",
                "נסיעות (דקות)": 45,
                "שיעור קבלה": "ללא שיעור",
                "הערה": "",
            }
        )
    return pd.DataFrame(rows)


def normalise_uploaded_schedule(uploaded_file: Any, fallback: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    """Read a CSV/XLSX file and map common Hebrew headers to the app's columns."""
    try:
        suffix = uploaded_file.name.lower().rsplit(".", 1)[-1]
        if suffix == "csv":
            raw = pd.read_csv(uploaded_file)
        elif suffix in {"xlsx", "xls"}:
            raw = pd.read_excel(uploaded_file)
        else:
            return fallback, "בשלב זה ניתן להעלות קובץ CSV או Excel בלבד."
    except Exception as error:
        return fallback, f"לא הצלחתי לקרוא את הקובץ: {error}"

    aliases = {
        "יום": "יום",
        "date": "יום",
        "תאריך": "יום",
        "תחילת צבא": "תחילת צבא",
        "שעת התחלה": "תחילת צבא",
        "התחלה": "תחילת צבא",
        "start": "תחילת צבא",
        "סיום צבא": "סיום צבא",
        "שעת סיום": "סיום צבא",
        "סיום": "סיום צבא",
        "end": "סיום צבא",
        "נסיעות": "נסיעות (דקות)",
        "זמן נסיעה": "נסיעות (דקות)",
        "נסיעות (דקות)": "נסיעות (דקות)",
        "travel_minutes": "נסיעות (דקות)",
        "שיעור קבלה": "שיעור קבלה",
        "שיעור": "שיעור קבלה",
        "kabbalah": "שיעור קבלה",
        "הערה": "הערה",
        "הערות": "הערה",
    }
    raw = raw.rename(columns={column: aliases.get(str(column).strip().lower(), column) for column in raw.columns})

    result = fallback.copy()
    for column in result.columns:
        if column in raw.columns:
            for row_index in range(min(len(raw), len(result))):
                value = raw.iloc[row_index][column]
                if pd.notna(value):
                    result.loc[row_index, column] = str(value)

    result["נסיעות (דקות)"] = pd.to_numeric(result["נסיעות (דקות)"], errors="coerce").fillna(45).astype(int)
    result["שיעור קבלה"] = result["שיעור קבלה"].where(
        result["שיעור קבלה"].isin(CLASS_OPTIONS), "ללא שיעור"
    )
    return result, None


def parse_clock(value: Any) -> time | None:
    """Accept HH:MM, spreadsheet time values, or return None for empty cells."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    value_str = str(value).strip()
    if not value_str or value_str.lower() in {"nan", "none", "-"}:
        return None
    for pattern in ("%H:%M", "%H.%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value_str, pattern).time()
        except ValueError:
            pass
    return None


def clock_label(value: time) -> str:
    return value.strftime("%H:%M")


def date_at(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock)


def hhmm_from_datetime(value: datetime) -> str:
    return value.strftime("%H:%M")


def bedtime_for_wake(wake_time: time, sleep_hours: float) -> time:
    reference = datetime.combine(date(2000, 1, 2), wake_time) - timedelta(hours=sleep_hours)
    return reference.time().replace(second=0, microsecond=0)


def add_event(events: list[dict[str, Any]], day_name: str, day_date: date, start: datetime, duration: int, title: str, category: str) -> None:
    end = start + timedelta(minutes=duration)
    events.append(
        {
            "תאריך": day_date,
            "יום": day_name,
            "התחלה": start,
            "סיום": end,
            "שעה": f"{hhmm_from_datetime(start)}–{hhmm_from_datetime(end)}",
            "אירוע": title,
            "סוג": category,
        }
    )


def ranges_overlap(first_start: datetime, first_end: datetime, second_start: datetime, second_end: datetime) -> bool:
    return first_start < second_end and second_start < first_end


def generate_day_plan(
    row: pd.Series,
    day_date: date,
    min_sleep_hours: float,
    class_length_minutes: int,
    default_wake: time,
) -> tuple[list[dict[str, Any]], list[str]]:
    """Build a transparent, rule-based starter plan for one day."""
    day_display = str(row["יום"])
    army_start = parse_clock(row["תחילת צבא"])
    army_end = parse_clock(row["סיום צבא"])
    travel_minutes = int(pd.to_numeric(row["נסיעות (דקות)"], errors="coerce") or 45)
    class_choice = str(row["שיעור קבלה"])
    note = str(row.get("הערה", "")).strip()

    events: list[dict[str, Any]] = []
    alerts: list[str] = []
    class_time = parse_clock(class_choice) if class_choice != "ללא שיעור" else None
    wake_time = class_time or default_wake
    sleep_time = bedtime_for_wake(wake_time, min_sleep_hours)

    # A planned bedtime is an anchor, rather than a calendar event, because it spans midnight.
    add_event(
        events,
        day_display,
        day_date,
        date_at(day_date, sleep_time),
        15,
        f"תחילת שגרת שינה — יעד: {min_sleep_hours:g} שעות לפני השכמה ב־{clock_label(wake_time)}",
        "שינה",
    )

    class_end: datetime | None = None
    if class_time:
        class_start = date_at(day_date, class_time)
        class_end = class_start + timedelta(minutes=class_length_minutes)
        add_event(events, day_display, day_date, class_start, class_length_minutes, "שיעור קבלה", "שיעור")

    if army_start and army_end:
        army_start_dt = date_at(day_date, army_start)
        army_end_dt = date_at(day_date, army_end)
        if army_end_dt <= army_start_dt:
            alerts.append(f"{day_display}: שעת סיום הצבא חייבת להיות אחרי שעת ההתחלה.")
        else:
            add_event(events, day_display, day_date, army_start_dt, int((army_end_dt - army_start_dt).total_seconds() / 60), "צבא", "צבא")

            is_morning_army = army_start <= time(9, 30)
            if is_morning_army and class_time:
                first_start = max(date_at(day_date, time(5, 15)), class_end + timedelta(minutes=30))
                add_event(events, day_display, day_date, first_start, 45, "אימון חוץ — הליכה מהירה / ריצה קלה", "אימון")
                add_event(events, day_display, day_date, first_start + timedelta(minutes=50), 20, "מקלחת והתארגנות", "אישי")
                add_event(events, day_display, day_date, first_start + timedelta(minutes=75), 20, "ארוחת בוקר", "אוכל")
                second_start = army_end_dt + timedelta(hours=2)
                add_event(events, day_display, day_date, second_start, 45, "אימון כוח / חדר כושר", "אימון")
                add_event(events, day_display, day_date, second_start + timedelta(minutes=55), 30, "ארוחה אחרי אימון", "אוכל")
            elif is_morning_army:
                # No early class: preserve a later wake-up and place the two workouts after army.
                first_start = army_end_dt + timedelta(hours=2)
                second_start = date_at(day_date, time(19, 0))
                add_event(events, day_display, day_date, first_start, 45, "אימון כוח / חדר כושר", "אימון")
                add_event(events, day_display, day_date, first_start + timedelta(minutes=55), 30, "ארוחה אחרי אימון", "אוכל")
                add_event(events, day_display, day_date, second_start, 45, "אימון חוץ — הליכה מהירה", "אימון")
                add_event(events, day_display, day_date, second_start + timedelta(minutes=55), 30, "ארוחת ערב", "אוכל")
            elif class_time:
                first_start = max(date_at(day_date, time(5, 15)), class_end + timedelta(minutes=30))
                second_start = army_start_dt - timedelta(minutes=travel_minutes + 75)
                add_event(events, day_display, day_date, first_start, 45, "אימון חוץ — הליכה מהירה / ריצה קלה", "אימון")
                add_event(events, day_display, day_date, second_start, 45, "אימון כוח / חדר כושר", "אימון")
            else:
                first_start = date_at(day_date, time(9, 15))
                second_start = army_end_dt + timedelta(hours=1, minutes=15)
                add_event(events, day_display, day_date, first_start, 45, "אימון חוץ — הליכה מהירה / ריצה קלה", "אימון")
                add_event(events, day_display, day_date, second_start, 45, "אימון כוח / חדר כושר", "אימון")
                add_event(events, day_display, day_date, second_start + timedelta(minutes=55), 30, "ארוחת ערב", "אוכל")

            add_event(events, day_display, day_date, army_start_dt - timedelta(minutes=travel_minutes), travel_minutes, "נסיעה לצבא + קריאת ספר", "נסיעה")
            add_event(events, day_display, day_date, army_end_dt + timedelta(minutes=15), 30, "ארוחה / התאוששות אחרי הצבא", "אוכל")
    else:
        alerts.append(f"{day_display}: חסרות שעות צבא. הוזן יום גמיש ללא תכנון אוטומטי מלא.")
        start = date_at(day_date, time(9, 0))
        add_event(events, day_display, day_date, start, 45, "אימון חוץ — הליכה מהירה / ריצה קלה", "אימון")
        add_event(events, day_display, day_date, start + timedelta(hours=9), 45, "אימון כוח / חדר כושר", "אימון")

    if not army_start:
        reading_start = date_at(day_date, time(7, 0)) if class_time else date_at(day_date, time(11, 10))
        add_event(events, day_display, day_date, reading_start, 45, "קריאת ספר", "קריאה")
    elif travel_minutes < 45:
        alerts.append(f"{day_display}: הנסיעה לצבא קצרה מ־45 דקות; יש להשלים קריאת ספר בזמן אחר.")

    if note and note.lower() not in {"nan", "none"}:
        alerts.append(f"{day_display}: הערה אישית — {note}")

    sorted_events = sorted(events, key=lambda event: event["התחלה"])
    for index, current in enumerate(sorted_events[:-1]):
        following = sorted_events[index + 1]
        if ranges_overlap(current["התחלה"], current["סיום"], following["התחלה"], following["סיום"]):
            alerts.append(
                f"{day_display}: התנגשות בין „{current['אירוע']}” ({current['שעה']}) "
                f"לבין „{following['אירוע']}” ({following['שעה']})."
            )

    # Sleep start is technically before an early-morning class; only use it as a target, not a collision.
    return sorted_events, alerts


def create_week_plan(schedule: pd.DataFrame, monday: date, min_sleep_hours: float, class_length_minutes: int, default_wake: time) -> tuple[pd.DataFrame, list[str]]:
    all_events: list[dict[str, Any]] = []
    all_alerts: list[str] = []
    for index, (_, row) in enumerate(schedule.iterrows()):
        events, alerts = generate_day_plan(
            row=row,
            day_date=monday + timedelta(days=index),
            min_sleep_hours=min_sleep_hours,
            class_length_minutes=class_length_minutes,
            default_wake=default_wake,
        )
        all_events.extend(events)
        all_alerts.extend(alerts)
    plan = pd.DataFrame(all_events)
    if not plan.empty:
        plan = plan.sort_values(["תאריך", "התחלה"]).reset_index(drop=True)
    return plan, all_alerts


def create_whatsapp_message(plan: pd.DataFrame, monday: date) -> str:
    if plan.empty:
        return "לא נוצרו אירועים. בדוק את שעות הצבא והפעל שוב את הבנייה."

    lines = [
        f"היי, אלו האירועים שלי להוספה ליומן לשבוע של {monday.strftime('%d/%m/%Y')}:",
        "",
    ]
    for (event_date, day_name), group in plan.groupby(["תאריך", "יום"], sort=False):
        lines.append(f"{day_name} — {event_date.strftime('%d/%m')}")
        for _, event in group.iterrows():
            if event["סוג"] == "שינה":
                lines.append(f"• {event['אירוע']}")
            else:
                lines.append(f"• {event['שעה']} — {event['אירוע']}")
        lines.append("")
    lines.extend(
        [
            "בבקשה הוסיפי את האירועים לפי השעות המופיעות למעלה.",
            "אם יש התנגשות ביומן, שלחי לי אותה לפני קביעה סופית.",
        ]
    )
    return "\n".join(lines)


def create_csv(plan: pd.DataFrame) -> bytes:
    export = plan.copy()
    if not export.empty:
        export["תאריך"] = export["תאריך"].apply(lambda value: value.strftime("%d/%m/%Y"))
        export["התחלה"] = export["התחלה"].apply(lambda value: value.strftime("%d/%m/%Y %H:%M"))
        export["סיום"] = export["סיום"].apply(lambda value: value.strftime("%d/%m/%Y %H:%M"))
    return export.to_csv(index=False).encode("utf-8-sig")


if "schedule" not in st.session_state:
    upcoming_monday = date.today() + timedelta(days=(7 - date.today().weekday()) % 7)
    st.session_state.monday = upcoming_monday
    st.session_state.schedule = build_default_week(upcoming_monday)

st.title("מתכנן שבוע — צבא, 75 Hard ושיעור קבלה")
st.caption("אבטיפוס מקומי: מזינים את מסגרת הצבא, בוחרים שיעור בוקר לכל יום ומקבלים הצעה שקופה עם בדיקת התנגשויות.")

with st.sidebar:
    st.header("הגדרות קבועות")
    selected_monday = st.date_input("יום ראשון של השבוע", value=st.session_state.monday, format="DD/MM/YYYY")
    if selected_monday != st.session_state.monday:
        st.session_state.monday = selected_monday
        st.session_state.schedule = build_default_week(selected_monday)

    min_sleep = st.slider("יעד שינה מינימלי (שעות)", min_value=7.0, max_value=9.5, value=8.0, step=0.25)
    class_length = st.slider("משך שיעור קבלה (דקות)", min_value=45, max_value=150, value=110, step=5)
    default_wake_label = st.selectbox("השכמה ביום ללא שיעור", ["05:50", "06:30", "07:00", "08:50"], index=0)
    default_wake = parse_clock(default_wake_label) or time(5, 50)

    st.divider()
    st.subheader("העלאת לו״ז צבאי")
    uploaded = st.file_uploader("CSV או Excel", type=["csv", "xlsx", "xls"])
    if uploaded:
        schedule, error_message = normalise_uploaded_schedule(uploaded, st.session_state.schedule)
        if error_message:
            st.error(error_message)
        else:
            st.session_state.schedule = schedule
            st.success("הקובץ נטען. בדוק את הטבלה ואשר את הזמנים.")

st.subheader("1. הזן את הלו״ז הצבאי של השבוע")
st.info("אפשר להשאיר יום בלי שעות צבא; האפליקציה תתייחס אליו כיום גמיש. כדי לשמור על פרטיות, הזן רק שעות — לא מיקום, תפקיד או פרטים צבאיים רגישים.")

edited_schedule = st.data_editor(
    st.session_state.schedule,
    num_rows="fixed",
    hide_index=True,
    use_container_width=True,
    column_config={
        "יום": st.column_config.TextColumn("יום", disabled=True),
        "תחילת צבא": st.column_config.TextColumn("תחילת צבא", help="פורמט HH:MM, לדוגמה 08:00"),
        "סיום צבא": st.column_config.TextColumn("סיום צבא", help="פורמט HH:MM, לדוגמה 12:00"),
        "נסיעות (דקות)": st.column_config.NumberColumn("נסיעות (דקות)", min_value=0, max_value=180, step=5),
        "שיעור קבלה": st.column_config.SelectboxColumn("שיעור קבלה", options=CLASS_OPTIONS),
        "הערה": st.column_config.TextColumn("הערה", help="לדוגמה: עבודה עם אבא, יציאה מוקדמת או מגבלה אחרת"),
    },
)
st.session_state.schedule = edited_schedule

if st.button("בנה לו״ז שבועי", type="primary", use_container_width=True):
    plan, alerts = create_week_plan(
        schedule=edited_schedule,
        monday=st.session_state.monday,
        min_sleep_hours=min_sleep,
        class_length_minutes=class_length,
        default_wake=default_wake,
    )
    st.session_state.plan = plan
    st.session_state.alerts = alerts
    st.session_state.whatsapp_message = create_whatsapp_message(plan, st.session_state.monday)
    st.session_state.whatsapp_output = st.session_state.whatsapp_message

if "plan" in st.session_state:
    plan: pd.DataFrame = st.session_state.plan
    alerts: list[str] = st.session_state.alerts

    st.divider()
    st.subheader("2. הלו״ז המוצע")
    st.caption("זהו מנוע חוקים התחלתי. הוא נועד להמחיש זרימה ולחשוף התנגשויות; תמיד בדוק את הזמנים לפני שליחה לעוזרת.")

    if alerts:
        with st.expander(f"התראות ותקלות אפשריות ({len(alerts)})", expanded=True):
            for alert in alerts:
                st.warning(alert)
    else:
        st.success("לא נמצאו התנגשויות אוטומטיות בתכנון הבסיסי.")

    display_plan = plan[["יום", "שעה", "אירוע", "סוג"]].copy()
    st.dataframe(display_plan, use_container_width=True, hide_index=True)

    category_counts = plan[plan["סוג"].isin(["אימון", "שיעור", "צבא"])]["סוג"].value_counts()
    metric_columns = st.columns(3)
    metric_columns[0].metric("אימונים שתוכננו", int(category_counts.get("אימון", 0)))
    metric_columns[1].metric("שיעורי קבלה", int(category_counts.get("שיעור", 0)))
    metric_columns[2].metric("ימי צבא", int((edited_schedule["תחילת צבא"].astype(str).str.strip() != "").sum()))

    st.divider()
    st.subheader("3. הודעה מוכנה להעתקה לעוזרת האישית")
    st.text_area(
        "העתק את ההודעה ושלח אותה בווטסאפ",
        value=st.session_state.whatsapp_message,
        height=420,
        key="whatsapp_output",
    )
    st.download_button(
        "הורד את הלו״ז כ־CSV",
        data=create_csv(plan),
        file_name=f"schedule_{st.session_state.monday.strftime('%Y_%m_%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with st.expander("איך מנוע התכנון עובד באבטיפוס הזה?"):
    st.markdown(
        """
        האפליקציה מתייחסת לשעות הצבא ולשיעור הקבלה כאילוצים עיקריים. יום עם שיעור מוקדם מתוכנן סביב שגרת שינה מוקדמת; יום ללא שיעור מקבל השכמה מאוחרת יותר ושיבוץ אימונים אחר. היא מסמנת חפיפות במקום להסתיר אותן.

        בגרסה הבאה אפשר להוסיף קליטת צילום מסך עם OCR, עריכת אירועים באמצעות גרירה, העדפות אוכל מפורטות, זמן עבודה עם אבא, וחיבור ישיר ליומן לאחר שתאשר שההצעות מדויקות.
        """
    )
