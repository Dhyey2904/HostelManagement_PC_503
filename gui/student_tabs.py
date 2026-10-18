from datetime import date, datetime, timedelta
from tkinter import messagebox, ttk

from gui.common import Tab, Table, form_row, safe
from hostel import (LAUNDRY_HOURS, MACHINES, MAX_STRIKES, MEAL_PRICE, MEALS, PRIORITIES,
                    HostelError, todays_menu)

CATEGORIES = ["Electrical", "Plumbing", "Wi-Fi", "Cleaning", "Furniture", "Other"]


class HomeTab(Tab):
    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        self.info = ttk.Label(self, justify="left", font=("Arial", 12))
        self.info.pack(anchor="w")
        ttk.Label(self, text="Notices").pack(anchor="w", pady=(15, 0))
        self.notices = Table(self, ("Date", "Title", "Message"), (90, 160, 500), height=10)
        self.notices.pack(fill="both", expand=True)

    def refresh(self):
        h = self.hostel
        me = h.student(self.username)
        mates = ", ".join(s.name for s in h.allotment.roommates(me.roll_no)) or "None"
        slot = h.laundry.slot_of(me.roll_no)
        slot_text = f"Machine {slot[0]} at {slot[1]}:00" if slot else "Not booked"
        self.info["text"] = (f"Name: {me.name}\nRoll no: {me.roll_no}\n"
                             f"Room: {me.room_no or 'Not allotted'}\nRoommates: {mates}\n"
                             f"Fee dues: Rs {h.fees.dues(me.roll_no):,.0f}\n"
                             f"Late returns: {me.strikes}/{MAX_STRIKES}\n"
                             f"Laundry today: {slot_text}")
        self.notices.load([(n.posted.strftime("%d-%m-%Y"), n.title, n.text)
                           for n in h.notices], use_first_as_id=False)


class RoommateTab(Tab):
    """Habit profile, matches and swaps."""

    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        left = ttk.LabelFrame(self, text="My habits", padding=10)
        left.pack(side="left", fill="y")
        self.sleep = form_row(left, 0, "Sleep time", ttk.Combobox(
            left, values=["Early", "Flexible", "Late"], state="readonly", width=12))
        self.clean = form_row(left, 1, "Cleanliness (1-5)", ttk.Spinbox(left, from_=1, to=5,
                                                                         width=12))
        self.diet = form_row(left, 2, "Diet", ttk.Combobox(
            left, values=["Veg", "Non-veg", "Jain"], state="readonly", width=12))
        self.language = form_row(left, 3, "Language", ttk.Entry(left, width=14))
        ttk.Button(left, text="Save", command=self.save).grid(row=4, column=1, sticky="ew", pady=8)

        ttk.Label(left, text="Request room change").grid(row=5, column=0, columnspan=2,
                                                         sticky="w", pady=(20, 0))
        self.target = form_row(left, 6, "Move to", ttk.Combobox(left, state="readonly", width=12))
        ttk.Button(left, text="Send request", command=self.request_swap).grid(
            row=7, column=1, sticky="ew", pady=5)
        self.swap_status = ttk.Label(left, text="")
        self.swap_status.grid(row=8, column=0, columnspan=2, sticky="w")

        right = ttk.Frame(self)
        right.pack(side="left", fill="both", expand=True, padx=(10, 0))
        ttk.Label(right, text="Students most compatible with you").pack(anchor="w")
        self.matches = Table(right, ("Name", "Program", "Room", "Score"), (150, 100, 70, 60))
        self.matches.pack(fill="both", expand=True)
        ttk.Label(right, text="Score is based on sleep time, cleanliness, diet, "
                              "language and program.").pack(anchor="w", pady=5)

    def refresh(self):
        me = self.hostel.student(self.username)
        self.sleep.set(me.sleep)
        self.clean.set(me.cleanliness)
        self.diet.set(me.diet)
        self.language.delete(0, "end")
        self.language.insert(0, me.language)
        self.target["values"] = [r.number for r in self.hostel.rooms.values()
                                 if r.gender == me.gender and r.number != me.room_no]
        self.matches.load([(s.name, s.program, s.room_no or "-", f"{score}%")
                           for score, s in self.hostel.allotment.best_matches(me.roll_no)],
                          use_first_as_id=False)
        mine = [r for r in self.hostel.allotment.swaps if r.roll_no == me.roll_no]
        self.swap_status["text"] = f"Last request: {mine[-1].to_room} ({mine[-1].status})" if mine else ""

    @safe
    def save(self):
        clean = int(self.clean.get())
        if not 1 <= clean <= 5:
            raise HostelError("Cleanliness should be 1 to 5")
        me = self.hostel.student(self.username)
        me.sleep, me.cleanliness = self.sleep.get(), clean
        me.diet, me.language = self.diet.get(), self.language.get().strip()
        self.refresh()

    @safe
    def request_swap(self):
        if not self.target.get():
            raise HostelError("Please choose a room")
        self.hostel.allotment.request_swap(self.username, self.target.get())
        messagebox.showinfo("Sent", "Request sent to warden")
        self.refresh()


