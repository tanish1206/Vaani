"""
Parchi (Prescription & Medicine Reminders) Service Layer.
Enforces verbatim medicine names, smart meal-slot scheduling,
and strict medical safety disclaimers.
"""

from datetime import date, datetime, timedelta, timezone
import json
from typing import Any, Dict, List, Optional

from app.core.i18n import render_template
from app.db.session import get_db

TIME_SLOT_HOURS = {
    "morning": "08:00",
    "afternoon": "13:30",
    "evening": "19:30",
    "night": "21:30",
}

_SLOT_LABELS = {
    "hi": {"morning": "सुबह", "afternoon": "दोपहर", "evening": "शाम", "night": "रात"},
    "mr": {"morning": "सकाळी", "afternoon": "दुपारी", "evening": "संध्याकाळी", "night": "रात्री"},
    "hinglish": {"morning": "subah", "afternoon": "dopahar", "evening": "shaam", "night": "raat"},
}


def _format_schedule_text(first_med: Dict[str, Any], days: int, lang: str) -> str:
    """Format a localized human-readable schedule summary for spoken replies."""
    time_suffix = "बजे" if lang == "hi" else ("वाजता" if lang == "mr" else "baje")
    day_suffix = "दिन" if lang == "hi" else ("दिवस" if lang == "mr" else "din")
    custom_time = first_med.get("time_str")

    if custom_time:
        return f"{custom_time} {time_suffix}, {days} {day_suffix}"

    times = first_med.get("times_of_day", [])
    if len(times) > 2:
        times_summary = (
            "दिन में तीन बार" if lang == "hi" else ("दिवसातून तीन वेळा" if lang == "mr" else "din mein teen baar")
        )
    elif len(times) == 1:
        slot = times[0]
        lang_map = _SLOT_LABELS.get(lang, _SLOT_LABELS["hinglish"])
        times_summary = lang_map.get(slot, slot)
    else:
        times_summary = (
            "सुबह और शाम" if lang == "hi" else ("सकाळी आणि संध्याकाळी" if lang == "mr" else "subah aur shaam")
        )

    food = first_med.get("with_food")
    food_note = ""
    if food == "after":
        food_note = ", खाने के बाद" if lang == "hi" else (", जेवणानंतर" if lang == "mr" else ", khaane ke baad")
    elif food == "before":
        food_note = ", खाने से पहले" if lang == "hi" else (", जेवणापूर्वी" if lang == "mr" else ", khaane se pehle")

    return f"{times_summary}{food_note}, {days} {day_suffix}"


def _format_patient_prefix(patient_label: Optional[str], lang: str) -> str:
    """Format localized patient prefix only when a real patient label was provided."""
    if not patient_label or not patient_label.strip():
        return ""
    if patient_label.lower() in ("none", "null", "mere liye", "self"):
        return ""
    if lang == "hi":
        return f"{patient_label} के लिए "
    if lang == "mr":
        return f"{patient_label} यांच्यासाठी "
    if lang == "en":
        return f"for {patient_label}: "
    return f"{patient_label} ke liye "


