import tkinter as tk
from tkinter import ttk

from gui import student_tabs, warden_tabs
from gui.login import LoginFrame
from gui.security_tab import GateTab

TABS = {
    "Warden": [("Students", warden_tabs.StudentsTab), ("Rooms", warden_tabs.RoomsTab),
               ("Complaints", warden_tabs.ComplaintsTab), ("Gate Pass", warden_tabs.GatePassTab),
               ("Room Swaps", warden_tabs.SwapTab), ("Mess", warden_tabs.MessTab),
               ("Fees", warden_tabs.FeesTab), ("Notices", warden_tabs.NoticesTab)],
    "Student": [("Home", student_tabs.HomeTab), ("Roommates", student_tabs.RoommateTab),
                ("Complaints", student_tabs.ComplaintTab), ("Gate Pass", student_tabs.GatePassTab),
                ("Mess", student_tabs.MessTab), ("Laundry", student_tabs.LaundryTab),
                ("Fees", student_tabs.FeesTab)],
    "Security": [("Gate", GateTab)],
}


class HostelApp(tk.Tk):
    def __init__(self, hostel):
        super().__init__()
        self.title("DAIICT Hostel Management")
        self.geometry("1050x650")
        style = ttk.Style(self)
        style.theme_use("clam")
        style.map("Treeview", background=[("selected", "#c8c8c8")],
                  foreground=[("selected", "black")])
        self.hostel = hostel
        self.frame = None
        self.show_login()
        self.after(5000, self.auto_check)

    def change_frame(self, frame):
        if self.frame:
            self.frame.destroy()
        self.frame = frame
        frame.pack(fill="both", expand=True)

    def show_login(self):
        self.change_frame(LoginFrame(self, self.hostel, self.open_main))

    def open_main(self, role, username):
        self.change_frame(MainFrame(self, self.hostel, role, username, self.show_login))

    def auto_check(self):
        """Escalate overdue complaints every 5s."""
        self.hostel.complaints.check_overdue()
        if isinstance(self.frame, MainFrame):
            self.frame.auto_refresh()
        self.after(5000, self.auto_check)


class MainFrame(ttk.Frame):
    def __init__(self, parent, hostel, role, username, on_logout):
        super().__init__(parent)
        name = hostel.students[username].name if role == "Student" else role
        top = ttk.Frame(self, padding=(10, 6))
        top.pack(fill="x")
        ttk.Label(top, text=f"Logged in as {name} ({role})").pack(side="left")
        ttk.Button(top, text="Logout", command=on_logout).pack(side="right")

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.tabs = []
        for title, tab_class in TABS[role]:
            tab = tab_class(self.notebook, hostel, username)
            self.notebook.add(tab, text=title)
            self.tabs.append(tab)
        self.notebook.bind("<<NotebookTabChanged>>", lambda e: self.current().refresh())

    def current(self):
        return self.tabs[self.notebook.index("current")]

    def auto_refresh(self):
        if self.current().auto_refresh:
            self.current().refresh()
