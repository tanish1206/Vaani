"""
Parchi (Prescription & Medicine Reminders) Service Layer.
Enforces verbatim medicine names, smart meal-slot scheduling,
and strict medical safety disclaimers.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta, timezone
import json

from app.db.session import get_db
from app.core.i18n import render_template

TIME_SLOT_HOURS = {
    "morning": "08:00",
    "afternoon": "13:30",
    "evening": "19:30",
    "night": "21:30"
}

class ParchiService:
    @staticmethod
    def save_prescription(patient_label: str, medicines: List[Dict[str, Any]],
                          doctor_note: Optional[str] = None, duration_days: Optional[int] = 5,
                          utterance_id: Optional[str] = None, lang: str = "hinglish") -> Dict[str, Any]:
        """Save prescription and schedule daily medicine reminders."""
        now = datetime.now(timezone.utc)
        today_str = date.today().isoformat()
        days = duration_days or 5

        with get_db() as conn:
            cur = conn.cursor()
            
            # 1. Insert Prescription
            cur.execute(
                """
                INSERT INTO prescriptions (patient_label, doctor_note, start_date, duration_days, status, utterance_id, created_at)
                VALUES (?, ?, ?, ?, 'active', ?, ?);
                """,
                (patient_label, doctor_note, today_str, days, utterance_id, now.isoformat())
            )
            presc_id = cur.lastrowid

            # 2. Insert Medicines & Generate Reminders
            total_reminders = 0
            med_names = []

            for med in medicines:
                name = med.get("name", "Dawa")
                med_names.append(name)
                dose_text = med.get("dose_text")
                with_food = med.get("with_food")
                times = med.get("times_of_day", ["morning", "evening"])

                cur.execute(
                    """
                    INSERT INTO medicines (prescription_id, name, dose_text, with_food, times_json)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (presc_id, name, dose_text, with_food, json.dumps(times))
                )
                med_id = cur.lastrowid

                # Generate reminder timestamps for each day
                for day_offset in range(days):
                    rem_date = date.today() + timedelta(days=day_offset)
                    for slot in times:
                        time_str = TIME_SLOT_HOURS.get(slot, "08:00")
                        due_iso = f"{rem_date.isoformat()}T{time_str}:00Z"
                        cur.execute(
                            """
                            INSERT INTO reminders (medicine_id, due_at, status)
                            VALUES (?, ?, 'pending');
                            """,
                            (med_id, due_iso)
                        )
                        total_reminders += 1

        med_summary = ", ".join(med_names)
        times_summary = "subah aur shaam"
        if len(medicines) > 0 and len(medicines[0].get("times_of_day", [])) > 2:
            times_summary = "din mein teen baar"

        food_note = ", khaane ke baad" if medicines and medicines[0].get("with_food") == "after" else ""
        schedule_text = f"{times_summary}{food_note}, {days} din"

        reply = render_template(
            "save_prescription",
            lang=lang,
            patient_label=patient_label,
            med_name=med_summary,
            schedule=schedule_text
        )

        return {
            "prescription_id": presc_id,
            "patient_label": patient_label,
            "medicines": medicines,
            "duration_days": days,
            "reminders_count": total_reminders,
            "reply_text": reply
        }

    @staticmethod
    def list_doses() -> Dict[str, Any]:
        """Fetch active doses and reminders for today."""
        today_prefix = date.today().isoformat()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT r.id, r.due_at, r.status, m.name, m.dose_text, m.with_food, p.patient_label
                FROM reminders r
                JOIN medicines m ON m.id = r.medicine_id
                JOIN prescriptions p ON p.id = m.prescription_id
                WHERE r.due_at LIKE ? AND p.status = 'active'
                ORDER BY r.due_at ASC;
                """,
                (f"{today_prefix}%",)
            )
            doses = [dict(row) for row in cur.fetchall()]

        if not doses:
            return {"doses": [], "reply_text": "Aaj ke liye koi dawa baaki nahi hai."}

        count = len(doses)
        first_med = doses[0]
        reply = f"Aaj kul {count} dawa lene ka waqt hai. Sabse pehle {first_med['patient_label']} ki {first_med['name']} hai."
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
                    (dose_id,)
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

        reply = f"{row['patient_label']} ki {med_name} lene ki pushti ho gayi hai."
        return {"status": "done", "reminder_id": rem_id, "medicine": med_name, "reply_text": reply}

        reply = f"{med_name} lene ka hisaab darj ho gaya. Badhiya!"
        return {"marked_done": True, "medicine_name": med_name, "reply_text": reply}

    @staticmethod
    def snooze_dose(minutes: int = 10) -> Dict[str, Any]:
        """Snooze pending reminder for specified minutes."""
        now = datetime.now(timezone.utc)
        snooze_until = (now + timedelta(minutes=minutes)).isoformat()
        with get_db() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE reminders 
                SET status = 'snoozed', snoozed_until = ? 
                WHERE id = (SELECT id FROM reminders WHERE status = 'pending' ORDER BY due_at ASC LIMIT 1);
                """,
                (snooze_until,)
            )

        reply = f"{minutes} minute ke liye reminder aage badha diya gaya hai."
        return {"snoozed": True, "minutes": minutes, "reply_text": reply}

