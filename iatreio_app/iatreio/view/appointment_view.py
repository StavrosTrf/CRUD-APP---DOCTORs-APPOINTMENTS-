"""Επίπεδο παρουσίασης — Διαχείριση Ραντεβού (UC003–UC008).

Λίστα ραντεβού + ενέργειες ανάλογα με τον ρόλο:
  Γραμματεία/Ασθενής: κράτηση, επαναπρογραμματισμός, ακύρωση/διαγραφή
  Γραμματεία:         check-in
  Ιατρός:             προβολή των δικών του ραντεβού
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from ..controller.exceptions import AppError
from ..model.entities import ROLE_DOCTOR, ROLE_PATIENT, ROLE_SECRETARY

CATEGORIES = ["Παθολόγος", "Καρδιολόγος", "Δερματολόγος",
              "Ορθοπεδικός", "Μικροβιολογικές εξετάσεις"]


class AppointmentView(ttk.Frame):
    def __init__(self, master, ctx, role, current_user):
        super().__init__(master, padding=10)
        self.ctx = ctx
        self.role = role
        self.user = current_user
        self.selected_id = None
        self._build()
        self.refresh()

    def _build(self):
        cols = ("when", "patient", "doctor", "category", "status")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        headers = {"when": "Ημ/νία & Ώρα", "patient": "Ασθενής",
                   "doctor": "Ιατρός", "category": "Κατηγορία",
                   "status": "Κατάσταση"}
        widths = {"when": 130, "patient": 160, "doctor": 160,
                  "category": 150, "status": 110}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c])
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # --- Φόρμα κράτησης ---
        if self.role in (ROLE_SECRETARY, ROLE_PATIENT):
            form = ttk.LabelFrame(self, text="Νέο Ραντεβού", padding=10)
            form.pack(fill="x", pady=8)

            ttk.Label(form, text="Ασθενής:").grid(row=0, column=0, sticky="e")
            self.patient_cb = ttk.Combobox(form, width=28, state="readonly")
            self.patient_cb.grid(row=0, column=1, padx=4, pady=3)

            ttk.Label(form, text="Ιατρός:").grid(row=0, column=2, sticky="e")
            self.doctor_cb = ttk.Combobox(form, width=24, state="readonly")
            self.doctor_cb.grid(row=0, column=3, padx=4, pady=3)

            ttk.Label(form, text="Κατηγορία:").grid(row=1, column=0, sticky="e")
            self.cat_cb = ttk.Combobox(form, width=28, values=CATEGORIES)
            self.cat_cb.grid(row=1, column=1, padx=4, pady=3)
            self.cat_cb.set(CATEGORIES[0])

            ttk.Label(form, text="Ημ/νία & Ώρα\n(YYYY-MM-DD HH:MM):").grid(
                row=1, column=2, sticky="e")
            self.dt_var = tk.StringVar(value="2026-06-20 10:00")
            ttk.Entry(form, textvariable=self.dt_var, width=24).grid(
                row=1, column=3, padx=4, pady=3)

            ttk.Button(form, text="Κράτηση", command=self.book).grid(
                row=2, column=0, columnspan=4, pady=6)
            self._load_combos()

        # --- Κουμπιά ενεργειών ---
        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=(4, 0))
        if self.role == ROLE_SECRETARY:
            ttk.Button(btns, text="Check-in", command=self.check_in).pack(
                side="left", padx=3)
        if self.role in (ROLE_SECRETARY, ROLE_PATIENT):
            ttk.Button(btns, text="Επαναπρογραμματισμός",
                       command=self.reschedule).pack(side="left", padx=3)
            ttk.Button(btns, text="Ακύρωση", command=self.cancel).pack(
                side="left", padx=3)
            ttk.Button(btns, text="Διαγραφή", command=self.delete).pack(
                side="left", padx=3)
        ttk.Button(btns, text="Ανανέωση", command=self.refresh).pack(
            side="right", padx=3)

    def _load_combos(self):
        self._patients = self.ctx.patients.list_patients()
        # Ασθενής βλέπει μόνο τον εαυτό του (αν είναι συνδεδεμένος με φάκελο).
        if self.role == ROLE_PATIENT and self.user.patient_id:
            self._patients = [p for p in self._patients
                              if p.id == self.user.patient_id]
        self.patient_cb["values"] = [
            f"{p.last_name} {p.first_name} ({p.amka})" for p in self._patients]
        if self._patients:
            self.patient_cb.current(0)

        self._doctors = self.ctx.user_repo.list_by_role(ROLE_DOCTOR)
        self.doctor_cb["values"] = [d.full_name for d in self._doctors]
        if self._doctors:
            self.doctor_cb.current(0)

    # --- Δεδομένα ---
    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        if self.role == ROLE_DOCTOR:
            appts = self.ctx.appointments.list_for_doctor(self.user.id)
        elif self.role == ROLE_PATIENT and self.user.patient_id:
            appts = self.ctx.appointments.list_for_patient(self.user.patient_id)
        else:
            appts = self.ctx.appointments.list_appointments()
        for a in appts:
            self.tree.insert("", "end", iid=str(a.id), values=(
                a.scheduled_at, a.patient_name, a.doctor_name,
                a.category, a.status))

    def _on_select(self, _e):
        sel = self.tree.selection()
        self.selected_id = int(sel[0]) if sel else None

    def _require_selection(self):
        if self.selected_id is None:
            messagebox.showwarning("Προσοχή", "Επιλέξτε ραντεβού.")
            return False
        return True

    # --- Ενέργειες ---
    def book(self):
        if not self._patients:
            messagebox.showwarning("Προσοχή", "Δεν υπάρχουν ασθενείς.")
            return
        patient = self._patients[self.patient_cb.current()]
        doctor = self._doctors[self.doctor_cb.current()]
        try:
            self.ctx.appointments.book_appointment(
                patient_id=patient.id, doctor_id=doctor.id,
                category=self.cat_cb.get(), scheduled_at=self.dt_var.get())
        except AppError as exc:
            messagebox.showerror("Σφάλμα", str(exc))
            return
        messagebox.showinfo("Επιτυχία", "Το ραντεβού καταχωρήθηκε.")
        self.refresh()

    def check_in(self):
        if not self._require_selection():
            return
        try:
            self.ctx.appointments.check_in(self.selected_id)
        except AppError as exc:
            messagebox.showerror("Σφάλμα", str(exc))
            return
        self.refresh()

    def reschedule(self):
        if not self._require_selection():
            return
        new_dt = simpledialog.askstring(
            "Επαναπρογραμματισμός", "Νέα ημ/νία & ώρα (YYYY-MM-DD HH:MM):")
        if not new_dt:
            return
        try:
            self.ctx.appointments.reschedule(self.selected_id, new_dt)
        except AppError as exc:
            messagebox.showerror("Σφάλμα", str(exc))
            return
        self.refresh()

    def cancel(self):
        if not self._require_selection():
            return
        try:
            self.ctx.appointments.cancel(self.selected_id)
        except AppError as exc:
            messagebox.showerror("Σφάλμα", str(exc))
            return
        self.refresh()

    def delete(self):
        if not self._require_selection():
            return
        if not messagebox.askyesno("Επιβεβαίωση", "Οριστική διαγραφή ραντεβού;"):
            return
        try:
            self.ctx.appointments.delete_appointment(self.selected_id)
        except AppError as exc:
            messagebox.showerror("Σφάλμα", str(exc))
            return
        self.refresh()
