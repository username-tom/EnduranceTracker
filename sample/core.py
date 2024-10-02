import helpers
from tkinter import messagebox


settings = {}
variables = {}
elements = {}

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

