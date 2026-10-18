import random
from datetime import date, datetime, timedelta

from models import Complaint, GatePass, Notice, Payment, SwapRequest

FEES = {1: 52000, 2: 42000}
DUE_DATE = date(2026, 9, 30)
FINE_PER_DAY = 50
MAX_FINE = 5000
MAX_STRIKES = 3
PRIORITIES = ["Low", "Medium", "High"]
SLA_MINUTES = {"Low": 10, "Medium": 5, "High": 2}  # kept short for demo
MEALS = ["Breakfast", "Lunch", "Dinner"]
MEAL_PRICE = {"Breakfast": 30, "Lunch": 55, "Dinner": 55}
MACHINES = 3
LAUNDRY_HOURS = range(8, 22)

MENU = {
    "Monday": ["Poha", "Rajma Chawal", "Paneer Masala"],
    "Tuesday": ["Idli Sambar", "Gujarati Thali", "Veg Biryani"],
    "Wednesday": ["Aloo Paratha", "Chole Bhature", "Dal Makhani"],
    "Thursday": ["Upma", "Kadhi Khichdi", "Mix Veg Roti"],
    "Friday": ["Masala Dosa", "Undhiyu Puri", "Malai Kofta"],
    "Saturday": ["Sandwich", "Pulao Raita", "Pav Bhaji"],
    "Sunday": ["Chole Kulche", "Special Thali", "Khichdi"],
}


class HostelError(Exception):
    pass


def todays_menu(day=None):
    day = day or date.today()
    return dict(zip(MEALS, MENU[day.strftime("%A")]))


class Hostel:
    """Holds all data of hostel."""

    def __init__(self):
        self.students = {}
        self.rooms = {}
        self.notices = []
        self.staff = {"warden": ("warden123", "Warden"),
                      "security": ("gate123", "Security")}
        self.last_id = 0
        self.allotment = Allotment(self)
        self.complaints = ComplaintDesk(self)
        self.gate = GateDesk(self)
        self.mess = Mess(self)
        self.laundry = Laundry(self)
        self.fees = FeeDesk(self)

    def new_id(self):
        self.last_id += 1
        return self.last_id

    def login(self, username, password):
        if username in self.staff and self.staff[username][0] == password:
            return self.staff[username][1]
        student = self.students.get(username)
        if student and student.password == password:
            return "Student"
        raise HostelError("Wrong username or password")

    def student(self, roll_no):
        if roll_no not in self.students:
            raise HostelError(f"No student with roll no {roll_no}")
        return self.students[roll_no]

    def add_student(self, student):
        if len(student.roll_no) != 9 or not student.roll_no.isdigit():
            raise HostelError("Roll no must be 9 digits")
        if student.roll_no in self.students:
            raise HostelError("Roll no already exists")
        if not student.name:
            raise HostelError("Name is required")
        if len(student.phone) != 10 or not student.phone.isdigit():
            raise HostelError("Phone must be 10 digits")
        self.students[student.roll_no] = student

    def remove_student(self, roll_no):
        if self.student(roll_no).room_no:
            self.allotment.vacate(roll_no)
        del self.students[roll_no]

    def post_notice(self, title, text):
        if not title or not text:
            raise HostelError("Title and text are required")
        self.notices.insert(0, Notice(title, text))


