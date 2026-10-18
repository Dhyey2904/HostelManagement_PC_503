from tkinter import messagebox, ttk

from hostel import HostelError


def safe(func):
    """Show errors as popup."""
    def wrapper(*args):
        try:
            func(*args)
        except HostelError as e:
            messagebox.showerror("Error", str(e))
        except ValueError:
            messagebox.showerror("Error", "Please enter valid values")
    return wrapper


class Table(ttk.Frame):
    """Treeview with a scrollbar."""

    def __init__(self, parent, columns, widths, height=10):
        super().__init__(parent)
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=height)
        for col, width in zip(columns, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width)
        bar = ttk.Scrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=bar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        bar.pack(side="right", fill="y")

    def load(self, rows, use_first_as_id=True):
        selected = self.selected()
        self.tree.delete(*self.tree.get_children())
        for row in rows:
            iid = str(row[0]) if use_first_as_id else None
            self.tree.insert("", "end", iid=iid, values=row)
        if selected and self.tree.exists(selected):
            self.tree.selection_set(selected)

    def selected(self):
        items = self.tree.selection()
        return items[0] if items else None

    def need_selection(self):
        if not self.selected():
            raise HostelError("Please select a row first")
        return self.selected()


class Tab(ttk.Frame):
    """Base class for all tabs."""
    auto_refresh = False

    def __init__(self, parent, hostel, username):
        super().__init__(parent, padding=10)
        self.hostel = hostel
        self.username = username

    def refresh(self):
        pass


def form_row(parent, row, label, widget):
    ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", pady=3, padx=(0, 8))
    widget.grid(row=row, column=1, sticky="ew", pady=3)
    return widget
