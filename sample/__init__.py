import sys
import os
OWD = os.getcwd()
# print(OWD)
sys.path.append(OWD)
os.chdir(OWD)

from docs.conf import *

from tkinter import *
from tkinter import ttk


root = Tk()

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
    main_background.grid_columnconfigure((0, 1), weight=1)

    main_menu = Menu(root)
    # root.config(menu=main_menu)
    elements['main_menu'] = main_menu
    load_menu()

    navigator = Frame(main_background, bg=NAVIGATOR_BG)
    navigator.grid(row=0, column=0, sticky="nsew")
    elements['navigator'] = navigator
    load_navigator()

    main_content = Frame(main_background, bg=CONTENT_BG)
    main_content.grid(row=0, column=1, sticky="nsew")
    elements['main_content'] = main_content
    load_main_content()

    root.update()

    login()


def load_menu():
    global root, settings, variables, elements

    root['menu'] = elements['main_menu']
    
    menu_app = Menu(elements['main_menu'])
    elements['main_menu'].add_cascade(label="App", menu=menu_app)
    elements['menu_app'] = menu_app
    elements['menu_app'].add_command(label="Exit", command=on_closing)

def load_navigator():
    global root, settings, variables, elements
    
    navigator = elements['navigator']
    navigator.grid_rowconfigure(0, weight=1)
    navigator.grid_columnconfigure(0, weight=1)

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

