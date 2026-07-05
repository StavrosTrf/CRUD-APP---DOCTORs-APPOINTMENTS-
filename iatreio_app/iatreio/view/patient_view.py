"""Επίπεδο παρουσίασης — Διαχείριση Ασθενών (CRUD).

Πίνακας (Treeview) + φόρμα. Καλεί τον PatientController. Ο ρόλος καθορίζει
αν επιτρέπεται εγγραφή/διαγραφή (η Γραμματεία έχει πλήρη CRUD).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from ..controller.exceptions import AppError
from ..model.entities import ROLE_SECRETARY


class PatientView(ttk.Frame):
    def __init__(self, master, ctx, role, on_select=None):
        super().__init__(master, padding=10)
        self.ctx = ctx
        self.role = role
        self.on_select = on_select          # callback(patient) για άλλες καρτέλες
        self.can_edit = (role == ROLE_SECRETARY)
        self.selected_id = None
        self._build()
        self.refresh()

    def _build(self):
        # --- Αναζήτηση ---
        top = ttk.Frame(self)
        top.pack(fill="x", pady=(0, 8))
        ttk.Label(top, text="Αναζήτηση:").pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.search_var, width=30)
        entry.pack(side="left", padx=5)
        entry.bind("<KeyRelease>", lambda e: self.refresh())
        ttk.Button(top, text="Ανανέωση", command=self.refresh).pack(side="left")

        # --- Πίνακας ---
        cols = ("amka", "last", "first", "phone", "email", "gdpr")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=10)
        headers = {
            "amka": "ΑΜΚΑ", "last": "Επώνυμο", "first": "Όνομα",
            "phone": "Τηλέφωνο", "email": "Email", "gdpr": "GDPR",
        }
        widths = {"amka": 110, "last": 120, "first": 120,
                  "phone": 100, "email": 170, "gdpr": 50}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c], anchor="w")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

        # --- Φόρμα ---
        form = ttk.LabelFrame(self, text="Στοιχεία Ασθενούς", padding=10)
        form.pack(fill="x", pady=8)
        self.vars = {k: tk.StringVar() for k in
                     ("amka", "first", "last", "phone", "email", "dob")}
        self.gdpr_var = tk.BooleanVar()
        labels = [("ΑΜΚΑ", "amka"), ("Όνομα", "first"), ("Επώνυμο", "last"),
                  ("Τηλέφωνο", "phone"), ("Email", "email"),
                  ("Ημ. Γέννησης (YYYY-MM-DD)", "dob")]
        for i, (lbl, key) in enumerate(labels):
            r, c = divmod(i, 2)
            ttk.Label(form, text=lbl + ":").grid(
                row=r, column=c * 2, sticky="e", padx=4, pady=3)
            ttk.Entry(form, textvariable=self.vars[key], width=24).grid(
                row=r, column=c * 2 + 1, padx=4, pady=3)
        ttk.Checkbutton(form, text="Συγκατάθεση GDPR",
                        variable=self.gdpr_var).grid(
            row=3, column=0, columnspan=2, sticky="w", padx=4, pady=4)

        # --- Κουμπιά ---
        btns = ttk.Frame(self)
        btns.pack(fill="x")
        ttk.Button(btns, text="Καθαρισμός", command=self.clear_form).pack(
            side="left", padx=3)
        if self.can_edit:
            ttk.Button(btns, text="Αποθήκευση", command=self.save).pack(
                side="left", padx=3)
            ttk.Button(btns, text="Διαγραφή", command=self.delete).pack(
                side="left", padx=3)
        else:
            ttk.Label(btns, text="(Πρόσβαση μόνο για ανάγνωση)",
                      foreground="#888").pack(side="left", padx=3)

    # --- Δεδομένα ---
    def refresh(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        patients = self.ctx.patients.search_patients(self.search_var.get())
        for p in patients:
            self.tree.insert("", "end", iid=str(p.id), values=(
                p.amka, p.last_name, p.first_name, p.phone, p.email,
                "Ναι" if p.gdpr_consent else "Όχι",
            ))

    def _on_row_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_id = int(sel[0])
        p = self.ctx.patients.get_patient(self.selected_id)
        self.vars["amka"].set(p.amka)
        self.vars["first"].set(p.first_name)
        self.vars["last"].set(p.last_name)
        self.vars["phone"].set(p.phone)
        self.vars["email"].set(p.email)
        self.vars["dob"].set(p.date_of_birth)
        self.gdpr_var.set(p.gdpr_consent)
        if self.on_select:
            self.on_select(p)

    def clear_form(self):
        self.selected_id = None
        for v in self.vars.values():
            v.set("")
        self.gdpr_var.set(False)
        self.tree.selection_remove(self.tree.selection())

    def save(self):
        data = dict(
            amka=self.vars["amka"].get(),
            first_name=self.vars["first"].get(),
            last_name=self.vars["last"].get(),
            phone=self.vars["phone"].get(),
            email=self.vars["email"].get(),
            date_of_birth=self.vars["dob"].get(),
            gdpr_consent=self.gdpr_var.get(),
        )
        try:
            if self.selected_id is None:
                self.ctx.patients.create_patient(**data)
                msg = "Ο ασθενής δημιουργήθηκε."
            else:
                self.ctx.patients.update_patient(self.selected_id, **data)
                msg = "Τα στοιχεία ενημερώθηκαν."
        except AppError as exc:
            messagebox.showerror("Σφάλμα", str(exc))
            return
        messagebox.showinfo("Επιτυχία", msg)
        self.clear_form()
        self.refresh()

    def delete(self):
        if self.selected_id is None:
            messagebox.showwarning("Προσοχή", "Επιλέξτε ασθενή από τον πίνακα.")
            return
        if not messagebox.askyesno("Επιβεβαίωση",
                                   "Διαγραφή ασθενούς και όλων των ραντεβού του;"):
            return
        try:
            self.ctx.patients.delete_patient(self.selected_id)
        except AppError as exc:
            messagebox.showerror("Σφάλμα", str(exc))
            return
        self.clear_form()
        self.refresh()
