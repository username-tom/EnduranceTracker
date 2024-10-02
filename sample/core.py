from helpers import *
from docs.conf import *
from tkinter import *
from tkinter import ttk

class TrackerError(Exception):
    pass


class TimeScheduler:
    def __init__(self, root, settings, variables, elements, target='plan'):
        self.root = root
        self.settings = settings
        self.variables = variables
        self.elements = elements
        self.target = target
        self.widgets = {}

        if target == 'plan' and 'plan_frame_plan' not in self.elements:
            raise TrackerError("Missing plan_frame_plan")

        if target == 'actual' and 'plan_frame_actual' not in self.elements:
            raise TrackerError("Missing plan_frame_actual")
        
        if 'drivers_raw' not in self.variables:
            raise TrackerError("Missing drivers_raw")
        
        self.create_widgets()

    def create_widgets(self):
        frame = self.elements['plan_frame_plan'] if self.target == 'plan' else self.elements['plan_frame_actual']
        for child in frame.winfo_children():
            child.destroy()

        self.root.update()
        temp_label = Label(frame, text='Hour', background=CONTENT_BG)
        temp_label.grid(row=0, column=0, sticky='news')
        self.widgets['label_hour'] = temp_label
        print(self.variables['drivers_time_slots'])

        for i, driver in enumerate(self.variables['drivers_raw']):
            temp_label = Label(frame, text=driver, background=CONTENT_BG)
            temp_label.grid(row=1 + i, column=0, sticky='news')
            self.widgets[f'label_{driver}'] = temp_label
            frame.grid_rowconfigure(1 + i, weight=1)

            for j in range(1, int(self.variables['total_time'].get()) + 1):
                temp_label = Label(frame, text=j, background=CONTENT_BG)
                temp_label.grid(row=0, column=j, sticky='news')

            for j in range(1, int(self.variables['total_time'].get()) + 1):
                temp_frame = Frame(frame, background='red')
                if self.variables['drivers_time_slots'][driver][j - 1] == '1':
                    temp_frame['background'] = 'green'
                elif self.variables['drivers_time_slots'][driver][j - 1] == '2':
                    temp_frame['background'] = 'yellow'
                temp_frame.grid(row=1 + i, column=j, sticky='news', padx=1, pady=1)
                self.widgets[f'frame_{driver}_{j}'] = temp_frame
                temp_frame.bind('<Button-1>', self.toggle_frame)
                frame.grid_columnconfigure(j, weight=1)

    def toggle_frame(self, event=None):
        global data_frame

        widget = event.widget
        if widget['background'] == 'green':
            widget['background'] = 'yellow'
            driver, hour = self.get_widget_name(widget)
            self.variables['drivers_time_slots'][driver][int(hour) - 1] = '2'
            update_data_frame_value(int(hour), self.variables['drivers_raw'].index(driver), value='2')
        elif widget['background'] == 'yellow':
            widget['background'] = 'red'
            driver, hour = self.get_widget_name(widget)
            self.variables['drivers_time_slots'][driver][int(hour) - 1] = '0'
            update_data_frame_value(int(hour), self.variables['drivers_raw'].index(driver), value='0')
        else:
            widget['background'] = 'green'
            driver, hour = self.get_widget_name(widget)
            self.variables['drivers_time_slots'][driver][int(hour) - 1] = '1'
            update_data_frame_value(int(hour), self.variables['drivers_raw'].index(driver), value='1')
            
    def get_widget_name(self, widget):
        for key, value in self.widgets.items():
            if value == widget:
                driver = key.split('_')[1]
                hour = key.split('_')[2]
                return driver, hour
        return False

    def __del__(self):
        for key, value in self.widgets.items():
            value.destroy()
        self.root.update()