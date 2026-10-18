from datetime import datetime
from tkinter import messagebox, ttk

from gui.common import Tab, Table, safe


class GateTab(Tab):
    auto_refresh = True

    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        box = ttk.LabelFrame(self, text="Check pass", padding=10)
        box.pack(fill="x")
        ttk.Label(box, text="Pass code").pack(side="left")
        self.code = ttk.Entry(box, width=10, font=("Arial", 14))
        self.code.pack(side="left", padx=5)
        ttk.Button(box, text="Going out", command=self.mark_out).pack(side="left", padx=5)
        ttk.Button(box, text="Coming in", command=self.mark_in).pack(side="left")

        ttk.Label(self, text="Students outside right now").pack(anchor="w", pady=(10, 0))
        self.outside = Table(self, ("Code", "Student", "Place", "Return by", "Overdue"),
                             (60, 150, 150, 120, 70), height=8)
        self.outside.pack(fill="x")
        ttk.Label(self, text="Approved passes (not left yet)").pack(anchor="w", pady=(10, 0))
        self.approved = Table(self, ("Code", "Student", "Place", "Return by"),
                              (60, 150, 150, 120), height=6)
        self.approved.pack(fill="x")

    def refresh(self):
        gate, names = self.hostel.gate, self.hostel.students
        now = datetime.now()
        self.outside.load([(p.code, names[p.roll_no].name, p.place,
                            p.return_by.strftime("%d-%m %H:%M"), "Yes" if now > p.return_by else "No")
                           for p in gate.with_status("Out")])
        self.approved.load([(p.code, names[p.roll_no].name, p.place,
                             p.return_by.strftime("%d-%m %H:%M"))
                            for p in gate.with_status("Approved")])

    @safe
    def mark_out(self):
        gate_pass = self.hostel.gate.mark_out(self.code.get())
        messagebox.showinfo("Out", f"{self.hostel.students[gate_pass.roll_no].name} can go out")
        self.code.delete(0, "end")
        self.refresh()

    @safe
    def mark_in(self):
        gate_pass = self.hostel.gate.mark_in(self.code.get())
        name = self.hostel.students[gate_pass.roll_no].name
        if gate_pass.late:
            messagebox.showwarning("Late", f"{name} came back late. Strike added.")
        else:
            messagebox.showinfo("In", f"{name} is back on time")
        self.code.delete(0, "end")
        self.refresh()
