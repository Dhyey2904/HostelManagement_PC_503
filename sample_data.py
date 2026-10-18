from datetime import date, datetime, timedelta

from models import GatePass, Payment, Room, Student


def load_sample_data(hostel):
    """Small data set for testing."""
    for block, gender in (("A", "Male"), ("B", "Female")):
        for floor in (1, 2):
            for num in range(1, 5):
                capacity = 1 if num == 4 else 2
                number = f"{block}-{floor}0{num}"
                hostel.rooms[number] = Room(number, gender, capacity)

    students = [
        Student("202611059", "Dhyey Patel", "Male", "B.Tech ICT", "9876500011",
                sleep="Late", cleanliness=4),
        Student("202611012", "Aarav Shah", "Male", "B.Tech ICT", "9876500012",
                sleep="Late", cleanliness=4, language="Gujarati"),
        Student("202611023", "Rohan Iyer", "Male", "M.Sc IT", "9876500013",
                sleep="Early", cleanliness=5, diet="Non-veg", language="Tamil"),
        Student("202611034", "Karan Mehta", "Male", "B.Tech MnC", "9876500014",
                cleanliness=2, language="Hindi"),
        Student("202611045", "Yash Trivedi", "Male", "B.Tech ICT", "9876500015",
                sleep="Late", cleanliness=3),
        Student("202611056", "Neel Desai", "Male", "M.Tech ICT", "9876500016"),
        Student("202611067", "Diya Patel", "Female", "B.Tech ICT", "9876500017",
                sleep="Early", cleanliness=5),
        Student("202611078", "Sneha Rao", "Female", "M.Sc DS", "9876500018",
                language="Telugu", diet="Non-veg"),
        Student("202611089", "Isha Joshi", "Female", "B.Tech ICT", "9876500019",
                sleep="Early", cleanliness=4),
        Student("202611090", "Riya Nair", "Female", "B.Tech EVD", "9876500020",
                sleep="Late", language="Malayalam"),
    ]
    for s in students:
        hostel.students[s.roll_no] = s

    for roll_no, room_no in [("202611059", "A-101"), ("202611012", "A-101"),
                             ("202611023", "A-102"), ("202611034", "A-103"),
                             ("202611045", "A-103"), ("202611067", "B-101"),
                             ("202611078", "B-102"), ("202611089", "B-102")]:
        hostel.allotment.allot(roll_no, room_no)

    hostel.complaints.add("202611059", "Wi-Fi", "Wi-Fi not working at night", "High")
    hostel.complaints.add("202611078", "Plumbing", "Tap is leaking in bathroom", "Medium")

    hostel.allotment.request_swap("202611023", "A-103")
    hostel.allotment.request_swap("202611034", "A-102")

    late = hostel.student("202611045")
    late.strikes = 2
    hostel.gate.passes.append(GatePass(hostel.new_id(), late.roll_no, "Infocity",
                                       "Dinner", datetime.now() - timedelta(minutes=30),
                                       status="Out", code="4321"))
    hostel.gate.request("202611089", "Home", "Weekend visit",
                        datetime.now() + timedelta(days=2))

    hostel.fees.payments.append(Payment(hostel.new_id(), "202611012", 42000, "UPI",
                                        date(2026, 9, 20)))
    hostel.fees.payments.append(Payment(hostel.new_id(), "202611059", 20000, "UPI",
                                        date(2026, 9, 25)))
    hostel.fees.payments.append(Payment(hostel.new_id(), "202611067", 42000, "Card",
                                        date(2026, 10, 5)))

    hostel.mess.ratings = {"Poha": [4, 5, 4], "Rajma Chawal": [3, 4], "Khichdi": [2, 3]}
    hostel.post_notice("Welcome", "Hostel fee due date is 30 Sep. Curfew is 10:30 PM.")
