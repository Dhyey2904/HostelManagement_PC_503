# DAIICT Hostel Management System

**Name:** Dhyey Patel  
**Enrollment No.:** 202611059  
**Group:** 19  
**Course ID:** PC 503  
**GitHub:** https://github.com/Dhyey2904/HostelManagement_PC_503

---

## About the Project

This is a desktop application for managing a college hostel, written in Python with a Tkinter GUI.
It has three types of users, the **Warden**, **Students** and **Security**, and each one gets
its own set of tabs after logging in. The app covers the main parts of hostel life: room allotment,
roommate matching, complaints, gate passes, the mess, laundry and fees.

The app starts with a small set of sample data (16 rooms in Block A for boys and Block B for girls, plus
10 students, some complaints, passes and payments), so every screen has something to show as soon as it opens.
All data is kept in memory, so it resets each time the program restarts.

## How to Run

**Requirements:** Python 3.10 or newer with Tkinter (Tkinter comes with the standard
Python installers for Windows and macOS). You don't need to install any other packages.

```bash
# 1. Clone the repository
git clone https://github.com/Dhyey2904/HostelManagement_PC_503.git
cd HostelManagement_PC_503

# 2. Run the app
python3 main.py        # on Windows: python main.py
```

On Linux, if you get a `No module named tkinter` error, install it first with
`sudo apt install python3-tk`.

## Login Credentials

| Role     | Username                     | Password    |
|----------|------------------------------|-------------|
| Warden   | `warden`                     | `warden123` |
| Security | `security`                   | `gate123`   |
| Student  | `202611059` (any roll no.)   | `pass123`   |

Every sample student uses the password `pass123`. Other roll numbers you can log in with:
`202611012`, `202611023`, `202611034`, `202611045`, `202611056` (boys) and
`202611067`, `202611078`, `202611089`, `202611090` (girls).

## Features

### Warden
- **Students**: add students (the roll no. must be 9 digits and the phone number 10 digits), view them and remove them.
- **Rooms**: a colour-coded floor map for each block and floor (green = empty, yellow = partly filled, red = full).
  You can allot a room, vacate a student, or use **Suggest best room** to pick the vacant room whose
  occupants match the student best.
- **Complaints**: see every active complaint with a live countdown to its deadline, and mark each one In Progress or Resolved.
  When a complaint passes its deadline, it is **escalated automatically** to a higher priority.
- **Gate Pass**: approve or reject students' outing requests. An approved pass gets a 4-digit code.
- **Room Swaps**: finds **mutual swaps** (two students who want each other's rooms) and **direct moves**
  into rooms that have a free bed, and approves them in one click.
- **Mess**: shows today's menu, the meal headcount after opt-outs, and a table of dish ratings.
- **Fees**: shows each student's fee, late fine, mess rebate, amount paid and dues, and lets the warden record payments.
- **Notices**: post notices that students see on their Home tab.

### Student
- **Home**: profile, room, roommates, fee dues and the latest notices.
- **Roommates**: set lifestyle preferences (sleep time, cleanliness, diet, language). The app then shows a
  **compatibility score out of 100** with other students, and you can request a room swap.
- **Complaints**: file a complaint (Wi-Fi, plumbing, electrical and so on) with a priority and track its status.
- **Gate Pass**: request a pass with a place, a reason and a return time, then see its status and gate code.
- **Mess**: see today's menu, rate a meal (1–5 stars) and opt out of future meals, which gives a rebate on fees.
- **Laundry**: book one washing machine slot for today (3 machines, 8 AM to 10 PM) or cancel it.
- **Fees**: see the fee breakdown and payment history, and pay online.

### Security
- **Gate**: enter a pass code to mark a student **Out** or **In**. If a student comes back after the return time,
  they get a **strike**. At 3 strikes the app posts a curfew alert and the student can't request new passes.

### Rules built into the app
- Rooms are separated by gender: Block A is for boys and Block B is for girls.
- Fees are ₹52,000 for a single room and ₹42,000 for a double room. The due date is 30 Sep 2026.
- The late fine is ₹50 per day, up to a maximum of ₹5,000.
- Complaint deadlines are kept short for the demo: High = 2 min, Medium = 5 min, Low = 10 min.
- Mess rebates are ₹30 for breakfast and ₹55 each for lunch and dinner.

## Project Structure

```
HostelManagement/
├── main.py            # Entry point: loads sample data and starts the GUI
├── models.py          # Dataclasses: Student, Room, Complaint, GatePass, Payment, ...
├── hostel.py          # Core logic: Hostel, Allotment, ComplaintDesk, GateDesk, Mess, Laundry, FeeDesk
├── sample_data.py     # Demo rooms, students and records
└── gui/
    ├── app.py         # Main window, role-based tabs, auto-refresh timer
    ├── login.py       # Login screen
    ├── common.py      # Shared Table widget, Tab base class, error handling helper
    ├── warden_tabs.py # Warden screens
    ├── student_tabs.py# Student screens
    └── security_tab.py# Security gate screen
```