class Allotment:
    """Rooms, roommate matching and swaps."""

    def __init__(self, hostel):
        self.hostel = hostel
        self.swaps = []

    def allot(self, roll_no, room_no):
        student = self.hostel.student(roll_no)
        room = self.hostel.rooms[room_no]
        if student.room_no == room_no:
            raise HostelError("Student is already in this room")
        if room.gender != student.gender:
            raise HostelError(f"{room_no} is a {room.gender.lower()} room")
        if room.is_full():
            raise HostelError(f"Room {room_no} is full")
        if student.room_no:
            self.vacate(roll_no)
        room.occupants.append(roll_no)
        student.room_no = room_no

    def vacate(self, roll_no):
        student = self.hostel.student(roll_no)
        if not student.room_no:
            raise HostelError("Student has no room")
        self.hostel.rooms[student.room_no].occupants.remove(roll_no)
        student.room_no = ""

    def occupancy(self):
        rooms = self.hostel.rooms.values()
        used = sum(len(r.occupants) for r in rooms)
        return used, sum(r.capacity for r in rooms)

    def roommates(self, roll_no):
        room_no = self.hostel.student(roll_no).room_no
        if not room_no:
            return []
        ids = self.hostel.rooms[room_no].occupants
        return [self.hostel.students[i] for i in ids if i != roll_no]

    @staticmethod
    def compatibility(a, b):
        """Score out of 100."""
        order = ["Early", "Flexible", "Late"]
        score = 30 - 15 * abs(order.index(a.sleep) - order.index(b.sleep))
        score += 25 - 6 * abs(a.cleanliness - b.cleanliness)
        score += 15 if a.diet == b.diet else 0
        score += 15 if a.language == b.language else 0
        score += 15 if a.program == b.program else 0
        return max(score, 0)

    def best_matches(self, roll_no, count=5):
        me = self.hostel.student(roll_no)
        others = [s for s in self.hostel.students.values()
                  if s.gender == me.gender and s.roll_no != roll_no]
        scored = [(self.compatibility(me, s), s) for s in others]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[:count]

    def suggest_room(self, roll_no):
        """Vacant room with best roommates."""
        me = self.hostel.student(roll_no)
        best_room, best_score = None, -1
        for room in self.hostel.rooms.values():
            if room.gender != me.gender or room.is_full() or room.number == me.room_no:
                continue
            mates = [self.hostel.students[i] for i in room.occupants]
            score = 50
            if mates:
                score = sum(self.compatibility(me, m) for m in mates) // len(mates)
            if score > best_score:
                best_room, best_score = room, score
        return best_room, best_score

    def request_swap(self, roll_no, to_room):
        student = self.hostel.student(roll_no)
        if not student.room_no:
            raise HostelError("You don't have a room yet")
        if to_room == student.room_no:
            raise HostelError("This is already your room")
        if self.hostel.rooms[to_room].gender != student.gender:
            raise HostelError("You can't move to that block")
        if any(r.roll_no == roll_no and r.status == "Open" for r in self.swaps):
            raise HostelError("You already have an open request")
        self.swaps.append(SwapRequest(self.hostel.new_id(), roll_no,
                                      student.room_no, to_room))

    def open_swaps(self):
        return [r for r in self.swaps if r.status == "Open"]

    def possible_swaps(self):
        """Mutual swaps and direct moves."""
        result = []
        used = set()
        requests = self.open_swaps()
        for a in requests:
            for b in requests:
                if a.id < b.id and a.to_room == b.from_room and b.to_room == a.from_room:
                    result.append(("Mutual swap", [a, b]))
                    used.update([a.id, b.id])
        for r in requests:
            if r.id not in used and not self.hostel.rooms[r.to_room].is_full():
                result.append(("Direct move", [r]))
        return result

    def approve_swap(self, requests):
        for r in requests:
            self.vacate(r.roll_no)
        for r in requests:
            self.allot(r.roll_no, r.to_room)
            r.status = "Done"


class ComplaintDesk:
    def __init__(self, hostel):
        self.hostel = hostel
        self.items = []

    def add(self, roll_no, category, text, priority):
        student = self.hostel.student(roll_no)
        if not student.room_no:
            raise HostelError("Only hostel residents can complain")
        if len(text) < 5:
            raise HostelError("Please describe the problem")
        deadline = datetime.now() + timedelta(minutes=SLA_MINUTES[priority])
        complaint = Complaint(self.hostel.new_id(), roll_no, student.room_no,
                              category, text, priority, deadline)
        self.items.append(complaint)
        return complaint

    def find(self, complaint_id):
        for c in self.items:
            if c.id == complaint_id:
                return c
        raise HostelError("Complaint not found")

    def set_status(self, complaint_id, status):
        complaint = self.find(complaint_id)
        if complaint.status == "Resolved":
            raise HostelError("Already resolved")
        complaint.status = status

    def check_overdue(self):
        """Escalate complaints past deadline."""
        for c in self.items:
            if c.status != "Resolved" and datetime.now() > c.deadline:
                level = min(PRIORITIES.index(c.priority) + 1, len(PRIORITIES) - 1)
                c.priority = PRIORITIES[level]
                c.status = "Escalated"
                c.deadline = datetime.now() + timedelta(minutes=SLA_MINUTES[c.priority])

    def of_student(self, roll_no):
        return [c for c in self.items if c.roll_no == roll_no]

    def active(self):
        return [c for c in self.items if c.status != "Resolved"]


class GateDesk:
    def __init__(self, hostel):
        self.hostel = hostel
        self.passes = []

    def request(self, roll_no, place, reason, return_by):
        student = self.hostel.student(roll_no)
        if not place or not reason:
            raise HostelError("Place and reason are required")
        if return_by <= datetime.now():
            raise HostelError("Return time should be in future")
        if student.strikes >= MAX_STRIKES:
            raise HostelError("Too many late returns, meet warden")
        if self.active_pass(roll_no):
            raise HostelError("You already have an active pass")
        self.passes.append(GatePass(self.hostel.new_id(), roll_no, place, reason, return_by))

    def active_pass(self, roll_no):
        for p in self.passes:
            if p.roll_no == roll_no and p.status in ("Pending", "Approved", "Out"):
                return p
        return None

    def find(self, pass_id):
        for p in self.passes:
            if p.id == pass_id:
                return p
        raise HostelError("Pass not found")

    def approve(self, pass_id):
        gate_pass = self.find(pass_id)
        if gate_pass.status != "Pending":
            raise HostelError("Only pending passes can be approved")
        gate_pass.status = "Approved"
        gate_pass.code = str(random.randint(1000, 9999))

    def reject(self, pass_id):
        self.find(pass_id).status = "Rejected"

    def by_code(self, code, status):
        for p in self.passes:
            if p.code == code.strip() and p.status == status:
                return p
        raise HostelError(f"No {status.lower()} pass with code {code}")

    def mark_out(self, code):
        gate_pass = self.by_code(code, "Approved")
        gate_pass.status = "Out"
        return gate_pass

    def mark_in(self, code):
        """Late return gives a strike."""
        gate_pass = self.by_code(code, "Out")
        gate_pass.status = "Returned"
        if datetime.now() > gate_pass.return_by:
            gate_pass.late = True
            student = self.hostel.student(gate_pass.roll_no)
            student.strikes += 1
            if student.strikes == MAX_STRIKES:
                self.hostel.post_notice("Curfew alert",
                                        f"{student.name} has {MAX_STRIKES} late returns")
        return gate_pass

    def with_status(self, status):
        return [p for p in self.passes if p.status == status]


