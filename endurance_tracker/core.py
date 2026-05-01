"""Core UI components: TimeScheduler and DatePicker."""

from tkinter import *
from tkinter import ttk, TclError
from tkcalendar import Calendar
from pandas import to_datetime
from math import ceil
from datetime import timedelta

from .config import (
    CONTENT_BG, CONTENT_BG_DARK, ENTRY_BG, ENTRY_FG, ENTRY_BG_DARK,
    HOUR_STINT_FONT,
)


class TrackerError(Exception):
    pass


class TimeScheduler:
    """Displays a grid of driver × stint slots and handles availability toggles."""

    def __init__(self, root, settings, variables, elements, db, target='plan'):
        self.root = root
        self.settings = settings
        self.variables = variables
        self.elements = elements
        self.target = target
        self.widgets = {}
        self.db = db

        if target == 'plan' and 'plan_frame_plan' not in self.elements:
            raise TrackerError("Missing plan_frame_plan")
        if target == 'actual' and 'plan_frame_actual' not in self.elements:
            raise TrackerError("Missing plan_frame_actual")
        if 'drivers_raw' not in self.variables:
            raise TrackerError("Missing drivers_raw")

        self.create_widgets()

    def create_widgets(self):
        frame = (self.elements['plan_frame_plan']
                 if self.target == 'plan'
                 else self.elements['plan_frame_actual'])

        for i in range(100):
            frame.grid_columnconfigure(i, weight=0)
        for child in frame.winfo_children():
            child.destroy()

        self.root.update()
        bg = CONTENT_BG_DARK if self.settings['dark_mode'] else CONTENT_BG

        temp_label = Label(frame, text='Hour', background=bg)
        temp_label.grid(row=0, column=0, sticky='news', padx='0 5')
        self.widgets['label_hour'] = temp_label

        temp_label = Label(frame, text='Stints', background=bg)
        temp_label.grid(row=1, column=0, sticky='news', padx='0 5')
        self.widgets['label_stints'] = temp_label

        for i, driver in enumerate(self.variables['drivers_raw']):
            temp_label = Label(frame, text=driver, background=bg)
            temp_label.grid(row=2 + i, column=0, sticky='news', padx='0 5')
            self.widgets[f'label_{driver}'] = temp_label
            frame.grid_rowconfigure(2 + i, weight=1)

            total_time = self.get_delta('total_time').total_seconds()
            total_time_in_h = ceil(total_time / 3600)
            stint_time = self.get_delta('theoretical_stint_time').total_seconds()

            stints = ceil(total_time / stint_time)
            if self.target == 'actual':
                stints += ceil(0)  # reserved for predicted stints
            remains = int(total_time % stint_time) / stint_time
            weight = ceil(1 / remains) if remains else 1

            time_frame = Frame(frame, background=bg)
            time_frame.grid(row=0, column=1, sticky='news', padx=0, pady=0,
                            columnspan=stints)
            time_frame.grid_columnconfigure(0, weight=1)

            for j in range(total_time_in_h):
                tf = Frame(time_frame,
                           background=ENTRY_BG_DARK if self.settings['dark_mode'] else ENTRY_BG)
                tf.grid(row=0, column=j, sticky='news', padx=0, pady=0)
                tf.grid_columnconfigure(0, weight=1)
                tf.grid_rowconfigure(0, weight=1)
                self.widgets[f'frame_{driver}_h_{j + 1}'] = tf

                lbl = Label(tf, text=f"{j + 1:02d}", background=bg,
                            font=HOUR_STINT_FONT)
                lbl.grid(row=0, column=0, sticky='news', padx=2, pady='0 1')
                self.widgets[f'label_{driver}_h_{j + 1}'] = lbl
                time_frame.grid_columnconfigure(j, weight=1)

            for j in range(stints):
                sf = Frame(frame,
                           background=ENTRY_BG_DARK if self.settings['dark_mode'] else ENTRY_BG)
                sf.grid(row=1, column=j + 1, sticky='news', padx=0, pady=0)
                sf.grid_columnconfigure(0, weight=1)
                sf.grid_rowconfigure(0, weight=1)
                self.widgets[f'frame_{driver}_s_{j + 1}'] = sf

                lbl = Label(sf, text=f"{j + 1:02d}", background=bg,
                            font=HOUR_STINT_FONT)
                lbl.grid(row=0, column=0, sticky='news', padx=2, pady='1 0')
                self.widgets[f'label_{driver}_s_{j + 1}'] = lbl

                slot_bg = 'red'
                slot_val = self.variables['drivers_time_slots'].get(driver, [])
                if j < len(slot_val):
                    if slot_val[j] == '1':
                        slot_bg = 'green'
                    elif slot_val[j] == '2':
                        slot_bg = 'yellow'

                cell = Frame(frame, background=slot_bg)
                cell.grid(row=2 + i, column=j + 1, sticky='news', padx=1, pady=1)
                self.widgets[f'frame_{driver}_{j + 1}'] = cell
                cell.bind('<Button-1>', self.toggle_frame)

                frame.grid_columnconfigure(j + 1,
                                           weight=1 if j == stints - 1 else weight)

    def toggle_frame(self, event=None):
        widget = event.widget
        driver, hour = self.get_widget_name(widget)
        if driver is False:
            return

        idx = int(hour) - 1
        slots = self.variables['drivers_time_slots'].setdefault(driver, [])
        while len(slots) <= idx:
            slots.append('0')

        current = widget['background']
        if current == 'green':
            widget['background'] = 'yellow'
            slots[idx] = '2'
        elif current == 'yellow':
            widget['background'] = 'red'
            slots[idx] = '0'
        else:
            widget['background'] = 'green'
            slots[idx] = '1'

        # Persist to DB
        if self.db is not None:
            available = [i + 1 for i, v in enumerate(slots) if v == '1']
            maybe = [i + 1 for i, v in enumerate(slots) if v == '2']
            unavailable = [i + 1 for i, v in enumerate(slots) if v == '0']
            self.db.update_driver_slots(driver, available, maybe, unavailable)

    def get_widget_name(self, widget):
        for key, value in self.widgets.items():
            if value == widget:
                parts = key.split('_')
                if len(parts) >= 3:
                    driver = parts[1]
                    hour = parts[2]
                    return driver, hour
        return False, False

    def __del__(self):
        for value in self.widgets.values():
            try:
                value.destroy()
            except Exception:
                pass
        try:
            self.root.update()
        except Exception:
            pass

    def get_delta(self, variable=''):
        if f'{variable}_h' not in self.variables:
            return timedelta(0)
        try:
            return timedelta(
                hours=float(self.variables[f'{variable}_h'].get()),
                minutes=float(self.variables[f'{variable}_m'].get()),
                seconds=float(self.variables[f'{variable}_s'].get()),
            )
        except (ValueError, TclError):
            return timedelta(0)


