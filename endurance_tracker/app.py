"""EnduranceTracker main application module.

Contains all Tkinter UI logic, globals, and the main() entry point.
"""

from tkinter import *
from tkinter import ttk, simpledialog, messagebox
from customtkinter import CTkOptionMenu
from threading import Thread
from datetime import datetime, timedelta
from tkcalendar import Calendar, DateEntry
from time import sleep
from math import ceil
import pytz
from pandas import DataFrame, concat

from .config import (
    GEOMETRY, STATUS_TIMES, DARK_MODE as _INITIAL_DARK_MODE,
    DATA_DIR, IS_SERVER, HOST, PORT,
    MAX_DRIVER, WEATHER_LENGTH,
    STATUS_BG, CONTENT_BG, STATUS_BG_DARK, CONTENT_BG_DARK,
    TAB_BG, TAB_BG_ACTIVE, TAB_BG_DARK, TAB_BG_DARK_ACTIVE,
    DARK_FG, ENTRY_BG, ENTRY_FG, ENTRY_BG_DARK, ENTRY_FG_DARK,
    LABEL_FG, LABEL_FG_DARK,
    BUTTON_BG, BUTTON_FG, BUTTON_BG_DARK, BUTTON_FG_DARK,
    HOUR_STINT_FONT, WEATHER_CONDITIONS, TRACK_CONDITIONS,
    DATA_ITEMS, TRACKER_COLUMNS,
    get_config, set_config,
)
from .db import Database
from .helpers import TrackerClient, TrackerServer, tz_diff, format_timedelta
from .core import TimeScheduler, DatePicker

# ─────────────────────────────────────────── module-level globals ─────────────

root: Tk = None
settings: dict = {}
variables: dict = {}
elements: dict = {}
current_event: str = 'Template'
tracker: DataFrame = None
server: TrackerServer = None
client: TrackerClient = None
DARK_MODE: bool = _INITIAL_DARK_MODE


# ─────────────────────────────────────── small helpers ────────────────────────

def get_db() -> Database:
    """Return the active Database instance (server or client)."""
    if variables.get('is_server') and variables['is_server'].get():
        return server.db
    return client.db


def get_delta(variable=''):
    """Return a timedelta from HH:MM:SS StringVars or a literal 'HH:MM:SS' string."""
    if f'{variable}_h' not in variables:
        try:
            parts = variable.split(':')
            return timedelta(hours=float(parts[0]),
                             minutes=float(parts[1]),
                             seconds=float(parts[2]))
        except Exception:
            return timedelta(0)
    try:
        return timedelta(
            hours=float(variables[f'{variable}_h'].get()),
            minutes=float(variables[f'{variable}_m'].get()),
            seconds=float(variables[f'{variable}_s'].get()),
        )
    except (ValueError, TclError):
        return timedelta(0)


def set_time(variable='', time='00:00:00'):
    if f'{variable}_h' not in variables:
        return
    parts = time.split(':')
    variables[f'{variable}_h'].set(parts[0] if len(parts) > 0 else '0')
    variables[f'{variable}_m'].set(parts[1] if len(parts) > 1 else '0')
    variables[f'{variable}_s'].set(parts[2] if len(parts) > 2 else '0')


def get_duration(variable='event_time_est', tz_from='US/Eastern', tz_to='GMT'):
    if variable not in variables:
        return timedelta(0)
    try:
        return datetime.now(pytz.utc) - tz_diff(variables[variable].get(),
                                                  tz_from, tz_to)
    except Exception:
        return timedelta(0)


# ─────────────────────────────────────────────── DB ↔ UI sync ─────────────────

def load_from_db():
    """Populate UI variables from the Database on startup."""
    global tracker

    db = get_db()
    event_data = db.get_event_data()

    # Event fields
    field_map = {
        'event': 'event',
        'event_date': 'event_date',
        'car': 'car',
        'current_position': 'current_position',
        'total_drivers': 'total_drivers',
    }
    for var_key, db_key in field_map.items():
        if var_key in variables and db_key in event_data:
            variables[var_key].set(event_data[db_key])

    # Time fields stored as HH:MM:SS
    time_fields = [
        'event_time', 'total_time', 'gap_2_start', 'practice_duration',
        'qualify_duration', 'time_to_green', 'time_to_start',
        'sim_time_start', 'theoretical_stint_time', 'average_stint_time',
    ]
    for field in time_fields:
        if field in event_data:
            set_time(field, event_data[field])

    # event_time_est (display only, derived from event_date + event_time)
    if 'event_date' in event_data and 'event_time' in event_data:
        variables.get('event_time_est',
                      StringVar()).set(
            f"{event_data.get('event_date', '')} "
            f"{event_data.get('event_time', '00:00:00')}"
        )

    # Drivers
    drivers_data = db.get_drivers()
    variables['drivers_raw'] = []
    variables['drivers_time_slots'] = {}

    total_stints = _compute_total_stints()

    for d in drivers_data:
        name = d['name']
        variables['drivers_raw'].append(name)
        slots = ['0'] * total_stints
        for idx in d['available']:
            i = int(idx) - 1
            if 0 <= i < total_stints:
                slots[i] = '1'
        for idx in d['maybe']:
            i = int(idx) - 1
            if 0 <= i < total_stints:
                slots[i] = '2'
        variables['drivers_time_slots'][name] = slots

    if 'drivers' in variables:
        variables['drivers'].set(variables['drivers_raw'])

    # Tracker DataFrame
    _reload_tracker_from_db(db)

    # Update driver dropdowns
    for key in ('race_tracker_edit_driver_entry',
                'race_tracker_edit_actual_driver_entry',
                'race_tracker_current_driver_entry',
                'race_tracker_current_actual_driver_entry'):
        if key in elements:
            elements[key].configure(values=variables['drivers_raw'])

    # Weather dropdowns
    for key in ('race_tracker_edit_actual_weather_entry',
                'race_tracker_current_actual_weather_entry'):
        if key in elements:
            elements[key].configure(values=WEATHER_CONDITIONS)


def _compute_total_stints() -> int:
    """Return the total number of theoretical stints based on current variables."""
    try:
        total = get_delta('total_time').total_seconds()
        stint = get_delta('theoretical_stint_time').total_seconds()
        if stint > 0:
            return ceil(total / stint)
    except Exception:
        pass
    return 100  # sensible default


def _reload_tracker_from_db(db: Database):
    """Re-build the in-memory tracker DataFrame from DB."""
    global tracker

    slots = db.get_tracker_slots()
    cols = TRACKER_COLUMNS
    rows = []
    for s in slots:
        rows.append([
            s['time_slot'],
            s['planned_driver'],
            s['planned_stint'],
            s['actual_stint'],
            s['actual_driver'],
            s['est_rain'],
            s['act_weather'],
            s['notes'],
        ])
    tracker = DataFrame(data=rows, columns=cols)

    # Update the listbox in the race tab if it exists
    if 'race_tracker_slots' in elements:
        variables['race_tracker_slots_raw'] = (
            tracker['Overall Time Slots'].values.tolist()
        )
        variables['race_tracker_slots'].set(variables['race_tracker_slots_raw'])
        elements['race_tracker_slots'].update()


def _tracker_row_to_db_slot(row_idx: int) -> dict:
    """Convert a tracker DataFrame row to a DB slot dict."""
    row = tracker.iloc[row_idx]
    return {
        'time_slot': str(row['Overall Time Slots']),
        'planned_driver': str(row['Driver']),
        'planned_stint': str(row['Theoretical Stints #']),
        'actual_driver': str(row['Actual Driver']),
        'actual_stint': str(row['Actual Stints #']),
        'est_rain': row['Est. Chance of Rain (%)'],
        'act_weather': str(row['Act. Weather at Time']),
        'act_track_condition': '',
        'notes': str(row['Notes']),
    }


# ─────────────────────────────────────────── main / loading ───────────────────

def main():
    global root, settings, variables, elements

    root = Tk()
    root.title("Endurance Tracker")
    root.geometry(GEOMETRY)
    root.resizable(True, True)
    root.option_add('*tearOff', FALSE)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    loading()
    root.mainloop()


