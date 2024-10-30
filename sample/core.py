from docs.conf import *
from tkinter import *
from tkinter import ttk
from helpers import *
from math import ceil
from datetime import timedelta
from tkcalendar import Calendar, DateEntry


class TrackerError(Exception):
    pass


class TimeScheduler:
    def __init__(self, root, settings, variables, elements, data, target='plan', current_event=''):
        
        self.root = root
        self.settings = settings
        self.variables = variables
        self.elements = elements
        self.target = target
        self.widgets = {}
        self.data = data
        self.current_event = current_event

        if target == 'plan' and 'plan_frame_plan' not in self.elements:
            raise TrackerError("Missing plan_frame_plan")

        if target == 'actual' and 'plan_frame_actual' not in self.elements:
            raise TrackerError("Missing plan_frame_actual")
        
        self.target = target
        
        if 'drivers_raw' not in self.variables:
            raise TrackerError("Missing drivers_raw")
        
        self.create_widgets()

    def create_widgets(self):
        frame = self.elements['plan_frame_plan'] if self.target == 'plan' else self.elements['plan_frame_actual']
        for i in range(25):
            frame.grid_columnconfigure(i, weight=0)
        for child in frame.winfo_children():
            child.destroy()

        self.root.update()
        temp_label = Label(frame, text='Hour', background=CONTENT_BG_DARK if self.settings['dark_mode'] else CONTENT_BG)
        temp_label.grid(row=0, column=0, sticky='news', padx='0 5')
        self.widgets['label_hour'] = temp_label
        # print(self.variables['drivers_time_slots'])

        temp_label = Label(frame, text='Stints', background=CONTENT_BG_DARK if self.settings['dark_mode'] else CONTENT_BG)
        temp_label.grid(row=1, column=0, sticky='news', padx='0 5')
        self.widgets['label_stints'] = temp_label

        for i, driver in enumerate(self.variables['drivers_raw']):
            temp_label = Label(frame, text=driver, background=CONTENT_BG_DARK if self.settings['dark_mode'] else CONTENT_BG)
            temp_label.grid(row=2 + i, column=0, sticky='news', padx='0 5')
            self.widgets[f'label_{driver}'] = temp_label
            frame.grid_rowconfigure(2 + i, weight=1)

            total_time = self.get_delta('total_time').total_seconds()
            total_time_in_h = ceil(total_time / 3600)
            stint_time = self.get_delta('theoretical_stint_time').total_seconds()
            stints = ceil(total_time / stint_time)
            remains = int(total_time % stint_time) / stint_time
            
            # print(total_time, stint_time, stints, remains)
            if remains == 0:
                weight = 1
            else:
                weight = ceil(1 / remains)
            # print(weight)

            time_frame = Frame(frame, background=CONTENT_BG_DARK if self.settings['dark_mode'] else CONTENT_BG)
            time_frame.grid(row=0, column=1, sticky='news', padx=0, pady=0, 
                            columnspan=stints)
            time_frame.grid_columnconfigure(0, weight=1)
            
            # hour_frame = Frame(time_frame, background=CONTENT_BG_DARK if self.settings['dark_mode'] else CONTENT_BG)
            # hour_frame.grid(row=0, column=0, sticky='news')

            for j in range(total_time_in_h):
                temp_frame = Frame(time_frame, background=ENTRY_BG if self.settings['dark_mode'] else ENTRY_FG)
                temp_frame.grid(row=0, column=j, sticky='news', padx=0, pady=0)
                temp_frame.grid_columnconfigure(0, weight=1)
                temp_frame.grid_rowconfigure(0, weight=1)
                self.widgets[f'frame_{driver}_h_{j + 1}'] = temp_frame

                temp_label = Label(temp_frame, text=f"{j + 1:02d}", 
                                   background=CONTENT_BG_DARK if self.settings['dark_mode'] else CONTENT_BG, 
                                   font=HOUR_STINT_FONT)
                temp_label.grid(row=0, column=0, sticky='news', padx=2, pady='0 1') 
                self.widgets[f'label_{driver}_h_{j + 1}'] = temp_label
                time_frame.grid_columnconfigure(j, weight=1)

            for j in range(stints):
                temp_frame = Frame(frame, background=ENTRY_BG if self.settings['dark_mode'] else ENTRY_FG)
                temp_frame.grid(row=1, column=j + 1, sticky='news', padx=0, pady=0)
                temp_frame.grid_columnconfigure(0, weight=1)
                temp_frame.grid_rowconfigure(0, weight=1)
                self.widgets[f'frame_{driver}_s_{j + 1}'] = temp_frame

                temp_label = Label(temp_frame, text=f"{j + 1:02d}", 
                                   background=CONTENT_BG_DARK if self.settings['dark_mode'] else CONTENT_BG, 
                                   font=HOUR_STINT_FONT)
                temp_label.grid(row=0, column=0, sticky='news', padx=2, pady='1 0')
                self.widgets[f'label_{driver}_s_{j + 1}'] = temp_label

                temp_frame = Frame(frame, background='red')
                if self.variables['drivers_time_slots'][driver][j] == '1':
                    temp_frame['background'] = 'green'
                elif self.variables['drivers_time_slots'][driver][j] == '2':
                    temp_frame['background'] = 'yellow'
                temp_frame.grid(row=2 + i, column=j + 1, sticky='news', padx=1, pady=1)
                self.widgets[f'frame_{driver}_{j + 1}'] = temp_frame
                temp_frame.bind('<Button-1>', self.toggle_frame)
                # frame.grid_columnconfigure(j + 1, weight=1)
                frame.grid_columnconfigure(j + 1, weight=weight)
                if j == stints - 1:
                    frame.grid_columnconfigure(j + 1, weight=1)

    def toggle_frame(self, event=None):
        widget = event.widget

        if self.target == 'plan':
            if widget['background'] == 'green':
                widget['background'] = 'yellow'
                driver, hour = self.get_widget_name(widget)
                self.variables['drivers_time_slots'][driver][int(hour) - 1] = '2'
                self.update_data_frame_value(int(hour), self.variables['drivers_raw'].index(driver) + R, value='2')
            elif widget['background'] == 'yellow':
                widget['background'] = 'red'
                driver, hour = self.get_widget_name(widget)
                self.variables['drivers_time_slots'][driver][int(hour) - 1] = '0'
                self.update_data_frame_value(int(hour), self.variables['drivers_raw'].index(driver) + R, value='0')
            else:
                widget['background'] = 'green'
                driver, hour = self.get_widget_name(widget)
                self.variables['drivers_time_slots'][driver][int(hour) - 1] = '1'
                self.update_data_frame_value(int(hour), self.variables['drivers_raw'].index(driver) + R, value='1')
            
            range = self.get_range(int(hour), self.variables['drivers_raw'].index(driver) + R)
            update_values(self.current_event, [self.variables['drivers_time_slots'][driver][int(hour) - 1]], range)
            get_values(self.current_event, range)

    def get_range(self, row=0, col=0):
        return f"{chr(65 + col)}{row + 1}"

    def update_data_frame_value(self, row=0, col=0, index='', value=None):
        if index not in INDEX:
            self.data.at[row, col] = value
        else:
            self.data.at[INDEX[index][0], INDEX[index][1]] = value
            print(self.data.at[INDEX[index][0], INDEX[index][1]])
    
    def get_widget_name(self, widget):
        for key, value in self.widgets.items():
            if value == widget:
                driver = key.split('_')[1]
                hour = key.split('_')[2]
                return driver, hour
        return False

    def __del__(self):
        for key, value in self.widgets.items():
            try:
                value.destroy()
            except TclError:
                pass
        self.root.update()

    def get_delta(self, variable=''):

        if f'{variable}_h' not in self.variables:
            return

        return timedelta(hours=float(self.variables[f'{variable}_h'].get()), 
                         minutes=float(self.variables[f'{variable}_m'].get()), 
                         seconds=float(self.variables[f'{variable}_s'].get()))
    