def load_tab_general():
    global root, settings, variables, elements

    tab_general = elements['tab_general']

    temp_label = Label(tab_general, text='Event', bg=CONTENT_BG)
    temp_label.grid(row=0, column=0, sticky="nsew")
    elements['label_event_name'] = temp_label

    variables['event'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event'])
    temp_entry.grid(row=0, column=1, sticky="nsew")
    elements['entry_event_name'] = temp_entry

    temp_label = Label(tab_general, text='Event Time (EST)', bg=CONTENT_BG)
    temp_label.grid(row=1, column=0, sticky="nsew")
    elements['label_event_time_est'] = temp_label

    variables['event_time_est'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event_time_est'])
    temp_entry.grid(row=1, column=1, sticky="nsew")
    elements['entry_event_time_est'] = temp_entry

    temp_label = Label(tab_general, text='Event Time (CST)', bg=CONTENT_BG)
    temp_label.grid(row=2, column=0, sticky="nsew")
    elements['label_event_time_cst'] = temp_label

    variables['event_time_cst'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event_time_cst'])
    temp_entry.grid(row=2, column=1, sticky="nsew")
    elements['entry_event_time_cst'] = temp_entry

    temp_label = Label(tab_general, text='Event Time (MST)', bg=CONTENT_BG)
    temp_label.grid(row=3, column=0, sticky="nsew")
    elements['label_event_time_mst'] = temp_label

    variables['event_time_mst'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['event_time_mst'])
    temp_entry.grid(row=3, column=1, sticky="nsew")
    elements['entry_event_time_mst'] = temp_entry

    temp_label = Label(tab_general, text='Car', bg=CONTENT_BG)
    temp_label.grid(row=4, column=0, sticky="nsew")
    elements['label_car'] = temp_label

    variables['car'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['car'])
    temp_entry.grid(row=4, column=1, sticky="nsew")
    elements['entry_car'] = temp_entry

    temp_label = Label(tab_general, text='Total Time', bg=CONTENT_BG)
    temp_label.grid(row=5, column=0, sticky="nsew")
    elements['label_total_time'] = temp_label

    variables['total_time'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['total_time'])
    temp_entry.grid(row=5, column=1, sticky="nsew")
    elements['entry_total_time'] = temp_entry

    temp_label = Label(tab_general, text='Current Position', bg=CONTENT_BG)
    temp_label.grid(row=6, column=0, sticky="nsew")
    elements['label_current_position'] = temp_label

    variables['current_position'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['current_position'])
    temp_entry.grid(row=6, column=1, sticky="nsew")
    elements['entry_current_position'] = temp_entry

    temp_label = Label(tab_general, text='Total Drivers', bg=CONTENT_BG)
    temp_label.grid(row=7, column=0, sticky="nsew")
    elements['label_total_drivers'] = temp_label

    variables['total_drivers'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['total_drivers'])
    temp_entry.grid(row=7, column=1, sticky="nsew")
    elements['entry_total_drivers'] = temp_entry

    temp_label = Label(tab_general, text='Gap to Race Start', bg=CONTENT_BG)
    temp_label.grid(row=8, column=0, sticky="nsew")
    elements['label_gap_2_start'] = temp_label

    variables['gap_2_start'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['gap_2_start'])
    temp_entry.grid(row=8, column=1, sticky="nsew")
    elements['entry_gap_2_start'] = temp_entry

    temp_label = Label(tab_general, text='Practice Duration', bg=CONTENT_BG)
    temp_label.grid(row=9, column=0, sticky="nsew")
    elements['label_practice_duration'] = temp_label

    variables['practice_duration'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['practice_duration'])
    temp_entry.grid(row=9, column=1, sticky="nsew")
    elements['entry_practice_duration'] = temp_entry

    temp_label = Label(tab_general, text='Qualify Duration', bg=CONTENT_BG)
    temp_label.grid(row=10, column=0, sticky="nsew")
    elements['label_qualify_duration'] = temp_label

    variables['qualify_duration'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['qualify_duration'])
    temp_entry.grid(row=10, column=1, sticky="nsew")
    elements['entry_qualify_duration'] = temp_entry

    temp_label = Label(tab_general, text='Time to Green', bg=CONTENT_BG)
    temp_label.grid(row=11, column=0, sticky="nsew")
    elements['label_time_to_green'] = temp_label
    
    variables['time_to_green'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['time_to_green'])
    temp_entry.grid(row=11, column=1, sticky="nsew")
    elements['entry_time_to_green'] = temp_entry

    temp_label = Label(tab_general, text='Time to Start', bg=CONTENT_BG)
    temp_label.grid(row=12, column=0, sticky="nsew")
    elements['label_time_to_start'] = temp_label
    
    variables['time_to_start'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['time_to_start'])
    temp_entry.grid(row=12, column=1, sticky="nsew")
    elements['entry_time_to_start'] = temp_entry

    temp_label = Label(tab_general, text='Sim. Time Start', bg=CONTENT_BG)
    temp_label.grid(row=13, column=0, sticky="nsew")
    elements['label_sim_time_start'] = temp_label

    variables['sim_time_start'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['sim_time_start'])
    temp_entry.grid(row=13, column=1, sticky="nsew")
    elements['entry_sim_time_start'] = temp_entry

    temp_label = Label(tab_general, text='Theoretical Stint Time', bg=CONTENT_BG)
    temp_label.grid(row=14, column=0, sticky="nsew")
    elements['label_theoretical_stint_time'] = temp_label

    variables['theoretical_stint_time'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['theoretical_stint_time'])
    temp_entry.grid(row=14, column=1, sticky="nsew")
    elements['entry_theoretical_stint_time'] = temp_entry

    temp_label = Label(tab_general, text='Average Stint Time', bg=CONTENT_BG)
    temp_label.grid(row=15, column=0, sticky="nsew")
    elements['label_average_stint_time'] = temp_label

    variables['average_stint_time'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['average_stint_time'])
    temp_entry.grid(row=15, column=1, sticky="nsew")
    elements['entry_average_stint_time'] = temp_entry

    temp_label = Label(tab_general, text='Drivers', bg=CONTENT_BG)
    temp_label.grid(column=2, row=0, sticky="nsew")
    elements['label_drivers'] = temp_label

    variables['drivers_raw'] = []
    variables['drivers'] = StringVar(value=variables['drivers_raw'])
    temp_listbox = Listbox(tab_general, 
                           height=8, 
                           listvariable=variables['drivers'],
                           selectmode=MULTIPLE)
    temp_listbox.grid(column=2, row=1, rowspan=8, sticky="nsew")
    elements['listbox_drivers'] = temp_listbox

    variables['add_driver'] = StringVar(value='')
    temp_entry = Entry(tab_general, textvariable=variables['add_driver'])
    temp_entry.grid(column=2, row=9, sticky="nsew")
    elements['add_driver'] = temp_entry

    
    temp_button = Button(tab_general, text="Add Driver", command=add_driver)
    temp_button.grid(column=2, row=10, sticky="nsew")
    elements['add_driver_button'] = temp_button

    temp_button = Button(tab_general, text="Remove Driver", command=remove_driver)
    temp_button.grid(column=2, row=11, sticky="nsew")
    elements['remove_driver_button'] = temp_button

def load_tab_plan():
    global root, settings, variables, elements

    pass

def load_tab_race():
    global root, settings, variables, elements

    pass



def on_closing():
    global root

    set_config('general', 'geometry', root.geometry())
    sleep(1)
    root.destroy()


if __name__ == "__main__":
    main()