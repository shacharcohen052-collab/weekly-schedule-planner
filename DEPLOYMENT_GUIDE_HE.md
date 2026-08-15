# מדריך פעולה: פרסום מתכנן השבוע שלך

## המטרה

המדריך הזה מפרסם את אפליקציית ה־Streamlit שכבר נבנתה עבורך באינטרנט. המסלול המומלץ הוא **GitHub → Streamlit Community Cloud**. GitHub ישמור את הקוד שלך וינהל גרסאות; Streamlit Community Cloud יריץ את `app.py` וייתן לך קישור לאפליקציה. למסלול הנוכחי **אין צורך ב־Vercel**.

> האפליקציה עדיין אינה מתחברת לווטסאפ או ליומן. היא מייצרת הודעה מוכנה להעתקה, ואתה שולח אותה ידנית לעוזרת האישית.

## מה יש בפרויקט

| קובץ | תפקיד |
|---|---|
| `app.py` | קוד הממשק ומנוע התכנון. זהו קובץ הכניסה לפריסה. |
| `requirements.txt` | רשימת ספריות ה־Python שהשרת יתקין. |
| `.gitignore` | מונע העלאה של קבצים מקומיים, סודות ולוחות זמנים פרטיים. |
| `README.md` | תיאור בסיסי והוראות הרצה מקומיות. |
| `sample_army_schedule.csv` | קובץ דוגמה בלבד, שאפשר להשאיר או למחוק. |

האפליקציה תומכת כרגע בהעלאת **CSV או Excel**. העלאת תמונה או PDF של לו״ז צבאי עדיין אינה ממירה את הלו״ז אוטומטית; זהו שיפור עתידי באמצעות OCR.

## שלב 1 — שמירת קבצי הפרויקט במחשב

הורד את הקובץ `weekly_schedule_planner.zip` שקיבלת, חלץ אותו לתיקייה במחשב שלך, וודא שבתוך התיקייה נמצאים לפחות `app.py`, `requirements.txt`, `README.md` ו־`.gitignore`. אל תוסיף לתיקיית הפרויקט לוחות זמנים צבאיים אמיתיים או מידע אישי; האפליקציה עצמה מאפשרת הזנה ידנית בכל הפעלה.

אם תרצה לבדוק את הקוד במחשב לפני פרסום, פתח מסוף בתוך התיקייה והריץ את הפקודות הבאות:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## שלב 2 — יצירת מאגר פרטי ב־GitHub

