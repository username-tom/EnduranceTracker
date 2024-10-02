import sys
import os
OWD = os.getcwd()
# print(OWD)
sys.path.append(OWD)
os.chdir(OWD)

from docs.conf import *

from tkinter import *
from tkinter import ttk, simpledialog, messagebox
from threading import Thread
from datetime import datetime, timedelta
from time import sleep
import pytz


root = Tk()
settings = {}
variables = {}
elements = {}

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
    global root, settings, variables, elements

    s = ttk.Style()
    s.configure("TNotebook", 
                tabposition="sw", 
                background=CONTENT_BG)
    s.configure("TNotebook.Tab",
                padding=[10, 0])
    
    main_background = Frame(root, bg="white")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    main_background.grid(row=0, column=0, sticky="nsew")
    elements['main_background'] = main_background
    main_background.grid_columnconfigure(0, weight=1)
    main_background.grid_columnconfigure(1, weight=4)
    main_background.grid_rowconfigure(0, weight=1)

    main_menu = Menu(root)
    # root.config(menu=main_menu)
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

    root.update()

    login()
    update_sheets_list()
    start_status()


def load_menu():
    global root, settings, variables, elements

    root['menu'] = elements['main_menu']
    
    menu_app = Menu(elements['main_menu'])
    elements['main_menu'].add_cascade(label="App", menu=menu_app)
    elements['menu_app'] = menu_app
    elements['menu_app'].add_command(label="Change Spreadsheet", command=change_spreadsheet)
    elements['menu_app'].add_command(label="Upload", command=lambda: update_values(
        elements['listbox_events'].curselection()[0], data_frame))
    elements['menu_app'].add_command(label="Exit", command=on_closing)

def load_status():
    global root, settings, variables, elements
    
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
    main_notebook.add(tab_race, text="Race")
    elements['tab_race'] = tab_race
    load_tab_race()

