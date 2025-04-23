'''
Frontend for the Endurance Tracker

Author: Tom Wu
Date: 2025-04-01
Version: 0.0.2
'''

import sys
import os
OWD = os.getcwd()
# print(OWD)
sys.path.append(OWD)
sys.path.append(f'{OWD}/sample')
sys.path.append(f'{OWD}/docs')
os.chdir(OWD)

from docs.conf import *

from tkinter import *
from tkinter import ttk, simpledialog, messagebox
from customtkinter import CTkOptionMenu
from threading import Thread
from datetime import datetime, timedelta
from tkcalendar import Calendar, DateEntry
from time import sleep
import pytz

root = Tk()
settings = {}
variables = {}
elements = {}
current_event = 'Template'
tracker = None
server = None
client = None
# data = None

from helpers import *
from core import *



def main():
    global root, settings, variables, elements

    root.title("Endurance Tracker")
    root.geometry(GEOMETRY)
    root.resizable(True, True)
    # root.tk.call('tk', 'windowingsystem')
    root.option_add('*tearOff', FALSE)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    loading()
    root.mainloop()

def loading():
    global root, settings, variables, elements, data, server, client, \
            DARK_MODE, STATUS_BG, CONTENT_BG, ENTRY_BG, BUTTON_BG, \
            STATUS_BG_DARK, CONTENT_BG_DARK, ENTRY_BG_DARK, \
            BUTTON_BG_DARK, LABEL_FG, LABEL_FG_DARK

    s = ttk.Style()
    # s.configure("TNotebook", 
    #             tabposition="sw", 
    #             background=CONTENT_BG)
    # s.configure("TNotebook.Tab",
    #             padding=[10, 0])
    
    s.theme_create("light", parent='default', settings={
        "TNotebook": {"configure": {"background": CONTENT_BG,
                                    "tabposition": "sw"}},
        "TNotebook.Tab": {
            "configure": {"padding": [20, 10], 
                          "background": CONTENT_BG, 
                          "foreground": LABEL_FG},
            "map": {"background": [("selected", TAB_BG_ACTIVE),
                                   ("active", TAB_BG_ACTIVE),
                                   ("!disabled", CONTENT_BG),
                                   ("readonly", CONTENT_BG)],
                    "foreground": [("selected", LABEL_FG),
                                   ("active", LABEL_FG),
                                   ("!disabled", LABEL_FG),
                                   ("readonly", LABEL_FG)]},
                    "expand": [("selected", [1, 0, 1, 0])]},
        "TComboBox": {
            "configure": {'fieldbackground': ENTRY_BG,
                          'foreground': ENTRY_FG,
                          'selectbackground': '',
                          'selectforeground': ENTRY_FG,
                          'bordercolor': '',
                          'background': ''},
            "map": {"background": [("active", ENTRY_BG),
                                   ("selected", ENTRY_BG),
                                   ("!disabled", ENTRY_BG),
                                   ("readonly", ENTRY_BG)],
                    "foreground": [("active", ENTRY_FG),
                                   ("selected", ENTRY_FG),
                                   ("!disabled", ENTRY_FG),
                                   ("readonly", ENTRY_FG)]}},
        "TScrollbar": {
            "configure": {'background': ENTRY_BG,
                          'troughcolor': '#f0f0f0',
                          'arrowcolor': 'grey'}},
        })
    
    s.theme_create("dark", parent='default', settings={
        "TNotebook": {"configure": {"background": CONTENT_BG_DARK,
                                    "tabposition": "sw"}},
        "TNotebook.Tab": {
            "configure": {"padding": [20, 10], 
                          "background": CONTENT_BG_DARK, 
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
            "configure": {'fieldbackground': ENTRY_BG_DARK,
                          'foreground': ENTRY_FG,
                          'selectbackground': '',
                          'selectforeground': ENTRY_FG_DARK,
                          'bordercolor': '',
                          'background': ''},
            "map": {"background": [("active", ENTRY_BG_DARK),
                                   ("selected", ENTRY_BG_DARK),
                                   ("!disabled", ENTRY_BG_DARK),
                                   ("readonly", ENTRY_BG_DARK)],
                    "foreground": [("active", ENTRY_FG_DARK),
                                   ("selected", ENTRY_FG_DARK),
                                   ("!disabled", ENTRY_FG_DARK),
                                   ("readonly", ENTRY_FG_DARK)]}},
        "TScrollbar": {
            "configure": {'background': ENTRY_BG_DARK,
                          'troughcolor': TAB_BG_DARK_ACTIVE,
                          'arrowcolor': 'grey'}},
        })
    
    if DARK_MODE:
        s.theme_use("dark")
    else:
        s.theme_use("light")
    
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
    # root.configure(menu=main_menu)
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

    # root.update()

    # login()
    # init_dark_mode()
    server = TrackerServer(HOST, PORT)
    client = TrackerClient(HOST, PORT)
    start_status()


def load_menu():
    global root, settings, variables, elements, current_event, data

    root['menu'] = elements['main_menu']
    
    menu_app = Menu(elements['main_menu'])
    elements['main_menu'].add_cascade(label="App", menu=menu_app)
    elements['menu_app'] = menu_app
    elements['menu_app'].add_checkbutton(label="Dark Mode", command=toggle_dark_mode, variable=settings['dark_mode'])
    elements['menu_app'].add_command(label="Exit", command=on_closing)

    menu_data = Menu(elements['main_menu'])
    elements['main_menu'].add_cascade(label="Data", menu=menu_data)
    elements['menu_data'] = menu_data
    # elements['menu_data'].add_command(label="Upload", command=lambda: update_values(current_event, data))
    # elements['menu_data'].add_command(label="Download", command=download_data)
    elements['menu_data'].add_command(label="Init Tracker", command=init_theoritical_stints)


def load_status():
    global root, settings, variables, elements, server, client
    
    status = elements['status']
    for i in range(16):
        status.grid_rowconfigure(i, weight=1)
    status.grid_columnconfigure(0, weight=1)
    status.grid_columnconfigure(1, weight=2)

    variables['time_gmt'] = StringVar(value='00:00:00')
    temp_label = Label(status, text='GMT', bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew")
    temp_label = Label(status, textvariable=variables['time_gmt'], bg=STATUS_BG, 
                       font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew")
    elements['label_time_gmt'] = temp_label

    for n, i in enumerate(STATUS_TIMES.split(',')):
        variables['time_' + i.lower()] = StringVar(value='00:00:00')
        temp_label = Label(status, text=i, bg=STATUS_BG, 
                           font=("Helvetica", 16, 'bold'))
        temp_label.grid(row=n + 1, column=0, sticky="nsew")
        temp_label = Label(status, textvariable=variables['time_' + i.lower()], 
                           bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
        temp_label.grid(row=n + 1, column=1, sticky="nsew")
        elements['label_time_' + i.lower()] = temp_label

    temp_separator = ttk.Separator(status, orient=HORIZONTAL)
    temp_separator.grid(row=len(STATUS_TIMES.split(',')) + 1, column=0, columnspan=2, sticky="nsew", pady=20)
    status.grid_rowconfigure(len(STATUS_TIMES.split(',')) + 1, weight=0)

    temp_label = Label(status, text='Session', bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=len(STATUS_TIMES.split(',')) + 2, column=0, sticky="nsew")
    elements['label_session'] = temp_label
    variables['current_session'] = StringVar(value='Planning')
    temp_label = Label(status, textvariable=variables['current_session'], 
                       bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=len(STATUS_TIMES.split(',')) + 2, column=1, sticky="nsew")

    variables['current_event_time'] = StringVar(value='00:00:00')
    temp_label = Label(status, text='Event Time', bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=len(STATUS_TIMES.split(',')) + 3, column=0, sticky="nsew")
    temp_label.bind('<Button-1>', copy_time)
    temp_label = Label(status, textvariable=variables['current_event_time'], bg=STATUS_BG, 
                       font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=len(STATUS_TIMES.split(',')) + 3, column=1, sticky="nsew")
    temp_label.bind('<Button-1>', copy_time)
    elements['label_event_time'] = temp_label

    variables['current_sim_time'] = StringVar(value='00:00:00')
    temp_label = Label(status, text='Sim Time', bg=STATUS_BG, font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=len(STATUS_TIMES.split(',')) + 4, column=0, sticky="nsew")
    temp_label.bind('<Button-1>', copy_time)
    temp_label = Label(status, textvariable=variables['current_sim_time'], bg=STATUS_BG, 
                       font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=len(STATUS_TIMES.split(',')) + 4, column=1, sticky="nsew")
    temp_label.bind('<Button-1>', copy_time)
    elements['label_sim_time'] = temp_label

    

def load_main_content():
    global root, settings, variables, elements
    
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

def load_tab_home():
    global root, settings, variables, elements, server, client

    tab_home = elements['tab_home']
    tab_home.grid_columnconfigure(0, weight=3)
    tab_home.grid_columnconfigure(1, weight=1)

    temp_label = Label(tab_home, text='Server', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew")
    elements['label_server'] = temp_label

    variables['is_server'] = BooleanVar(value=IS_SERVER)
    temp_check = Checkbutton(tab_home, variable=variables['is_server'], 
                             bg=CONTENT_BG, selectcolor=CONTENT_BG, command=toggle_server)
    temp_check.grid(row=0, column=1, sticky="nsew")
    elements['check_server'] = temp_check

    temp_button = Button(tab_home, text='Start Server', command=server.start, bg=BUTTON_BG, fg=BUTTON_FG)
    temp_button.grid(row=1, column=0, sticky="nsew", pady=2)
    elements['button_start_server'] = temp_button
    temp_button = Button(tab_home, text='Stop Server', command=server.stop, bg=BUTTON_BG, fg=BUTTON_FG)
    temp_button.grid(row=1, column=1, sticky="nsew", pady=2)
    elements['button_stop_server'] = temp_button

    temp_button = Button(tab_home, text='Start Client', command=client.connect, bg=BUTTON_BG, fg=BUTTON_FG)
    temp_button.grid(row=2, column=0, sticky="nsew", pady=2)
    elements['button_start_client'] = temp_button
    temp_button = Button(tab_home, text='Stop Client', command=client.disconnect, bg=BUTTON_BG, fg=BUTTON_FG)
    temp_button.grid(row=2, column=1, sticky="nsew", pady=2)
    elements['button_stop_client'] = temp_button

    temp_label = Label(tab_home, text='Host', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=3, column=0, sticky="nsew")
    elements['label_host'] = temp_label
    
    variables['host'] = StringVar(value=HOST)
    temp_entry = Entry(tab_home, textvariable=variables['host'], justify='center', insertbackground='black')
    temp_entry.grid(row=3, column=1, sticky="nsew", pady=2)
    elements['entry_host'] = temp_entry

    temp_label = Label(tab_home, text='Port', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=4, column=0, sticky="nsew")
    elements['label_port'] = temp_label

    variables['port'] = IntVar(value=PORT)
    temp_entry = Entry(tab_home, textvariable=variables['port'], justify='center', insertbackground='black')
    temp_entry.grid(row=4, column=1, sticky="nsew", pady=2)
    elements['entry_port'] = temp_entry

    temp_label = Label(tab_home, text='Send', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=5, column=0, sticky="nsew")
    elements['label_send'] = temp_label

    variables['send'] = StringVar(value='')
    temp_entry = Entry(tab_home, textvariable=variables['send'], 
                       justify='center', insertbackground='black')
    temp_entry.grid(row=5, column=1, sticky="nsew", pady=2)
    elements['entry_send'] = temp_entry
    temp_entry.bind('<Return>', send_message)

    temp_button = Button(tab_home, text='Send', command=send_message, bg=BUTTON_BG, fg=BUTTON_FG)
    temp_button.grid(row=5, column=2, sticky="nsew", pady=2)
    elements['button_send'] = temp_button



def load_tab_general():
    global root, settings, variables, elements

    tab_general = elements['tab_general']
    tab_general.grid_columnconfigure((1), weight=1)
    tab_general.grid_columnconfigure((2), weight=2)
    for i in range(16):
        tab_general.grid_rowconfigure(i, weight=1)

    temp_label = Label(tab_general, text='Event', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew")
    elements['label_event_name'] = temp_label

    variables['event'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event'], justify='center', insertbackground='white')
    temp_entry.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['entry_event_name'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('event', '', variables['event'].get()))

    temp_label = Label(tab_general, text='Event Date', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=1, column=0, sticky="nsew")
    elements['label_event_date'] = temp_label

    variables['event_date'] = StringVar(value='')
    temp_entry = Frame(tab_general, bg=CONTENT_BG)
    temp_entry.grid(row=1, column=1, sticky="nsew", pady=2)
    temp_entry.grid_columnconfigure(0, weight=1)
    temp_entry.grid_rowconfigure(0, weight=1)
    elements['entry_event_date'] = temp_entry
    temp_date = DatePicker(temp_entry, root, settings, variables, elements)
    elements['date_picker_event_date'] = temp_date
    temp_date.entry.bind('<Return>', 
                         lambda : update_value('event_date', '', variables['event_date'].get()))

    temp_label = Label(tab_general, text='Event Time', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=2, column=0, sticky="nsew")
    elements['label_event_time'] = temp_label

    variables['event_time_h'] = StringVar(value='')
    variables['event_time_m'] = StringVar(value='')
    variables['event_time_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=5, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['event_time_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['event_time_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_event_time_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('event_time', '',
                                          f'{variables['event_time_h'].get()}:{variables['event_time_m'].get()}:{variables['event_time_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['event_time_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['event_time_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_event_time_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('event_time', '', 
                                          f'{variables['event_time_h'].get()}:{variables['event_time_m'].get()}:{variables['event_time_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['event_time_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['event_time_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_event_time_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('event_time', '', 
                                          f'{variables['event_time_h'].get()}:{variables['event_time_m'].get()}:{variables['event_time_s'].get()}'))

    temp_label = Label(tab_general, text='Event Timezone', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=3, column=0, sticky="nsew")
    elements['label_event_timezone'] = temp_label

    variables['event_timezone'] = StringVar(value='')
    temp_entry = Frame(tab_general, bg=CONTENT_BG)
    temp_entry.grid(row=3, column=1, sticky="nsew", pady=2)
    temp_entry.grid_columnconfigure(0, weight=1)
    temp_entry.grid_rowconfigure(0, weight=1)
    elements['entry_event_timezone'] = temp_entry
    temp_option = CTkOptionMenu(temp_entry, variables['event_timezone'], *pytz.all_timezones)
    elements['entry_event_timezone'] = temp_option
    temp_option.entry.bind('<Return>', 
                           lambda : update_value('event_timezone', '', variables['event_timezone'].get()))

    temp_label = Label(tab_general, text='Car', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=4, column=0, sticky="nsew")
    elements['label_car'] = temp_label

    variables['car'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['car'], justify='center', insertbackground='black')
    temp_entry.grid(row=4, column=1, sticky="nsew", pady=2)
    elements['entry_car'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('car', '', variables['car'].get()))

    temp_label = Label(tab_general, text='Total Time', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=5, column=0, sticky="nsew")
    elements['label_total_time'] = temp_label

    variables['total_time_h'] = StringVar(value='')
    variables['total_time_m'] = StringVar(value='')
    variables['total_time_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=5, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['total_time_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['total_time_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_total_time_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('total_time', '',
                                          f'{variables['total_time_h'].get()}:{variables['total_time_m'].get()}:{variables['total_time_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['total_time_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['total_time_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_total_time_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('total_time', '', 
                                          f'{variables['total_time_h'].get()}:{variables['total_time_m'].get()}:{variables['total_time_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['total_time_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['total_time_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_total_time_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('total_time', '',
                                          f'{variables['total_time_h'].get()}:{variables['total_time_m'].get()}:{variables['total_time_s'].get()}'))

    temp_label = Label(tab_general, text='Current Position', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=6, column=0, sticky="nsew")
    elements['label_current_position'] = temp_label

    variables['current_position'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['current_position'], justify='center', insertbackground='black')
    temp_entry.grid(row=6, column=1, sticky="nsew", pady=2)
    elements['entry_current_position'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('current_position', '', variables['current_position'].get()))

    temp_label = Label(tab_general, text='Total Drivers', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=7, column=0, sticky="nsew")
    elements['label_total_drivers'] = temp_label

    variables['total_drivers'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['total_drivers'], justify='center', insertbackground='black')
    temp_entry.grid(row=7, column=1, sticky="nsew", pady=2)
    elements['entry_total_drivers'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('total_drivers', '', variables['total_drivers'].get()))

    temp_label = Label(tab_general, text='Gap to Race Start', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=8, column=0, sticky="nsew")
    elements['label_gap_2_start'] = temp_label

    variables['gap_2_start_h'] = StringVar(value='')
    variables['gap_2_start_m'] = StringVar(value='')
    variables['gap_2_start_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=8, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['gap_2_start_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['gap_2_start_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_gap_2_start_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('gap_2_start', '',
                                          f'{variables['gap_2_start_h'].get()}:{variables['gap_2_start_m'].get()}:{variables['gap_2_start_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['gap_2_start_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['gap_2_start_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_gap_2_start_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('gap_2_start', '',
                                          f'{variables['gap_2_start_h'].get()}:{variables['gap_2_start_m'].get()}:{variables['gap_2_start_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['gap_2_start_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['gap_2_start_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_gap_2_start_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('gap_2_start', '',
                                          f'{variables['gap_2_start_h'].get()}:{variables['gap_2_start_m'].get()}:{variables['gap_2_start_s'].get()}'))

    temp_label = Label(tab_general, text='Practice Duration', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=9, column=0, sticky="nsew")
    elements['label_practice_duration'] = temp_label

    variables['practice_duration_h'] = StringVar(value='')
    variables['practice_duration_m'] = StringVar(value='')
    variables['practice_duration_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=9, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['practice_duration_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['practice_duration_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_practice_duration_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('practice_duration', '',
                                          f'{variables['practice_duration_h'].get()}:{variables['practice_duration_m'].get()}:{variables['practice_duration_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['practice_duration_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['practice_duration_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_practice_duration_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('practice_duration', '',
                                          f'{variables['practice_duration_h'].get()}:{variables['practice_duration_m'].get()}:{variables['practice_duration_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['practice_duration_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['practice_duration_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_practice_duration_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('practice_duration', '',
                                          f'{variables['practice_duration_h'].get()}:{variables['practice_duration_m'].get()}:{variables['practice_duration_s'].get()}'))

    temp_label = Label(tab_general, text='Qualify Duration', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=10, column=0, sticky="nsew")
    elements['label_qualify_duration'] = temp_label

    variables['qualify_duration_h'] = StringVar(value='')
    variables['qualify_duration_m'] = StringVar(value='')
    variables['qualify_duration_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=10, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['qualify_duration_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['qualify_duration_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_qualify_duration_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('qualify_duration', '',
                                          f'{variables['qualify_duration_h'].get()}:{variables['qualify_duration_m'].get()}:{variables['qualify_duration_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['qualify_duration_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['qualify_duration_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_qualify_duration_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('qualify_duration', '',
                                          f'{variables['qualify_duration_h'].get()}:{variables['qualify_duration_m'].get()}:{variables['qualify_duration_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['qualify_duration_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['qualify_duration_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_qualify_duration_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('qualify_duration', '',
                                          f'{variables['qualify_duration_h'].get()}:{variables['qualify_duration_m'].get()}:{variables['qualify_duration_s'].get()}'))

    temp_label = Label(tab_general, text='Time to Green', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=11, column=0, sticky="nsew")
    elements['label_time_to_green'] = temp_label
    
    variables['time_to_green_h'] = StringVar(value='')
    variables['time_to_green_m'] = StringVar(value='')
    variables['time_to_green_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=11, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['time_to_green_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['time_to_green_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_time_to_green_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('time_to_green', '',
                                          f'{variables['time_to_green_h'].get()}:{variables['time_to_green_m'].get()}:{variables['time_to_green_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['time_to_green_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['time_to_green_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_time_to_green_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('time_to_green', '', 
                                          f'{variables['time_to_green_h'].get()}:{variables['time_to_green_m'].get()}:{variables['time_to_green_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['time_to_green_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['time_to_green_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_time_to_green_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('time_to_green', '', 
                                          f'{variables['time_to_green_h'].get()}:{variables['time_to_green_m'].get()}:{variables['time_to_green_s'].get()}'))

    temp_label = Label(tab_general, text='Time to Start', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=12, column=0, sticky="nsew")
    elements['label_time_to_start'] = temp_label
    
    variables['time_to_start_h'] = StringVar(value='')
    variables['time_to_start_m'] = StringVar(value='')
    variables['time_to_start_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=12, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['time_to_start_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['time_to_start_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_time_to_start_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('time_to_start', '',
                                          f'{variables['time_to_start_h'].get()}:{variables['time_to_start_m'].get()}:{variables['time_to_start_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['time_to_start_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['time_to_start_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_time_to_start_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('time_to_start', '', 
                                          f'{variables['time_to_start_h'].get()}:{variables['time_to_start_m'].get()}:{variables['time_to_start_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['time_to_start_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['time_to_start_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_time_to_start_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('time_to_start', '',
                                          f'{variables['time_to_start_h'].get()}:{variables['time_to_start_m'].get()}:{variables['time_to_start_s'].get()}'))

    temp_label = Label(tab_general, text='Sim. Time Start', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=13, column=0, sticky="nsew")
    elements['label_sim_time_start'] = temp_label

    variables['sim_time_start_h'] = StringVar(value='')
    variables['sim_time_start_m'] = StringVar(value='')
    variables['sim_time_start_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=13, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['sim_time_start_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['sim_time_start_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_sim_time_start_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('sim_time_start', '',
                                          f'{variables['sim_time_start_h'].get()}:{variables['sim_time_start_m'].get()}:{variables['sim_time_start_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['sim_time_start_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['sim_time_start_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_sim_time_start_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('sim_time_start', '',
                                          f'{variables['sim_time_start_h'].get()}:{variables['sim_time_start_m'].get()}:{variables['sim_time_start_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['sim_time_start_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['sim_time_start_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_sim_time_start_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('sim_time_start', '',
                                          f'{variables['sim_time_start_h'].get()}:{variables['sim_time_start_m'].get()}:{variables['sim_time_start_s'].get()}'))

    temp_label = Label(tab_general, text='Theoretical Stint Time', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=14, column=0, sticky="nsew")
    elements['label_theoretical_stint_time'] = temp_label

    variables['theoretical_stint_time_h'] = StringVar(value='')
    variables['theoretical_stint_time_m'] = StringVar(value='')
    variables['theoretical_stint_time_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=14, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['theoretical_stint_time_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['theoretical_stint_time_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_theoretical_stint_time_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('theoretical_stint_time', '',
                                          f'{variables['theoretical_stint_time_h'].get()}:{variables['theoretical_stint_time_m'].get()}:{variables['theoretical_stint_time_s'].get()}'))    
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['theoretical_stint_time_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['theoretical_stint_time_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_theoretical_stint_time_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('theoretical_stint_time', '', 
                                          f'{variables['theoretical_stint_time_h'].get()}:{variables['theoretical_stint_time_m'].get()}:{variables['theoretical_stint_time_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['theoretical_stint_time_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['theoretical_stint_time_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_theoretical_stint_time_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('theoretical_stint_time', '', 
                                          f'{variables['theoretical_stint_time_h'].get()}:{variables['theoretical_stint_time_m'].get()}:{variables['theoretical_stint_time_s'].get()}'))

    temp_label = Label(tab_general, text='Average Stint Time', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=15, column=0, sticky="nsew")
    elements['label_average_stint_time'] = temp_label

    variables['average_stint_time_h'] = StringVar(value='')
    variables['average_stint_time_m'] = StringVar(value='')
    variables['average_stint_time_s'] = StringVar(value='')
    temp_frame = Frame(tab_general, bg=CONTENT_BG)
    temp_frame.grid(row=15, column=1, sticky="nsew")
    temp_frame.grid_rowconfigure(0, weight=1)
    temp_frame.grid_columnconfigure((0, 2, 4), weight=1)
    elements['average_stint_time_frame'] = temp_frame
    temp_entry = Entry(temp_frame, textvariable=variables['average_stint_time_h'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['entry_average_stint_time_h'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('average_stint_time', '',
                                          f'{variables['average_stint_time_h'].get()}:{variables['average_stint_time_m'].get()}:{variables['average_stint_time_s'].get()}'))    
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['average_stint_time_colon'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['average_stint_time_m'], width=5, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=2, sticky="nsew", pady=2)
    elements['entry_average_stint_time_m'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('average_stint_time', '', 
                                          f'{variables['average_stint_time_h'].get()}:{variables['average_stint_time_m'].get()}:{variables['average_stint_time_s'].get()}'))
    temp_label = Label(temp_frame, text=':', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=3, sticky="nsew", pady=2)
    elements['average_stint_time_colon_2'] = temp_label
    temp_entry = Entry(temp_frame, textvariable=variables['average_stint_time_s'], width=3, justify='center', insertbackground='black')
    temp_entry.grid(row=0, column=4, sticky="nsew", pady=2)
    elements['entry_average_stint_time_s'] = temp_entry
    temp_entry.bind('<Return>', 
                    lambda : update_value('average_stint_time', '', 
                                          f'{variables['average_stint_time_h'].get()}:{variables['average_stint_time_m'].get()}:{variables['average_stint_time_s'].get()}'))

    temp_label = Label(tab_general, text='Drivers', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(column=2, row=0, sticky="nsew", padx=10)
    elements['label_drivers'] = temp_label

    variables['drivers_raw'] = []
    variables['drivers_time_slots'] = {}
    variables['drivers'] = StringVar(value=variables['drivers_raw'])
    temp_listbox = Listbox(tab_general, 
                           height=8, 
                           width=20,
                           listvariable=variables['drivers'],
                           selectmode=MULTIPLE)
    temp_listbox.grid(column=2, row=1, rowspan=8, sticky="nsew", padx=10)
    elements['listbox_drivers'] = temp_listbox

    variables['add_driver'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['add_driver'], insertbackground='black')
    temp_entry.grid(column=2, row=9, sticky="nsew", padx=10, pady=2)
    elements['add_driver'] = temp_entry

    
    temp_button = Button(tab_general, text="Add Driver", command=add_driver)
    temp_button.grid(column=2, row=10, sticky="nsew", padx=10, pady=2)
    elements['add_driver_button'] = temp_button

    temp_button = Button(tab_general, text="Remove Driver", command=remove_driver)
    temp_button.grid(column=2, row=11, sticky="nsew", padx=10, pady=2)
    elements['remove_driver_button'] = temp_button

def load_tab_plan():
    global root, settings, variables, elements

    tab_plan = elements['tab_plan']
    tab_plan.grid_columnconfigure(0, weight=1)
    tab_plan.grid_rowconfigure((1, 3), weight=1)

    temp_label = Label(tab_plan, text='Plan', bg=CONTENT_BG, font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew")
    elements['label_plan_plan'] = temp_label

    temp_label = Label(tab_plan, text='Actual', bg=CONTENT_BG, font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=2, column=0, sticky="nsew")
    elements['label_plan_actual'] = temp_label

    plan_frame = Frame(tab_plan, bg=CONTENT_BG)
    plan_frame.grid(row=1, column=0, sticky="nsew", padx=10)
    elements['plan_frame_plan'] = plan_frame

    actual_frame = Frame(tab_plan, bg=CONTENT_BG)
    actual_frame.grid(row=3, column=0, sticky="nsew", padx=10)
    elements['plan_frame_actual'] = actual_frame

def load_tab_race():
    global root, settings, variables, elements, tracker

    tab_race = elements['tab_race']
    tab_race.grid_columnconfigure((1), weight=1)
    tab_race.grid_rowconfigure(0, weight=1)

    temp_frame = Frame(tab_race, bg=CONTENT_BG)
    temp_frame.grid(row=0, column=0, sticky="nsew", rowspan=10, padx=10)
    temp_frame.grid_columnconfigure(0, weight=1)
    temp_frame.grid_rowconfigure(0, weight=1)
    elements['race_tracker_slots_frame'] = temp_frame

    variables['race_tracker_slots_raw'] = []
    variables['race_tracker_slots'] = StringVar()
    temp_list = Listbox(temp_frame, 
                        height=20, width=10,
                        listvariable=variables['race_tracker_slots'],
                        selectmode=SINGLE,
                        exportselection=False)
    temp_list.grid(row=0, column=0, sticky="nsew", padx='5 0')
    elements['race_tracker_slots'] = temp_list
    temp_list.bind('<<ListboxSelect>>', change_race_slot)

    ys = ttk.Scrollbar(temp_frame, orient = 'vertical', command = temp_list.yview)
    temp_list['yscrollcommand'] = ys.set
    ys.grid(column=1, row=0, sticky='ns')

    input_frame = Frame(tab_race, bg=CONTENT_BG)
    input_frame.grid(row=0, column=1, sticky="nsew", padx=5)
    elements['race_tracker_input_frame'] = input_frame
    for i in range(13):
        if i != 5:
            input_frame.grid_rowconfigure(i, weight=1)
    input_frame.grid_columnconfigure((0, 1), weight=1)

    temp_separator = ttk.Separator(input_frame, orient=HORIZONTAL)
    temp_separator.grid(row=5, column=0, columnspan=2, sticky="nsew", pady=10)

    temp_label = Label(input_frame, bg=CONTENT_BG, text='Edit', font=("Helvetica", 16, 'bold'))
    edit_frame = LabelFrame(input_frame, bg=CONTENT_BG, labelwidget=temp_label)
    edit_frame.grid(row=0, column=0, rowspan=5, sticky="nsew")
    elements['race_tracker_edit_frame'] = edit_frame
    elements['race_tracker_edit_frame_label'] = temp_label
    for i in range(6):
        edit_frame.grid_rowconfigure(i, weight=1)
    edit_frame.grid_rowconfigure(6, weight=2)
    edit_frame.grid_columnconfigure((0, 1), weight=1)

    temp_label = Label(input_frame, bg=CONTENT_BG, text='Add', font=("Helvetica", 16, 'bold'))
    current_frame = LabelFrame(input_frame, bg=CONTENT_BG, 
                               labelwidget=temp_label)
    current_frame.grid(row=7, column=0, rowspan=7, sticky="nsew")
    elements['race_tracker_current_frame'] = current_frame
    elements['race_tracker_current_frame_label'] = temp_label
    for i in range(7):
        current_frame.grid_rowconfigure(i, weight=1)
    current_frame.grid_rowconfigure(7, weight=2)
    current_frame.grid_columnconfigure((0, 1), weight=1)

    # edit frame
    temp_label = Label(edit_frame, text='Driver', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['race_tracker_edit_driver_label'] = temp_label

    variables['race_tracker_edit_driver'] = StringVar(value='')
    # temp_entry = Entry(edit_frame, textvariable=variables['race_tracker_edit_driver'], insertbackground='black')
    temp_entry = CTkOptionMenu(edit_frame, variable=variables['race_tracker_edit_driver'],
                               state="readonly", corner_radius=0, button_color=BUTTON_BG,
                               dynamic_resizing=False)
    temp_entry.grid(row=0, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_edit_driver_entry'] = temp_entry

    temp_label = Label(edit_frame, text='Theoretical Stint #', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=1, column=0, sticky="nsew", pady=2)
    elements['race_tracker_edit_theoretical_stint_label'] = temp_label

    variables['race_tracker_edit_theoretical_stint'] = StringVar(value='')
    temp_entry = Entry(edit_frame, textvariable=variables['race_tracker_edit_theoretical_stint'], insertbackground='black')
    temp_entry.grid(row=1, column=1, sticky="nsew", pady=2, padx=10)
    elements['race_tracker_edit_theoretical_stint_entry'] = temp_entry

    temp_label = Label(edit_frame, text='Actual Stint #', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=2, column=0, sticky="nsew", pady=2)
    elements['race_tracker_edit_actual_stint_label'] = temp_label

    variables['race_tracker_edit_actual_stint'] = StringVar(value='')
    temp_entry = Entry(edit_frame, textvariable=variables['race_tracker_edit_actual_stint'], insertbackground='black')
    temp_entry.grid(row=2, column=1, sticky="nsew", pady=2, padx=10)
    elements['race_tracker_edit_actual_stint_entry'] = temp_entry

    temp_label = Label(edit_frame, text='Actual Driver', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=3, column=0, sticky="nsew", pady=2)
    elements['race_tracker_edit_actual_driver_label'] = temp_label

    variables['race_tracker_edit_actual_driver'] = StringVar(value='')
    # temp_entry = Entry(edit_frame, textvariable=variables['race_tracker_edit_actual_driver'], insertbackground='black')
    temp_entry = CTkOptionMenu(edit_frame, variable=variables['race_tracker_edit_actual_driver'],
                               state="readonly", corner_radius=0, button_color=BUTTON_BG,
                               dynamic_resizing=False)
    temp_entry.grid(row=3, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_edit_actual_driver_entry'] = temp_entry

    temp_label = Label(edit_frame, text='Est. Chance of Rain (%)', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=4, column=0, sticky="nsew", pady=2)
    elements['race_tracker_edit_est_chance_of_rain_label'] = temp_label

    variables['race_tracker_edit_est_chance_of_rain'] = StringVar(value='')
    temp_entry = Entry(edit_frame, textvariable=variables['race_tracker_edit_est_chance_of_rain'], insertbackground='black')
    temp_entry.grid(row=4, column=1, sticky="nsew", pady=2, padx=10)
    elements['race_tracker_edit_est_chance_of_rain_entry'] = temp_entry

    temp_label = Label(edit_frame, text='Actual Weather', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=5, column=0, sticky="nsew", pady=2)
    elements['race_tracker_edit_actual_weather_label'] = temp_label

    # temp_frame = Frame(edit_frame, bg=CONTENT_BG)
    # temp_frame.grid(row=5, column=1, sticky="we")
    # elements['race_tracker_edit_actual_weather_frame'] = temp_frame
    # temp_frame.grid_columnconfigure(0, weight=1)
    # temp_frame.grid_rowconfigure(0, weight=1)

    variables['race_tracker_edit_actual_weather'] = StringVar(value='')
    # temp_entry = ttk.Combobox(edit_frame, textvariable=variables['race_tracker_edit_actual_weather'],
    #                           state="readonly")
    temp_entry = CTkOptionMenu(edit_frame, variable=variables['race_tracker_edit_actual_weather'],
                               state="readonly", corner_radius=0, button_color=BUTTON_BG,
                               dynamic_resizing=False)
    temp_entry.grid(row=5, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_edit_actual_weather_entry'] = temp_entry
    # print(type(temp_entry), isinstance(temp_entry, Entry))

    temp_frame = Frame(edit_frame, bg=CONTENT_BG)
    temp_entry = Text(temp_frame, height=2, width=15)
    temp_entry.grid(column = 0, row = 0, sticky = 'nwes')
    ys = ttk.Scrollbar(temp_frame, orient = 'vertical', command = temp_entry.yview)
    xs = ttk.Scrollbar(temp_frame, orient = 'horizontal', command = temp_entry.xview)
    temp_entry['yscrollcommand'] = ys.set
    temp_entry['xscrollcommand'] = xs.set
    xs.grid(column = 0, row = 1, sticky = 'we')
    ys.grid(column = 1, row = 0, sticky = 'ns')
    temp_frame.grid_columnconfigure(0, weight = 1)
    temp_frame.grid_rowconfigure(0, weight = 1)
    temp_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", pady=5, padx=10)
    elements['race_tracker_edit_notes_text_frame'] = temp_frame
    elements['race_tracker_edit_notes_text'] = temp_entry

    temp_button = Button(input_frame, text="Update", command=edit_update)
    temp_button.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
    elements['race_tracker_edit_update_button'] = temp_button

    temp_button = Button(input_frame, text="Reset", command=edit_reset)
    temp_button.grid(row=2, column=1, sticky="nsew", padx=20, pady=20)
    elements['race_tracker_edit_reset_button'] = temp_button

    temp_button = Button(input_frame, text="Delete", command=edit_delete)
    temp_button.grid(row=3, column=1, sticky="nsew", padx=20, pady=20)
    elements['race_tracker_edit_delete_button'] = temp_button

    # current frame
    temp_label = Label(current_frame, text='Race Time', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew", pady=2)
    elements['race_tracker_current_time_label'] = temp_label

    variables['race_tracker_current_time'] = StringVar(value='')
    temp_entry = Entry(current_frame, textvariable=variables['race_tracker_current_time'], insertbackground='black')
    temp_entry.grid(row=0, column=1, sticky="nsew", pady=2, padx=10)
    elements['race_tracker_current_time_entry'] = temp_entry

    temp_label = Label(current_frame, text='Driver', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=1, column=0, sticky="nsew", pady=2)
    elements['race_tracker_current_driver_label'] = temp_label

    variables['race_tracker_current_driver'] = StringVar(value='')
    # temp_entry = Entry(current_frame, textvariable=variables['race_tracker_current_driver'], insertbackground='black')
    temp_entry = CTkOptionMenu(current_frame, variable=variables['race_tracker_current_driver'],
                               state="readonly", corner_radius=0, button_color=BUTTON_BG,
                               dynamic_resizing=False)
    temp_entry.grid(row=1, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_current_driver_entry'] = temp_entry

    temp_label = Label(current_frame, text='Theoretical Stint #', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=2, column=0, sticky="nsew", pady=2)
    elements['race_tracker_current_theoretical_stint_label'] = temp_label

    variables['race_tracker_current_theoretical_stint'] = StringVar(value='')
    temp_entry = Entry(current_frame, textvariable=variables['race_tracker_current_theoretical_stint'], insertbackground='black')
    temp_entry.grid(row=2, column=1, sticky="nsew", pady=2, padx=10)
    elements['race_tracker_current_theoretical_stint_entry'] = temp_entry

    temp_label = Label(current_frame, text='Actual Stint #', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=3, column=0, sticky="nsew", pady=2)
    elements['race_tracker_current_actual_stint_label'] = temp_label

    variables['race_tracker_current_actual_stint'] = StringVar(value='')
    temp_entry = Entry(current_frame, textvariable=variables['race_tracker_current_actual_stint'], insertbackground='black')
    temp_entry.grid(row=3, column=1, sticky="nsew", pady=2, padx=10)
    elements['race_tracker_current_actual_stint_entry'] = temp_entry

    temp_label = Label(current_frame, text='Actual Driver', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=4, column=0, sticky="nsew", pady=2)
    elements['race_tracker_current_actual_driver_label'] = temp_label

    variables['race_tracker_current_actual_driver'] = StringVar(value='')
    # temp_entry = Entry(current_frame, textvariable=variables['race_tracker_current_actual_driver'], insertbackground='black')
    temp_entry = CTkOptionMenu(current_frame, variable=variables['race_tracker_current_actual_driver'],
                               state="readonly", corner_radius=0, button_color=BUTTON_BG,
                               dynamic_resizing=False)
    temp_entry.grid(row=4, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_current_actual_driver_entry'] = temp_entry

    temp_label = Label(current_frame, text='Est. Chance of Rain (%)', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=5, column=0, sticky="nsew", pady=2)
    elements['race_tracker_current_est_chance_of_rain_label'] = temp_label

    variables['race_tracker_current_est_chance_of_rain'] = StringVar(value='')
    temp_entry = Entry(current_frame, textvariable=variables['race_tracker_current_est_chance_of_rain'], insertbackground='black')
    temp_entry.grid(row=5, column=1, sticky="nsew", pady=2, padx=10)
    elements['race_tracker_current_est_chance_of_rain_entry'] = temp_entry

    temp_label = Label(current_frame, text='Actual Weather', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=6, column=0, sticky="nsew", pady=2)
    elements['race_tracker_current_actual_weather_label'] = temp_label

    variables['race_tracker_current_actual_weather'] = StringVar(value='')
    temp_entry = CTkOptionMenu(current_frame, variable=variables['race_tracker_current_actual_weather'],
                               state="readonly", corner_radius=0, button_color=BUTTON_BG,
                               dynamic_resizing=False)
    # temp_entry = ttk.Combobox(current_frame, textvariable=variables['race_tracker_current_actual_weather'],
    #                           state="readonly")
    temp_entry.grid(row=6, column=1, sticky="ew", pady=2, padx=10)
    elements['race_tracker_current_actual_weather_entry'] = temp_entry

    temp_frame = Frame(current_frame, bg=CONTENT_BG)
    temp_entry = Text(temp_frame, height=2, width=15)
    temp_entry.grid(column = 0, row = 0, sticky = 'nwes')
    ys = ttk.Scrollbar(temp_frame, orient = 'vertical', command = temp_entry.yview)
    xs = ttk.Scrollbar(temp_frame, orient = 'horizontal', command = temp_entry.xview)
    temp_entry['yscrollcommand'] = ys.set
    temp_entry['xscrollcommand'] = xs.set
    xs.grid(column = 0, row = 1, sticky = 'we')
    ys.grid(column = 1, row = 0, sticky = 'ns')
    temp_frame.grid_columnconfigure(0, weight = 1)
    temp_frame.grid_rowconfigure(0, weight = 1)
    temp_frame.grid(row=7, column=0, columnspan=2, sticky="nsew", pady=5, padx=10)
    elements['race_tracker_current_notes_text'] = temp_entry
    elements['race_tracker_current_notes_text_frame'] = temp_frame

    temp_button = Button(input_frame, text="Add", command=current_add)
    temp_button.grid(row=7, column=1, sticky="nsew", padx=20, pady=10)
    elements['add_button'] = temp_button

    temp_button = Button(input_frame, text="Practice", command=current_sessions)
    temp_button.grid(row=8, column=1, sticky="nsew", padx=20, pady=10)
    elements['session_button'] = temp_button

    temp_button = Button(input_frame, text='Back', command=current_back)
    temp_button.grid(row=9, column=1, sticky="nsew", padx=20, pady=10)
    elements['back_button'] = temp_button

    temp_button = Button(input_frame, text='Pitting IN', command=current_pit)
    temp_button.grid(row=10, column=1, sticky="nsew", padx=20, pady=10)
    elements['pit_button'] = temp_button

    temp_button = Button(input_frame, text='Copy from Above', command=current_copy)
    temp_button.grid(row=11, column=1, sticky="nsew", padx=20, pady=10)
    elements['copy_button'] = temp_button

def init_time_scheduler():
    global root, settings, variables, elements, data, current_event

    if 'plan_content' in elements:
        elements['plan_content'].__del__()
    if 'actual_content' in elements:
        elements['actual_content'].__del__()

    for i in range(8):
        elements['plan_frame_plan'].grid_rowconfigure(i, weight=0)
        elements['plan_frame_actual'].grid_rowconfigure(i, weight=0)
    root.update()

    plan_content = TimeScheduler(root, settings, variables, elements, data, 
                                 target='plan', current_event=current_event)
    elements['plan_content'] = plan_content

    actual_content = TimeScheduler(root, settings, variables, elements, data, 
                                   target='actual', current_event=current_event)
    elements['actual_content'] = actual_content

    init_dark_mode()


def start_status():
    global root, settings, variables, elements

    settings['status_thread'] = Thread(target=update_status, daemon=True)
    settings['status_state'] = True
    settings['status_thread'].start()

def get_delta(variable=''):
    global root, settings, variables, elements

    if f'{variable}_h' not in variables:
        return timedelta(hours=float(variable.split(':')[0]),
                         minutes=float(variable.split(':')[1]),
                         seconds=float(variable.split(':')[2]))

    return timedelta(hours=float(variables[f'{variable}_h'].get()), 
                     minutes=float(variables[f'{variable}_m'].get()), 
                     seconds=float(variables[f'{variable}_s'].get()))

def set_time(variable='', time='00:00:00'):
    global root, settings, variables, elements

    if f'{variable}_h' not in variables:
        return

    variables[f'{variable}_h'].set(time.split(':')[0])
    variables[f'{variable}_m'].set(time.split(':')[1])
    variables[f'{variable}_s'].set(time.split(':')[2])

def get_duration(variable='event_time_est', tz_from='US/Eastern', tz_to='GMT'):
    global root, settings, variables, elements

    if variable not in variables:
        return

    return datetime.now(pytz.utc) - tz_diff(variables[variable].get(), tz_from, tz_to)

def update_status():
    global root, settings, variables, elements

    # root.update()
    while settings['status_state']:

        # handling timezones
        variables['time_gmt'].set(datetime.now(pytz.timezone('GMT')).strftime('%H:%M:%S'))
        for i in STATUS_TIMES.split(","):
            variables['time_' + i.lower()].set(datetime.now().astimezone(pytz.timezone(i)).strftime('%H:%M:%S'))
        
        # handling race times
        race_length = get_delta('total_time')
        now = datetime.now(pytz.utc)
        event_start = tz_diff(variables['event_time_est'].get(), 'US/Eastern', 'GMT')
        event_end = event_start + race_length

        if event_start < now < event_end:
            duration = get_duration()
            practice, qualify, to_green, to_start, sim_start = map(get_delta, 
            ['practice_duration', 'qualify_duration', 'time_to_green', 'time_to_start', 'sim_time_start'])
            gap_2_start = str(practice + qualify + to_green + to_start).split('.')[0]
            set_time('gap_2_start', gap_2_start)

            elements['session_button'].configure(state=NORMAL)
            elements['back_button'].configure(state=NORMAL)
            elements['pit_button'].configure(state=NORMAL)

            if duration <= practice:
                session, event_time = 'Practice', duration
            elif duration <= practice + qualify:
                session, event_time = 'Qualify', duration - practice
            elif duration <= practice + qualify + to_green:
                session, event_time = 'Waiting for Drivers', duration - practice - qualify
                variables['current_sim_time'].set(str(duration - practice - qualify + sim_start).split('.')[0])
            elif duration <= practice + qualify + to_green + to_start:
                session, event_time = 'Formation Lap', duration - practice - qualify
                variables['current_sim_time'].set(str(duration - practice - qualify + sim_start).split('.')[0])
            else:
                session, event_time = 'Race Started', duration - practice - qualify
                variables['current_sim_time'].set(str(duration - practice - qualify + sim_start).split('.')[0])
            if duration > practice + qualify + to_green + to_start + race_length:
                session, event_time = 'Race Over', timedelta(0)
                elements['session_button'].configure(state=DISABLED, text='Race Over')
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

        # handling elements
        # download_data()

        handshake()

        sleep(1)


def add_driver():
    global settings, variables, elements, current_event, data

    if variables['add_driver'].get() == '':
        return
    
    if variables['add_driver'].get() in variables['drivers_raw']:
        return
    
    if len(variables['drivers_raw']) == MAX_DRIVER:
        messagebox.showerror("Driver not added!", "Maximum number of drivers reached")
        return
    
    variables['drivers_raw'].append(variables['add_driver'].get())
    variables['drivers'].set(variables['drivers_raw'])

    if variables['add_driver'].get() not in variables['drivers_time_slots']:
        variables['drivers_time_slots'][variables['add_driver'].get()] = ['0'] * int(variables['total_time'].get())

    reset_drivers_time_slots()
    variables['add_driver'].set('')

    for i in ['race_tracker_edit_driver_entry',
              'race_tracker_edit_actual_driver_entry',
              'race_tracker_current_driver_entry',
              'race_tracker_current_actual_driver_entry']:
        elements[i].configure(values=variables['drivers_raw'])

def remove_driver():
    global settings, variables, elements, current_event, data

    listbox_drivers = elements['listbox_drivers']
    if len(listbox_drivers.curselection()) == 0:
        return
    
    to_delete = []
    for i in listbox_drivers.curselection():
        to_delete.append(variables['drivers_raw'][i])
    for i in to_delete:
        variables['drivers_raw'].remove(i)
        variables['drivers_time_slots'][i] = ['0'] * int(variables['total_time'].get())
    variables['drivers'].set(variables['drivers_raw'])


    reset_drivers_time_slots()

    for i in ['race_tracker_edit_driver_entry',
              'race_tracker_edit_actual_driver_entry',
              'race_tracker_current_driver_entry',
              'race_tracker_current_actual_driver_entry']:
        elements[i].configure(values=variables['drivers_raw'])


def reset_drivers_time_slots():
    global settings, variables, elements, current_event, server, client

    if variables['is_server'].get():
        server.update_drivers_time_slots()
    else:
        client.update_drivers_time_slots()

    
    # print(type(data.iloc[:101, R:Z]))
    # update_values(current_event, data.iloc[1:101, R:Z], 'R2:Y100')
    init_time_scheduler()

def on_closing():
    global root, settings, variables, elements, SHEET_ID, STATUS_TIMES, DARK_MODE

    settings['status_state'] = False
    settings['status_thread'] = None
    
    set_config('general', 'geometry', root.geometry())
    set_config('settings', 'sheet_id', SHEET_ID)
    set_config('settings', 'times', str(STATUS_TIMES))
    set_config('general', 'dark_mode', str(DARK_MODE))
    set_config('general', 'data_dir', DATA_DIR)
    set_config('general', 'server', variables['is_server'].get())
    set_config('com', 'host', variables['host'].get())
    set_config('com', 'port', variables['port'].get())

    sleep(1)
    root.destroy()

def change_race_slot(event=None):
    global root, settings, variables, elements, data, tracker

    slots_list = elements['race_tracker_slots']
    slots_list.focus_set()
    selected = slots_list.curselection()
    if len(selected) == 0:
        return
    
    slot = variables['race_tracker_slots_raw'].index(slots_list.get(selected[0]))

    variables['race_tracker_edit_driver'].set(tracker.loc[slot, 'Driver'])
    variables['race_tracker_edit_theoretical_stint'].set(tracker.loc[slot, 'Theoretical Stints #'])
    variables['race_tracker_edit_actual_stint'].set(tracker.loc[slot, 'Actual Stints #'])
    variables['race_tracker_edit_actual_driver'].set(tracker.loc[slot, 'Actual Driver'])
    variables['race_tracker_edit_est_chance_of_rain'].set(tracker.loc[slot, 'Est. Chance of Rain (%)'])
    variables['race_tracker_edit_actual_weather'].set(tracker.loc[slot, 'Act. Weather at Time'])
    elements['race_tracker_edit_notes_text'].delete('1.0', 'end')
    elements['race_tracker_edit_notes_text'].insert('end', str(tracker.loc[slot, 'Notes']))

def update_race_slot(event=None):
    global root, settings, variables, elements, data, tracker


def edit_update(event=None):
    global root, settings, variables, elements, tracker, current_event

    slots_list = elements['race_tracker_slots']
    selected = slots_list.curselection()
    if len(selected) == 0:
        return
    
    slot = variables['race_tracker_slots_raw'].index(slots_list.get(selected[0])) + 1
    # print(tracker)
    tracker.at[slot, 'Driver'] = variables['race_tracker_edit_driver'].get()
    tracker.at[slot, 'Theoretical Stints #'] = variables['race_tracker_edit_theoretical_stint'].get()
    tracker.at[slot, 'Actual Stints #'] = variables['race_tracker_edit_actual_stint'].get()
    tracker.at[slot, 'Actual Driver'] = variables['race_tracker_edit_actual_driver'].get()
    tracker.at[slot, 'Est. Chance of Rain (%)'] = variables['race_tracker_edit_est_chance_of_rain'].get()
    tracker.at[slot, 'Act. Weather at Time'] = variables['race_tracker_edit_actual_weather'].get()
    tracker.at[slot, 'Notes'] = elements['race_tracker_edit_notes_text'].get('1.0', 'end-1c')

    # print(tracker.iloc[slot, 1:8].T.values.tolist())
    update_values(current_event, tracker.iloc[slot, 1:8].T.values.tolist(), f'E{slot + 1}:K{slot + 1}')

def edit_reset(event=None):
    global root, settings, variables, elements, tracker, current_event

    slots_list = elements['race_tracker_slots']
    selected = slots_list.curselection()
    if len(selected) == 0:
        return
    
    slot = variables['race_tracker_slots_raw'].index(slots_list.get(selected[0]))
    # print(slot)
    variables['race_tracker_edit_driver'].set(tracker.at[slot, 'Driver'])
    variables['race_tracker_edit_theoretical_stint'].set(tracker.at[slot, 'Theoretical Stints #'])
    variables['race_tracker_edit_actual_stint'].set(tracker.at[slot, 'Actual Stints #'])
    variables['race_tracker_edit_actual_driver'].set(tracker.at[slot, 'Actual Driver'])
    variables['race_tracker_edit_est_chance_of_rain'].set(tracker.at[slot, 'Est. Chance of Rain (%)'])
    variables['race_tracker_edit_actual_weather'].set(tracker.at[slot, 'Act. Weather at Time'])
    elements['race_tracker_edit_notes_text'].delete('1.0', 'end')
    elements['race_tracker_edit_notes_text'].insert('end', tracker.at[slot, 'Notes'])

def edit_delete(event=None):
    global root, settings, variables, elements, tracker, current_event, data

    slots_list = elements['race_tracker_slots']
    selected = slots_list.curselection()
    if len(selected) == 0:
        return
    
    slot = variables['race_tracker_slots_raw'].index(slots_list.get(selected[0]))
    if slots_list.get(selected[0]).split(':')[1] in ['00', '15', '30', '45'] and \
        slots_list.get(selected[0]).split(':')[2] == '00':
        variables['race_tracker_edit_driver'].set(tracker.at[slot, 'Driver'])
        variables['race_tracker_edit_theoretical_stint'].set(tracker.at[slot, 'Theoretical Stints #'])
        variables['race_tracker_edit_actual_stint'].set('')
        variables['race_tracker_edit_actual_driver'].set('')
        variables['race_tracker_edit_est_chance_of_rain'].set(tracker.at[slot, 'Est. Chance of Rain (%)'])
        variables['race_tracker_edit_actual_weather'].set('Unknown')
        elements['race_tracker_edit_notes_text'].delete('1.0', 'end')

    else:
        tracker.drop(slot, inplace=True)
        tracker.reset_index(drop=True, inplace=True)
        data.at[TRACKER_RANGE[0]:TRACKER_RANGE[1], TRACKER_RANGE[2]:TRACKER_RANGE[3]] = tracker.values
        update_values(current_event, 
                      data.iloc[TRACKER_RANGE[0]:TRACKER_RANGE[1], 
                                TRACKER_RANGE[2]:TRACKER_RANGE[3]].values.tolist(), 
                      'D2:K200')
        # update_variables_from_data_frame()
        slots_list.selection_set(slot - 1)
        change_race_slot()
        

def current_add(event=None):
    global root, settings, variables, elements, tracker, current_event, data

    if variables['race_tracker_current_time'].get() == '':
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
        elements['race_tracker_current_notes_text'].get('1.0', 'end-1c')
    ]

    add_to_tracker(to_add)

def add_to_tracker(to_add):
    global root, settings, variables, elements, tracker, current_event, data

    tracker.loc[len(tracker.index)] = to_add
    temp = tracker.iloc[2:, :].copy()
    temp.sort_values(by='Overall Time Slots', inplace=True)
    tracker.iloc[2:, :] = temp.values.tolist()
    tracker.reset_index(drop=True, inplace=True)

    slots_list = elements['race_tracker_slots']
    variables['race_tracker_slots_raw'] = tracker['Overall Time Slots'].values.tolist()
    variables['race_tracker_slots'].set(variables['race_tracker_slots_raw'])
    slots_list.update()
    slots_list.selection_set(variables['race_tracker_slots_raw'].index(to_add[0]))
    # print(tracker)

    data.loc[len(data.index)] = data.iloc[-1, :].values.tolist()
    data.iloc[TRACKER_RANGE[0]:TRACKER_RANGE[1], TRACKER_RANGE[2]:TRACKER_RANGE[3]] = tracker.values.tolist()
    update_values(current_event, 
                  data.iloc[TRACKER_RANGE[0]:TRACKER_RANGE[1], TRACKER_RANGE[2]:TRACKER_RANGE[3]], 
                  'D2:K200')

    variables['race_tracker_current_time'].set('')


def current_sessions(event=None):
    global root, settings, variables, elements, tracker, current_event

    session_button = elements['session_button']
    if session_button['text'] == 'Practice':
        session_button.configure(text='Qualify')
        variables['practice_duration'].set(get_duration().strftime('%H:%M:%S'))
        update_values(current_event, [variables['practice_duration'].get()], 'B9')
    elif session_button['text'] == 'Qualify':
        session_button.configure(text='Waiting for Drivers')
        variables['qualify_duration'].set(
            (get_duration() - get_delta('practice_duration')).strftime('%H:%M:%S'))
        update_values(current_event, [variables['qualify_duration'].get()], 'B10')
    elif session_button['text'] == 'Waiting for Drivers':
        session_button.configure(text='Waiting for Race Start')
        variables['time_to_green'].set(
            (get_duration() - get_delta('practice_duration') - get_delta('qualify_duration')).strftime('%H:%M:%S'))
        update_values(current_event, [variables['time_to_green'].get()], 'B11')
    elif session_button['text'] == 'Waiting for Race Start':
        session_button.configure(text='Race Started')
        variables['time_to_start'].set(
            (get_duration() - get_delta('practice_duration') - 
             get_delta('qualify_duration') - get_delta('time_to_green')).strftime('%H:%M:%S'))
        variables['gap_2_start'].set(get_duration().strftime('%H:%M:%S'))
        update_values(current_event, [variables['time_to_start'].get()], 'B12')
        update_values(current_event, [variables['gap_2_start'].get()], 'B8')
    elif session_button['text'] == 'Race Started':
        session_button.configure(text='Race Over')

        # add race over in data
        to_add = [
            variables['current_event_time'].get(),
            variables['race_tracker_current_driver'].get(),
            variables['race_tracker_current_theoretical_stint'].get(),
            variables['race_tracker_current_actual_stint'].get(),
            variables['race_tracker_current_actual_driver'].get(),
            variables['race_tracker_current_est_chance_of_rain'].get(),
            variables['race_tracker_current_actual_weather'].get(),
            'RACE OVER'
        ]

        add_to_tracker(to_add)
        
def current_back(event=None):
    global root, settings, variables, elements, tracker, current_event, data

    session_button = elements['session_button']
    if session_button['text'] == 'Qualify':
        session_button.configure(text='Practice')
    elif session_button['text'] == 'Waiting for Drivers':
        session_button.configure(text='Qualify')
    elif session_button['text'] == 'Waiting for Race Start':
        session_button.configure(text='Waiting for Drivers')
    elif session_button['text'] == 'Race Started':
        session_button.configure(text='Waiting for Drivers')
        variables['time_to_start'].set('01:00:00')
    elif session_button['text'] == 'Race Over':
        session_button.configure(text='Race Started')

        # Delete rows where "Notes" column has "RACE OVER" and reindex data
        data[data['Notes'] != 'RACE OVER'].reset_index(drop=True, inplace=True)

def current_pit(event=None):
    global root, settings, variables, elements, tracker, current_event

    pit_button = elements['pit_button']
    if pit_button['text'] == 'Pitting IN':
        pit_button.configure(text='Pitting OUT')

        # add pit in data
        to_add = [
            variables['current_event_time'].get(),
            variables['race_tracker_current_driver'].get(),
            variables['race_tracker_current_theoretical_stint'].get(),
            variables['race_tracker_current_actual_stint'].get(),
            variables['race_tracker_current_actual_driver'].get(),
            variables['race_tracker_current_est_chance_of_rain'].get(),
            variables['race_tracker_current_actual_weather'].get(),
            'PITTING IN'
        ]

        add_to_tracker(to_add)

    elif pit_button['text'] == 'Pitting OUT':
        pit_button.configure(text='Pitting IN')

        # add pit out data
        to_add = [
            variables['current_event_time'].get(),
            variables['race_tracker_current_driver'].get(),
            variables['race_tracker_current_theoretical_stint'].get(),
            variables['race_tracker_current_actual_stint'].get(),
            variables['race_tracker_current_actual_driver'].get(),
            variables['race_tracker_current_est_chance_of_rain'].get(),
            variables['race_tracker_current_actual_weather'].get(),
            'PITTING OUT'
        ]

        add_to_tracker(to_add)

        variables['race_tracker_current_actual_stint'].set(
            int(variables['race_tracker_current_actual_stint'].get()) + 1)

    calculate_avg_stint_time()

def current_copy(event=None):
    global root, settings, variables, elements, tracker, current_event

    variables['race_tracker_current_driver'].set(variables['race_tracker_edit_driver'].get())
    variables['race_tracker_current_est_chance_of_rain'].set(
        variables['race_tracker_edit_est_chance_of_rain'].get())
    variables['race_tracker_current_theoretical_stint'].set(
        variables['race_tracker_edit_theoretical_stint'].get())
    variables['race_tracker_current_actual_driver'].set(
        variables['race_tracker_current_actual_driver'].get())
    variables['race_tracker_current_actual_stint'].set(
        variables['race_tracker_edit_actual_stint'].get())
    variables['race_tracker_current_actual_weather'].set(
        variables['race_tracker_edit_actual_weather'].get())

# def update_variables_from_data_frame(reset_slots=False):
#     global root, settings, variables, elements, data, creds, tracker

#     variables['event'].set(get_data_frame_value(index='INDEX_EVENT_NAME'))
#     variables['event_time_est'].set(get_data_frame_value(index='INDEX_EVENT_TIME_EST'))
#     try:
#         est = datetime.strptime(variables['event_time_est'].get(), '%m-%d-%Y %H:%M:%S')
#     except ValueError:
#         est = datetime.strptime(variables['event_time_est'].get(), '%m-%d-%Y %I:%M:%S %p')
#     cst = est - timedelta(hours=1)
#     mst = est - timedelta(hours=2)
#     variables['event_time_cst'].set(cst.strftime('%m-%d-%Y %H:%M:%S %p'))
#     variables['event_time_mst'].set(mst.strftime('%m-%d-%Y %H:%M:%S %p'))
#     variables['car'].set(get_data_frame_value(index='INDEX_CAR'))
#     set_time('total_time', get_data_frame_value(index='INDEX_TOTAL_TIME'))
#     variables['current_position'].set(get_data_frame_value(index='INDEX_CURRENT_POSITION'))
#     variables['total_drivers'].set(get_data_frame_value(index='INDEX_TOTAL_DRIVER'))
#     set_time('gap_2_start', get_data_frame_value(index='INDEX_GAP_TO_RACE_START'))
#     set_time('practice_duration', get_data_frame_value(index='INDEX_PRACTICE_DURATION'))
#     set_time('qualify_duration', get_data_frame_value(index='INDEX_QUALIFY_DURATION'))
#     set_time('time_to_green', get_data_frame_value(index='INDEX_TIME_TO_GREEN'))
#     set_time('time_to_start', get_data_frame_value(index='INDEX_TIME_TO_START'))
#     set_time('sim_time_start', get_data_frame_value(index='INDEX_SIM_TIME_START'))
#     set_time('theoretical_stint_time', get_data_frame_value(index='INDEX_THEORETICAL_STINT_TIME'))
#     variables['average_stint_time'].set(get_data_frame_value(index='INDEX_AVERAGE_STINT_TIME'))
#     variables['weather'] = []
#     variables['drivers_time_slots'] = {}
#     variables['drivers_raw'] = []
#     variables['drivers'].set(variables['drivers_raw'])
#     root.update()

#     stints = ceil(get_delta('total_time') / get_delta('theoretical_stint_time'))

#     for i in range(1, 9):
#         driver = get_data_frame_value(index='INDEX_DRIVER_' + str(i))
#         if driver != '':
#             variables['drivers_raw'].append(driver)
#             variables['drivers_time_slots'][driver] = []
#             for j in range(1, stints + 1):
#                 variables['drivers_time_slots'][driver].append(get_data_frame_value(col=Q + i, row=j))

#     variables['drivers'].set(variables['drivers_raw'])
#     elements['listbox_drivers'].update()

#     tracker_raw = DataFrame(data=data.iloc[TRACKER_RANGE[0]:TRACKER_RANGE[1], 
#                                            TRACKER_RANGE[2]:TRACKER_RANGE[3]].values.tolist(), 
#                             columns=data.iloc[0, TRACKER_RANGE[2]:TRACKER_RANGE[3]].values.tolist())
#     tracker_raw.sort_values(by='Overall Time Slots', inplace=True)
#     temp = tracker_raw.iloc[:-2, :].copy()
#     temp.sort_values(by='Overall Time Slots', inplace=True)
#     tracker = tracker_raw.iloc[-2:, :].copy()
#     tracker = concat([tracker, temp], ignore_index=True)
#     # tracker.iloc[2:, :] = temp.values.tolist()
#     # tracker.reset_index(drop=True, inplace=True)
#     # tracker.columns = tracker.iloc[0]
#     # print(tracker.loc[:201, "Overall Time Slots"].values.tolist())
#     variables['race_tracker_slots_raw'] = tracker.loc[:201, "Overall Time Slots"].values.tolist()
#     for i in variables['race_tracker_slots_raw']:
#         if i in ['Practice', 'Qualify']:
#             continue
#         if get_delta(i) <= get_delta('total_time') + get_delta('theoretical_stint_time'):
#             continue
#         else:
#             del variables['race_tracker_slots_raw'][variables['race_tracker_slots_raw'].index(i):]
#             break
#     variables['race_tracker_slots'].set(variables['race_tracker_slots_raw'])
#     slots_list = elements['race_tracker_slots']
#     if reset_slots:
#         slots_list.selection_set(0)
#     change_race_slot()

#     for i in range(WEATHER_LENGTH):
#         variables['weather'].append(get_data_frame_value(col=Z, row=i + 1))

#     for i in ['race_tracker_edit_actual_weather_entry',
#               'race_tracker_current_actual_weather_entry']:
#         elements[i].configure(values=variables['weather'])

#     for i in ['race_tracker_edit_driver_entry',
#               'race_tracker_edit_actual_driver_entry',
#               'race_tracker_current_driver_entry',
#               'race_tracker_current_actual_driver_entry']:
#         elements[i].configure(values=variables['drivers_raw'])


#     calculate_avg_stint_time()

def calculate_avg_stint_time():
    global root, settings, variables, elements, data, tracker

    variables['stint_time_raw'] = []
    pits = tracker.loc[(tracker['Notes'] == 'PITTING IN') | (tracker['Notes'] == 'PITTING OUT')]
    if pits.empty:
        return

    total = 0
    prev_pit = 0
    for i in range(len(pits)):
        if pits.iloc[i, 7] == 'PITTING IN':
            total += 1
            if int(pits.iloc[i, 3]) == total:
                if pits.iloc[i + 1, 7] == 'PITTING OUT':
                    if prev_pit == 0:
                        variables['stint_time_raw'].append(get_delta(pits.iloc[i + 1, 0]))
                    else:
                        variables['stint_time_raw'].append(get_delta(pits.iloc[i + 1, 0]) - get_delta(pits.iloc[prev_pit, 0]))
                    prev_pit = i + i
    
    variables['average_stint_time'].set(str(sum(variables['stint_time_raw'], timedelta(0)) / len(variables['stint_time_raw'])).split('.')[0])


def copy_time(event=None):
    global root, settings, variables, elements

    root.clipboard_clear()
    root.clipboard_append(variables['current_event_time'].get())
    root.update()

def init_theoritical_stints(event=None):
    global root, settings, variables, elements, data, tracker

    tracker.iloc[:, 1:] = ''
    tracker.iloc[2:, 0] = ''

    total_time = get_delta('total_time')
    total_time_mins = ceil(total_time.total_seconds() / 60)
    theoretical_stint_time = get_delta('theoretical_stint_time')
    theoretical_stint_time_mins = ceil(theoretical_stint_time.total_seconds() / 60)
    stints = ceil(total_time / theoretical_stint_time)

    index = 2
    for i in range(total_time_mins):
        if i % 15 == 0:
            slot = int(i / 15)
            time = timedelta(minutes=15) * slot
            tracker.iloc[index, 0] = format_timedelta(time)
            index += 1
        
        elif i % ceil(theoretical_stint_time_mins) == 0:
            time = timedelta(minutes=i)
            tracker.iloc[index, 0] = format_timedelta(time)
            index += 1

    for i, t in enumerate(tracker['Overall Time Slots'][2:]):
        print(i, t)
        if t == '':
            break
        if get_delta(t) > total_time:
            break

        current_time = get_delta(t)
        current_time_mins = ceil(current_time.total_seconds() / 60)

        for j in range(stints):
            if j + theoretical_stint_time_mins <= current_time_mins <= (j + 1) * theoretical_stint_time_mins:
                tracker.at[i + 2, "Theoretical Stint #"] = j + 1

                for driver in variables['drivers_raw']:
                    if int(variables['drivers_time_slots'][driver][j]) == 1:
                        tracker.at[i + 2, "Driver"] = driver
                        break
                break

        
    print(tracker)

def dark_mode():
    global root, settings, variables, elements, \
            DARK_MODE, STATUS_BG, CONTENT_BG, ENTRY_BG, BUTTON_BG, \
            STATUS_BG_DARK, CONTENT_BG_DARK, ENTRY_BG_DARK, \
            BUTTON_BG_DARK, LABEL_FG, LABEL_FG_DARK
    
    settings['dark_mode'].set('True')
    elements['status'].configure(bg=STATUS_BG_DARK)
    elements['main_content'].configure(bg=CONTENT_BG_DARK)

    elements['plan_content'].widgets['label_hour'].configure(fg=LABEL_FG_DARK, bg=CONTENT_BG_DARK)
    elements['plan_content'].widgets['label_stints'].configure(fg=LABEL_FG_DARK, bg=CONTENT_BG_DARK)
    elements['actual_content'].widgets['label_hour'].configure(fg=LABEL_FG_DARK, bg=CONTENT_BG_DARK)
    elements['actual_content'].widgets['label_stints'].configure(fg=LABEL_FG_DARK, bg=CONTENT_BG_DARK)
    
    for i in ['date_picker_event_time_est', 'date_picker_event_time_cst', 'date_picker_event_time_mst']:
        elements[i].master.configure(bg=CONTENT_BG_DARK)
        elements[i].widgets['main_frame'].configure(bg=ENTRY_BG_DARK)
        elements[i].entry.configure(bg=ENTRY_BG_DARK, fg=ENTRY_FG_DARK)
        try:
            elements[i].entry.configure(insertbackground='white')
        except TclError:
            pass
        elements[i].date_picker_icon.configure(bg=ENTRY_BG_DARK, fg=BUTTON_FG_DARK)
            
    for i in elements:
        element = elements[i]
        if isinstance(element, Label):
            element.configure(bg=CONTENT_BG_DARK, fg='white')
        elif isinstance(element, ttk.Separator):
            element.configure(bg=CONTENT_BG_DARK)
        elif isinstance(element, CTkOptionMenu):
            element.configure(fg_color=ENTRY_BG_DARK, dropdown_fg_color=ENTRY_BG_DARK, 
                              button_color=BUTTON_BG_DARK, dropdown_text_color=ENTRY_FG_DARK,
                              text_color=ENTRY_FG_DARK)
        elif isinstance(element, Entry):
            element.configure(background=ENTRY_BG_DARK, foreground=ENTRY_FG_DARK)
            try:
                element.configure(insertbackground='white')
            except TclError:
                pass
        elif isinstance(element, Text):
            element.configure(bg=ENTRY_BG_DARK, fg=ENTRY_FG_DARK)
        elif isinstance(element, Button):
            element.configure(bg=BUTTON_BG_DARK, fg=BUTTON_FG_DARK)
        elif isinstance(element, Listbox):
            element.configure(bg=ENTRY_BG_DARK, fg=ENTRY_FG_DARK)
        elif isinstance(element, Scrollbar):
            pass
        elif isinstance(element, LabelFrame):
            element.configure(bg=CONTENT_BG_DARK)
        elif isinstance(element, Frame):
            element.configure(bg=CONTENT_BG_DARK)
            
    elements['status'].configure(bg=STATUS_BG_DARK)
    
    for i in elements['status'].winfo_children():
        # element = elements[i]
        if isinstance(i, Label):
            i.configure(bg=STATUS_BG_DARK, fg='white')
        # elif isinstance(i, ttk.Separator):
        #     i.configure(bg=STATUS_BG)

    for i in elements['main_notebook'].winfo_children():
        i.configure(bg=CONTENT_BG_DARK)

    plan = elements['plan_content']
    actual = elements['actual_content']
    if isinstance(plan, TimeScheduler):
        for widget in plan.widgets:
            if isinstance(plan.widgets[widget], Label):
                plan.widgets[widget].configure(bg=CONTENT_BG_DARK, fg=ENTRY_FG_DARK)
            elif isinstance(plan.widgets[widget], Frame):
                if len(widget.split('_')) == 4:
                    plan.widgets[widget].configure(bg=ENTRY_FG_DARK)

    if isinstance(actual, TimeScheduler):
        for widget in actual.widgets:
            if isinstance(actual.widgets[widget], Label):
                actual.widgets[widget].configure(bg=CONTENT_BG_DARK, fg=ENTRY_FG_DARK)
            elif isinstance(actual.widgets[widget], Frame):
                if len(widget.split('_')) == 4:
                    actual.widgets[widget].configure(bg=ENTRY_FG_DARK)

    s = ttk.Style()
    s.theme_use("dark")

def light_mode():
    global root, settings, variables, elements, \
            DARK_MODE, STATUS_BG, CONTENT_BG, ENTRY_BG, BUTTON_BG, \
            STATUS_BG_DARK, CONTENT_BG_DARK, ENTRY_BG_DARK, \
            BUTTON_BG_DARK, LABEL_FG, LABEL_FG_DARK

    settings['dark_mode'].set('False')
    elements['status'].configure(bg=STATUS_BG)
    elements['main_content'].configure(bg=CONTENT_BG)

    elements['plan_content'].widgets['label_hour'].configure(fg=LABEL_FG, bg=CONTENT_BG)
    elements['plan_content'].widgets['label_stints'].configure(fg=LABEL_FG, bg=CONTENT_BG)
    elements['actual_content'].widgets['label_hour'].configure(fg=LABEL_FG, bg=CONTENT_BG)
    elements['actual_content'].widgets['label_stints'].configure(fg=LABEL_FG, bg=CONTENT_BG)
    
    for i in ['date_picker_event_time_est', 'date_picker_event_time_cst', 'date_picker_event_time_mst']:
        elements[i].master.configure(bg=CONTENT_BG)
        elements[i].widgets['main_frame'].configure(bg=ENTRY_BG)
        elements[i].entry.configure(bg=ENTRY_BG, fg=ENTRY_FG)
        try:
            elements[i].entry.configure(insertbackground='black')
        except TclError:
            pass
        elements[i].date_picker_icon.configure(bg=ENTRY_BG, fg=BUTTON_FG)
            
    for i in elements:
        element = elements[i]
        if isinstance(element, Label):
            element.configure(bg=CONTENT_BG, fg='black')
        elif isinstance(element, ttk.Separator):
            element.configure(bg=CONTENT_BG)
        elif isinstance(element, CTkOptionMenu):
            element.configure(fg_color=ENTRY_BG, dropdown_fg_color=ENTRY_BG, 
                              button_color=BUTTON_BG, dropdown_text_color=ENTRY_FG,
                              text_color=ENTRY_FG)
        elif isinstance(element, Entry):
            try:
                element.configure(insertbackground='black')
            except TclError:
                pass
            element.configure(background=ENTRY_BG, foreground=ENTRY_FG)
        elif isinstance(element, Text):
            element.configure(bg=ENTRY_BG, fg=ENTRY_FG)
        elif isinstance(element, Button):
            element.configure(bg=BUTTON_BG, fg=BUTTON_FG)
        elif isinstance(element, Listbox):
            element.configure(bg=ENTRY_BG, fg=ENTRY_FG)
        elif isinstance(element, Scrollbar):
            pass
        elif isinstance(element, LabelFrame):
            element.configure(bg=CONTENT_BG)
        elif isinstance(element, Frame):
            element.configure(bg=CONTENT_BG)

    elements['status'].configure(bg=STATUS_BG)
            
    for i in elements['status'].winfo_children():
        # element = elements[i]
        if isinstance(i, Label):
            i.configure(bg=STATUS_BG, fg='black')
        # elif isinstance(i, ttk.Separator):
        #     i.configure(bg=STATUS_BG)

    for i in elements['main_notebook'].winfo_children():
        i.configure(bg=CONTENT_BG)

    plan = elements['plan_content']
    actual = elements['actual_content']
    if isinstance(plan, TimeScheduler):
        for widget in plan.widgets:
            if isinstance(plan.widgets[widget], Label):
                plan.widgets[widget].configure(bg=CONTENT_BG, fg=ENTRY_FG)
            elif isinstance(plan.widgets[widget], Frame):
                if len(widget.split('_')) == 4:
                    plan.widgets[widget].configure(bg=ENTRY_FG)

    if isinstance(actual, TimeScheduler):
        for widget in actual.widgets:
            if isinstance(actual.widgets[widget], Label):
                actual.widgets[widget].configure(bg=CONTENT_BG, fg=ENTRY_FG)
            elif isinstance(plan.widgets[widget], Frame):
                if len(widget.split('_')) == 4:
                    actual.widgets[widget].configure(bg=ENTRY_FG)

    s = ttk.Style()
    s.theme_use("light")

def init_dark_mode():
    global root, settings, variables, elements, DARK_MODE

    if settings['dark_mode'].get():
        dark_mode()

    else:
        light_mode()
        
    root.update()

def toggle_dark_mode(event=None):
    global root, settings, variables, elements, DARK_MODE

    if DARK_MODE:
        DARK_MODE = False
        settings['dark_mode'].set(False)
        light_mode()

        
    else:
        DARK_MODE = True
        settings['dark_mode'].set(True)
        dark_mode()
        
    root.update()

def toggle_server(event=None):
    global variables, server, client

    if variables['is_server'].get(): 

        variables['is_server'].set(True)
        client.disconnect()

    else:

        variables['is_server'].set(False)
        server.stop()

def update_value(item='', index='', value=None):
    global server, client

    if variables['is_server'].get():
        server.update_value(item, index, value)
    else:
        client.update_value(item, index, value)

def send_message():
    global variables, server, client

    if variables['is_server'].get():
        server.send(variables['send'].get())
    else:
        client.send(variables['send'].get())

def handshake():
    global variables, server, client

    pass

if __name__ == "__main__":
    main()