class ComplaintTab(Tab):
    auto_refresh = True

    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        form = ttk.LabelFrame(self, text="New complaint", padding=10)
        form.pack(fill="x")
        self.category = form_row(form, 0, "Category", ttk.Combobox(form, values=CATEGORIES,
                                                                   state="readonly"))
        self.priority = form_row(form, 1, "Priority", ttk.Combobox(form, values=PRIORITIES,
                                                                   state="readonly"))
        self.text = form_row(form, 2, "Problem", ttk.Entry(form, width=60))
        self.category.current(0)
        self.priority.current(1)
        ttk.Button(form, text="Submit", command=self.submit).grid(row=3, column=1, sticky="w", pady=5)
        self.table = Table(self, ("ID", "Category", "Problem", "Priority", "Status", "Time left"),
                           (40, 90, 300, 70, 90, 80))
        self.table.pack(fill="both", expand=True, pady=(10, 0))

    def refresh(self):
        self.table.load([(c.id, c.category, c.text, c.priority, c.status,
                          c.time_left() if c.status != "Resolved" else "-")
                         for c in self.hostel.complaints.of_student(self.username)])

    @safe
    def submit(self):
        self.hostel.complaints.add(self.username, self.category.get(), self.text.get().strip(),
                                   self.priority.get())
        self.text.delete(0, "end")
        self.refresh()


class GatePassTab(Tab):
    auto_refresh = True

    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        form = ttk.LabelFrame(self, text="Request gate pass", padding=10)
        form.pack(fill="x")
        self.place = form_row(form, 0, "Going to", ttk.Entry(form, width=30))
        self.reason = form_row(form, 1, "Reason", ttk.Entry(form, width=30))
        self.return_by = form_row(form, 2, "Return by (dd-mm-yyyy hh:mm)", ttk.Entry(form, width=30))
        later = datetime.now() + timedelta(hours=3)
        self.return_by.insert(0, later.strftime("%d-%m-%Y %H:%M"))
        ttk.Button(form, text="Request", command=self.request).grid(row=3, column=1, sticky="w", pady=5)
        self.status = ttk.Label(self, font=("Arial", 12))
        self.status.pack(anchor="w", pady=10)
        self.table = Table(self, ("ID", "Place", "Return by", "Status", "Code"),
                           (40, 150, 130, 90, 60))
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        active = self.hostel.gate.active_pass(self.username)
        if active and active.code:
            self.status["text"] = f"Your pass code: {active.code}  (show this at the gate)"
        elif active:
            self.status["text"] = "Your pass is waiting for warden approval"
        else:
            self.status["text"] = "No active pass"
        mine = [p for p in self.hostel.gate.passes if p.roll_no == self.username]
        self.table.load([(p.id, p.place, p.return_by.strftime("%d-%m %H:%M"),
                          "Late" if p.late else p.status, p.code or "-") for p in mine])

    @safe
    def request(self):
        try:
            return_by = datetime.strptime(self.return_by.get().strip(), "%d-%m-%Y %H:%M")
        except ValueError:
            raise HostelError("Date format should be dd-mm-yyyy hh:mm")
        self.hostel.gate.request(self.username, self.place.get().strip(),
                                 self.reason.get().strip(), return_by)
        self.refresh()


class MessTab(Tab):
    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        self.menu = ttk.Label(self, font=("Arial", 12), justify="left")
        self.menu.pack(anchor="w")

        rate = ttk.LabelFrame(self, text="Rate today's meal", padding=10)
        rate.pack(fill="x", pady=10)
        self.rate_meal = ttk.Combobox(rate, values=MEALS, state="readonly", width=12)
        self.rate_meal.current(0)
        self.rate_meal.pack(side="left")
        ttk.Label(rate, text="Stars").pack(side="left", padx=(10, 3))
        self.stars = ttk.Spinbox(rate, from_=1, to=5, width=4)
        self.stars.set(4)
        self.stars.pack(side="left")
        ttk.Button(rate, text="Rate", command=self.rate).pack(side="left", padx=10)

        skip = ttk.LabelFrame(self, text="Skip a meal (money is adjusted in fees)", padding=10)
        skip.pack(fill="x")
        days = [date.today() + timedelta(days=i) for i in range(1, 8)]
        self.day = ttk.Combobox(skip, values=[d.strftime("%d-%m-%Y") for d in days],
                                state="readonly", width=12)
        self.day.current(0)
        self.day.pack(side="left")
        self.skip_meal = ttk.Combobox(skip, values=MEALS, state="readonly", width=12)
        self.skip_meal.current(0)
        self.skip_meal.pack(side="left", padx=5)
        ttk.Button(skip, text="Skip", command=self.skip).pack(side="left")
        self.rebate = ttk.Label(skip)
        self.rebate.pack(side="right")
        self.table = Table(self, ("Date", "Meal", "Refund"), (120, 120, 80), height=6)
        self.table.pack(fill="both", expand=True, pady=(10, 0))

    def refresh(self):
        menu = todays_menu()
        self.menu["text"] = "Today's menu:   " + "   |   ".join(f"{m}: {d}" for m, d in menu.items())
        rows = [(d.strftime("%d-%m-%Y"), meal, MEAL_PRICE[meal])
                for _, d, meal in self.hostel.mess.opt_outs_of(self.username)]
        self.table.load(rows, use_first_as_id=False)
        self.rebate["text"] = f"Total refund: Rs {self.hostel.mess.rebate(self.username)}"

    @safe
    def rate(self):
        stars = int(self.stars.get())
        if not 1 <= stars <= 5:
            raise HostelError("Stars should be 1 to 5")
        self.hostel.mess.rate(self.username, self.rate_meal.get(), stars)
        messagebox.showinfo("Thanks", "Rating saved")

    @safe
    def skip(self):
        day = datetime.strptime(self.day.get(), "%d-%m-%Y").date()
        self.hostel.mess.opt_out(self.username, day, self.skip_meal.get())
        self.refresh()


