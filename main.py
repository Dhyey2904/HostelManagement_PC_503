from gui.app import HostelApp
from hostel import Hostel
from sample_data import load_sample_data

if __name__ == "__main__":
    hostel = Hostel()
    load_sample_data(hostel)
    HostelApp(hostel).mainloop()