class Mess:
    def __init__(self, hostel):
        self.hostel = hostel
        self.opt_outs = []
        self.ratings = {}
        self.rated = set()

    def opt_out(self, roll_no, day, meal):
        if day <= date.today():
            raise HostelError("Opt out at least one day before")
        if (roll_no, day, meal) in self.opt_outs:
            raise HostelError("Already opted out")
        self.opt_outs.append((roll_no, day, meal))

    def opt_outs_of(self, roll_no):
        return sorted(o for o in self.opt_outs if o[0] == roll_no)

    def rebate(self, roll_no):
        return sum(MEAL_PRICE[meal] for r, day, meal in self.opt_outs if r == roll_no)

    def headcount(self, day):
        residents = len([s for s in self.hostel.students.values() if s.room_no])
        counts = {}
        for meal in MEALS:
            skipped = len([o for o in self.opt_outs if o[1] == day and o[2] == meal])
            counts[meal] = residents - skipped
        return counts

    def rate(self, roll_no, meal, stars):
        key = (roll_no, date.today(), meal)
        if key in self.rated:
            raise HostelError("You already rated this meal")
        dish = todays_menu()[meal]
        self.ratings.setdefault(dish, []).append(stars)
        self.rated.add(key)

    def dish_report(self):
        report = [(dish, sum(s) / len(s), len(s)) for dish, s in self.ratings.items()]
        return sorted(report, key=lambda row: row[1], reverse=True)


class Laundry:
    """Today's washing machine slots."""

    def __init__(self, hostel):
        self.hostel = hostel
        self.slots = {}

    def book(self, roll_no, machine, hour):
        if hour <= datetime.now().hour:
            raise HostelError("This slot time has passed")
        if (machine, hour) in self.slots:
            raise HostelError("Slot already booked")
        if roll_no in self.slots.values():
            raise HostelError("Only one slot per student")
        self.slots[(machine, hour)] = roll_no

    def cancel(self, roll_no):
        for key, owner in list(self.slots.items()):
            if owner == roll_no:
                del self.slots[key]

    def slot_of(self, roll_no):
        for key, owner in self.slots.items():
            if owner == roll_no:
                return key
        return None


class FeeDesk:
    def __init__(self, hostel):
        self.hostel = hostel
        self.payments = []

    def fee(self, roll_no):
        room_no = self.hostel.student(roll_no).room_no
        return FEES[self.hostel.rooms[room_no].capacity] if room_no else 0

    def payments_of(self, roll_no):
        return [p for p in self.payments if p.roll_no == roll_no]

    def paid(self, roll_no):
        return sum(p.amount for p in self.payments_of(roll_no))

    def fine(self, roll_no):
        """Fine counted till fee cleared."""
        need = self.fee(roll_no) - self.hostel.mess.rebate(roll_no)
        if need <= 0:
            return 0
        total = 0
        last_day = date.today()
        for p in sorted(self.payments_of(roll_no), key=lambda p: p.paid_on):
            total += p.amount
            if total >= need:
                last_day = p.paid_on
                break
        late_days = max((last_day - DUE_DATE).days, 0)
        return min(late_days * FINE_PER_DAY, MAX_FINE)

    def dues(self, roll_no):
        total = (self.fee(roll_no) + self.fine(roll_no)
                 - self.hostel.mess.rebate(roll_no) - self.paid(roll_no))
        return max(total, 0)

    def pay(self, roll_no, amount, mode):
        if amount <= 0:
            raise HostelError("Amount should be positive")
        if amount > self.dues(roll_no):
            raise HostelError(f"Amount is more than dues (Rs {self.dues(roll_no):.0f})")
        payment = Payment(self.hostel.new_id(), roll_no, amount, mode)
        self.payments.append(payment)
        return payment

    def total_dues(self):
        return sum(self.dues(r) for r in self.hostel.students)
