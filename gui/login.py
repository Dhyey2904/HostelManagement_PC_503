import tkinter as tk
from tkinter import messagebox, ttk

from hostel import HostelError


class LoginFrame(ttk.Frame):
    def __init__(self, parent, hostel, on_login):
        super().__init__(parent)
        self.hostel = hostel
        self.on_login = on_login
        self.username = tk.StringVar()
        self.password = tk.StringVar()

        box = ttk.Frame(self, padding=20, relief="groove")
        box.place(relx=0.5, rely=0.45, anchor="center")
        ttk.Label(box, text="DAIICT Hostel Management",
                  font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        ttk.Label(box, text="Username / Roll no").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(box, textvariable=self.username).grid(row=1, column=1, pady=4)
        ttk.Label(box, text="Password").grid(row=2, column=0, sticky="w", pady=4)
        entry = ttk.Entry(box, textvariable=self.password, show="*")
        entry.grid(row=2, column=1, pady=4)
        entry.bind("<Return>", lambda e: self.login())
        ttk.Button(box, text="Login", command=self.login).grid(
            row=3, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(box, text="warden/warden123  |  202611059/pass123  |  security/gate123",
                  foreground="gray").grid(row=4, column=0, columnspan=2, pady=(10, 0))

    def login(self):
        username = self.username.get().strip()
        try:
            role = self.hostel.login(username, self.password.get())
        except HostelError as e:
            messagebox.showerror("Login failed", str(e))
            return
        self.on_login(role, username)
