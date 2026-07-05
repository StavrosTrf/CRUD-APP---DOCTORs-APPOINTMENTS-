"""Σύνδεση των επιπέδων (composition root) και αρχικά δεδομένα.

Το AppContext δημιουργεί τη βάση, τα repositories (Data Access Layer) και τους
controllers (Business Logic Layer). Χρησιμοποιείται τόσο από την εφαρμογή
(main.py) όσο και από τα unit tests, ώστε να δοκιμάζεται το ίδιο wiring.
"""
from __future__ import annotations

from .model.database import Database
from .model.user_repository import UserRepository
from .model.patient_repository import PatientRepository
from .model.appointment_repository import AppointmentRepository
from .model.medical_record_repository import MedicalRecordRepository
from .model.entities import ROLE_DOCTOR, ROLE_SECRETARY, ROLE_PATIENT
from .controller.auth_controller import AuthController
from .controller.patient_controller import PatientController
from .controller.appointment_controller import AppointmentController
from .controller.medical_record_controller import MedicalRecordController
from .util.security import generate_amka


class AppContext:
    def __init__(self, db_path: str = "iatreio.db") -> None:
        self.db = Database(db_path)

        # --- Data Access Layer ---
        self.user_repo = UserRepository(self.db)
        self.patient_repo = PatientRepository(self.db)
        self.appt_repo = AppointmentRepository(self.db)
        self.record_repo = MedicalRecordRepository(self.db)

        # --- Business Logic Layer ---
        self.auth = AuthController(self.user_repo)
        self.patients = PatientController(self.patient_repo)
        self.appointments = AppointmentController(
            self.appt_repo, self.patient_repo, self.user_repo
        )
        self.records = MedicalRecordController(self.record_repo, self.appt_repo)

    def is_empty(self) -> bool:
        cur = self.db.cursor()
        cur.execute("SELECT COUNT(*) AS c FROM users")
        return cur.fetchone()["c"] == 0

    def seed_demo_data(self) -> None:
        """Δημιουργεί ενδεικτικούς λογαριασμούς και δεδομένα επίδειξης."""
        # Λογαριασμοί (κωδικός για όλους: 1234)
        self.auth.register_user("doctor", "1234", ROLE_DOCTOR,
                                full_name="Δρ. Ιωάννης Παπαδόπουλος")
        self.auth.register_user("doctor2", "1234", ROLE_DOCTOR,
                                full_name="Δρ. Μαρία Γεωργίου")
        self.auth.register_user("secretary", "1234", ROLE_SECRETARY,
                                full_name="Ελένη Γραμματίδου")

        # Ασθενείς με έγκυρους (Luhn) ΑΜΚΑ
        p1 = self.patients.create_patient(
            amka=generate_amka("150385", "1234"),
            first_name="Νικόλαος", last_name="Αντωνίου",
            phone="6900000001", email="nikos@example.com",
            date_of_birth="1985-03-15", gdpr_consent=True,
        )
        p2 = self.patients.create_patient(
            amka=generate_amka("220790", "5678"),
            first_name="Σοφία", last_name="Δημητρίου",
            phone="6900000002", email="sofia@example.com",
            date_of_birth="1990-07-22", gdpr_consent=True,
        )

        # Λογαριασμός ασθενούς συνδεδεμένος με φάκελο
        self.auth.register_user("patient", "1234", ROLE_PATIENT,
                                full_name="Νικόλαος Αντωνίου",
                                patient_id=p1.id)

        # Ένα ραντεβού επίδειξης
        doctor = self.user_repo.get_by_username("doctor")
        self.appointments.book_appointment(
            patient_id=p1.id, doctor_id=doctor.id,
            category="Παθολόγος", scheduled_at="2026-06-15 10:00",
            notes="Ετήσιος έλεγχος",
        )
        # δεύτερος ασθενής χωρίς ραντεβού — για να φαίνεται η αναζήτηση
        _ = p2

    def close(self) -> None:
        self.db.close()
