"""Επίπεδο παρουσίασης — Κεντρικό παράθυρο (role-based dashboard).

Εμφανίζει καρτέλες ανάλογα με τον ρόλο του συνδεδεμένου χρήστη και παρέχει
αποσύνδεση (UC002).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..model.entities import ROLE_DOCTOR, ROLE_PATIENT, ROLE_SECRETARY
from .patient_view import PatientView
from .appointment_view import AppointmentView
from .medical_record_view import MedicalRecordView

ROLE_LABELS = {
    ROLE_DOCTOR: "Ιατρός",
    ROLE_SECRETARY: "Γραμματεία",
    ROLE_PATIENT: "Ασθενής",
}


class MainWindow(ttk.Frame):
    def __init__(self, master, ctx, user, on_logout):
        super().__init__(master)
        self.ctx = ctx
        self.user = user
        self.on_logout = on_logout
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        # --- Μπάρα κορυφής ---
        bar = ttk.Frame(self, padding=(10, 6))
        bar.pack(fill="x")
        role_label = ROLE_LABELS.get(self.user.role, self.user.role)
        ttk.Label(
            bar,
            text=f"Συνδεδεμένος: {self.user.full_name or self.user.username}"
                 f"  ·  Ρόλος: {role_label}",
            font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Button(bar, text="Αποσύνδεση", command=self._logout).pack(
            side="right")
        ttk.Separator(self).pack(fill="x")

        # --- Καρτέλες ανά ρόλο ---
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=8)

        if self.user.role in (ROLE_SECRETARY, ROLE_DOCTOR):
            nb.add(PatientView(nb, self.ctx, self.user.role),
                   text="Ασθενείς")
        nb.add(
            AppointmentView(nb, self.ctx, self.user.role, self.user),
            text="Ραντεβού")
        if self.user.role in (ROLE_DOCTOR, ROLE_SECRETARY):
            nb.add(
                MedicalRecordView(nb, self.ctx, self.user.role, self.user),
                text="Ιατρικός Φάκελος")

    def _logout(self):
        self.ctx.auth.logout()
        self.destroy()
        self.on_logout()
