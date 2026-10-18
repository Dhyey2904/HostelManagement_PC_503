import tkinter as tk
from datetime import date, timedelta
from tkinter import messagebox, ttk

from gui.common import Tab, Table, form_row, safe
from hostel import MEALS, MENU, HostelError
from models import Student

PROGRAMS = ["B.Tech ICT", "B.Tech MnC", "B.Tech EVD", "M.Tech ICT", "M.Sc IT", "M.Sc DS"]
ROOM_COLORS = {"free": "#d9ead3", "partial": "#fff2cc", "full": "#f4cccc"}


class StudentsTab(Tab):
    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        self.table = Table(self, ("Roll no", "Name", "Gender", "Program", "Room", "Phone", "Strikes"),
                           (90, 140, 70, 100, 70, 100, 60), height=20)
        self.table.pack(side="left", fill="both", expand=True)

        form = ttk.LabelFrame(self, text="Add student", padding=10)
        form.pack(side="left", fill="y", padx=(10, 0))
        self.roll = form_row(form, 0, "Roll no", ttk.Entry(form))
        self.name = form_row(form, 1, "Name", ttk.Entry(form))
        self.gender = form_row(form, 2, "Gender", ttk.Combobox(form, values=["Male", "Female"],
                                                               state="readonly"))
        self.program = form_row(form, 3, "Program", ttk.Combobox(form, values=PROGRAMS,
                                                                 state="readonly"))
        self.phone = form_row(form, 4, "Phone", ttk.Entry(form))
        self.gender.current(0)
        self.program.current(0)
        ttk.Button(form, text="Add", command=self.add).grid(row=5, column=0, columnspan=2,
                                                            sticky="ew", pady=(10, 3))
        ttk.Button(form, text="Delete selected", command=self.delete).grid(
            row=6, column=0, columnspan=2, sticky="ew")

    def refresh(self):
        self.table.load([(s.roll_no, s.name, s.gender, s.program, s.room_no or "-", s.phone,
                          s.strikes) for s in self.hostel.students.values()])

    @safe
    def add(self):
        student = Student(self.roll.get().strip(), self.name.get().strip(), self.gender.get(),
                          self.program.get(), self.phone.get().strip())
        self.hostel.add_student(student)
        for entry in (self.roll, self.name, self.phone):
            entry.delete(0, "end")
        self.refresh()

    @safe
    def delete(self):
        roll_no = self.table.need_selection()
        if messagebox.askyesno("Delete", f"Delete student {roll_no}?"):
            self.hostel.remove_student(roll_no)
            self.refresh()


class RoomsTab(Tab):
    """Floor map with room allotment."""

    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        self.selected_room = None
        left = ttk.Frame(self)
        left.pack(side="left", fill="both", expand=True)
        top = ttk.Frame(left)
        top.pack(fill="x")
        ttk.Label(top, text="Block").pack(side="left")
        self.block = ttk.Combobox(top, values=["A", "B"], width=4, state="readonly")
        self.block.pack(side="left", padx=5)
        ttk.Label(top, text="Floor").pack(side="left")
        self.floor = ttk.Combobox(top, values=[1, 2], width=4, state="readonly")
        self.floor.pack(side="left", padx=5)
        self.block.current(0)
        self.floor.current(0)
        self.block.bind("<<ComboboxSelected>>", lambda e: self.draw())
        self.floor.bind("<<ComboboxSelected>>", lambda e: self.draw())
        self.occupancy = ttk.Label(top)
        self.occupancy.pack(side="right")

        self.canvas = tk.Canvas(left, height=220, bg="white")
        self.canvas.pack(fill="x", pady=10)
        ttk.Label(left, text="Green = empty, Yellow = partly filled, Red = full. "
                             "Click a room to select it.").pack(anchor="w")

        right = ttk.LabelFrame(self, text="Allotment", padding=10)
        right.pack(side="left", fill="y", padx=(10, 0))
        self.room_info = ttk.Label(right, text="No room selected", justify="left")
        self.room_info.pack(anchor="w")
        ttk.Label(right, text="Student").pack(anchor="w", pady=(10, 0))
        self.student = ttk.Combobox(right, width=30, state="readonly")
        self.student.pack(fill="x")
        ttk.Button(right, text="Allot selected room", command=self.allot).pack(fill="x", pady=(10, 3))
        ttk.Button(right, text="Vacate student", command=self.vacate).pack(fill="x", pady=3)
        ttk.Button(right, text="Suggest best room", command=self.suggest).pack(fill="x", pady=3)

    def refresh(self):
        self.student["values"] = [f"{s.roll_no} - {s.name} ({s.room_no or 'no room'})"
                                  for s in self.hostel.students.values()]
        used, total = self.hostel.allotment.occupancy()
        self.occupancy["text"] = f"Beds used: {used}/{total}"
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        prefix = f"{self.block.get()}-{self.floor.get()}"
        rooms = [r for r in self.hostel.rooms.values() if r.number.startswith(prefix)]
        for i, room in enumerate(rooms):
            x = 20 + i * 150
            if not room.occupants:
                color = ROOM_COLORS["free"]
            elif room.is_full():
                color = ROOM_COLORS["full"]
            else:
                color = ROOM_COLORS["partial"]
            border = 3 if room.number == self.selected_room else 1
            box = self.canvas.create_rectangle(x, 40, x + 130, 170, fill=color, width=border)
            text = self.canvas.create_text(x + 65, 105, text=f"{room.number}\n"
                                           f"{len(room.occupants)}/{room.capacity} beds",
                                           justify="center")
            for item in (box, text):
                self.canvas.tag_bind(item, "<Button-1>",
                                     lambda e, n=room.number: self.select_room(n))
        self.show_room()

    def select_room(self, number):
        self.selected_room = number
        self.draw()

    def show_room(self):
        if not self.selected_room:
            return
        room = self.hostel.rooms[self.selected_room]
        names = [self.hostel.students[r].name for r in room.occupants] or ["(empty)"]
        self.room_info["text"] = (f"Room {room.number} ({room.gender})\n"
                                  f"Capacity: {room.capacity}\n\nOccupants:\n" + "\n".join(names))

    def chosen_student(self):
        if not self.student.get():
            raise HostelError("Please choose a student")
        return self.student.get().split(" - ")[0]

    @safe
    def allot(self):
        if not self.selected_room:
            raise HostelError("Please click a room first")
        self.hostel.allotment.allot(self.chosen_student(), self.selected_room)
        self.refresh()

    @safe
    def vacate(self):
        self.hostel.allotment.vacate(self.chosen_student())
        self.refresh()

    @safe
    def suggest(self):
        room, score = self.hostel.allotment.suggest_room(self.chosen_student())
        if room is None:
            raise HostelError("No vacant room found")
        self.block.set(room.number[0])
        self.floor.set(room.number[2])
        self.select_room(room.number)
        messagebox.showinfo("Suggestion", f"Best room is {room.number} "
                                          f"(compatibility {score}%)")


