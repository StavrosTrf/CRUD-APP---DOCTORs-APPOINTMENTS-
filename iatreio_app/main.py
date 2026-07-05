"""Σημείο εισόδου της εφαρμογής Διαχείρισης Ιατρείου.

Δημιουργεί τη βάση (και αρχικά δεδομένα αν είναι κενή), εκκινεί την Tkinter
και διαχειρίζεται τη ροή Login -> Dashboard -> Logout.

Εκτέλεση:  python main.py
Δοκιμαστικοί λογαριασμοί (κωδικός: 1234):  doctor · secretary · patient
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from iatreio.app_context import AppContext
from iatreio.view.login_view import LoginView
from iatreio.view.main_window import MainWindow

DB_PATH = "iatreio.db"


class Application:
    def __init__(self) -> None:
        self.ctx = AppContext(DB_PATH)
        if self.ctx.is_empty():
            self.ctx.seed_demo_data()

        self.root = tk.Tk()
        self.root.title("Σύστημα Διαχείρισης Ιατρείου — Ομάδα 4")
        self.root.geometry("960x680")
        self.root.minsize(820, 600)
        try:
            ttk.Style().theme_use("clam")
        except tk.TclError:
            pass

        self.show_login()

    def _clear(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()

    def show_login(self) -> None:
        self._clear()
        LoginView(self.root, self.ctx, on_success=self.show_main)

    def show_main(self, user) -> None:
        self._clear()
        MainWindow(self.root, self.ctx, user, on_logout=self.show_login)

    def run(self) -> None:
        self.root.mainloop()
        self.ctx.close()


if __name__ == "__main__":
    Application().run()