class DatePicker:
    def __init__(self, master, root, settings, variables, elements):
        self.root = root
        self.settings = settings
        self.variables = variables
        self.elements = elements
        self.master = master
        self.widgets = {}
        self.create_widgets()

    def create_widgets(self):
        frame = Frame(self.master, background=CONTENT_BG, relief='sunken', borderwidth=1)
        frame.grid(row=0, column=0, sticky='news')
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.widgets['main_frame'] = frame
        
        self.entry = Entry(frame, width=20, border=0, borderwidth=0, relief='flat', justify='center')
        if self.master == self.elements['entry_event_time_est']:
            self.entry.config(textvariable=self.variables['event_time_est'])
            self.widgets['entry_var'] = self.variables['event_time_est']
        elif self.master == self.elements['entry_event_time_cst']:
            self.entry.config(textvariable=self.variables['event_time_cst'])
            self.widgets['entry_var'] = self.variables['event_time_cst']
        elif self.master == self.elements['entry_event_time_mst']:
            self.entry.config(textvariable=self.variables['event_time_mst'])
            self.widgets['entry_var'] = self.variables['event_time_mst']
        else: 
            raise TrackerError("Invalid master")
        
        self.entry.grid(row=0, column=0, sticky='news', padx=(0, 5))
        self.widgets['entry'] = self.entry

        self.date_picker_icon = Button(frame, text='📅', command=self.open_date_picker,
                                        border=0, borderwidth=0, relief='flat')
        self.date_picker_icon.grid(row=0, column=1, sticky='news')
        self.widgets['date_picker_icon'] = self.date_picker_icon

    def open_date_picker(self):
        top = Toplevel(self.root)
        top.resizable(False, False)
        top.title("Select Date and Time")
        
        cal = Calendar(top, selectmode='day')
        cal.grid(column=0, row=0, padx=0, pady=0)
        self.widgets['calendar'] = cal
        cal.see(to_datetime(self.variables['event_time_est'].get()))

        time_frame = Frame(top)
        time_frame.grid(column=0, row=1, padx=0, pady=0)
        self.widgets['time_frame'] = time_frame

        if self.master == self.elements['entry_event_time_est']:
            hour = StringVar(value=self.variables['event_time_est'].get().split(' ')[1].split(':')[0])
            minute = StringVar(value=self.variables['event_time_est'].get().split(' ')[1].split(':')[1])
            second = StringVar(value=self.variables['event_time_est'].get().split(' ')[1].split(':')[2])
        elif self.master == self.elements['entry_event_time_cst']:
            hour = StringVar(value=self.variables['event_time_cst'].get().split(' ')[1].split(':')[0])
            minute = StringVar(value=self.variables['event_time_cst'].get().split(' ')[1].split(':')[1])
            second = StringVar(value=self.variables['event_time_cst'].get().split(' ')[1].split(':')[2])
        elif self.master == self.elements['entry_event_time_mst']:
            hour = StringVar(value=self.variables['event_time_mst'].get().split(' ')[1].split(':')[0])
            minute = StringVar(value=self.variables['event_time_mst'].get().split(' ')[1].split(':')[1])
            second = StringVar(value=self.variables['event_time_mst'].get().split(' ')[1].split(':')[2])
        else: 
            raise TrackerError("Invalid master")
        self.widgets['hour'] = hour
        self.widgets['minute'] = minute
        self.widgets['second'] = second

        hour_entry = Entry(time_frame, textvariable=hour)
        hour_entry.grid(row=0, column=0, padx=0, pady=0)
        self.widgets['hour_entry'] = hour_entry
        temp_label = Label(time_frame, text=':')
        temp_label.grid(row=0, column=1, padx=0, pady=0)

        minute_entry = Entry(time_frame, textvariable=minute)
        minute_entry.grid(row=0, column=2, padx=0, pady=0)
        self.widgets['minute_entry'] = minute_entry
        temp_label = Label(time_frame, text=':')
        temp_label.grid(row=0, column=3, padx=0, pady=0)

        second_entry = Entry(time_frame, textvariable=second)
        second_entry.grid(row=0, column=4, padx=0, pady=0)
        self.widgets['second_entry'] = second_entry

        def on_date_select():
            selected_date = cal.selection_get()
            hour_int = int(hour.get())
            period = "AM" if hour_int < 12 else "PM"
            self.widgets['entry_var'].set(f"{selected_date.strftime('%m-%d-%Y')} "
                                          f"{hour_int:02d}:{int(minute.get()):02d}:{int(second.get()):02d} "
                                          f"{period}")
            top.destroy()

        select_button = Button(top, text="Select", command=on_date_select)
        select_button.grid(column=0, row=2, pady=5)