def load_tab_home():
    global root, settings, variables, elements

    tab_home = elements['tab_home']
    tab_home.grid_columnconfigure(0, weight=3)
    tab_home.grid_columnconfigure(1, weight=1)

    temp_label = Label(tab_home, text='Events', bg=CONTENT_BG, font=("Helvetica", 16, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew", pady='30 5')
    elements['label_home_events'] = temp_label

    variables['all_events_raw'] = []
    variables['all_events'] = StringVar(value=variables['all_events_raw'])
    temp_listbox = Listbox(tab_home, 
                           height=12, 
                           listvariable=variables['all_events'],
                           selectmode=SINGLE)
    temp_listbox.grid(row=1, column=0, sticky="nsew", padx=10, rowspan=12)
    elements['listbox_events'] = temp_listbox
    temp_listbox.bind('<<ListboxSelect>>', change_sheet)

    temp_button = Button(tab_home, text="Add Event", command=add_event_popup)
    temp_button.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
    elements['add_event_button'] = temp_button




def load_tab_general():
    global root, settings, variables, elements

    tab_general = elements['tab_general']
    tab_general.grid_columnconfigure((0, 1), weight=1)
    tab_general.grid_columnconfigure((2), weight=2)
    for i in range(16):
        tab_general.grid_rowconfigure(i, weight=1)

    temp_label = Label(tab_general, text='Event', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=0, column=0, sticky="nsew")
    elements['label_event_name'] = temp_label

    variables['event'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event'])
    temp_entry.grid(row=0, column=1, sticky="nsew", pady=2)
    elements['entry_event_name'] = temp_entry

    temp_label = Label(tab_general, text='Event Time (EST)', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=1, column=0, sticky="nsew")
    elements['label_event_time_est'] = temp_label

    variables['event_time_est'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event_time_est'])
    temp_entry.grid(row=1, column=1, sticky="nsew", pady=2)
    elements['entry_event_time_est'] = temp_entry

    temp_label = Label(tab_general, text='Event Time (CST)', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=2, column=0, sticky="nsew")
    elements['label_event_time_cst'] = temp_label

    variables['event_time_cst'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event_time_cst'])
    temp_entry.grid(row=2, column=1, sticky="nsew", pady=2)
    elements['entry_event_time_cst'] = temp_entry

    temp_label = Label(tab_general, text='Event Time (MST)', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=3, column=0, sticky="nsew")
    elements['label_event_time_mst'] = temp_label

    variables['event_time_mst'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event_time_mst'])
    temp_entry.grid(row=3, column=1, sticky="nsew", pady=2)
    elements['entry_event_time_mst'] = temp_entry

    temp_label = Label(tab_general, text='Car', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=4, column=0, sticky="nsew")
    elements['label_car'] = temp_label

    variables['car'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['car'])
    temp_entry.grid(row=4, column=1, sticky="nsew", pady=2)
    elements['entry_car'] = temp_entry

    temp_label = Label(tab_general, text='Total Time', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=5, column=0, sticky="nsew")
    elements['label_total_time'] = temp_label

    variables['total_time'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['total_time'])
    temp_entry.grid(row=5, column=1, sticky="nsew", pady=2)
    elements['entry_total_time'] = temp_entry

    temp_label = Label(tab_general, text='Current Position', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=6, column=0, sticky="nsew")
    elements['label_current_position'] = temp_label

    variables['current_position'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['current_position'])
    temp_entry.grid(row=6, column=1, sticky="nsew", pady=2)
    elements['entry_current_position'] = temp_entry

    temp_label = Label(tab_general, text='Total Drivers', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=7, column=0, sticky="nsew")
    elements['label_total_drivers'] = temp_label

    variables['total_drivers'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['total_drivers'])
    temp_entry.grid(row=7, column=1, sticky="nsew", pady=2)
    elements['entry_total_drivers'] = temp_entry

    temp_label = Label(tab_general, text='Gap to Race Start', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=8, column=0, sticky="nsew")
    elements['label_gap_2_start'] = temp_label

    variables['gap_2_start'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['gap_2_start'])
    temp_entry.grid(row=8, column=1, sticky="nsew", pady=2)
    elements['entry_gap_2_start'] = temp_entry

    temp_label = Label(tab_general, text='Practice Duration', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=9, column=0, sticky="nsew")
    elements['label_practice_duration'] = temp_label

    variables['practice_duration'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['practice_duration'])
    temp_entry.grid(row=9, column=1, sticky="nsew", pady=2)
    elements['entry_practice_duration'] = temp_entry

    temp_label = Label(tab_general, text='Qualify Duration', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=10, column=0, sticky="nsew")
    elements['label_qualify_duration'] = temp_label

    variables['qualify_duration'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['qualify_duration'])
    temp_entry.grid(row=10, column=1, sticky="nsew", pady=2)
    elements['entry_qualify_duration'] = temp_entry

    temp_label = Label(tab_general, text='Time to Green', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=11, column=0, sticky="nsew")
    elements['label_time_to_green'] = temp_label
    
    variables['time_to_green'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['time_to_green'])
    temp_entry.grid(row=11, column=1, sticky="nsew", pady=2)
    elements['entry_time_to_green'] = temp_entry

    temp_label = Label(tab_general, text='Time to Start', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=12, column=0, sticky="nsew")
    elements['label_time_to_start'] = temp_label
    
    variables['time_to_start'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['time_to_start'])
    temp_entry.grid(row=12, column=1, sticky="nsew", pady=2)
    elements['entry_time_to_start'] = temp_entry

    temp_label = Label(tab_general, text='Sim. Time Start', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=13, column=0, sticky="nsew")
    elements['label_sim_time_start'] = temp_label

    variables['sim_time_start'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['sim_time_start'])
    temp_entry.grid(row=13, column=1, sticky="nsew", pady=2)
    elements['entry_sim_time_start'] = temp_entry

    temp_label = Label(tab_general, text='Theoretical Stint Time', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=14, column=0, sticky="nsew")
    elements['label_theoretical_stint_time'] = temp_label

    variables['theoretical_stint_time'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['theoretical_stint_time'])
    temp_entry.grid(row=14, column=1, sticky="nsew", pady=2)
    elements['entry_theoretical_stint_time'] = temp_entry

    temp_label = Label(tab_general, text='Average Stint Time', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(row=15, column=0, sticky="nsew")
    elements['label_average_stint_time'] = temp_label

    variables['average_stint_time'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['average_stint_time'])
    temp_entry.grid(row=15, column=1, sticky="nsew", pady=2)
    elements['entry_average_stint_time'] = temp_entry

    temp_label = Label(tab_general, text='Drivers', bg=CONTENT_BG, font=("Helvetica", 10, 'bold'))
    temp_label.grid(column=2, row=0, sticky="nsew", padx=10)
    elements['label_drivers'] = temp_label

    variables['drivers_raw'] = []
    variables['drivers_time_slots'] = {}
    variables['drivers'] = StringVar(value=variables['drivers_raw'])
    temp_listbox = Listbox(tab_general, 
                           height=8, 
                           listvariable=variables['drivers'],
                           selectmode=MULTIPLE)
    temp_listbox.grid(column=2, row=1, rowspan=8, sticky="nsew", padx=10)
    elements['listbox_drivers'] = temp_listbox

    variables['add_driver'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['add_driver'])
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
    plan_frame.grid(row=1, column=0, sticky="nsew")
    elements['plan_frame_plan'] = plan_frame

    actual_frame = Frame(tab_plan, bg=CONTENT_BG)
    actual_frame.grid(row=3, column=0, sticky="nsew")
    elements['plan_frame_actual'] = actual_frame

def init_time_scheduler():
    global root, settings, variables, elements, data_frame

    if 'plan_content' in elements:
        elements['plan_content'].__del__()
    if 'actual_content' in elements:
        elements['actual_content'].__del__()
    root.update()

    plan_content = TimeScheduler(root, settings, variables, elements, target='plan')
    elements['plan_content'] = plan_content

    actual_content = TimeScheduler(root, settings, variables, elements, target='actual')
    elements['actual_content'] = actual_content

def load_tab_race():
    global root, settings, variables, elements

    pass

def start_status():
    global root, settings, variables, elements

    settings['status_thread'] = Thread(target=update_status, daemon=True)
    settings['status_state'] = True
    settings['status_thread'].start()

def update_status():
    global root, settings, variables, elements

    # root.update()
    while settings['status_state']:

        variables['time_gmt'].set(datetime.now(pytz.timezone('GMT')).strftime('%H:%M:%S'))
        for i in STATUS_TIMES.split(","):
            variables['time_' + i.lower()].set(datetime.now().astimezone(pytz.timezone(i)).strftime('%H:%M:%S'))
        sleep(1)


def add_driver():
    global settings, variables, elements

    if variables['add_driver'].get() == '':
        return
    
    if variables['add_driver'].get() in variables['drivers_raw']:
        return
    
    if len(variables['drivers_raw']) == 8:
        messagebox.showerror("Driver not added!", "Maximum number of drivers reached")
        return
    
    variables['drivers_raw'].append(variables['add_driver'].get())
    variables['drivers'].set(variables['drivers_raw'])
    variables['add_driver'].set('')

    if variables['add_driver'].get() not in variables['drivers_time_slots']:
        variables['drivers_time_slots'][variables['add_driver'].get()] = []

    #TODO: update data frame

def remove_driver():
    global settings, variables, elements

    listbox_drivers = elements['listbox_drivers']
    if len(listbox_drivers.curselection()) == 0:
        return
    
    to_delete = []
    for i in listbox_drivers.curselection():
        to_delete.append(variables['drivers_raw'][i])
    for i in to_delete:
        variables['drivers_raw'].remove(i)
    variables['drivers'].set(variables['drivers_raw'])

    #TODO: update data frame

def on_closing():
    global root, settings, variables, elements

    settings['status_state'] = False
    
    set_config('general', 'geometry', root.geometry())
    sleep(1)
    root.destroy()

def change_spreadsheet():
    global SAMPLE_SPREADSHEET_ID, root, settings, variables, elements

    id = simpledialog.askstring("Attention", "Enter new spreadsheet ID")

    SAMPLE_SPREADSHEET_ID = id
    update_sheets_list()

def update_sheets_list(index=0):
    variables['all_events_raw'] = get_sheets()
    variables['all_events'].set(variables['all_events_raw'])
    elements['listbox_events'].update()
    elements['listbox_events'].selection_set(index)
    change_sheet()

def change_sheet(event=None):
    global root, settings, variables, elements, data_frame

    event_list = elements['listbox_events']
    selected = event_list.curselection()
    if len(selected) == 0:
        return
    
    event = event_list.get(selected[0])
    get_values(event)
    update_variables_from_data_frame()
    init_time_scheduler()

def add_event_popup():
    global root, settings, variables, elements

    name = simpledialog.askstring("Attention", "Enter new event name")
    if name is None:
        return
    
    add_event(name)
    original_sheet_len = len(variables['all_events_raw'])
    update_sheets_list(original_sheet_len)

def update_variables_from_data_frame():
    global root, settings, variables, elements, data_frame

    variables['event'].set(get_data_frame_value(index='INDEX_EVENT_NAME'))
    variables['event_time_est'].set(get_data_frame_value(index='INDEX_EVENT_TIME_EST'))
    try:
        est = datetime.strptime(variables['event_time_est'].get(), '%m-%d-%Y %H:%M:%S')
    except ValueError:
        est = datetime.strptime(variables['event_time_est'].get(), '%m-%d-%Y %I:%M:%S %p')
    cst = est - timedelta(hours=1)
    mst = est - timedelta(hours=2)
    variables['event_time_cst'].set(cst.strftime('%m-%d-%Y %H:%M:%S %p'))
    variables['event_time_mst'].set(mst.strftime('%m-%d-%Y %H:%M:%S %p'))
    variables['car'].set(get_data_frame_value(index='INDEX_CAR'))
    variables['total_time'].set(get_data_frame_value(index='INDEX_TOTAL_TIME'))
    variables['current_position'].set(get_data_frame_value(index='INDEX_CURRENT_POSITION'))
    variables['total_drivers'].set(get_data_frame_value(index='INDEX_TOTAL_DRIVER'))
    variables['gap_2_start'].set(get_data_frame_value(index='INDEX_GAP_TO_RACE_START'))
    variables['practice_duration'].set(get_data_frame_value(index='INDEX_PRACTICE_DURATION'))
    variables['qualify_duration'].set(get_data_frame_value(index='INDEX_QUALIFY_DURATION'))
    variables['time_to_green'].set(get_data_frame_value(index='INDEX_TIME_TO_GREEN'))
    variables['time_to_start'].set(get_data_frame_value(index='INDEX_TIME_TO_START'))
    variables['sim_time_start'].set(get_data_frame_value(index='INDEX_SIM_TIME_START'))
    variables['theoretical_stint_time'].set(get_data_frame_value(index='INDEX_THEORETICAL_STINT_TIME'))
    variables['average_stint_time'].set(get_data_frame_value(index='INDEX_AVERAGE_STINT_TIME'))
    variables['weather'] = []
    variables['drivers_time_slots'] = {}
    variables['drivers_raw'] = []
    variables['drivers'].set(variables['drivers_raw'])
    root.update()

    for i in range(1, 9):
        driver = get_data_frame_value(index='INDEX_DRIVER_' + str(i))
        if driver != f'Driver {i}':
            variables['drivers_raw'].append(driver)
            variables['drivers_time_slots'][driver] = []
            for j in range(1, int(variables['total_time'].get()) + 1):
                variables['drivers_time_slots'][driver].append(get_data_frame_value(col=Q + i, row=j))

    variables['drivers'].set(variables['drivers_raw'])
    elements['listbox_drivers'].update()



    for i in range(WEATHER_LENGTH):
        variables['weather'].append(get_data_frame_value(col=Z, row=i + 1))

    #TODO: add race data readers



if __name__ == "__main__":
    main()