class DatePicker:
    """An Entry + calendar-button widget for selecting a date."""

    def __init__(self, master, root, settings, variables, elements):
        self.root = root
        self.settings = settings
        self.variables = variables
        self.elements = elements
        self.master = master
        self.widgets = {}
        self.create_widgets()

    def create_widgets(self):
        frame = Frame(self.master, background=CONTENT_BG, relief='sunken',
                      borderwidth=1)
        frame.grid(row=0, column=0, sticky='news')
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.widgets['main_frame'] = frame

        self.entry = Entry(frame, width=20, border=0, borderwidth=0,
                           relief='flat', justify='center')
        if self.master == self.elements.get('entry_event_date'):
            self.entry.config(textvariable=self.variables['event_date'])
            self.widgets['entry_var'] = self.variables['event_date']
        else:
            raise TrackerError("Invalid master for DatePicker")

        self.entry.grid(row=0, column=0, sticky='news', padx=(0, 5))
        self.widgets['entry'] = self.entry

        self.date_picker_icon = Button(frame, text='📅',
                                       command=self.open_date_picker,
                                       border=0, borderwidth=0, relief='flat')
        self.date_picker_icon.grid(row=0, column=1, sticky='news')
        self.widgets['date_picker_icon'] = self.date_picker_icon

    def open_date_picker(self):
        top = Toplevel(self.root)
        top.resizable(False, False)
        top.title("Select Date")

        cal = Calendar(top, selectmode='day')
        cal.grid(column=0, row=0, padx=0, pady=0)
        self.widgets['calendar'] = cal

        try:
            cal.see(to_datetime(self.variables['event_date'].get()))
        except Exception:
            pass

        def on_date_select():
            selected_date = cal.selection_get()
            self.widgets['entry_var'].set(
                f"{selected_date.strftime('%m-%d-%Y')} ")
            top.destroy()

        select_button = Button(top, text="Select", command=on_date_select)
        select_button.grid(column=0, row=2, pady=5)