class ComplaintsTab(Tab):
    auto_refresh = True

    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        ttk.Label(self, text="Complaints not solved before deadline get escalated "
                             "automatically.").pack(anchor="w", pady=(0, 5))
        self.table = Table(self, ("ID", "Student", "Room", "Category", "Problem", "Priority",
                                  "Status", "Time left"),
                           (40, 120, 60, 80, 220, 70, 90, 80), height=18)
        self.table.pack(fill="both", expand=True)
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=(8, 0))
        ttk.Button(buttons, text="Mark in progress",
                   command=lambda: self.change("In progress")).pack(side="left")
        ttk.Button(buttons, text="Mark resolved",
                   command=lambda: self.change("Resolved")).pack(side="left", padx=5)

    def refresh(self):
        rows = []
        for c in self.hostel.complaints.items:
            left = c.time_left() if c.status != "Resolved" else "-"
            rows.append((c.id, self.hostel.students[c.roll_no].name, c.room_no, c.category,
                         c.text, c.priority, c.status, left))
        self.table.load(rows)

    @safe
    def change(self, status):
        self.hostel.complaints.set_status(int(self.table.need_selection()), status)
        self.refresh()


class GatePassTab(Tab):
    auto_refresh = True

    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        columns = ("ID", "Student", "Place", "Reason", "Return by", "Status", "Code")
        widths = (40, 130, 120, 150, 120, 80, 60)
        ttk.Label(self, text="Pending requests").pack(anchor="w")
        self.pending = Table(self, columns, widths, height=6)
        self.pending.pack(fill="x")
        buttons = ttk.Frame(self)
        buttons.pack(fill="x", pady=5)
        ttk.Button(buttons, text="Approve", command=self.approve).pack(side="left")
        ttk.Button(buttons, text="Reject", command=self.reject).pack(side="left", padx=5)
        ttk.Label(self, text="All passes").pack(anchor="w", pady=(10, 0))
        self.all = Table(self, columns, widths, height=10)
        self.all.pack(fill="both", expand=True)

    def row(self, p):
        status = "Late" if p.late else p.status
        return (p.id, self.hostel.students[p.roll_no].name, p.place, p.reason,
                p.return_by.strftime("%d-%m %H:%M"), status, p.code or "-")

    def refresh(self):
        self.pending.load([self.row(p) for p in self.hostel.gate.with_status("Pending")])
        self.all.load([self.row(p) for p in reversed(self.hostel.gate.passes)])

    @safe
    def approve(self):
        self.hostel.gate.approve(int(self.pending.need_selection()))
        self.refresh()

    @safe
    def reject(self):
        self.hostel.gate.reject(int(self.pending.need_selection()))
        self.refresh()


