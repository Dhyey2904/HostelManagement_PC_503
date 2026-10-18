from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass
class Student:
    roll_no: str
    name: str
    gender: str
    program: str
    phone: str
    password: str = "pass123"
    room_no: str = ""
    sleep: str = "Flexible"
    cleanliness: int = 3
    diet: str = "Veg"
    language: str = "Gujarati"
    strikes: int = 0


@dataclass
class Room:
    number: str
    gender: str
    capacity: int
    occupants: list = field(default_factory=list)

    @property
    def floor(self):
        return int(self.number[2])

    def is_full(self):
        return len(self.occupants) >= self.capacity

    def free_beds(self):
        return self.capacity - len(self.occupants)


@dataclass
class Complaint:
    id: int
    roll_no: str
    room_no: str
    category: str
    text: str
    priority: str
    deadline: datetime
    status: str = "Open"

    def time_left(self):
        seconds = int((self.deadline - datetime.now()).total_seconds())
        if seconds < 0:
            return "Overdue"
        return f"{seconds // 60}m {seconds % 60:02d}s"


@dataclass
class GatePass:
    id: int
    roll_no: str
    place: str
    reason: str
    return_by: datetime
    status: str = "Pending"
    code: str = ""
    late: bool = False


@dataclass
class SwapRequest:
    id: int
    roll_no: str
    from_room: str
    to_room: str
    status: str = "Open"


@dataclass
class Payment:
    id: int
    roll_no: str
    amount: float
    mode: str
    paid_on: date = field(default_factory=date.today)


@dataclass
class Notice:
    title: str
    text: str
    posted: date = field(default_factory=date.today)