class LaundryTab(Tab):
    """Book a washing machine slot."""

    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        ttk.Label(self, text="Today's slots. Click a free slot to book it.").pack(anchor="w")
        self.grid_frame = ttk.Frame(self)
        self.grid_frame.pack(anchor="w", pady=10)
        ttk.Button(self, text="Cancel my booking", command=self.cancel).pack(anchor="w")

    def refresh(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        for m in range(1, MACHINES + 1):
            ttk.Label(self.grid_frame, text=f"Machine {m}").grid(row=0, column=m, padx=5)
        now = datetime.now().hour
        slots = self.hostel.laundry.slots
        for row, hour in enumerate(LAUNDRY_HOURS, start=1):
            ttk.Label(self.grid_frame, text=f"{hour}:00").grid(row=row, column=0, padx=(0, 10))
            for m in range(1, MACHINES + 1):
                owner = slots.get((m, hour))
                if owner == self.username:
                    text = "Yours"
                elif owner:
                    text = "Booked"
                elif hour <= now:
                    text = "-"
                else:
                    text = "Free"
                button = ttk.Button(self.grid_frame, text=text, width=8,
                                    command=lambda m=m, h=hour: self.book(m, h))
                if text != "Free":
                    button.state(["disabled"])
                button.grid(row=row, column=m, padx=2, pady=1)

    @safe
    def book(self, machine, hour):
        self.hostel.laundry.book(self.username, machine, hour)
        self.refresh()

    def cancel(self):
        self.hostel.laundry.cancel(self.username)
        self.refresh()


class FeesTab(Tab):
    def __init__(self, parent, hostel, username):
        super().__init__(parent, hostel, username)
        self.info = ttk.Label(self, font=("Arial", 12), justify="left")
        self.info.pack(anchor="w")
        pay = ttk.LabelFrame(self, text="Pay fees", padding=10)
        pay.pack(fill="x", pady=10)
        ttk.Label(pay, text="Amount").pack(side="left")
        self.amount = ttk.Entry(pay, width=12)
        self.amount.pack(side="left", padx=5)
        self.mode = ttk.Combobox(pay, values=["UPI", "Card", "Net Banking"], state="readonly",
                                 width=12)
        self.mode.current(0)
        self.mode.pack(side="left")
        ttk.Button(pay, text="Pay", command=self.pay).pack(side="left", padx=5)
        self.table = Table(self, ("ID", "Date", "Mode", "Amount"), (60, 110, 100, 90), height=8)
        self.table.pack(fill="both", expand=True)

    def refresh(self):
        fees, r = self.hostel.fees, self.username
        self.info["text"] = (f"Room fee: Rs {fees.fee(r):,}\n"
                             f"Mess refund: - Rs {self.hostel.mess.rebate(r)}\n"
                             f"Late fine: + Rs {fees.fine(r)}\n"
                             f"Paid: - Rs {fees.paid(r):,.0f}\n"
                             f"Balance: Rs {fees.dues(r):,.0f}")
        self.table.load([(p.id, p.paid_on.strftime("%d-%m-%Y"), p.mode, p.amount)
                         for p in fees.payments_of(r)])

    @safe
    def pay(self):
        payment = self.hostel.fees.pay(self.username, float(self.amount.get()), self.mode.get())
        self.amount.delete(0, "end")
        messagebox.showinfo("Receipt", f"Receipt no: {payment.id}\nAmount: Rs {payment.amount:,.0f}\n"
                                       f"Mode: {payment.mode}\nDate: {payment.paid_on}")
        self.refresh()
