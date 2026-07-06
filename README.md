# Εφαρμογή Διαχείρισης Ιατρείου — Ομάδα 4

Desktop CRUD εφαρμογή τριών επιπέδων, αρχιτεκτονικής **Model–View–Controller**,
υλοποιημένη σε **Python + Tkinter** με βάση δεδομένων **SQLite3**.
Βασίζεται στο SRS «Εφαρμογή Διαχείρισης Ιατρείου» (Πανεπιστήμιο Δυτικής Αττικής,
Τεχνολογία Λογισμικού).

Δεν χρησιμοποιεί τεχνολογίες web ή client–server / Electron — είναι αυτόνομη
native desktop εφαρμογή, όπως απαιτείται.

---

## 1. Γρήγορη εκκίνηση

Απαιτείται Python 3.10+ με την Tkinter (στα Windows περιλαμβάνεται· σε Linux:
`sudo apt install python3-tk`).

```bash
# Εκτέλεση εφαρμογής
python main.py

# Εκτέλεση unit tests
pip install pytest
python -m pytest
```

Στην πρώτη εκτέλεση δημιουργείται αυτόματα το αρχείο `iatreio.db` με
δοκιμαστικά δεδομένα.

### Δοκιμαστικοί λογαριασμοί (κωδικός για όλους: `1234`)

| Username    | Ρόλος       | Καρτέλες                                   |
|-------------|-------------|--------------------------------------------|
| `doctor`    | Ιατρός      | Ασθενείς (read), Ραντεβού, Ιατρικός Φάκελος |
| `secretary` | Γραμματεία  | Ασθενείς (CRUD), Ραντεβού (+check-in), Φάκελος |
| `patient`   | Ασθενής     | Ραντεβού (δικά του)                         |

---

## 2. Αρχιτεκτονική (3 επίπεδα / MVC)

```
┌─────────────────────────────────────────────┐
│  Presentation Layer  →  iatreio/view/        │  (Tkinter — View)
│  login_view, main_window, patient_view,      │
│  appointment_view, medical_record_view       │
├─────────────────────────────────────────────┤
│  Business Logic Layer → iatreio/controller/  │  (Controller)
│  auth, patient, appointment, medical_record  │
│  + validators + exceptions                   │
├─────────────────────────────────────────────┤
│  Data Access Layer   →  iatreio/model/       │  (Model)
│  database (SQLite3) + entities + repositories│
└─────────────────────────────────────────────┘
```

- **Model**: οντότητες (`entities.py`) + repositories (DAO) που εκτελούν καθαρό
  SQL πάνω στην SQLite3. Καμία γνώση UI.
- **Controller**: επιχειρησιακοί κανόνες & επικύρωση. Δεν εισάγει `tkinter` ούτε
  `sqlite3` απευθείας — μιλάει στο Model μέσω των repositories.
- **View**: Tkinter widgets. Δεν αγγίζει τη βάση· καλεί μόνο controllers και
  εμφανίζει αποτελέσματα/σφάλματα.
- Το `app_context.py` είναι το *composition root* που συνδέει τα τρία επίπεδα και
  χρησιμοποιείται τόσο από την εφαρμογή όσο και από τα tests.

```
iatreio_app/
├── main.py                  # σημείο εισόδου (ροή Login→Dashboard)
├── pytest.ini
├── requirements.txt
├── iatreio/
│   ├── app_context.py       # wiring + seed δεδομένων
│   ├── util/security.py     # PBKDF2 hashing + έλεγχος ΑΜΚΑ (Luhn)
│   ├── model/               # ── Data Access Layer ──
│   │   ├── database.py, entities.py
│   │   └── *_repository.py
│   ├── controller/          # ── Business Logic Layer ──
│   │   ├── exceptions.py, validators.py
│   │   └── *_controller.py
│   └── view/                # ── Presentation Layer (Tkinter) ──
└── tests/                   # 49 unit tests (pytest)
```

---

## 3. Υλοποιημένες λειτουργίες (επιλογή από το SRS)

Σύμφωνα με την εκφώνηση υλοποιούνται 4 βασικές λειτουργικές ομάδες σε μικρή
κλίμακα, η καθεμία με πλήρη κύκλο **CRUD** όπου έχει νόημα:

| Λειτουργική ομάδα            | Use Cases SRS              | Τι καλύπτεται                                            |
|------------------------------|----------------------------|---------------------------------------------------------|
| Αυθεντικοποίηση              | UC001, UC002               | Login/Logout, hashing κωδικών, κλείδωμα μετά 5 αποτυχίες (§4.2) |
| Διαχείριση Ασθενών           | (σχετ. UC009, UC011), GDPR UC010 | Create/Read/Update/Delete, επικύρωση ΑΜΚΑ & email, GDPR consent |
| Διαχείριση Ραντεβού          | UC003, UC004, UC005, UC006, UC008 | Κράτηση, λίστα, επαναπρογραμματισμός, check-in, ακύρωση/διαγραφή, έλεγχος double-booking & ωραρίου |
| Ιατρικός Φάκελος & Συνταγή   | UC011, UC012, UC013        | Προβολή ιστορικού, καταχώρηση διάγνωσης & αγωγής         |

### Επιχειρησιακοί κανόνες που επιβάλλονται
- ΑΜΚΑ: 11 ψηφία με έγκυρο ψηφίο ελέγχου (αλγόριθμος Luhn).
- Δεν επιτρέπεται κράτηση χωρίς συγκατάθεση GDPR του ασθενούς.
- Δεν επιτρέπεται double-booking: ο ιατρός δεν μπορεί να έχει δύο ενεργά
  ραντεβού στην ίδια ώρα (διαθεσιμότητα — UC005).
- Τα ραντεβού περιορίζονται εντός ωραρίου λειτουργίας (09:00–21:00).
- Check-in μόνο σε προγραμματισμένο ραντεβού· καταχώρηση φακέλου μόνο μετά το
  check-in (το ραντεβού ολοκληρώνεται αυτόματα).
- Κωδικοί αποθηκεύονται ως PBKDF2-HMAC-SHA256 hash με μοναδικό salt (§4.2).

---

## 4. Δοκιμές (Unit Tests)

49 tests με `pytest`, που καλύπτουν το επίπεδο Model + Controller (επιχειρησιακή
λογική και πρόσβαση δεδομένων) χωρίς εξάρτηση από το GUI. Κάθε test τρέχει σε
καθαρή βάση SQLite στη μνήμη (`:memory:`).

```bash
python -m pytest <onoma_arxeiou_unittest>            # αναλυτικά
python -m pytest <onoma_arxeiou_unittest>  -q        # σύντομα
```

Κατανομή:
- `test_security.py` — hashing & επικύρωση ΑΜΚΑ (8)
- `test_auth_controller.py` — login/logout/κλείδωμα (8)
- `test_patient_controller.py` — CRUD & επικυρώσεις ασθενών (11)
- `test_appointment_controller.py` — κράτηση/conflicts/check-in/ακύρωση (15)
- `test_medical_record_controller.py` — ιστορικό & συνταγή (7)

---

## 5. Σημειώσεις

- Οι διασυνδέσεις με εξωτερικά συστήματα του SRS (ΗΔΙΚΑ/ΕΟΠΥΥ, SMTP/SMS, POS)
  δεν υλοποιούνται — βρίσκονται εκτός του ζητούμενου εύρους «μικρής κλίμακας».
- Η βάση `iatreio.db` δημιουργείται στον τρέχοντα φάκελο. Διαγράφοντάς την,
  δημιουργείται εκ νέου με τα δοκιμαστικά δεδομένα.