def loading():
    global root, settings, variables, elements, server, client, DARK_MODE, tracker

    # ── ttk themes ────────────────────────────────────────────────────────────
    s = ttk.Style()
    s.theme_create("light", parent='default', settings={
        "TNotebook": {"configure": {"background": CONTENT_BG, "tabposition": "sw"}},
        "TNotebook.Tab": {
            "configure": {"padding": [20, 10], "background": CONTENT_BG,
                          "foreground": LABEL_FG},
            "map": {"background": [("selected", TAB_BG_ACTIVE),
                                   ("active", TAB_BG_ACTIVE),
                                   ("!disabled", CONTENT_BG),
                                   ("readonly", CONTENT_BG)],
                    "foreground": [("selected", LABEL_FG), ("active", LABEL_FG),
                                   ("!disabled", LABEL_FG), ("readonly", LABEL_FG)]},
            "expand": [("selected", [1, 0, 1, 0])]},
        "TComboBox": {
            "configure": {'fieldbackground': ENTRY_BG, 'foreground': ENTRY_FG,
                          'selectbackground': '', 'selectforeground': ENTRY_FG,
                          'bordercolor': '', 'background': ''},
            "map": {"background": [("active", ENTRY_BG), ("selected", ENTRY_BG),
                                   ("!disabled", ENTRY_BG), ("readonly", ENTRY_BG)],
                    "foreground": [("active", ENTRY_FG), ("selected", ENTRY_FG),
                                   ("!disabled", ENTRY_FG), ("readonly", ENTRY_FG)]}},
        "TScrollbar": {"configure": {'background': ENTRY_BG,
                                     'troughcolor': '#f0f0f0',
                                     'arrowcolor': 'grey'}},
    })

    s.theme_create("dark", parent='default', settings={
        "TNotebook": {"configure": {"background": CONTENT_BG_DARK,
                                    "tabposition": "sw"}},
        "TNotebook.Tab": {
            "configure": {"padding": [20, 10], "background": CONTENT_BG_DARK,
                          "foreground": LABEL_FG_DARK},
            "map": {"background": [("selected", TAB_BG_DARK_ACTIVE),
                                   ("active", TAB_BG_DARK_ACTIVE),
                                   ("!disabled", STATUS_BG_DARK),
                                   ("readonly", STATUS_BG_DARK)],
                    "foreground": [("selected", LABEL_FG_DARK),
                                   ("active", LABEL_FG_DARK),
                                   ("!disabled", LABEL_FG_DARK),
                                   ("readonly", LABEL_FG_DARK)]},
            "expand": [("selected", [1, 0, 1, 0])]},
        "TComboBox": {
            "configure": {'fieldbackground': ENTRY_BG_DARK, 'foreground': ENTRY_FG,
                          'selectbackground': '', 'selectforeground': ENTRY_FG_DARK,
                          'bordercolor': '', 'background': ''},
            "map": {"background": [("active", ENTRY_BG_DARK),
                                   ("selected", ENTRY_BG_DARK),
                                   ("!disabled", ENTRY_BG_DARK),
                                   ("readonly", ENTRY_BG_DARK)],
                    "foreground": [("active", ENTRY_FG_DARK),
                                   ("selected", ENTRY_FG_DARK),
                                   ("!disabled", ENTRY_FG_DARK),
                                   ("readonly", ENTRY_FG_DARK)]}},
        "TScrollbar": {"configure": {'background': ENTRY_BG_DARK,
                                     'troughcolor': TAB_BG_DARK_ACTIVE,
                                     'arrowcolor': 'grey'}},
    })

    if DARK_MODE:
        s.theme_use("dark")
    else:
        s.theme_use("light")

    # ── layout ────────────────────────────────────────────────────────────────
    main_background = Frame(root, bg="white")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    main_background.grid(row=0, column=0, sticky="nsew")
    elements['main_background'] = main_background
    main_background.grid_columnconfigure(0, weight=1)
    main_background.grid_columnconfigure(1, weight=4)
    main_background.grid_rowconfigure(0, weight=1)

    settings['dark_mode'] = BooleanVar(value=DARK_MODE)

    main_menu = Menu(root)
    elements['main_menu'] = main_menu
    load_menu()

    status = Frame(main_background, bg=STATUS_BG)
    status.grid(row=0, column=0, sticky="nsew")
    elements['status'] = status
    load_status()

    main_content = Frame(main_background, bg=CONTENT_BG)
    main_content.grid(row=0, column=1, sticky="nsew")
    elements['main_content'] = main_content
    load_main_content()

    # ── init tracker DataFrame (empty) ────────────────────────────────────────
    tracker = DataFrame(columns=TRACKER_COLUMNS)

    # ── server / client ───────────────────────────────────────────────────────
    db = Database(DATA_DIR)
    server = TrackerServer(HOST, PORT, db=db)
    client = TrackerClient(HOST, PORT, db=db)

    load_from_db()
    start_status()


def load_menu():
    root['menu'] = elements['main_menu']

    menu_app = Menu(elements['main_menu'])
    elements['main_menu'].add_cascade(label="App", menu=menu_app)
    elements['menu_app'] = menu_app
    elements['menu_app'].add_checkbutton(label="Dark Mode",
                                         command=toggle_dark_mode,
                                         variable=settings['dark_mode'])
    elements['menu_app'].add_command(label="Exit", command=on_closing)

    menu_data = Menu(elements['main_menu'])
    elements['main_menu'].add_cascade(label="Data", menu=menu_data)
    elements['menu_data'] = menu_data
    elements['menu_data'].add_command(label="Init Tracker",
                                      command=init_theoretical_stints)