class ParchiService:
    @staticmethod
    def save_prescription(
        patient_label: Optional[str],
        medicines: List[Dict[str, Any]],
        doctor_note: Optional[str] = None,
        duration_days: Optional[int] = 5,
        utterance_id: Optional[str] = None,
        lang: str = "hinglish",
    ) -> Dict[str, Any]:
        """Save prescription and schedule daily medicine reminders."""
        now = datetime.now(timezone.utc)
        today_str = date.today().isoformat()
        days = duration_days or 5
        db_patient = patient_label.strip() if (patient_label and patient_label.strip()) else "Self"

        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO prescriptions (patient_label, doctor_note, start_date, duration_days, status, utterance_id, created_at)
                VALUES (?, ?, ?, ?, 'active', ?, ?);
                """,
                (db_patient, doctor_note, today_str, days, utterance_id, now.isoformat()),
            )
            presc_id = cur.lastrowid

            total_reminders = 0
            med_names: List[str] = []

            for med in medicines:
                name = med.get("name", "Dawa")
                med_names.append(name)
                dose_text = med.get("dose_text")
                with_food = med.get("with_food")
                times = med.get("times_of_day", ["morning", "evening"])
                time_str_override = med.get("time_str")

                cur.execute(
                    """
                    INSERT INTO medicines (prescription_id, name, dose_text, with_food, times_json)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (presc_id, name, dose_text, with_food, json.dumps(times)),
                )
                med_id = cur.lastrowid

                for day_offset in range(days):
                    rem_date = date.today() + timedelta(days=day_offset)
                    for slot in times:
                        time_str = time_str_override or TIME_SLOT_HOURS.get(slot, "08:00")
                        due_iso = f"{rem_date.isoformat()}T{time_str}:00Z"
                        cur.execute(
                            "INSERT INTO reminders (medicine_id, due_at, status) VALUES (?, ?, 'pending');",
                            (med_id, due_iso),
                        )
                        total_reminders += 1

        first_med = medicines[0] if medicines else {}
        schedule_text = _format_schedule_text(first_med, days, lang)
        patient_prefix = _format_patient_prefix(patient_label, lang)

        reply = render_template(
            "save_prescription",
            lang=lang,
            patient_prefix=patient_prefix,
            patient_label=patient_label or "",
            med_name=", ".join(med_names),
            schedule=schedule_text,
        )

        return {
            "prescription_id": presc_id,
            "patient_label": patient_label,
            "medicines": medicines,
            "duration_days": days,
            "reminders_count": total_reminders,
            "reply_text": reply,
        }

    @staticmethod
    def list_doses() -> Dict[str, Any]:
        """Fetch active doses and reminders for today."""
        today_prefix = date.today().isoformat()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.id, r.due_at, r.status, m.name, m.dose_text, m.with_food, p.patient_label, p.duration_days
                FROM reminders r
                JOIN medicines m ON m.id = r.medicine_id
                JOIN prescriptions p ON p.id = m.prescription_id
                WHERE r.due_at LIKE ? AND p.status = 'active'
                ORDER BY r.due_at ASC;
                """,
                (f"{today_prefix}%",),
            )
            doses = [dict(row) for row in cur.fetchall()]

        if not doses:
            return {"doses": [], "reply_text": "Aaj ke liye koi dawa baaki nahi hai."}

        first_med = doses[0]
        reply = f"Aaj kul {len(doses)} dawa lene ka waqt hai. Sabse pehle {first_med['patient_label']} ki {first_med['name']} hai."
        return {"doses": doses, "reply_text": reply}

    @staticmethod
    def mark_dose_done(medicine_name: Optional[str] = None, dose_id: Optional[int] = None) -> Dict[str, Any]:
        """Mark specific reminder or earliest pending reminder as completed."""
        now = datetime.now(timezone.utc).isoformat()
        with get_db() as conn:
            cur = conn.cursor()
            if dose_id:
                cur.execute(
                    """
                    SELECT r.id, m.name, p.patient_label
                    FROM reminders r
                    JOIN medicines m ON m.id = r.medicine_id
                    JOIN prescriptions p ON p.id = m.prescription_id
                    WHERE r.id = ?;
                    """,
                    (dose_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT r.id, m.name, p.patient_label
                    FROM reminders r
                    JOIN medicines m ON m.id = r.medicine_id
                    JOIN prescriptions p ON p.id = m.prescription_id
                    WHERE r.status = 'pending'
                    ORDER BY r.due_at ASC
                    LIMIT 1;
                    """
                )
            row = cur.fetchone()
            if not row:
                return {"reply_text": "Koi pending dawa nahi mili."}

            rem_id = row["id"]
            med_name = row["name"]
            cur.execute("UPDATE reminders SET status = 'done', done_at = ? WHERE id = ?;", (now, rem_id))

        return {
            "status": "done",
            "reminder_id": rem_id,
            "medicine": med_name,
            "reply_text": f"{row['patient_label']} ki {med_name} lene ki pushti ho gayi hai.",
        }

    @staticmethod
    def snooze_dose(minutes: int = 10) -> Dict[str, Any]:
        """Snooze pending reminder for specified minutes."""
        snooze_until = (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE reminders
                SET status = 'snoozed', snoozed_until = ?
                WHERE id = (SELECT id FROM reminders WHERE status = 'pending' ORDER BY due_at ASC LIMIT 1);
                """,
                (snooze_until,),
            )

        return {
            "snoozed": True,
            "minutes": minutes,
            "reply_text": f"{minutes} minute ke liye reminder aage badha diya gaya hai.",
        }
