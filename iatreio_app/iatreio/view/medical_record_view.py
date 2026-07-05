"""Επίπεδο παρουσίασης — Ιατρικός Φάκελος (UC011/UC012/UC013).

Επιλογή ασθενούς -> προβολή ιστορικού. Ο Ιατρός μπορεί να καταχωρήσει νέα
εγγραφή επιλέγοντας ένα ραντεβού που έχει κάνει check-in.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from ..controller.exceptions import AppError
from ..model.entities import ROLE_DOCTOR, STATUS_CHECKED_IN


class MedicalRecordView(ttk.Frame):
    def __init__(self, master, ctx, role, current_user):
        super().__init__(master, padding=10)
        self.ctx = ctx
        self.role = role
        self.user = current_user
        self.can_write = (role == ROLE_DOCTOR)
        self.patient = None
        self._build()
        self._load_patients()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Ασθενής:").pack(side="left")
        self.patient_cb = ttk.Combobox(top, width=34, state="readonly")
        self.patient_cb.pack(side="left", padx=5)
        self.patient_cb.bind("<<ComboboxSelected>>",
                             lambda e: self.load_history())

        # --- Ιστορικό ---
        cols = ("when", "doctor", "diagnosis", "prescription")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=8)
        for c, t, w in [("when", "Ημ/νία", 120), ("doctor", "Ιατρός", 150),
                        ("diagnosis", "Διάγνωση", 220),
                        ("prescription", "Αγωγή", 220)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True)

        # --- Φόρμα καταχώρησης (μόνο Ιατρός) ---
        if self.can_write:
            form = ttk.LabelFrame(self, text="Νέα Εγγραφή Φακέλου", padding=10)
            form.pack(fill="x", pady=8)

            ttk.Label(form, text="Ραντεβού (Check-in):").grid(
                row=0, column=0, sticky="e")
            self.appt_cb = ttk.Combobox(form, width=40, state="readonly")
            self.appt_cb.grid(row=0, column=1, columnspan=3, padx=4, pady=3)

            self.symptoms = self._text_field(form, "Συμπτώματα:", 1)
            self.diagnosis = self._text_field(form, "Διάγνωση:", 2)
            self.observations = self._text_field(form, "Παρατηρήσεις:", 3)
            self.prescription = self._text_field(form, "Συνταγή/Αγωγή:", 4)

            ttk.Button(form, text="Καταχώρηση", command=self.add_record).grid(
                row=5, column=0, columnspan=4, pady=6)
        else:
            ttk.Label(self, text="(Προβολή μόνο)",
                      foreground="#888").pack(anchor="w")

    def _text_field(self, parent, label, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="ne",
                                           padx=4, pady=3)
        txt = tk.Text(parent, width=50, height=2)
        txt.grid(row=row, column=1, columnspan=3, padx=4, pady=3)
        return txt

    # --- Δεδομένα ---
    def _load_patients(self):
        self._patients = self.ctx.patients.list_patients()
        self.patient_cb["values"] = [
            f"{p.last_name} {p.first_name} ({p.amka})" for p in self._patients]
        if self._patients:
            self.patient_cb.current(0)
            self.load_history()

    def load_history(self):
        idx = self.patient_cb.current()
        if idx < 0:
            return
        self.patient = self._patients[idx]
        for row in self.tree.get_children():
            self.tree.delete(row)
        for r in self.ctx.records.get_history(self.patient.id):
            self.tree.insert("", "end", values=(
                r.created_at, r.doctor_name, r.diagnosis, r.prescription))
        if self.can_write:
            self._load_checked_in_appts()

    def _load_checked_in_appts(self):
        appts = self.ctx.appointments.list_for_patient(self.patient.id)
        self._open_appts = [a for a in appts if a.status == STATUS_CHECKED_IN]
        self.appt_cb["values"] = [
            f"#{a.id} · {a.scheduled_at} · {a.category}"
            for a in self._open_appts]
        if self._open_appts:
            self.appt_cb.current(0)
        else:
            self.appt_cb.set("")

    def add_record(self):
        if not getattr(self, "_open_appts", None) or self.appt_cb.current() < 0:
            messagebox.showwarning(
                "Προσοχή",
                "Δεν υπάρχει ραντεβού σε κατάσταση check-in για τον ασθενή.")
            return
        appt = self._open_appts[self.appt_cb.current()]
        try:
            self.ctx.records.add_record(
                doctor_id=self.user.id,
                appointment_id=appt.id,
                symptoms=self.symptoms.get("1.0", "end").strip(),
                diagnosis=self.diagnosis.get("1.0", "end").strip(),
                observations=self.observations.get("1.0", "end").strip(),
                prescription=self.prescription.get("1.0", "end").strip())
        except AppError as exc:
            messagebox.showerror("Σφάλμα", str(exc))
            return
        messagebox.showinfo("Επιτυχία", "Η εγγραφή καταχωρήθηκε.")
        for t in (self.symptoms, self.diagnosis,
                  self.observations, self.prescription):
            t.delete("1.0", "end")
        self.load_history()