def load_status():
    status = elements['status']
    for i in range(16):
        status.grid_rowconfigure(i, weight=1)
    status.grid_columnconfigure(0, weight=1)
    status.grid_columnconfigure(1, weight=2)

    variables['time_gmt'] = StringVar(value='00:00:00')
    temp_label = Label(status, text='GMT', bg=STATUS_BG,
                       font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew")
    temp_label = Label(status, textvariable=variables['time_gmt'], bg=STATUS_BG,
                       font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew")
    elements['label_time_gmt'] = temp_label

    for n, tz in enumerate(STATUS_TIMES.split(',')):
        variables['time_' + tz.lower()] = StringVar(value='00:00:00')
        Label(status, text=tz, bg=STATUS_BG,
              font=("Helvetica", 16, 'bold')).grid(row=n + 1, column=0,
                                                   sticky="nsew")
        lbl = Label(status, textvariable=variables['time_' + tz.lower()],
                    bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
        lbl.grid(row=n + 1, column=1, sticky="nsew")
        elements['label_time_' + tz.lower()] = lbl

    sep_row = len(STATUS_TIMES.split(',')) + 1
    ttk.Separator(status, orient=HORIZONTAL).grid(
        row=sep_row, column=0, columnspan=2, sticky="nsew", pady=20)
    status.grid_rowconfigure(sep_row, weight=0)

    Label(status, text='Session', bg=STATUS_BG,
          font=("Helvetica", 16, 'bold')).grid(row=sep_row + 1, column=0,
                                               sticky="nsew")
    variables['current_session'] = StringVar(value='Planning')
    Label(status, textvariable=variables['current_session'], bg=STATUS_BG,
          font=("Helvetica", 16, 'bold')).grid(row=sep_row + 1, column=1,
                                               sticky="nsew")

    variables['current_event_time'] = StringVar(value='00:00:00')
    lbl = Label(status, text='Event Time', bg=STATUS_BG,
                font=("Helvetica", 16, 'bold'))
    lbl.grid(row=sep_row + 2, column=0, sticky="nsew")
    lbl.bind('<Button-1>', copy_time)
    lbl = Label(status, textvariable=variables['current_event_time'],
                bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
    lbl.grid(row=sep_row + 2, column=1, sticky="nsew")
    lbl.bind('<Button-1>', copy_time)
    elements['label_event_time'] = lbl

    variables['current_sim_time'] = StringVar(value='00:00:00')
    lbl = Label(status, text='Sim Time', bg=STATUS_BG,
                font=("Helvetica", 16, 'bold'))
    lbl.grid(row=sep_row + 3, column=0, sticky="nsew")
    lbl.bind('<Button-1>', copy_time)
    lbl = Label(status, textvariable=variables['current_sim_time'],
                bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
    lbl.grid(row=sep_row + 3, column=1, sticky="nsew")
    lbl.bind('<Button-1>', copy_time)
    elements['label_sim_time'] = lbl


def load_main_content():
    main_content = elements['main_content']
    main_content.grid_rowconfigure(0, weight=1)
    main_content.grid_columnconfigure(0, weight=1)

    main_notebook = ttk.Notebook(main_content)
    main_notebook.grid(row=0, column=0, sticky="nsew")
    elements['main_notebook'] = main_notebook
    main_notebook.grid_columnconfigure(0, weight=1)
    main_notebook.grid_rowconfigure(0, weight=1)

    tab_home = Frame(main_notebook, bg=CONTENT_BG)
    main_notebook.add(tab_home, text="Home")
    elements['tab_home'] = tab_home
    load_tab_home()

    tab_general = Frame(main_notebook, bg=CONTENT_BG)
    main_notebook.add(tab_general, text="General")
    elements['tab_general'] = tab_general
    load_tab_general()

    tab_plan = Frame(main_notebook, bg=CONTENT_BG)
    main_notebook.add(tab_plan, text="Master Plan")
    elements['tab_plan'] = tab_plan
    load_tab_plan()

    tab_race = Frame(main_notebook, bg=CONTENT_BG)
    main_notebook.add(tab_race, text="Race Notes")
    elements['tab_race'] = tab_race
    load_tab_race()


# ────────────────────────────────────────────── tab loaders ──────────────────

def load_tab_home():
    tab_home = elements['tab_home']
    tab_home.grid_columnconfigure(0, weight=3)
    tab_home.grid_columnconfigure(1, weight=1)

    Label(tab_home, text='Server', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=0, column=0, sticky="nsew")

    variables['is_server'] = BooleanVar(value=IS_SERVER)
    Checkbutton(tab_home, variable=variables['is_server'],
                bg=CONTENT_BG, selectcolor=CONTENT_BG,
                command=toggle_server).grid(row=0, column=1, sticky="nsew")

    btn = Button(tab_home, text='Start Server', command=lambda: server.start(),
                 bg=BUTTON_BG, fg=BUTTON_FG)
    btn.grid(row=1, column=0, sticky="nsew", pady=2)
    elements['button_start_server'] = btn

    btn = Button(tab_home, text='Stop Server', command=lambda: server.stop(),
                 bg=BUTTON_BG, fg=BUTTON_FG)
    btn.grid(row=1, column=1, sticky="nsew", pady=2)
    elements['button_stop_server'] = btn

    btn = Button(tab_home, text='Start Client', command=lambda: client.connect(),
                 bg=BUTTON_BG, fg=BUTTON_FG)
    btn.grid(row=2, column=0, sticky="nsew", pady=2)
    elements['button_start_client'] = btn

    btn = Button(tab_home, text='Stop Client', command=lambda: client.disconnect(),
                 bg=BUTTON_BG, fg=BUTTON_FG)
    btn.grid(row=2, column=1, sticky="nsew", pady=2)
    elements['button_stop_client'] = btn

    Label(tab_home, text='Host', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=3, column=0, sticky="nsew")
    variables['host'] = StringVar(value=HOST)
    Entry(tab_home, textvariable=variables['host'],
          justify='center', insertbackground='black').grid(row=3, column=1,
                                                           sticky="nsew", pady=2)

    Label(tab_home, text='Port', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=4, column=0, sticky="nsew")
    variables['port'] = IntVar(value=PORT)
    Entry(tab_home, textvariable=variables['port'],
          justify='center', insertbackground='black').grid(row=4, column=1,
                                                           sticky="nsew", pady=2)

    Label(tab_home, text='Send', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=5, column=0, sticky="nsew")
    variables['send'] = StringVar(value='')
    entry_send = Entry(tab_home, textvariable=variables['send'],
                       justify='center', insertbackground='black')
    entry_send.grid(row=5, column=1, sticky="nsew", pady=2)
    entry_send.bind('<Return>', send_message)
    Button(tab_home, text='Send', command=send_message,
           bg=BUTTON_BG, fg=BUTTON_FG).grid(row=5, column=2, sticky="nsew",
                                             pady=2)


def _make_time_row(parent, row, label_text, var_prefix, bg):
    """Create a row with a label and HH:MM:SS entry boxes."""
    Label(parent, text=label_text, bg=bg,
          font=("Helvetica", 10, 'bold')).grid(row=row, column=0, sticky="nsew")

    variables[f'{var_prefix}_h'] = StringVar(value='')
    variables[f'{var_prefix}_m'] = StringVar(value='')
    variables[f'{var_prefix}_s'] = StringVar(value='')

    frame = Frame(parent, bg=bg)
    frame.grid(row=row, column=1, sticky="nsew")
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements[f'{var_prefix}_frame'] = frame

    def save(event=None):
        update_value(var_prefix, '',
                     f"{variables[f'{var_prefix}_h'].get()}:"
                     f"{variables[f'{var_prefix}_m'].get()}:"
                     f"{variables[f'{var_prefix}_s'].get()}")

    for col, width, key in ((0, 3, 'h'), (2, 5, 'm'), (4, 3, 's')):
        ent = Entry(frame, textvariable=variables[f'{var_prefix}_{key}'],
                    width=width, justify='center', insertbackground='black')
        ent.grid(row=0, column=col, sticky="nsew", pady=2)
        ent.bind('<Return>', save)
        elements[f'entry_{var_prefix}_{key}'] = ent
        if col < 4:
            Label(frame, text=':', bg=bg,
                  font=("Helvetica", 10, 'bold')).grid(row=0, column=col + 1,
                                                        sticky="nsew", pady=2)


def load_tab_general():
    tab_general = elements['tab_general']
    tab_general.grid_columnconfigure(1, weight=1)
    tab_general.grid_columnconfigure(2, weight=2)
    for i in range(16):
        tab_general.grid_rowconfigure(i, weight=1)
    bg = CONTENT_BG

    # Event name
    Label(tab_general, text='Event', bg=bg,
          font=("Helvetica", 10, 'bold')).grid(row=0, column=0, sticky="nsew")
    variables['event'] = StringVar(value='')
    ent = Entry(tab_general, textvariable=variables['event'],
                justify='center', insertbackground='white')
    ent.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['entry_event_name'] = ent
    ent.bind('<Return>',
             lambda e: update_value('event', '', variables['event'].get()))

    # Event date
    Label(tab_general, text='Event Date', bg=bg,
          font=("Helvetica", 10, 'bold')).grid(row=1, column=0, sticky="nsew")
    variables['event_date'] = StringVar(value='')
    date_frame = Frame(tab_general, bg=bg)
    date_frame.grid(row=1, column=1, sticky="nsew", pady=2)
    date_frame.grid_columnconfigure(0, weight=1)
    date_frame.grid_rowconfigure(0, weight=1)
    elements['entry_event_date'] = date_frame
    date_picker = DatePicker(date_frame, root, settings, variables, elements)
    elements['date_picker_event_date'] = date_picker
    date_picker.entry.bind(
        '<Return>',
        lambda e: update_value('event_date', '',
                               variables['event_date'].get()))

    # Event time
    _make_time_row(tab_general, 2, 'Event Time', 'event_time', bg)

    # Event timezone
    Label(tab_general, text='Event Timezone', bg=bg,
          font=("Helvetica", 10, 'bold')).grid(row=3, column=0, sticky="nsew")
    variables['event_timezone'] = StringVar(value='')
    tz_frame = Frame(tab_general, bg=bg)
    tz_frame.grid(row=3, column=1, sticky="nsew", pady=2)
    tz_frame.grid_columnconfigure(0, weight=1)
    tz_frame.grid_rowconfigure(0, weight=1)
    tz_option = CTkOptionMenu(tz_frame, variables['event_timezone'],
                              *pytz.all_timezones)
    elements['entry_event_timezone'] = tz_option
    tz_option.entry.bind(
        '<Return>',
        lambda e: update_value('event_timezone', '',
                               variables['event_timezone'].get()))

    # Car
    Label(tab_general, text='Car', bg=bg,
          font=("Helvetica", 10, 'bold')).grid(row=4, column=0, sticky="nsew")
    variables['car'] = StringVar(value='')
    ent = Entry(tab_general, textvariable=variables['car'],
                justify='center', insertbackground='black')
    ent.grid(row=4, column=1, sticky="nsew", pady=2)
    elements['entry_car'] = ent
    ent.bind('<Return>',
             lambda e: update_value('car', '', variables['car'].get()))

    # Time fields
    _make_time_row(tab_general, 5, 'Total Time', 'total_time', bg)
    # Fix the row override from _make_time_row — general tab rows
    elements['total_time_frame'] = elements.pop('total_time_frame', None)

    Label(tab_general, text='Current Position', bg=bg,
          font=("Helvetica", 10, 'bold')).grid(row=6, column=0, sticky="nsew")
    variables['current_position'] = StringVar(value='')
    ent = Entry(tab_general, textvariable=variables['current_position'],
                justify='center', insertbackground='black')
    ent.grid(row=6, column=1, sticky="nsew", pady=2)
    elements['entry_current_position'] = ent
    ent.bind('<Return>',
             lambda e: update_value('current_position', '',
                                    variables['current_position'].get()))

    Label(tab_general, text='Total Drivers', bg=bg,
          font=("Helvetica", 10, 'bold')).grid(row=7, column=0, sticky="nsew")
    variables['total_drivers'] = StringVar(value='')
    ent = Entry(tab_general, textvariable=variables['total_drivers'],
                justify='center', insertbackground='black')
    ent.grid(row=7, column=1, sticky="nsew", pady=2)
    elements['entry_total_drivers'] = ent
    ent.bind('<Return>',
             lambda e: update_value('total_drivers', '',
                                    variables['total_drivers'].get()))

    _make_time_row(tab_general, 8, 'Gap to Race Start', 'gap_2_start', bg)
    _make_time_row(tab_general, 9, 'Practice Duration', 'practice_duration', bg)
    _make_time_row(tab_general, 10, 'Qualify Duration', 'qualify_duration', bg)
    _make_time_row(tab_general, 11, 'Time to Green', 'time_to_green', bg)
    _make_time_row(tab_general, 12, 'Time to Start', 'time_to_start', bg)
    _make_time_row(tab_general, 13, 'Sim. Time Start', 'sim_time_start', bg)
    _make_time_row(tab_general, 14, 'Theoretical Stint Time',
                   'theoretical_stint_time', bg)
    _make_time_row(tab_general, 15, 'Average Stint Time', 'average_stint_time', bg)

    # Hidden variable for event_time_est used by status updater
    variables['event_time_est'] = StringVar(value='')

    # Drivers list
    Label(tab_general, text='Drivers', bg=bg,
          font=("Helvetica", 10, 'bold')).grid(column=2, row=0, sticky="nsew",
                                               padx=10)
    variables['drivers_raw'] = []
    variables['drivers_time_slots'] = {}
    variables['drivers'] = StringVar(value=variables['drivers_raw'])
    listbox = Listbox(tab_general, height=8, width=20,
                      listvariable=variables['drivers'], selectmode=MULTIPLE)
    listbox.grid(column=2, row=1, rowspan=8, sticky="nsew", padx=10)
    elements['listbox_drivers'] = listbox

    variables['add_driver'] = StringVar(value='')
    ent = Entry(tab_general, textvariable=variables['add_driver'],
                insertbackground='black')
    ent.grid(column=2, row=9, sticky="nsew", padx=10, pady=2)
    elements['add_driver'] = ent

    Button(tab_general, text="Add Driver", command=add_driver).grid(
        column=2, row=10, sticky="nsew", padx=10, pady=2)
    Button(tab_general, text="Remove Driver", command=remove_driver).grid(
        column=2, row=11, sticky="nsew", padx=10, pady=2)


def load_tab_plan():
    tab_plan = elements['tab_plan']
    tab_plan.grid_columnconfigure(0, weight=1)
    tab_plan.grid_rowconfigure((1, 3), weight=1)

    Label(tab_plan, text='Plan', bg=CONTENT_BG,
          font=("Helvetica", 16, 'bold')).grid(row=0, column=0, sticky="nsew")
    Label(tab_plan, text='Actual', bg=CONTENT_BG,
          font=("Helvetica", 16, 'bold')).grid(row=2, column=0, sticky="nsew")

    plan_frame = Frame(tab_plan, bg=CONTENT_BG)
    plan_frame.grid(row=1, column=0, sticky="nsew", padx=10)
    elements['plan_frame_plan'] = plan_frame

    actual_frame = Frame(tab_plan, bg=CONTENT_BG)
    actual_frame.grid(row=3, column=0, sticky="nsew", padx=10)
    elements['plan_frame_actual'] = actual_frame


def load_tab_race():
    global tracker

    tab_race = elements['tab_race']
    tab_race.grid_columnconfigure(1, weight=1)
    tab_race.grid_rowconfigure(0, weight=1)

    # Slots listbox
    slots_frame = Frame(tab_race, bg=CONTENT_BG)
    slots_frame.grid(row=0, column=0, sticky="nsew", rowspan=10, padx=10)
    slots_frame.grid_columnconfigure(0, weight=1)
    slots_frame.grid_rowconfigure(0, weight=1)
    elements['race_tracker_slots_frame'] = slots_frame

    variables['race_tracker_slots_raw'] = []
    variables['race_tracker_slots'] = StringVar()
    slots_list = Listbox(slots_frame, height=20, width=10,
                         listvariable=variables['race_tracker_slots'],
                         selectmode=SINGLE, exportselection=False)
    slots_list.grid(row=0, column=0, sticky="nsew", padx='5 0')
    elements['race_tracker_slots'] = slots_list
    slots_list.bind('<<ListboxSelect>>', change_race_slot)

    ys = ttk.Scrollbar(slots_frame, orient='vertical', command=slots_list.yview)
    slots_list['yscrollcommand'] = ys.set
    ys.grid(column=1, row=0, sticky='ns')

    # Input panel
    input_frame = Frame(tab_race, bg=CONTENT_BG)
    input_frame.grid(row=0, column=1, sticky="nsew", padx=5)
    elements['race_tracker_input_frame'] = input_frame
    for i in range(13):
        if i != 5:
            input_frame.grid_rowconfigure(i, weight=1)
    input_frame.grid_columnconfigure((0, 1), weight=1)

    ttk.Separator(input_frame, orient=HORIZONTAL).grid(
        row=5, column=0, columnspan=2, sticky="nsew", pady=10)

    # Edit frame
    lbl = Label(input_frame, bg=CONTENT_BG, text='Edit',
                font=("Helvetica", 16, 'bold'))
    edit_frame = LabelFrame(input_frame, bg=CONTENT_BG, labelwidget=lbl)
    edit_frame.grid(row=0, column=0, rowspan=5, sticky="nsew")
    elements['race_tracker_edit_frame'] = edit_frame
    for i in range(6):
        edit_frame.grid_rowconfigure(i, weight=1)
    edit_frame.grid_rowconfigure(6, weight=2)
    edit_frame.grid_columnconfigure((0, 1), weight=1)

    # Add frame
    lbl = Label(input_frame, bg=CONTENT_BG, text='Add',
                font=("Helvetica", 16, 'bold'))
    current_frame = LabelFrame(input_frame, bg=CONTENT_BG, labelwidget=lbl)
    current_frame.grid(row=7, column=0, rowspan=7, sticky="nsew")
    elements['race_tracker_current_frame'] = current_frame
    for i in range(7):
        current_frame.grid_rowconfigure(i, weight=1)
    current_frame.grid_rowconfigure(7, weight=2)
    current_frame.grid_columnconfigure((0, 1), weight=1)

    # ── edit frame widgets ────────────────────────────────────────────────────
    Label(edit_frame, text='Driver', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=0, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_edit_driver'] = StringVar(value='')
    drv = CTkOptionMenu(edit_frame, variable=variables['race_tracker_edit_driver'],
                        state="readonly", corner_radius=0,
                        button_color=BUTTON_BG, dynamic_resizing=False)
    drv.grid(row=0, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_edit_driver_entry'] = drv

    Label(edit_frame, text='Theoretical Stint #', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=1, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_edit_theoretical_stint'] = StringVar(value='')
    Entry(edit_frame,
          textvariable=variables['race_tracker_edit_theoretical_stint'],
          insertbackground='black').grid(row=1, column=1, sticky="nsew",
                                         pady=2, padx=10)

    Label(edit_frame, text='Actual Stint #', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=2, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_edit_actual_stint'] = StringVar(value='')
    Entry(edit_frame, textvariable=variables['race_tracker_edit_actual_stint'],
          insertbackground='black').grid(row=2, column=1, sticky="nsew",
                                         pady=2, padx=10)

    Label(edit_frame, text='Actual Driver', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=3, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_edit_actual_driver'] = StringVar(value='')
    adrv = CTkOptionMenu(
        edit_frame, variable=variables['race_tracker_edit_actual_driver'],
        state="readonly", corner_radius=0, button_color=BUTTON_BG,
        dynamic_resizing=False)
    adrv.grid(row=3, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_edit_actual_driver_entry'] = adrv

    Label(edit_frame, text='Est. Chance of Rain (%)', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=4, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_edit_est_chance_of_rain'] = StringVar(value='')
    Entry(edit_frame,
          textvariable=variables['race_tracker_edit_est_chance_of_rain'],
          insertbackground='black').grid(row=4, column=1, sticky="nsew",
                                         pady=2, padx=10)

    Label(edit_frame, text='Actual Weather', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=5, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_edit_actual_weather'] = StringVar(value='')
    wth = CTkOptionMenu(
        edit_frame, variable=variables['race_tracker_edit_actual_weather'],
        state="readonly", corner_radius=0, button_color=BUTTON_BG,
        dynamic_resizing=False)
    wth.grid(row=5, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_edit_actual_weather_entry'] = wth

    # Notes text area
    notes_frame = Frame(edit_frame, bg=CONTENT_BG)
    notes_txt = Text(notes_frame, height=2, width=15)
    notes_txt.grid(column=0, row=0, sticky='nwes')
    ys = ttk.Scrollbar(notes_frame, orient='vertical', command=notes_txt.yview)
    xs = ttk.Scrollbar(notes_frame, orient='horizontal', command=notes_txt.xview)
    notes_txt['yscrollcommand'] = ys.set
    notes_txt['xscrollcommand'] = xs.set
    xs.grid(column=0, row=1, sticky='we')
    ys.grid(column=1, row=0, sticky='ns')
    notes_frame.grid_columnconfigure(0, weight=1)
    notes_frame.grid_rowconfigure(0, weight=1)
    notes_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=5,
                     padx=10)
    elements['race_tracker_edit_notes_text_frame'] = notes_frame
    elements['race_tracker_edit_notes_text'] = notes_txt

    Button(input_frame, text="Update", command=edit_update).grid(
        row=1, column=1, sticky="nsew", padx=20, pady=20)
    Button(input_frame, text="Reset", command=edit_reset).grid(
        row=2, column=1, sticky="nsew", padx=20, pady=20)
    Button(input_frame, text="Delete", command=edit_delete).grid(
        row=3, column=1, sticky="nsew", padx=20, pady=20)

    # ── add (current) frame widgets ───────────────────────────────────────────
    Label(current_frame, text='Race Time', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=0, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_current_time'] = StringVar(value='')
    Entry(current_frame, textvariable=variables['race_tracker_current_time'],
          insertbackground='black').grid(row=0, column=1, sticky="nsew",
                                         pady=2, padx=10)

    Label(current_frame, text='Driver', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=1, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_current_driver'] = StringVar(value='')
    cdrv = CTkOptionMenu(
        current_frame, variable=variables['race_tracker_current_driver'],
        state="readonly", corner_radius=0, button_color=BUTTON_BG,
        dynamic_resizing=False)
    cdrv.grid(row=1, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_current_driver_entry'] = cdrv

    Label(current_frame, text='Theoretical Stint #', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=2, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_current_theoretical_stint'] = StringVar(value='')
    Entry(current_frame,
          textvariable=variables['race_tracker_current_theoretical_stint'],
          insertbackground='black').grid(row=2, column=1, sticky="nsew",
                                         pady=2, padx=10)

    Label(current_frame, text='Actual Stint #', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=3, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_current_actual_stint'] = StringVar(value='')
    Entry(current_frame,
          textvariable=variables['race_tracker_current_actual_stint'],
          insertbackground='black').grid(row=3, column=1, sticky="nsew",
                                         pady=2, padx=10)

    Label(current_frame, text='Actual Driver', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=4, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_current_actual_driver'] = StringVar(value='')
    cadrv = CTkOptionMenu(
        current_frame, variable=variables['race_tracker_current_actual_driver'],
        state="readonly", corner_radius=0, button_color=BUTTON_BG,
        dynamic_resizing=False)
    cadrv.grid(row=4, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_current_actual_driver_entry'] = cadrv

    Label(current_frame, text='Est. Chance of Rain (%)', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=5, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_current_est_chance_of_rain'] = StringVar(value='')
    Entry(current_frame,
          textvariable=variables['race_tracker_current_est_chance_of_rain'],
          insertbackground='black').grid(row=5, column=1, sticky="nsew",
                                         pady=2, padx=10)

    Label(current_frame, text='Actual Weather', bg=CONTENT_BG,
          font=("Helvetica", 10, 'bold')).grid(row=6, column=0, sticky="nsew",
                                               pady=2)
    variables['race_tracker_current_actual_weather'] = StringVar(value='')
    cwth = CTkOptionMenu(
        current_frame, variable=variables['race_tracker_current_actual_weather'],
        state="readonly", corner_radius=0, button_color=BUTTON_BG,
        dynamic_resizing=False)
    cwth.grid(row=6, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_current_actual_weather_entry'] = cwth

    cur_notes_frame = Frame(current_frame, bg=CONTENT_BG)
    cur_notes_txt = Text(cur_notes_frame, height=2, width=15)
    cur_notes_txt.grid(column=0, row=0, sticky='nwes')
    ys = ttk.Scrollbar(cur_notes_frame, orient='vertical',
                       command=cur_notes_txt.yview)
    xs = ttk.Scrollbar(cur_notes_frame, orient='horizontal',
                       command=cur_notes_txt.xview)
    cur_notes_txt['yscrollcommand'] = ys.set
    cur_notes_txt['xscrollcommand'] = xs.set
    xs.grid(column=0, row=1, sticky='we')
    ys.grid(column=1, row=0, sticky='ns')
    cur_notes_frame.grid_columnconfigure(0, weight=1)
    cur_notes_frame.grid_rowconfigure(0, weight=1)
    cur_notes_frame.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=5,
                         padx=10)
    elements['race_tracker_current_notes_text'] = cur_notes_txt
    elements['race_tracker_current_notes_text_frame'] = cur_notes_frame

    btn = Button(input_frame, text="Add", command=current_add)
    btn.grid(row=7, column=1, sticky="nsew", padx=20, pady=10)
    elements['add_button'] = btn

    btn = Button(input_frame, text="Practice", command=current_sessions)
    btn.grid(row=8, column=1, sticky="nsew", padx=20, pady=10)
    elements['session_button'] = btn

    btn = Button(input_frame, text='Back', command=current_back)
    btn.grid(row=9, column=1, sticky="nsew", padx=20, pady=10)
    elements['back_button'] = btn

    btn = Button(input_frame, text='Pitting IN', command=current_pit)
    btn.grid(row=10, column=1, sticky="nsew", padx=20, pady=10)
    elements['pit_button'] = btn

    btn = Button(input_frame, text='Copy from Above', command=current_copy)
    btn.grid(row=11, column=1, sticky="nsew", padx=20, pady=10)
    elements['copy_button'] = btn


# ───────────────────────────────────────────── status thread ──────────────────

def start_status():
    settings['status_thread'] = Thread(target=update_status, daemon=True)
    settings['status_state'] = True
    settings['status_thread'].start()


def update_status():
    while settings.get('status_state', False):
        variables['time_gmt'].set(
            datetime.now(pytz.timezone('GMT')).strftime('%H:%M:%S'))
        for tz in STATUS_TIMES.split(","):
            variables['time_' + tz.lower()].set(
                datetime.now().astimezone(pytz.timezone(tz)).strftime('%H:%M:%S'))

        race_length = get_delta('total_time')
        now = datetime.now(pytz.utc)
        try:
            event_start = tz_diff(variables['event_time_est'].get(),
                                  'US/Eastern', 'GMT')
            event_end = event_start + race_length
        except Exception:
            sleep(1)
            continue

        if event_start < now < event_end:
            duration = get_duration()
            practice = get_delta('practice_duration')
            qualify = get_delta('qualify_duration')
            to_green = get_delta('time_to_green')
            to_start = get_delta('time_to_start')
            sim_start = get_delta('sim_time_start')

            gap = str(practice + qualify + to_green + to_start).split('.')[0]
            set_time('gap_2_start', gap)

            if 'session_button' in elements:
                elements['session_button'].configure(state=NORMAL)
                elements['back_button'].configure(state=NORMAL)
                elements['pit_button'].configure(state=NORMAL)

            if duration <= practice:
                session, event_time = 'Practice', duration
            elif duration <= practice + qualify:
                session, event_time = 'Qualify', duration - practice
            elif duration <= practice + qualify + to_green:
                session = 'Waiting for Drivers'
                event_time = duration - practice - qualify
                variables['current_sim_time'].set(
                    str(duration - practice - qualify + sim_start).split('.')[0])
            elif duration <= practice + qualify + to_green + to_start:
                session = 'Formation Lap'
                event_time = duration - practice - qualify
                variables['current_sim_time'].set(
                    str(duration - practice - qualify + sim_start).split('.')[0])
            else:
                session = 'Race Started'
                event_time = duration - practice - qualify
                variables['current_sim_time'].set(
                    str(duration - practice - qualify + sim_start).split('.')[0])

            if duration > practice + qualify + to_green + to_start + race_length:
                session = 'Race Over'
                event_time = timedelta(0)
                if 'session_button' in elements:
                    elements['session_button'].configure(state=DISABLED,
                                                         text='Race Over')
                    elements['back_button'].configure(state=DISABLED)
                    elements['pit_button'].configure(state=DISABLED)

            variables['current_session'].set(session)
            variables['current_event_time'].set(str(event_time).split('.')[0])
        elif now < event_start:
            variables['current_session'].set('Planning')
            variables['current_event_time'].set('00:00:00')
        else:
            variables['current_session'].set('Race Over')
            variables['current_event_time'].set('00:00:00')

        handshake()
        sleep(1)


def handshake():
    pass


# ─────────────────────────────────────────────── driver actions ───────────────

def add_driver():
    name = variables['add_driver'].get()
    if not name:
        return
    if name in variables['drivers_raw']:
        return
    if len(variables['drivers_raw']) == MAX_DRIVER:
        messagebox.showerror("Driver not added!",
                             "Maximum number of drivers reached")
        return

    variables['drivers_raw'].append(name)
    variables['drivers'].set(variables['drivers_raw'])

    total_stints = _compute_total_stints()
    variables['drivers_time_slots'][name] = ['0'] * total_stints

    get_db().add_driver(name)
    reset_drivers_time_slots()
    variables['add_driver'].set('')

    for key in ('race_tracker_edit_driver_entry',
                'race_tracker_edit_actual_driver_entry',
                'race_tracker_current_driver_entry',
                'race_tracker_current_actual_driver_entry'):
        if key in elements:
            elements[key].configure(values=variables['drivers_raw'])


def remove_driver():
    listbox = elements['listbox_drivers']
    if not listbox.curselection():
        return
    to_delete = [variables['drivers_raw'][i] for i in listbox.curselection()]
    for name in to_delete:
        variables['drivers_raw'].remove(name)
        variables['drivers_time_slots'].pop(name, None)
        get_db().remove_driver(name)

    variables['drivers'].set(variables['drivers_raw'])
    reset_drivers_time_slots()

    for key in ('race_tracker_edit_driver_entry',
                'race_tracker_edit_actual_driver_entry',
                'race_tracker_current_driver_entry',
                'race_tracker_current_actual_driver_entry'):
        if key in elements:
            elements[key].configure(values=variables['drivers_raw'])


def reset_drivers_time_slots():
    db = get_db()
    for name, slots in variables.get('drivers_time_slots', {}).items():
        available = [i + 1 for i, v in enumerate(slots) if v == '1']
        maybe = [i + 1 for i, v in enumerate(slots) if v == '2']
        unavailable = [i + 1 for i, v in enumerate(slots) if v == '0']
        db.update_driver_slots(name, available, maybe, unavailable)
    init_time_scheduler()


def init_time_scheduler():
    if 'plan_content' in elements:
        elements['plan_content'].__del__()
    if 'actual_content' in elements:
        elements['actual_content'].__del__()

    for i in range(8):
        if 'plan_frame_plan' in elements:
            elements['plan_frame_plan'].grid_rowconfigure(i, weight=0)
        if 'plan_frame_actual' in elements:
            elements['plan_frame_actual'].grid_rowconfigure(i, weight=0)
    root.update()

    db = get_db()
    plan_content = TimeScheduler(root, settings, variables, elements, db,
                                 target='plan')
    elements['plan_content'] = plan_content

    actual_content = TimeScheduler(root, settings, variables, elements, db,
                                   target='actual')
    elements['actual_content'] = actual_content

    init_dark_mode()


# ──────────────────────────────────────────── tracker actions ─────────────────

def change_race_slot(event=None):
    slots_list = elements['race_tracker_slots']
    slots_list.focus_set()
    selected = slots_list.curselection()
    if not selected:
        return

    slot = variables['race_tracker_slots_raw'].index(
        slots_list.get(selected[0]))

    variables['race_tracker_edit_driver'].set(
        tracker.loc[slot, 'Driver'])
    variables['race_tracker_edit_theoretical_stint'].set(
        tracker.loc[slot, 'Theoretical Stints #'])
    variables['race_tracker_edit_actual_stint'].set(
        tracker.loc[slot, 'Actual Stints #'])
    variables['race_tracker_edit_actual_driver'].set(
        tracker.loc[slot, 'Actual Driver'])
    variables['race_tracker_edit_est_chance_of_rain'].set(
        tracker.loc[slot, 'Est. Chance of Rain (%)'])
    variables['race_tracker_edit_actual_weather'].set(
        tracker.loc[slot, 'Act. Weather at Time'])
    elements['race_tracker_edit_notes_text'].delete('1.0', 'end')
    elements['race_tracker_edit_notes_text'].insert(
        'end', str(tracker.loc[slot, 'Notes']))


def edit_update(event=None):
    slots_list = elements['race_tracker_slots']
    selected = slots_list.curselection()
    if not selected:
        return

    slot = variables['race_tracker_slots_raw'].index(
        slots_list.get(selected[0]))

    tracker.at[slot, 'Driver'] = variables['race_tracker_edit_driver'].get()
    tracker.at[slot, 'Theoretical Stints #'] = (
        variables['race_tracker_edit_theoretical_stint'].get())
    tracker.at[slot, 'Actual Stints #'] = (
        variables['race_tracker_edit_actual_stint'].get())
    tracker.at[slot, 'Actual Driver'] = (
        variables['race_tracker_edit_actual_driver'].get())
    tracker.at[slot, 'Est. Chance of Rain (%)'] = (
        variables['race_tracker_edit_est_chance_of_rain'].get())
    tracker.at[slot, 'Act. Weather at Time'] = (
        variables['race_tracker_edit_actual_weather'].get())
    tracker.at[slot, 'Notes'] = (
        elements['race_tracker_edit_notes_text'].get('1.0', 'end-1c'))

    time_slot = str(tracker.at[slot, 'Overall Time Slots'])
    get_db().update_tracker_slot(time_slot, _tracker_row_to_db_slot(slot))


def edit_reset(event=None):
    slots_list = elements['race_tracker_slots']
    selected = slots_list.curselection()
    if not selected:
        return

    slot = variables['race_tracker_slots_raw'].index(
        slots_list.get(selected[0]))

    variables['race_tracker_edit_driver'].set(tracker.at[slot, 'Driver'])
    variables['race_tracker_edit_theoretical_stint'].set(
        tracker.at[slot, 'Theoretical Stints #'])
    variables['race_tracker_edit_actual_stint'].set(
        tracker.at[slot, 'Actual Stints #'])
    variables['race_tracker_edit_actual_driver'].set(
        tracker.at[slot, 'Actual Driver'])
    variables['race_tracker_edit_est_chance_of_rain'].set(
        tracker.at[slot, 'Est. Chance of Rain (%)'])
    variables['race_tracker_edit_actual_weather'].set(
        tracker.at[slot, 'Act. Weather at Time'])
    elements['race_tracker_edit_notes_text'].delete('1.0', 'end')
    elements['race_tracker_edit_notes_text'].insert(
        'end', str(tracker.at[slot, 'Notes']))


def edit_delete(event=None):
    slots_list = elements['race_tracker_slots']
    selected = slots_list.curselection()
    if not selected:
        return

    slot = variables['race_tracker_slots_raw'].index(
        slots_list.get(selected[0]))
    time_slot_str = str(tracker.at[slot, 'Overall Time Slots'])

    # Standard 15-min slots: just clear actual data, keep slot
    parts = time_slot_str.split(':')
    is_standard = (len(parts) == 3
                   and parts[1] in ['00', '15', '30', '45']
                   and parts[2] == '00')
    if is_standard:
        variables['race_tracker_edit_actual_stint'].set('')
        variables['race_tracker_edit_actual_driver'].set('')
        variables['race_tracker_edit_actual_weather'].set('Unknown')
        elements['race_tracker_edit_notes_text'].delete('1.0', 'end')
        tracker.at[slot, 'Actual Stints #'] = ''
        tracker.at[slot, 'Actual Driver'] = ''
        tracker.at[slot, 'Act. Weather at Time'] = 'Unknown'
        tracker.at[slot, 'Notes'] = ''
        get_db().update_tracker_slot(time_slot_str,
                                     _tracker_row_to_db_slot(slot))
    else:
        get_db().delete_tracker_slot(time_slot_str)
        tracker.drop(slot, inplace=True)
        tracker.reset_index(drop=True, inplace=True)
        variables['race_tracker_slots_raw'] = (
            tracker['Overall Time Slots'].values.tolist())
        variables['race_tracker_slots'].set(variables['race_tracker_slots_raw'])
        slots_list.selection_set(max(0, slot - 1))
        change_race_slot()


def current_add(event=None):
    if not variables['race_tracker_current_time'].get():
        messagebox.showerror("Error", "Missing time")
        return

    to_add = [
        variables['race_tracker_current_time'].get(),
        variables['race_tracker_current_driver'].get(),
        variables['race_tracker_current_theoretical_stint'].get(),
        variables['race_tracker_current_actual_stint'].get(),
        variables['race_tracker_current_actual_driver'].get(),
        variables['race_tracker_current_est_chance_of_rain'].get(),
        variables['race_tracker_current_actual_weather'].get(),
        elements['race_tracker_current_notes_text'].get('1.0', 'end-1c'),
    ]
    add_to_tracker(to_add)


def add_to_tracker(to_add):
    global tracker

    tracker.loc[len(tracker.index)] = to_add

    # Sort time slots (indices 2+ only; Practice and Qualify stay at front)
    if len(tracker) > 2:
        temp = tracker.iloc[2:, :].copy()
        temp.sort_values(by='Overall Time Slots', inplace=True)
        tracker.iloc[2:, :] = temp.values.tolist()
    tracker.reset_index(drop=True, inplace=True)

    slots_list = elements['race_tracker_slots']
    variables['race_tracker_slots_raw'] = (
        tracker['Overall Time Slots'].values.tolist())
    variables['race_tracker_slots'].set(variables['race_tracker_slots_raw'])
    slots_list.update()

    try:
        slots_list.selection_set(
            variables['race_tracker_slots_raw'].index(to_add[0]))
    except ValueError:
        pass

    slot_dict = {
        'time_slot': to_add[0],
        'planned_driver': to_add[1],
        'planned_stint': to_add[2],
        'actual_stint': to_add[3],
        'actual_driver': to_add[4],
        'est_rain': to_add[5],
        'act_weather': to_add[6],
        'act_track_condition': '',
        'notes': to_add[7],
    }
    get_db().add_tracker_slot(slot_dict)
    variables['race_tracker_current_time'].set('')


def current_sessions(event=None):
    session_button = elements['session_button']
    db = get_db()

    if session_button['text'] == 'Practice':
        session_button.configure(text='Qualify')
        val = get_duration().strftime('%H:%M:%S')
        set_time('practice_duration', val)
        db.set_event_field('practice_duration', val)

    elif session_button['text'] == 'Qualify':
        session_button.configure(text='Waiting for Drivers')
        val = (get_duration() - get_delta('practice_duration')
               ).strftime('%H:%M:%S')
        set_time('qualify_duration', val)
        db.set_event_field('qualify_duration', val)

    elif session_button['text'] == 'Waiting for Drivers':
        session_button.configure(text='Waiting for Race Start')
        val = (get_duration() - get_delta('practice_duration')
               - get_delta('qualify_duration')).strftime('%H:%M:%S')
        set_time('time_to_green', val)
        db.set_event_field('time_to_green', val)

    elif session_button['text'] == 'Waiting for Race Start':
        session_button.configure(text='Race Started')
        val_start = (get_duration() - get_delta('practice_duration')
                     - get_delta('qualify_duration')
                     - get_delta('time_to_green')).strftime('%H:%M:%S')
        val_gap = get_duration().strftime('%H:%M:%S')
        set_time('time_to_start', val_start)
        set_time('gap_2_start', val_gap)
        db.set_event_field('time_to_start', val_start)
        db.set_event_field('gap_2_start', val_gap)

    elif session_button['text'] == 'Race Started':
        session_button.configure(text='Race Over')
        to_add = [
            variables['current_event_time'].get(),
            variables['race_tracker_current_driver'].get(),
            variables['race_tracker_current_theoretical_stint'].get(),
            variables['race_tracker_current_actual_stint'].get(),
            variables['race_tracker_current_actual_driver'].get(),
            variables['race_tracker_current_est_chance_of_rain'].get(),
            variables['race_tracker_current_actual_weather'].get(),
            'RACE OVER',
        ]
        add_to_tracker(to_add)


def current_back(event=None):
    session_button = elements['session_button']
    text = session_button['text']
    if text == 'Qualify':
        session_button.configure(text='Practice')
    elif text == 'Waiting for Drivers':
        session_button.configure(text='Qualify')
    elif text == 'Waiting for Race Start':
        session_button.configure(text='Waiting for Drivers')
    elif text == 'Race Started':
        session_button.configure(text='Waiting for Drivers')
        set_time('time_to_start', '01:00:00')
    elif text == 'Race Over':
        session_button.configure(text='Race Started')


def current_pit(event=None):
    pit_button = elements['pit_button']
    to_add = [
        variables['current_event_time'].get(),
        variables['race_tracker_current_driver'].get(),
        variables['race_tracker_current_theoretical_stint'].get(),
        variables['race_tracker_current_actual_stint'].get(),
        variables['race_tracker_current_actual_driver'].get(),
        variables['race_tracker_current_est_chance_of_rain'].get(),
        variables['race_tracker_current_actual_weather'].get(),
        '',
    ]
    if pit_button['text'] == 'Pitting IN':
        pit_button.configure(text='Pitting OUT')
        to_add[7] = 'PITTING IN'
        add_to_tracker(to_add)
    elif pit_button['text'] == 'Pitting OUT':
        pit_button.configure(text='Pitting IN')
        to_add[7] = 'PITTING OUT'
        add_to_tracker(to_add)
        try:
            variables['race_tracker_current_actual_stint'].set(
                int(variables['race_tracker_current_actual_stint'].get()) + 1)
        except (ValueError, TclError):
            pass

    calculate_avg_stint_time()


def current_copy(event=None):
    variables['race_tracker_current_driver'].set(
        variables['race_tracker_edit_driver'].get())
    variables['race_tracker_current_est_chance_of_rain'].set(
        variables['race_tracker_edit_est_chance_of_rain'].get())
    variables['race_tracker_current_theoretical_stint'].set(
        variables['race_tracker_edit_theoretical_stint'].get())
    variables['race_tracker_current_actual_stint'].set(
        variables['race_tracker_edit_actual_stint'].get())
    variables['race_tracker_current_actual_weather'].set(
        variables['race_tracker_edit_actual_weather'].get())


def calculate_avg_stint_time():
    variables['stint_time_raw'] = []
    pits = tracker.loc[
        (tracker['Notes'] == 'PITTING IN') | (tracker['Notes'] == 'PITTING OUT')
    ]
    if pits.empty:
        return

    total = 0
    prev_pit = 0
    for i in range(len(pits)):
        if pits.iloc[i, 7] == 'PITTING IN':
            total += 1
            if int(pits.iloc[i, 3]) == total:
                if (i + 1 < len(pits)
                        and pits.iloc[i + 1, 7] == 'PITTING OUT'):
                    t_out = get_delta(pits.iloc[i + 1, 0])
                    if prev_pit == 0:
                        variables['stint_time_raw'].append(t_out)
                    else:
                        variables['stint_time_raw'].append(
                            t_out - get_delta(pits.iloc[prev_pit, 0]))
                    prev_pit = i + 1

    if variables['stint_time_raw']:
        avg = (sum(variables['stint_time_raw'], timedelta(0))
               / len(variables['stint_time_raw']))
        variables.get('average_stint_time',
                      StringVar()).set(str(avg).split('.')[0])


def copy_time(event=None):
    root.clipboard_clear()
    root.clipboard_append(variables['current_event_time'].get())
    root.update()


def init_theoretical_stints(event=None):
    global tracker

    tracker.iloc[:, 1:] = ''
    tracker.iloc[2:, 0] = ''

    total_time = get_delta('total_time')
    total_time_mins = ceil(total_time.total_seconds() / 60)
    theoretical_stint_time = get_delta('theoretical_stint_time')
    theoretical_stint_time_mins = ceil(theoretical_stint_time.total_seconds() / 60)
    stints = ceil(total_time.total_seconds() / theoretical_stint_time.total_seconds()) if theoretical_stint_time.total_seconds() > 0 else 0

    index = 2
    for i in range(total_time_mins):
        if index >= len(tracker):
            break
        if i % 15 == 0:
            time = timedelta(minutes=15) * (i // 15)
            tracker.iloc[index, 0] = format_timedelta(time)
            index += 1
        elif theoretical_stint_time_mins > 0 and i % ceil(theoretical_stint_time_mins) == 0:
            time = timedelta(minutes=i)
            tracker.iloc[index, 0] = format_timedelta(time)
            index += 1

    for i, t in enumerate(tracker['Overall Time Slots'].iloc[2:]):
        if t == '':
            break
        if get_delta(t) > total_time:
            break

        current_time_mins = ceil(get_delta(t).total_seconds() / 60)

        for j in range(stints):
            lower = j * theoretical_stint_time_mins
            upper = (j + 1) * theoretical_stint_time_mins
            if lower <= current_time_mins <= upper:
                tracker.at[i + 2, 'Theoretical Stints #'] = j + 1
                for driver in variables['drivers_raw']:
                    slots = variables['drivers_time_slots'].get(driver, [])
                    if j < len(slots) and slots[j] == '1':
                        tracker.at[i + 2, 'Driver'] = driver
                        break
                break

    print(tracker)


# ──────────────────────────────────────────────── UI event handlers ───────────

def send_message(event=None):
    if variables.get('is_server') and variables['is_server'].get():
        server.send(variables['send'].get())
    else:
        client.send(variables['send'].get())


def toggle_server(event=None):
    if variables['is_server'].get():
        variables['is_server'].set(True)
        client.disconnect()
    else:
        variables['is_server'].set(False)
        server.stop()


def update_value(item='', index='', value=None):
    if variables.get('is_server') and variables['is_server'].get():
        server.update_value(item, index, value)
    else:
        client.update_value(item, index, value)


def on_closing():
    global DARK_MODE

    settings['status_state'] = False

    set_config('general', 'geometry', root.geometry())
    set_config('settings', 'times', str(STATUS_TIMES))
    set_config('general', 'dark_mode', str(DARK_MODE))
    set_config('general', 'data_dir', DATA_DIR)
    if 'is_server' in variables:
        set_config('general', 'server', str(variables['is_server'].get()))
    if 'host' in variables:
        set_config('com', 'host', variables['host'].get())
    if 'port' in variables:
        set_config('com', 'port', str(variables['port'].get()))

    # Close DB connections
    try:
        if server and server.db:
            server.db.close()
    except Exception:
        pass

    sleep(0.5)
    root.destroy()


# ──────────────────────────────────────────────────── theme ───────────────────

def dark_mode():
    global DARK_MODE

    DARK_MODE = True
    settings['dark_mode'].set(True)

    elements['status'].configure(bg=STATUS_BG_DARK)
    elements['main_content'].configure(bg=CONTENT_BG_DARK)

    for key in ('plan_content', 'actual_content'):
        ts = elements.get(key)
        if isinstance(ts, TimeScheduler):
            if 'label_hour' in ts.widgets:
                ts.widgets['label_hour'].configure(fg=LABEL_FG_DARK,
                                                   bg=CONTENT_BG_DARK)
            if 'label_stints' in ts.widgets:
                ts.widgets['label_stints'].configure(fg=LABEL_FG_DARK,
                                                     bg=CONTENT_BG_DARK)

    for key in ('date_picker_event_date',):
        dp = elements.get(key)
        if dp is not None and hasattr(dp, 'master'):
            try:
                dp.master.configure(bg=CONTENT_BG_DARK)
                dp.widgets['main_frame'].configure(bg=ENTRY_BG_DARK)
                dp.entry.configure(bg=ENTRY_BG_DARK, fg=ENTRY_FG_DARK,
                                   insertbackground='white')
                dp.date_picker_icon.configure(bg=ENTRY_BG_DARK,
                                              fg=BUTTON_FG_DARK)
            except Exception:
                pass

    _apply_theme_to_elements(dark=True)

    for child in elements['status'].winfo_children():
        if isinstance(child, Label):
            child.configure(bg=STATUS_BG_DARK, fg='white')

    for child in elements['main_notebook'].winfo_children():
        child.configure(bg=CONTENT_BG_DARK)

    _apply_theme_to_scheduler(dark=True)

    s = ttk.Style()
    s.theme_use("dark")


def light_mode():
    global DARK_MODE

    DARK_MODE = False
    settings['dark_mode'].set(False)

    elements['status'].configure(bg=STATUS_BG)
    elements['main_content'].configure(bg=CONTENT_BG)

    for key in ('plan_content', 'actual_content'):
        ts = elements.get(key)
        if isinstance(ts, TimeScheduler):
            if 'label_hour' in ts.widgets:
                ts.widgets['label_hour'].configure(fg=LABEL_FG, bg=CONTENT_BG)
            if 'label_stints' in ts.widgets:
                ts.widgets['label_stints'].configure(fg=LABEL_FG,
                                                     bg=CONTENT_BG)

    for key in ('date_picker_event_date',):
        dp = elements.get(key)
        if dp is not None and hasattr(dp, 'master'):
            try:
                dp.master.configure(bg=CONTENT_BG)
                dp.widgets['main_frame'].configure(bg=ENTRY_BG)
                dp.entry.configure(bg=ENTRY_BG, fg=ENTRY_FG,
                                   insertbackground='black')
                dp.date_picker_icon.configure(bg=ENTRY_BG, fg=BUTTON_FG)
            except Exception:
                pass

    _apply_theme_to_elements(dark=False)

    for child in elements['status'].winfo_children():
        if isinstance(child, Label):
            child.configure(bg=STATUS_BG, fg='black')

    for child in elements['main_notebook'].winfo_children():
        child.configure(bg=CONTENT_BG)

    _apply_theme_to_scheduler(dark=False)

    s = ttk.Style()
    s.theme_use("light")


def _apply_theme_to_elements(dark: bool):
    bg_c = CONTENT_BG_DARK if dark else CONTENT_BG
    bg_e = ENTRY_BG_DARK if dark else ENTRY_BG
    fg_e = ENTRY_FG_DARK if dark else ENTRY_FG
    bg_b = BUTTON_BG_DARK if dark else BUTTON_BG
    fg_b = BUTTON_FG_DARK if dark else BUTTON_FG
    fg_l = 'white' if dark else 'black'

    for element in elements.values():
        try:
            if isinstance(element, Label):
                element.configure(bg=bg_c, fg=fg_l)
            elif isinstance(element, CTkOptionMenu):
                element.configure(fg_color=bg_e,
                                  dropdown_fg_color=bg_e,
                                  button_color=bg_b,
                                  dropdown_text_color=fg_e,
                                  text_color=fg_e)
            elif isinstance(element, Entry):
                element.configure(background=bg_e, foreground=fg_e)
                try:
                    element.configure(
                        insertbackground='white' if dark else 'black')
                except TclError:
                    pass
            elif isinstance(element, Text):
                element.configure(bg=bg_e, fg=fg_e)
            elif isinstance(element, Button):
                element.configure(bg=bg_b, fg=fg_b)
            elif isinstance(element, Listbox):
                element.configure(bg=bg_e, fg=fg_e)
            elif isinstance(element, LabelFrame):
                element.configure(bg=bg_c)
            elif isinstance(element, Frame):
                element.configure(bg=bg_c)
        except (TclError, AttributeError):
            pass

    elements['status'].configure(bg=STATUS_BG_DARK if dark else STATUS_BG)


def _apply_theme_to_scheduler(dark: bool):
    bg_c = CONTENT_BG_DARK if dark else CONTENT_BG
    fg_e = ENTRY_FG_DARK if dark else ENTRY_FG

    for key in ('plan_content', 'actual_content'):
        ts = elements.get(key)
        if not isinstance(ts, TimeScheduler):
            continue
        for wkey, widget in ts.widgets.items():
            try:
                if isinstance(widget, Label):
                    widget.configure(bg=bg_c, fg=fg_e)
                elif isinstance(widget, Frame):
                    if len(wkey.split('_')) == 4:
                        widget.configure(bg=fg_e)
            except (TclError, AttributeError):
                pass


def init_dark_mode():
    if settings.get('dark_mode') and settings['dark_mode'].get():
        dark_mode()
    else:
        light_mode()
    root.update()


def toggle_dark_mode(event=None):
    global DARK_MODE

    if DARK_MODE:
        DARK_MODE = False
        settings['dark_mode'].set(False)
        light_mode()
    else:
        DARK_MODE = True
        settings['dark_mode'].set(True)
        dark_mode()
    root.update()


if __name__ == "__main__":
    main()
