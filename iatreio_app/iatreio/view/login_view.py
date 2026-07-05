"""Επίπεδο παρουσίασης — Οθόνη σύνδεσης (UC001 Login).

Το View δεν περιέχει επιχειρησιακή λογική· καλεί τον AuthController και
εμφανίζει το αποτέλεσμα. Σε επιτυχία ειδοποιεί τον caller μέσω callback.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from ..controller.exceptions import AppError


class LoginView(ttk.Frame):
    def __init__(self, master, ctx, on_success):
        super().__init__(master, padding=30)
        self.ctx = ctx
        self.on_success = on_success
        self.pack(fill="both", expand=True)
        self._build()

    def _build(self):
        ttk.Label(self, text="Σύστημα Διαχείρισης Ιατρείου",
                  font=("Segoe UI", 16, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 4))
        ttk.Label(self, text="Είσοδος Χρήστη",
                  font=("Segoe UI", 11)).grid(
            row=1, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(self, text="Όνομα χρήστη:").grid(
            row=2, column=0, sticky="e", padx=5, pady=6)
        self.username = ttk.Entry(self, width=28)
        self.username.grid(row=2, column=1, pady=6)

        ttk.Label(self, text="Κωδικός:").grid(
            row=3, column=0, sticky="e", padx=5, pady=6)
        self.password = ttk.Entry(self, width=28, show="•")
        self.password.grid(row=3, column=1, pady=6)

        btn = ttk.Button(self, text="Είσοδος", command=self._do_login)
        btn.grid(row=4, column=0, columnspan=2, pady=20, ipadx=10)

        hint = ("Δοκιμαστικοί λογαριασμοί (κωδικός: 1234):\n"
                "doctor · secretary · patient")
        ttk.Label(self, text=hint, foreground="#666",
                  font=("Segoe UI", 8), justify="center").grid(
            row=5, column=0, columnspan=2)

        self.username.focus_set()
        self.password.bind("<Return>", lambda e: self._do_login())
        self.username.bind("<Return>", lambda e: self.password.focus_set())

    def _do_login(self):
        try:
            user = self.ctx.auth.login(
                self.username.get(), self.password.get())
        except AppError as exc:
            messagebox.showerror("Αποτυχία σύνδεσης", str(exc))
            self.password.delete(0, tk.END)
            return
        self.destroy()
        self.on_success(user)