היכנס אל [GitHub](https://github.com) וצור חשבון אם אין לך. לחץ על סימן `+` בפינה העליונה ובחר **New repository**. תן למאגר שם כגון `weekly-schedule-planner`, סמן אותו כ־**Private**, והשאר את האפשרויות ליצירת README או `.gitignore` כבויות — הם כבר נמצאים בפרויקט. לאחר מכן לחץ **Create repository**.

הגדרת המאגר כפרטי מומלצת, משום שהפרויקט עוסק בשגרה אישית ועלול בעתיד להכיל נתונים רגישים. גם במאגר פרטי, אל תעלה קובצי לו״ז אמיתיים, סיסמאות, מפתחות API או פרטים צבאיים שאינם הכרחיים.

## שלב 3 — העלאת הקוד ל־GitHub

### הדרך הפשוטה: העלאה בדפדפן

בדף המאגר החדש ב־GitHub בחר **uploading an existing file** או **Add file → Upload files**. גרור אל הדף את הקבצים הבאים מתיקיית הפרויקט: `app.py`, `requirements.txt`, `README.md`, `.gitignore` ו־`sample_army_schedule.csv` אם ברצונך להשאיר קובץ דוגמה. בתחתית הדף כתוב הודעת commit כגון `גרסה ראשונה של מתכנן השבוע` ולחץ **Commit changes**.

### הדרך למי שמשתמש במסוף

פתח מסוף בתיקייה שבה חילצת את הפרויקט. החלף את `YOUR_USERNAME` בשם המשתמש שלך ב־GitHub ואת שם המאגר אם בחרת שם אחר.

```bash
git init
git add app.py requirements.txt README.md .gitignore sample_army_schedule.csv
git commit -m "Initial Streamlit schedule planner"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/weekly-schedule-planner.git
git push -u origin main
```

אם Git מבקש ממך לזהות את עצמך לפני ה־commit, הגדר פעם אחת את השם והאימייל שלך:

```bash
git config --global user.name "השם שלך"
git config --global user.email "your-email@example.com"
```

## שלב 4 — פריסה ב־Streamlit Community Cloud

פתח את [Streamlit Community Cloud](https://share.streamlit.io/) והתחבר באמצעות חשבון GitHub. בחלל העבודה לחץ **Create app**. Streamlit מציינת שבמסך זה בוחרים את המאגר, את הענף ואת קובץ האפליקציה, ואז לוחצים **Deploy** [1].

מלא את השדות כך:

| שדה במסך הפריסה | מה לבחור |
|---|---|
| Repository | `YOUR_USERNAME/weekly-schedule-planner` |
| Branch | `main` |
| Main file path | `app.py` |
| App URL (אופציונלי) | שם קצר כמו `weekly-schedule-planner` |

לחץ **Deploy** והמתן עד שהבנייה מסתיימת. מכיוון ש־`requirements.txt` נמצא בתיקייה הראשית לצד `app.py`, סביבת הפריסה תזהה אותו ותתקין את הספריות הדרושות [2]. כאשר הפריסה מצליחה, תקבל כתובת אינטרנט קבועה לאפליקציה.

## שלב 5 — בדיקה לפני שימוש

פתח את הקישור שקיבלת ובדוק את הפעולות הבאות: הזן יום צבא בוקר ויום צבא צהריים, בחר שיעור קבלה ביום אחד, לחץ **בנה לו״ז שבועי**, ובדוק שההתראות וההודעה להעתקה מופיעות. תוכל להעלות את `sample_army_schedule.csv` כדי לראות תרחיש דוגמה.

אם מתקבלת שגיאת בנייה, פתח את לוגי הפריסה ב־Streamlit. הסיבה הנפוצה היא שם קובץ שגוי או תלות חסרה. ודא ש־`requirements.txt` נמצא בשורש המאגר או לצד `app.py`, כפי שמנחה התיעוד הרשמי [2].

## שלב 6 — עדכון האפליקציה בעתיד

כל שינוי בקוד מתבצע בתיקייה המקומית ואז נשלח ל־GitHub. Streamlit Community Cloud מפרסמת שעדכון באמצעות `git push` גורם לאפליקציה להתעדכן אוטומטית [3]. לדוגמה:

```bash
git add app.py
git commit -m "שיפור מנוע התכנון"
git push
```

לאחר כמה רגעים רענן את הקישור של האפליקציה כדי לראות את השינוי.

## כללי פרטיות ואבטחה

אין בפרויקט הנוכחי סודות או מפתחות API, ולכן אין צורך להגדיר Secrets. אם בעתיד תחבר Google Calendar, API או מערכת הודעות, אל תכתוב סיסמאות בתוך `app.py` ואל תעלה אותן ל־GitHub. השתמש במנגנון secrets של שירות הפריסה. אין להעלות ל־GitHub צילומים, קבצים או פרטים מבצעיים; הזן רק שעות כלליות שהאפליקציה באמת צריכה לתכנון.

## הצעד הבא המומלץ

אחרי שהקישור החי עובד, השתמש בו שבוע אחד עם הזנה ידנית והודעת הווטסאפ המוכנה. אחר כך יהיה נכון להוסיף שלושה מצבי יום — **רגיל**, **צפוף** ו־**התאוששות** — לפני שמוסיפים OCR או חיבור ליומן.

## מקורות

[1]: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app "Streamlit Docs — Prep and deploy your app on Community Cloud"
[2]: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies "Streamlit Docs — App dependencies for Community Cloud"
[3]: https://streamlit.io/cloud "Streamlit Community Cloud"