class SwapTab(Tab):
    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        self.options = []
        ttk.Label(self, text="Open swap requests").pack(anchor="w")
        self.requests = Table(self, ("ID", "Student", "From", "Wants"), (40, 160, 80, 80), height=7)
        self.requests.pack(fill="x")
        ttk.Label(self, text="Possible swaps found by the system").pack(anchor="w", pady=(10, 0))
        self.found = Table(self, ("No", "Type", "Details"), (40, 110, 500), height=7)
        self.found.pack(fill="x")
        ttk.Button(self, text="Approve selected swap", command=self.approve).pack(anchor="w", pady=8)

    def refresh(self):
        names = self.hostel.students
        self.requests.load([(r.id, names[r.roll_no].name, r.from_room, r.to_room)
                            for r in self.hostel.allotment.open_swaps()])
        self.options = self.hostel.allotment.possible_swaps()
        rows = []
        for i, (kind, requests) in enumerate(self.options):
            details = ", ".join(f"{names[r.roll_no].name}: {r.from_room} -> {r.to_room}"
                                for r in requests)
            rows.append((i + 1, kind, details))
        self.found.load(rows)

    @safe
    def approve(self):
        index = int(self.found.need_selection()) - 1
        self.hostel.allotment.approve_swap(self.options[index][1])
        messagebox.showinfo("Done", "Rooms swapped successfully")
        self.refresh()


class MessTab(Tab):
    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        ttk.Label(self, text="Weekly menu").pack(anchor="w")
        self.menu = Table(self, ["Day"] + MEALS, (100, 180, 180, 180), height=7)
        self.menu.pack(fill="x")
        bottom = ttk.Frame(self)
        bottom.pack(fill="both", expand=True, pady=(10, 0))
        left = ttk.Frame(bottom)
        left.pack(side="left", fill="both", expand=True)
        ttk.Label(left, text="Expected students (after opt-outs)").pack(anchor="w")
        self.count = Table(left, ["Date"] + MEALS, (100, 90, 90, 90), height=7)
        self.count.pack(fill="both", expand=True)
        right = ttk.Frame(bottom)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        ttk.Label(right, text="Dish ratings").pack(anchor="w")
        self.ratings = Table(right, ("Dish", "Average", "Votes"), (150, 70, 60), height=7)
        self.ratings.pack(fill="both", expand=True)

    def refresh(self):
        self.menu.load([(day, *dishes) for day, dishes in MENU.items()])
        rows = []
        for i in range(1, 8):
            day = date.today() + timedelta(days=i)
            counts = self.hostel.mess.headcount(day)
            rows.append((day.strftime("%d %b"), *counts.values()))
        self.count.load(rows)
        self.ratings.load([(dish, f"{avg:.1f}", votes)
                           for dish, avg, votes in self.hostel.mess.dish_report()])


class FeesTab(Tab):
    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        self.table = Table(self, ("Roll no", "Name", "Room", "Fee", "Rebate", "Fine", "Paid", "Dues"),
                           (90, 140, 60, 70, 60, 60, 70, 70), height=16)
        self.table.pack(fill="both", expand=True)
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", pady=(8, 0))
        ttk.Label(bottom, text="Amount").pack(side="left")
        self.amount = ttk.Entry(bottom, width=10)
        self.amount.pack(side="left", padx=5)
        self.mode = ttk.Combobox(bottom, values=["Cash", "UPI", "Card"], width=8, state="readonly")
        self.mode.current(0)
        self.mode.pack(side="left")
        ttk.Button(bottom, text="Record payment", command=self.pay).pack(side="left", padx=5)
        self.total = ttk.Label(bottom)
        self.total.pack(side="right")

    def refresh(self):
        fees = self.hostel.fees
        rows = []
        for s in self.hostel.students.values():
            r = s.roll_no
            rows.append((r, s.name, s.room_no or "-", fees.fee(r), self.hostel.mess.rebate(r),
                         fees.fine(r), fees.paid(r), fees.dues(r)))
        self.table.load(rows)
        self.total["text"] = f"Total pending: Rs {fees.total_dues():,.0f}"

    @safe
    def pay(self):
        roll_no = self.table.need_selection()
        self.hostel.fees.pay(roll_no, float(self.amount.get()), self.mode.get())
        self.amount.delete(0, "end")
        self.refresh()


class NoticesTab(Tab):
    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        self.table = Table(self, ("Date", "Title", "Message"), (90, 160, 500), height=12)
        self.table.pack(fill="both", expand=True)
        form = ttk.LabelFrame(self, text="New notice", padding=10)
        form.pack(fill="x", pady=(10, 0))
        self.title = form_row(form, 0, "Title", ttk.Entry(form, width=40))
        self.text = form_row(form, 1, "Message", tk.Text(form, height=3, width=60))
        ttk.Button(form, text="Post", command=self.post).grid(row=2, column=1, sticky="w", pady=5)

    def refresh(self):
        self.table.load([(n.posted.strftime("%d-%m-%Y"), n.title, n.text)
                         for n in self.hostel.notices], use_first_as_id=False)

    @safe
    def post(self):
        self.hostel.post_notice(self.title.get().strip(), self.text.get("1.0", "end").strip())
        self.title.delete(0, "end")
        self.text.delete("1.0", "end")
        self.refresh()