class Dropdown:
    def __init__(self, master, root, settings, variables, elements, options=[], target='edit'):
        self.root = root
        self.settings = settings
        self.variables = variables
        self.elements = elements
        self.master = master
        self.options = options
        self.widgets = {}
        self.create_widgets()
        self.target = target

    def create_widgets(self):
        frame = Frame(self.master, background=CONTENT_BG)
        frame.grid(row=0, column=0, sticky='news')
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self.widgets['main_frame'] = frame

        if self.target == 'edit' and self.variables['race_tracker_edit_actual_weather']:
            temp_entry = Entry(frame, textvariable=self.variables['race_tracker_edit_actual_weather'])
            self.widgets['entry'] = temp_entry
            temp_entry.grid(row=0, column=0, sticky='news', padx=(0, 0))
            self.elements['race_tracker_edit_actual_weather_textbox'] = temp_entry
            
            temp_button = Button(frame, text='▼', command=self.open_dropdown, 
                                 border=0, borderwidth=0, relief='flat', 
                                 justify='center', anchor='center')
            self.widgets['button'] = temp_button
            temp_button.grid(row=0, column=1, sticky='news', padx=(0, 0))
            self.elements['race_tracker_edit_actual_weather_button'] = temp_button

        elif self.target == 'current' and self.variables['race_tracker_current_actual_weather']:
            temp_entry = Entry(frame, textvariable=self.variables['race_tracker_current_actual_weather'])
            self.widgets['entry'] = temp_entry
            temp_entry.grid(row=0, column=0, sticky='news', padx=(0, 0))
            self.elements['race_tracker_current_actual_weather_textbox'] = temp_entry

            temp_button = Button(frame, text='▼', command=self.open_dropdown,
                                    border=0, borderwidth=0, relief='flat',
                                    justify='center', anchor='center')
            self.widgets['button'] = temp_button
            temp_button.grid(row=0, column=1, sticky='news', padx=(0, 0))

            
        else:
            raise TrackerError("Missing variable [race_tracker_edit_actual_weather]")
        
    def open_dropdown(self):
        top = Toplevel(self.root, background=ENTRY_BG if self.settings['dark_mode'] else ENTRY_BG_DARK)
        top.resizable(False, False)
        top.title("Select Weather Condition")
        
        for option in self.options:
            temp_button = Button(top, text=option, command=lambda option=option: self.select_option(option),
                                 background=ENTRY_BG if self.settings['dark_mode'] else ENTRY_BG_DARK,
                                 foreground=ENTRY_FG if self.settings['dark_mode'] else ENTRY_FG_DARK)
            temp_button.pack(fill='x')

    def select_option(self, option):
        if self.target == 'edit':
            self.variables['race_tracker_edit_actual_weather'].set(option)
        elif self.target == 'plan':
            self.variables['race_tracker_current_actual_weather'].set(option)