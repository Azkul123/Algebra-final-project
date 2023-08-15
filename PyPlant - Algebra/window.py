'''
This is the main python file which is ran when you wish to start the program. You can resize the window but... some animations struggle with it
You don't need any API keys to run this app :D, but do remember that openmeteo only allows 1000 request
admin: username: admin pass: 12345
'''

import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from database import create_user,edit_user,delete_user,get_data
import re
import json
import requests
import datetime as dt
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as tkagg
import matplotlib.ticker as ticker
import random


class App(ctk.CTk):
    '''
    This class serves as the main window of tkinter
    '''
    def __init__(self, window_width, window_height):

        #basic setup
        super().__init__()
        self.title("PyPlant")
        self.iconbitmap("images_and_data/leaf_icon.ico")  #has to be a .ico file
        self.window_width = window_width
        self.window_height = window_height
        self.screen_width = self.winfo_screenwidth()
        self.screen_heigth = self.winfo_screenheight()
        self.minsize(window_width,window_height)
        self.maxsize(window_width*2,window_height*2)
        #the self.frame is destroyed and recreated every time you open some new window inside of the App
        self.frame = None
        self.current_username = None
        self.current_password = None

        self.pyplant_logo = Image.open("images_and_data/pyplant_logo.png")
        self.pyplant_logo_tk = ImageTk.PhotoImage(self.pyplant_logo)

        #used in the full_image method to store all image ratios
        self.resized_images = {}

        #setting for what place we are getting weather info
        data = self.get_json_data("images_and_data/city_coords.json")
        self.coord_var = data["current_city"]

        #screen setup (makes it so the screen always starts a bit above the middle of the screen)
        self.geometry(f"{window_width}x{window_height}+{int(self.screen_width/2-window_width/2)}+{int(self.screen_heigth/2-window_height/1.5)}")

        self.update_temp()

        self.create_login_window()
        
        #run
        self.mainloop()


    def update_time(self):
        '''
        Gets current time, seperates it into time and date (it doesn't have an after())
        '''
        current_dt = dt.datetime.now()
        current_time = current_dt.time()
        current_date = current_dt.date()
        current_time = current_time.strftime("%H:%M")

        return f"Current date: {current_date}\nCurrent_time: {current_time}"


    def update_temp(self):
        '''
        When the method is run all the planters outside get the temp that is currently outside
        '''
        data = self.get_json_data("images_and_data/plant_info.json")
        weather_data = self.get_weather_info()

        for x in data["planters"]:
            if x["location"] == "outside":
                x["temperature"] = weather_data["current_weather"]["temperature"]

        with open("images_and_data/plant_info.json", "w") as file:
            json.dump(data, file, indent=4)


    def create_login_window(self):
        '''
        This method creates the login frame and all the widgets inside it
        '''

        if self.frame:
            self.frame.destroy()
        self.frame = ctk.CTkFrame(self)
        self.frame.bg = ""
        self.frame.pack(expand=True,fill="both")
        self.frame.rowconfigure((0,1,2),weight=1, uniform="a")
        self.frame.rowconfigure(1,weight=2, uniform="a")
        self.frame.columnconfigure((0,1,2),weight=1, uniform="a")
        self.frame.columnconfigure(1,weight=2, uniform="a")


        frame = ctk.CTkFrame(self.frame)
        frame.grid(column=1,row=1, sticky="nswe")
        frame.rowconfigure((0,1,2,3,4,5,6), weight=1, uniform="a")
        frame.columnconfigure((0,1,2,3,4), weight=1, uniform="a")
        
        logo_canvas = tk.Canvas(frame, background="#31C48D", bd=0, highlightthickness=0, relief="ridge",width=1,height=50)
        logo_canvas.grid(column=0,row=0,rowspan=2,columnspan=5,sticky="nswe",pady=5,padx=2)
        logo_canvas.create_image(0,0,image=self.pyplant_logo_tk)
        logo_canvas.bind("<Configure>", lambda event: self.full_image(event,self.pyplant_logo,logo_canvas))

        #widgets
        name_entry = ctk.CTkEntry(frame, placeholder_text="Enter Username/Email")
        pass_entry = ctk.CTkEntry(frame, placeholder_text="Enter Password", show="*")
        self.login_btn = ctk.CTkButton(frame, text="Login", command=lambda: self.login(name_entry,pass_entry))
        register_btn = ctk.CTkButton(frame, text="Register", command=self.create_register_window)

        #placing widgets (the labels are created without a variable)
        ctk.CTkLabel(frame,text="Username:",font=("Helvetica",13)).grid(row=3,column=1, pady=5)
        ctk.CTkLabel(frame,text="Password:",font=("Helvetica",13)).grid(row=4,column=1, pady=5)
        name_entry.grid(row=3, column=2, columnspan=2, sticky="we", pady=5)
        pass_entry.grid(row=4, column=2, columnspan=2, sticky="we", pady=5)
        self.login_btn.grid(row=5, column=2, sticky="we", padx=5, pady=5)
        register_btn.grid(row=5, column=3, sticky="we",padx=5, pady=5)


    def login(self, username, password):
        '''
        Logs you in
        '''
        email_l, name_l, pass_l = get_data() #Yeah I'm pretty sure you shouldn't do this in like a real application...
        
        if username.get().lower() in email_l or username.get().lower() in name_l and password.get() in pass_l:
            self.current_username,self.current_password = username.get().lower(), password.get() #don't do this in a real app 
            return self.create_main_menu()
        else:
            return self.show_popup(self.login_btn,"Wrong username or password.")


    def create_register_window(self):
        '''
        This method creates a register window that gives the user the oppurtunity to register a new user into the database
        '''
        self.frame.destroy()
        self.frame = ctk.CTkFrame(self)
        self.frame.bg = ""
        self.frame.pack(expand=True,fill="both")
        self.frame.rowconfigure((0,1,2),weight=1, uniform="a")
        self.frame.rowconfigure(1,weight=2, uniform="a")
        self.frame.columnconfigure((0,1,2),weight=1, uniform="a")
        self.frame.columnconfigure(1,weight=2, uniform="a")


        #these variables  need to become true for the user to succesfully register
        self.check_register = {
            "email_entry": False,
            "name_entry": False,
            "pass_entry": False,
            "c_pass_entry": False
        }

        frame = ctk.CTkFrame(self.frame)
        frame.grid(column=1,row=1, sticky="nswe")
        frame.rowconfigure((0,1,2,3,4,5,6), weight=1, uniform="a")
        frame.columnconfigure((0,1,2,3,4,5), weight=1, uniform="a")

        #widgets (these ones have self. because it just makes it easier to create logic for validation)
        self.email_entry = ctk.CTkEntry(frame, placeholder_text="Enter your e-mail address", validate="focusout", validatecommand=lambda:self.validate_entry(self.email_entry))
        self.email_entry_check = ctk.CTkLabel(frame, text="✓", fg_color="transparent", text_color="gray", font=(None,25))
        self.name_entry = ctk.CTkEntry(frame, placeholder_text="Enter a username", validate="focusout", validatecommand=lambda:self.validate_entry(self.name_entry))
        self.name_entry_check = ctk.CTkLabel(frame, text="✓", fg_color="transparent", text_color="gray", font=(None,25))
        self.pass_entry = ctk.CTkEntry(frame, placeholder_text="Enter password", validate="focusout", validatecommand=lambda:self.validate_entry(self.pass_entry))
        self.pass_entry_check = ctk.CTkLabel(frame, text="✓", fg_color="transparent", text_color="gray", font=(None,25))
        self.c_pass_entry = ctk.CTkEntry(frame, placeholder_text="Confirm password", show="*", validate="focusout", validatecommand=lambda:self.validate_entry(self.c_pass_entry))
        self.c_pass_entry_check = ctk.CTkLabel(frame, text="✓", fg_color="transparent", text_color="gray", font=(None,25))
        self.confirm_btn = ctk.CTkButton(frame,text="Confirm", command=lambda: self.register(self.email_entry,self.name_entry,self.pass_entry,self.c_pass_entry))
        self.back_btn = ctk.CTkButton(frame, image=arrow_l_ctk, command=self.create_login_window, text="",width=20)

        #placing widgets and creating some labels
        ctk.CTkLabel(frame,text="E-mail:",font=("Helvetica",13),padx=5).grid(row=1,column=0,sticky="e",columnspan=2)
        ctk.CTkLabel(frame,text="Username:",font=("Helvetica",13),padx=5).grid(row=2,column=0,sticky="e",columnspan=2)
        ctk.CTkLabel(frame,text="Password:",font=("Helvetica",13),padx=5).grid(row=3,column=0,sticky="e",columnspan=2)
        ctk.CTkLabel(frame,text="Confirm Password:",font=("Helvetica",13),padx=5).grid(row=4,column=0,sticky="e",columnspan=2)
        self.email_entry.grid(row=1, column=2, columnspan=3, sticky="we")
        self.email_entry_check.grid(row=1, column=5, sticky="w", padx=5)
        self.name_entry.grid(row=2, column=2, columnspan=3, sticky="we")
        self.name_entry_check.grid(row=2, column=5, sticky="w", padx=5)
        self.pass_entry.grid(row=3, column=2, columnspan=3, sticky="we")
        self.pass_entry_check.grid(row=3, column=5, sticky="w", padx=5)
        self.c_pass_entry.grid(row=4, column=2, columnspan=3, sticky="we")
        self.c_pass_entry_check.grid(row=4, column=5,sticky="w", padx=5)
        self.confirm_btn.grid(row=5, column=4, sticky="we",padx=5)
        self.back_btn.grid(row=5, column=2, sticky="w")


    def register(self, email, name, password):
        '''
        Creates a new user in the database if the information is correct, otherwise returns some error
        '''
        # email_l,name_l,pass_l = get_data()

        if all(self.check_register.values()):
            self.show_popup(self.confirm_btn,"User succesfully created, going back to the login page.")
            create_user(email.get().lower(),name.get().lower(),password.get())
            self.after(2000,lambda: self.create_login_window())

        else:
            self.show_popup(self.confirm_btn, "Please correctly fill out all fields.")


    def create_main_menu(self):
        '''
        Creates the main menu of the application
        '''      

        if self.frame:
            self.frame.destroy()
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(expand=True, fill="both")
        self.frame.rowconfigure((0,1,2,3,4,5,6), weight=1, uniform="a")
        self.frame.columnconfigure((0,1,2,3,4), weight=1, uniform="a")

        #buttons
        ctk.CTkButton(self.frame,text="PLANTERS", command=self.create_planter_window, font=(None, 20)).grid(row=2,column=1,rowspan=3, sticky="nswe", padx=10)
        ctk.CTkButton(self.frame,text="PLANT\nDATA", command=self.create_repository_window, font=(None, 20)).grid(row=2,column=2,rowspan=3, sticky="nswe", padx=10)
        ctk.CTkButton(self.frame,text="OPTIONS", command=self.create_options_window, font=(None, 20)).grid(row=2,column=3,rowspan=3, sticky="nswe", padx=10)


    def sync_btn(self):
        '''
        Just randomizes the data in the planters
        '''
        data = self.get_json_data("images_and_data/plant_info.json")

        moist_list = ["optimal", "moderate", "low"]

        for x in range(len(data["planters"])):
            temperature = random.randint(5,30)
            moisture = random.choice(moist_list)
            if data["planters"][x]["location"] == "inside":
               data["planters"][x]["temperature"] = temperature
            data["planters"][x]["moisture"] = moisture

        with open("images_and_data/plant_info.json", "w") as file:
            json.dump(data, file, indent=4)

        self.create_planter_window()


    def create_planter_window(self):
        '''
        This method creates the planter window when called
        '''
        if self.frame:
            self.frame.destroy()
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(expand=True, fill="both")
        self.frame.rowconfigure((0,1,2,3,4,5,6), weight=1, uniform="b")
        self.frame.columnconfigure((0,1,2,3,4), weight=1, uniform="a")


        window = ctk.CTkScrollableFrame(self.frame) #not as good as creating the scrollbar yourself (if you move the scroll fast it glitches)
        window.grid(row=2,column=1,rowspan=4,columnspan=3,sticky="nswe")

        data = self.get_json_data("images_and_data/plant_info.json")
        plant_data = data["plants"]
        planter_data = data["planters"]

        #this code here is for creating all the data that goes into the window
        planter_frames = []
        self.original_pic_list = []
        self.picture_list = []
        self.canvas_list = []

        for _ in range(len(planter_data)):
            frame = ctk.CTkFrame(window)
            frame.rowconfigure((0,1,2,3,4), weight=1, uniform="b")
            frame.columnconfigure((0,1,2,3,4,5), weight=1, uniform="a")
            planter_frames.append(frame)

        for x in range(len(planter_frames)):
            current_plant_id = planter_data[x]["plant_id"]
            for plant in range(len(plant_data)):
                if current_plant_id == plant_data[plant]["id"]:
                    current_plant = plant
            
            #packing the frames
            planter_frames[x].pack(expand=True,fill="x",pady=5, padx=5)
            #creating labels
            ctk.CTkLabel(planter_frames[x],text="Plant:").grid(row=0,column=0,padx=5,sticky="w")
            ctk.CTkLabel(planter_frames[x],text=plant_data[current_plant]["name"]).grid(row=0,column=1,columnspan=2,padx=5,sticky="w")
            ctk.CTkLabel(planter_frames[x],text="Location:").grid(row=1,column=0,padx=5,sticky="w")
            ctk.CTkLabel(planter_frames[x],text=planter_data[x]["location"]).grid(row=1,column=1,columnspan=2,padx=5,sticky="w")
            ctk.CTkLabel(planter_frames[x],text="Temp:").grid(row=2,column=0,padx=5,sticky="w")
            ctk.CTkLabel(planter_frames[x],text=f"{planter_data[x]['temperature']}°C").grid(row=2,column=1,columnspan=2,padx=5,sticky="w")
            ctk.CTkLabel(planter_frames[x],text="Moisture:").grid(row=3,column=0,padx=5,sticky="w")
            ctk.CTkLabel(planter_frames[x],text=planter_data[x]["moisture"]).grid(row=3,column=1,columnspan=2,padx=5,sticky="w")

            #creating buttons
            ctk.CTkButton(planter_frames[x],text="EDIT",command=lambda x=x: self.edit_planter_window(x)).grid(row=4,column=3,sticky="e")

            #creating all the data for the pictures
            picture = Image.open(plant_data[current_plant]["photo"])
            self.picture_list.append(ImageTk.PhotoImage(picture))
            self.original_pic_list.append(picture)
            canvas = tk.Canvas(planter_frames[x], background="#31C48D", bd=0,highlightthickness=3, highlightbackground="#31C48D", relief="ridge",width=1,height=50 )
            canvas.place(relx=0.7, rely=0, relheight=1,relwidth=0.3)
            self.canvas_list.append(canvas)

        #for loop that sets a bind for each image so its always sized correctly
        for canvas_index, canvas in enumerate(self.canvas_list):
            canvas.bind("<Configure>", lambda event, index=canvas_index, c=canvas: self.fill_image(event, self.original_pic_list[index], c))

        #buttons
        ctk.CTkButton(self.frame, text="",image=arrow_b_ctk, command=self.create_main_menu, width=50).grid(row=1,column=1, sticky="ws",pady=5)
        ctk.CTkButton(self.frame, text="Weather Info", command=self.create_weather_info).grid(row=1,column=2, sticky="wse",pady=5,padx=5)
        ctk.CTkButton(self.frame, text="New Planter", command=self.createnew_planter_window).grid(row=1,column=3, sticky="wse",pady=5, padx=5)
        ctk.CTkButton(self.frame, text="Sync", command=self.sync_btn).grid(row=0,column=4, sticky="nwse",pady=10, padx=5)


    def create_weather_info(self):
        '''
        Creates a new window that contains graph with the information about today's weather and humidity
        '''
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Today's weather")
        width = self.winfo_width()/1.2
        height = self.winfo_height()/1.2
        edit_window.minsize(width,height)
        edit_window.maxsize(width*2,width*2)
        edit_window.rowconfigure((0,1,2,3,4,5,6), weight=1, uniform="a")
        edit_window.columnconfigure((0,1,2,3), weight=1, uniform="a")

        weather_data = self.get_weather_info()
        
        hourly_data = weather_data.get('hourly', {})
        time_list = hourly_data.get('time', [])
        x_labels = [time[-5:] for time in time_list]
        temperature_list = hourly_data.get('temperature_2m', [])
        humidity_list = hourly_data.get('relativehumidity_2m', [])

        tabview = ctk.CTkTabview(edit_window)
        tabview.add("Line")
        tabview.add("Scatter")
        tabview.add("Step")
        tabview.add("Line_hum")
        tabview.add("Scatter_hum")
        tabview.add("Step_hum")
        tabview.grid(row=3,column=0,rowspan=3,columnspan=3, sticky="nswe",padx=10)

        line_frame = ctk.CTkFrame(tabview.tab("Line"))
        line_frame.pack(expand=True,fill="both")
        line_frame.rowconfigure(0,weight=1,uniform="a")
        line_frame.columnconfigure((0,1),weight=1,uniform="a")

        line_frame_hum = ctk.CTkFrame(tabview.tab("Line_hum"))
        line_frame_hum.pack(expand=True,fill="both")
        line_frame_hum.rowconfigure(0,weight=1,uniform="a")
        line_frame_hum.columnconfigure((0,1),weight=1,uniform="a")

        scatter_frame = ctk.CTkFrame(tabview.tab("Scatter"))
        scatter_frame.pack(expand=True,fill="both")
        scatter_frame.rowconfigure(0,weight=1,uniform="a")
        scatter_frame.columnconfigure((0,1),weight=1,uniform="a")

        scatter_frame_hum = ctk.CTkFrame(tabview.tab("Scatter_hum"))
        scatter_frame_hum.pack(expand=True,fill="both")
        scatter_frame_hum.rowconfigure(0,weight=1,uniform="a")
        scatter_frame_hum.columnconfigure((0,1),weight=1,uniform="a")

        step_frame = ctk.CTkFrame(tabview.tab("Step"))
        step_frame.pack(expand=True,fill="both")
        step_frame.rowconfigure(0,weight=1,uniform="a")
        step_frame.columnconfigure((0,1),weight=1,uniform="a")

        step_frame_hum = ctk.CTkFrame(tabview.tab("Step_hum"))
        step_frame_hum.pack(expand=True,fill="both")
        step_frame_hum.rowconfigure(0,weight=1,uniform="a")
        step_frame_hum.columnconfigure((0,1),weight=1,uniform="a")

        #line graphs
        fig, ax = plt.subplots()
        ax.plot(x_labels, temperature_list)
        ax.set_xlabel("Time")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title('Temperature Variation')
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(0, 50)
        canvas = tkagg.FigureCanvasTkAgg(fig, master=line_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True,fill="both")

        fig, ax = plt.subplots()
        ax.plot(x_labels, humidity_list)
        ax.set_xlabel("Time")
        ax.set_ylabel("Humidity 2m (%)")
        ax.set_title('Humidity variation')
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(0, 100)
        canvas = tkagg.FigureCanvasTkAgg(fig, master=line_frame_hum)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True,fill="both")

        #scatter graphs
        fig, ax = plt.subplots()
        ax.scatter(x_labels, temperature_list)
        ax.set_xlabel("Time")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title("Temperature Variation")
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(0, 50)
        scatter_canvas = tkagg.FigureCanvasTkAgg(fig, master=scatter_frame)
        scatter_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        scatter_canvas.draw()

        fig, ax = plt.subplots()
        ax.scatter(x_labels, humidity_list)
        ax.set_xlabel("Time")
        ax.set_ylabel("Humidity 2m (%)")
        ax.set_title('Humidity variation')
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(0, 100)
        canvas = tkagg.FigureCanvasTkAgg(fig, master=scatter_frame_hum)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True,fill="both")

        #stepgraphs
        fig, ax = plt.subplots()
        ax.step(x_labels, temperature_list)
        ax.set_xlabel("Time")
        ax.set_ylabel("Temperature (°C)")
        ax.set_title("Temperature Variation")
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(0, 50)
        scatter_canvas = tkagg.FigureCanvasTkAgg(fig, master=step_frame)
        scatter_canvas.get_tk_widget().pack(side="top", fill="both", expand=True)
        scatter_canvas.draw()

        fig, ax = plt.subplots()
        ax.step(x_labels, humidity_list)
        ax.set_xlabel("Time")
        ax.set_ylabel("Humidity 2m (%)")
        ax.set_title('Humidity variation')
        ax.xaxis.set_major_locator(ticker.MultipleLocator(2))
        ax.tick_params(axis='x', rotation=45)
        ax.set_ylim(0, 100)
        canvas = tkagg.FigureCanvasTkAgg(fig, master=step_frame_hum)
        canvas.draw()
        canvas.get_tk_widget().pack(expand=True,fill="both")

        ctk.CTkLabel(edit_window,text=self.update_time(),justify="left").grid(row=0,column=0,sticky="nw",padx=5,pady=5)


    def edit_planter_window(self, planter_id):
        '''
        Creates the window for editing existing planter
        '''
        planter_id = planter_id+1

        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Editing")
        width = self.winfo_width()/2
        height = self.winfo_height()/2
        edit_window.minsize(width,height)
        edit_window.maxsize(width*2,width*2)
        edit_window.rowconfigure((0,1,2,3,4,5,6), weight=1, uniform="a")
        edit_window.columnconfigure((0,1,2,3,4), weight=1, uniform="a")        
        
        data = self.get_json_data("images_and_data/plant_info.json")
        plant_data = data["plants"]
        planter_data = data["planters"]
        for x in planter_data:
            if x["id"] == planter_id:
                plant_id = x["plant_id"]
                break

        for x in plant_data:
            if x["id"] == plant_id:
                the_plant = x
                break
        
        for x in planter_data:
            if x["id"] == planter_id:
                the_planter = x
                break

        planter_temp = the_planter['temperature']
        if the_plant["care"]["temperature"] == "warmer":
            temp_text = f"15-28 °C\n{planter_temp} °C"
            if planter_temp > 15 and planter_temp < 28:
                ctk.CTkLabel(edit_window, text="✓", fg_color="transparent", text_color="green", font=(None,25)).grid(row=1,column=2,sticky="w")
            else:
                ctk.CTkLabel(edit_window, text="X", fg_color="transparent", text_color="red", font=(None,25)).grid(row=1,column=2,sticky="w")
        elif the_plant["care"]["temperature"] == "moderate":
            temp_text = f"12-28 °C\n{planter_temp} °C"
            if planter_temp > 12 and planter_temp < 28:
                ctk.CTkLabel(edit_window, text="✓", fg_color="transparent", text_color="green", font=(None,25)).grid(row=1,column=2,sticky="w")
            else:
                ctk.CTkLabel(edit_window, text="X", fg_color="transparent", text_color="red", font=(None,25)).grid(row=1,column=2,sticky="w")
                ctk.CTkLabel(edit_window, text="Move the plant!", fg_color="transparent").grid(row=1,column=3,sticky="w")
        else:
            temp_text = f"6-24 °C\n{planter_temp} °C"
            if planter_temp > 6 and planter_temp < 24:
                ctk.CTkLabel(edit_window, text="✓", fg_color="transparent", text_color="green", font=(None,25)).grid(row=1,column=2,sticky="w")
            else:
                ctk.CTkLabel(edit_window, text="X", fg_color="transparent", text_color="red", font=(None,25)).grid(row=1,column=2,sticky="w")
        water_var = tk.IntVar(value=0)
        ctk.CTkSlider(  edit_window,
                        progress_color="#38a7fc",
                        from_=0,
                        to=100,
                        button_color="white",
                        button_hover_color="white",
                        variable=water_var,
                        state="disabled").grid(row=2,column=4, sticky="we")

        if the_planter["moisture"] == "optimal":
            moist_text = "The plant is well maintained"
            self.change_variable(water_var,100,random.randint(80,100), True)
        elif the_planter["moisture"] == "moderate":
            moist_text = "The plant needs moisture"
            self.change_variable(water_var,100,random.randint(40,60), True)
        else:
            moist_text = "The plant is dangerously low on moisture!"
            self.change_variable(water_var,100,random.randint(10,30), True)

        ctk.CTkLabel(edit_window,text="Optimal Temp:\nCurrent Temp:").grid(row=1,column=0,sticky="w",padx=5,pady=5)
        ctk.CTkLabel(edit_window,text=temp_text).grid(row=1,column=1,sticky="w",padx=5,pady=5)

        ctk.CTkLabel(edit_window,text="Current moisture:").grid(row=2,column=0,sticky="w",padx=5,pady=5)
        ctk.CTkLabel(edit_window,text=moist_text).grid(row=2,column=1,columnspan=2,sticky="w",padx=5,pady=5)
        ctk.CTkButton(edit_window,text="Add Water",command=lambda:self.change_variable(water_var, 100, 100, True)).grid(row=2,column=3,sticky="we",padx=5,pady=5)

        ctk.CTkLabel(edit_window,text=self.update_time(),justify="left").grid(row=0,column=0,sticky="nw",padx=5,pady=5)
        ctk.CTkButton(edit_window,text="Back",command=lambda:self.update_planter(water_var.get(), planter_id-1,edit_window)).grid(row=6,column=0,sticky="we",padx=5)
        ctk.CTkButton(edit_window,text="Delete",command=lambda:self.empty_planter(planter_id-1,edit_window)).grid(row=6,column=4,sticky="we",padx=5)


    def update_planter(self, water, planter, close_window):
        data = self.get_json_data("images_and_data/plant_info.json")

        if water > 79:
            data["planters"][planter]["moisture"] = "optimal"

            with open("images_and_data/plant_info.json", "w") as file:
                json.dump(data, file, indent=4)
        
            self.create_planter_window()
        
        close_window.destroy()
        

    def change_variable(self,variable, maximum:int, add:int, switch:bool):
        '''
        Takes a variable and then makes it slowly increase over time until the max 
        '''
        current_value = variable.get()
        if switch and add >= 0 and current_value <= maximum:
            add -= 1
            current_value += 1
            variable.set(current_value)
            self.after(15,lambda: self.change_variable(variable,maximum,add,switch))
        if switch == False and add >= 0  and current_value >= maximum:
            add -= 1
            current_value -= 1
            variable.set(current_value)
            self.after(15,lambda: self.change_variable(variable,maximum,add,switch))


    def createnew_planter_window(self):
        '''
        Allows the creation of new planters as long as there are empty planters left
        '''
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Editing")
        width = self.winfo_width()/2
        height = self.winfo_height()/2
        edit_window.minsize(width,height)
        edit_window.maxsize(width*2,width*2)
        edit_window.rowconfigure((0,1,2,3,4,5,6), weight=1, uniform="a")
        edit_window.columnconfigure((0,1,2), weight=1, uniform="a")   

        data = self.get_json_data("images_and_data/plant_info.json")
        plant_data = data["plants"]
        planter_data = data["planters"]
        planters_left = data["max_planters"] - len(planter_data)
        
        plant_list = [plant_data[x]["name"] for x in range(len(plant_data))]

        #options
        ctk.CTkLabel(edit_window, text=f"Empty Planters left: {planters_left}").grid(row=0,column=0,columnspan=2,sticky="w", padx=10)

        ctk.CTkLabel(edit_window, text="Choose plant:").grid(row=1,column=0,sticky="e",padx=5)
        choose_var = tk.StringVar(value=plant_list[0])
        ctk.CTkOptionMenu(edit_window, values=plant_list, variable=choose_var).grid(row=1, column=1, sticky="e", padx=5)

        ctk.CTkLabel(edit_window, text="Choose location:").grid(row=2,column=0,sticky="e",padx=5)
        loc_var = tk.StringVar(value="inside")
        ctk.CTkOptionMenu(edit_window, values=["inside","outside"], variable=loc_var).grid(row=2, column=1, sticky="e", padx=5)

        c_button = ctk.CTkButton(edit_window, text="Create", command=lambda: self.create_planter(choose_var.get(), loc_var.get(), edit_window))
        c_button.grid(row=6,column=2,sticky="ew", padx=5)
        ctk.CTkButton(edit_window,text="Cancel",command=lambda:edit_window.destroy()).grid(row=6,column=0,sticky="we",padx=5)

        if planters_left <= 0:
            c_button.configure(state="disabled")


    def create_planter(self, plant, location, close_window):
        '''
        updates the jsons and creates a new planter
        '''
        data = self.get_json_data("images_and_data/plant_info.json")
        plant_data = data["plants"]
        planter_data = data["planters"]
        planter_id = len(planter_data)+1

        weather_data = self.get_weather_info()

        for x in range(len(plant_data)):
            if plant_data[x]["name"] == plant:
                plant_id = plant_data[x]["id"]
                break
        

        if location == "inside":
            temp = 20
        else:
            temp = int(weather_data["current_weather"]["temperature"])

        new_entry = {
            "id": planter_id,
            "plant_id": plant_id,
            "location": location,
            "temperature": temp,
            "moisture": "low"
        }

        data["planters"].append(new_entry)

        with open("images_and_data/plant_info.json", "w") as file:
            json.dump(data, file, indent=4)

        close_window.destroy()
        self.create_planter_window()


    def empty_planter(self, planter_index, close_window):
        '''
        Deletes certain planter from the json
        '''
        data = self.get_json_data("images_and_data/plant_info.json")

        #we find the index of the plant
        
        #remove the plant
        if planter_index is not None:
            remove_planter = data["planters"].pop(planter_index)

            #update the indexes
            for planter in data["planters"]:
                if planter["id"] > planter_index:
                    planter["id"] -= 1
        
        #dump it
        with open("images_and_data/plant_info.json", "w") as file:
            json.dump(data, file, indent=4)

        close_window.destroy()
        self.create_planter_window()


    def create_options_window(self):
        '''
        Creates the options window
        '''
        if self.frame:
            self.frame.destroy()
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(expand=True, fill="both")
        self.frame.rowconfigure((0,1,2,3), weight=1, uniform="a")
        self.frame.columnconfigure((0,1,2,3), weight=1, uniform="a")


        #back button
        ctk.CTkButton(self.frame, text="",image=arrow_b_ctk, command=self.create_main_menu, width=50).grid(row=0,column=1, sticky="ws")

        email_l,name_l,pass_l = get_data()

        data = self.get_json_data("images_and_data/city_coords.json")
        for city, value in data["cities"].items():
            if value == data["current_city"]:
                current_place = city
                break
        
        window = ctk.CTkFrame(self.frame)
        window.grid(row=1,column=1,rowspan=2,columnspan=2, sticky="nswe")
        window.rowconfigure((0,1,2,3,4,5,6,7,8), weight=1, uniform="a")
        window.columnconfigure((0,1,2,3), weight=1, uniform="a")

        #options
        ctk.CTkLabel(window,text="Location:").grid(row=1, column=0, sticky="ew")
        location_var = tk.StringVar(value=current_place)
        ctk.CTkOptionMenu(window, values=[x for x in data["cities"]], variable=location_var).grid(row=1,column=1,sticky="ew")

        radio_var = tk.IntVar()
        ctk.CTkLabel(window,text="Themes:").grid(row=2, column=0, sticky="ew")
        ctk.CTkRadioButton(window, text="Light Theme", variable=radio_var, value=0, command=lambda: ctk.set_appearance_mode("light")).grid(row=2,column=1,sticky="ew")
        ctk.CTkRadioButton(window, text="Dark Theme", variable=radio_var, value=1, command=lambda: ctk.set_appearance_mode("dark")).grid(row=2,column=2,sticky="ew")
        
        #admin
        if self.current_username == name_l[0] and self.current_password == pass_l[0]:
            self.adminbtn = ctk.CTkButton(window,text="Admin", command=lambda:self.admin_access(window))
            self.adminbtn.grid(row=7,column=3,sticky="e",padx=10,pady=4)
        #save btn
        ctk.CTkButton(window, text="Save", command=lambda: self.save_options(location_var.get())).grid(row=8,column=3, sticky="e", padx=10,pady=4)


    def save_options(self, location):
        data = self.get_json_data("images_and_data/city_coords.json")

        for city, value in data["cities"].items():
            if city == location:
                data["current_city"] = value
                break
        self.coord_var = value
        with open("images_and_data/city_coords.json", "w") as file:
            json.dump(data, file, indent=4)            
        self.update_temp()


    def admin_access(self, window):
        '''
        Creates a widget so the admin can manipulate user information
        '''
        self.email_var = tk.StringVar(value="")
        self.username_var = tk.StringVar(value="")
        self.password_var = tk.StringVar(value="")
        self.adminbtn.configure(state="disabled")

        self.treeview_canvas = tk.Canvas(window,bg="black")
        self.table = ttk.Treeview(self.treeview_canvas, columns=("email","username","password"),show="headings")
        self.table.column("email", width=10)
        self.table.column("username", width=10)
        self.table.column("password", width=10)

        self.table.heading("email", text="E-mail")
        self.table.heading("username", text="Username")
        self.table.heading("password", text="Password")

        self.treeview_canvas.grid(row=4,column=0,rowspan=4,columnspan=3,sticky="nswe", padx=15)

        # Update the window size when the canvas is resized
        def on_canvas_resize(event):
            table_width = event.width
            table_height = event.height
            self.treeview_canvas.itemconfigure(self.tree_id, width=table_width, height=table_height)

        def update_table(del_all):
            '''
            Makes treeview objects for the treeview object in panel 3 (the del_all parameter is here for updating the existing list)
            '''
            if del_all == True:
                for child in self.table.get_children():
                    self.table.delete(child)
            email_l,name_l,pass_l = get_data()
            for i in range(len(email_l)):
                self.table.insert(parent="", index=i, values=(email_l[i],name_l[i],pass_l[i]))


        def item_select(_):
            '''
            Makes it so when you click an item in the self.table its values get stored in the various variables
            '''
            for i in self.table.selection():
                self.email_var.set(self.table.item(i)["values"][0])
                self.username_var.set(self.table.item(i)["values"][1])
                self.password_var.set(self.table.item(i)["values"][2])


        def delete_selected():
            '''
            deletes all selected items from the self.table and the sql database: Database.db (based on their unique pin number)
            '''
            for_deletion = []
            for i in self.table.selection():
                for_deletion.append(self.table.item(i)["values"][0])
                self.table.delete(i)
            for x in for_deletion:
                delete_user(x)

        def edit_selected():
            '''
            edits a selected item from the self.table
            '''
            edit_user(self.email_var.get().lower(),self.username_var.get().lower(),self.password_var.get())
            self.current_password = self.password_var.get()
            #we have to clear the self.table so there are no duplicates when we update the object
            update_table(True)

        self.treeview_canvas.bind("<Configure>", on_canvas_resize)
        self.table.bind("<<TreeviewSelect>>", item_select)
        self.tree_id = self.treeview_canvas.create_window((0,0),window=self.table, anchor=tk.NW)

        update_table(False)
        #entries
        ctk.CTkEntry(window,textvariable=self.email_var).grid(row=4,column=3,sticky="we",padx=10)
        ctk.CTkEntry(window,textvariable=self.username_var).grid(row=5,column=3,sticky="we",padx=10)
        ctk.CTkEntry(window,textvariable=self.password_var).grid(row=6,column=3,sticky="we",padx=10)

        #btns
        ctk.CTkButton(window,text="Edit",command= edit_selected).grid(row=8,column=0)
        ctk.CTkButton(window,text="Delete",command= delete_selected).grid(row=8,column=1)


    def create_repository_window(self):
        '''
        Creates the repository window where plant information can be viewed and modified
        '''
        if self.frame:
            self.frame.destroy()
        self.geometry(f"{self.window_width}x{self.window_height}+{int(self.screen_width/2-self.window_width/2)}+{int(self.screen_heigth/2-self.window_height/1.5)}")
        self.frame = ctk.CTkFrame(self)
        self.frame.pack(expand=True, fill="both")
        self.frame.rowconfigure((0,1,2,3,4,5), weight=1, uniform="a")
        self.frame.columnconfigure((0,1,2,3,4), weight=1, uniform="a")

        
        #data from json
        plant_data = self.get_json_data("images_and_data/plant_info.json")
        plant_data = plant_data["plants"]

        #creating the panels
        start_pos = 0.2
        move_pos = -0.5
        panel_list = []
        plant_number = len(plant_data)

        if plant_number == 0:
            pass #this would mean there are no panels to be made because the database is empty... if it was a real application it should probably have this

        elif plant_number < 3: #if there are less than  3 plants we don't need more than 1 panel
            panel_list.append(PlantPanel(self.frame,start_pos,move_pos))
 
        elif plant_number > 2: #here we check if there are for example 10 plants we can just divide that by 2 and they fit into 5 frames, however if there are eleven plants we need an extra panel
            if plant_number % 2 == 0: 
                for x in range(int(plant_number/2)):
                    panel_list.append(PlantPanel(self.frame,start_pos,move_pos))
                    start_pos += 0.7
                    move_pos += 0.7
            else:
                for x in range(int((plant_number+1)/2)):
                    panel_list.append(PlantPanel(self.frame,start_pos,move_pos))
                    start_pos += 0.7
                    move_pos += 0.7

            
        #adding info on each panel using for loops
        current_plant = 0 #very important variable
        for x in range(len(panel_list)):
            #configuring the rows and columns for each panel
            panel_list[x].rowconfigure((0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15), weight=1, uniform="b")
            panel_list[x].columnconfigure((0,1,2,3,4), weight=1, uniform = "a")

            #placing labels and information onto the panels
            ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant]['name']}", bg_color="#31C48D", anchor="center", corner_radius=10, font=(None,16)).grid(row=0,column=0,columnspan=2, sticky="we", )
            ctk.CTkLabel(panel_list[x], text="Name:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=1,column=0,sticky="w", padx=2)
            ctk.CTkLabel(panel_list[x], text="Moisture:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=2,column=0,sticky="w", padx=2)
            ctk.CTkLabel(panel_list[x], text="Light:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=3,column=0,sticky="w", padx=2)
            ctk.CTkLabel(panel_list[x], text="Temp:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=4,column=0,sticky="w", padx=2)
            ctk.CTkLabel(panel_list[x], text="Substrate:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=5,column=0,sticky="w", padx=2)

            ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant]['name']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=1,column=1,columnspan=2,sticky="w")
            ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant]['care']['moisture']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=2,column=1,columnspan=2,sticky="w")
            ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant]['care']['light']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=3,column=1,columnspan=2,sticky="w")
            ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant]['care']['temperature']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=4,column=1,columnspan=2,sticky="w")
            ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant]['care']['substrate']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=5,column=1,columnspan=2,sticky="w")

            edit_button = ctk.CTkButton(panel_list[x], text="Edit Plant", command=lambda plant=current_plant:self.edit_plant_window(plant_data[plant]), width=100)
            edit_button.grid(row=5, column=4, rowspan=2, sticky="wes", padx=10, pady=10)


            if current_plant+1 <= plant_number-1: #we have to run a check here to see if we need to put one more plant on the panel or if the last panel only has 1 plant
                ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant+1]['name']}", bg_color="#31C48D", anchor="center", corner_radius=10, font=(None,16)).grid(row=7,column=0,columnspan=2, sticky="we", )
                ctk.CTkLabel(panel_list[x], text="Name:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=8,column=0,sticky="w", padx=2)
                ctk.CTkLabel(panel_list[x], text="Moisture:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=9,column=0,sticky="w", padx=2)
                ctk.CTkLabel(panel_list[x], text="Light:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=10,column=0,sticky="w", padx=2)
                ctk.CTkLabel(panel_list[x], text="Temp:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=11,column=0,sticky="w", padx=2)
                ctk.CTkLabel(panel_list[x], text="Substrate:", bg_color="transparent", anchor="w", font=(None,14)).grid(row=12,column=0,sticky="w", padx=2)

                ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant+1]['name']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=8,column=1,columnspan=2,sticky="w")
                ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant+1]['care']['moisture']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=9,column=1,columnspan=2,sticky="w")
                ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant+1]['care']['light']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=10,column=1,columnspan=2,sticky="w")
                ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant+1]['care']['temperature']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=11,column=1,columnspan=2,sticky="w")
                ctk.CTkLabel(panel_list[x], text=f"{plant_data[current_plant+1]['care']['substrate']}", bg_color="transparent", anchor="w", font=(None,14)).grid(row=12,column=1,columnspan=2,sticky="w")

                edit_button = ctk.CTkButton(panel_list[x], text="Edit Plant", command=lambda plant=current_plant+1:self.edit_plant_window(plant_data[plant]), width=100)
                edit_button.grid(row=13, column=4, sticky="we", padx=10)
                current_plant += 2
            #adding scroll buttons on the panel if there is more than 1 panel
            if plant_number > 2:
                button_left = ctk.CTkButton(panel_list[x], text="", command=lambda: self.move_plants(panel_list, "left"), image=arrow_l_ctk, width=20)
                button_right = ctk.CTkButton(panel_list[x], text="", command=lambda: self.move_plants(panel_list, "right"), image=arrow_r_ctk, width=20)
                if x == 0:
                    button_right.place(relx=0.9, rely=0.9)
                elif x == len(panel_list) - 1:
                    button_left.place(relx=0.02, rely=0.9)
                else:
                    button_right.place(relx=0.9, rely=0.9)
                    button_left.place(relx=0.02, rely=0.9)


        
        #creating the pictures, all their necessary elements and converting them to usable formats
        self.original_pic_list = []
        self.picture_list = []
        self.canvas_list = []
        current_plant = 0 #reset this counter

        for x in range(len(panel_list)):
            picture = Image.open(plant_data[current_plant]["photo"])
            self.picture_list.append(ImageTk.PhotoImage(picture))
            self.original_pic_list.append(picture)
            if current_plant+1 <= plant_number-1:
                picture = Image.open(plant_data[current_plant+1]["photo"])
                self.picture_list.append(ImageTk.PhotoImage(picture))
                self.original_pic_list.append(picture)
                current_plant +=2

        current_plant = 0 
        # only issue with this is the fact that if you try resizing the window it takes a really long time (its not smooth)
        for panel in range(len(panel_list)):
            canvas = tk.Canvas(panel_list[panel], background="#31C48D", bd=0,highlightthickness=3, highlightbackground="#31C48D", relief="ridge",width=1,height=50)
            canvas.place(relx=0.6,rely=0,relheight=0.34,relwidth=0.4)
            canvas.create_image(0,0,image=self.picture_list[current_plant])
            self.canvas_list.append(canvas)

            if current_plant+1 <= plant_number-1:
                canvas2 = tk.Canvas(panel_list[panel], background="#31C48D", bd=0,highlightthickness=3, highlightbackground="#31C48D", relief="ridge",width=1,height=50)
                canvas2.place(relx=0.6,rely=0.44,relheight=0.34,relwidth=0.4)
                canvas2.create_image(0,0,image=self.picture_list[current_plant+1])
                self.canvas_list.append(canvas2)
                current_plant += 2
        
        for canvas_index, canvas in enumerate(self.canvas_list):
            canvas.bind("<Configure>", lambda event, index=canvas_index, c=canvas: self.fill_image(event, self.original_pic_list[index], c))

        #other widgets on self.frame
        ctk.CTkButton(self.frame, text="",image=arrow_b_ctk, command=self.create_main_menu, width=50).grid(row=0,column=1, sticky="ws")
        ctk.CTkButton(self.frame, text="Create New Plant", command=self.create_plant_window).grid(row=0,column=3, sticky="wse")
        ctk.CTkButton(self.frame, text="FIX WINDOW", command=self.create_repository_window).grid(row=5,column=4,sticky="se")


    def move_plants(self, panel_list, direction):
        '''
        Moves all the plants in the panel_list in a given direction)
        '''
        if direction == "right":
            for panel in panel_list:
                    panel.animate_forward()
        else:
            panel_list.reverse() #reversing the list so it animates in the other direction
            for panel in panel_list:
                    panel.animate_backwards()


    def get_json_data(self,json_file):
        '''
        gets data from plant_info.json
        '''
        with open(json_file) as file:
            data = json.load(file)
        
        return data


    def edit_plant_window(self, plant_info):
        '''
        Opens up a new window using tk.Toplevel and in this window you can edit the json file for the current plant you want to edit
        '''
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Editing")
        edit_window.iconbitmap("images_and_data/leaf_icon.ico")  #has to be a .ico file
        width = self.winfo_width()/4
        height = self.winfo_height()/3
        edit_window.minsize(width,height)
        edit_window.maxsize(width*2,width*2)
        edit_window.geometry(f"{width}x{height}+{int(self.screen_width/2-width/2)}+{int(self.screen_heigth/2-height/1.5)}") #don't know why it doesn't start in the middle, bugs
        edit_window.rowconfigure((0,1,2,3,4,5,6), weight=1, uniform="a")
        edit_window.columnconfigure((0,1,2), weight=1, uniform="a")

        plant_id = plant_info["id"]
        ctk.CTkLabel(edit_window, text="Name:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=0,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Moisture:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=1,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Light:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=2,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Temp:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=3,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Substrate:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=4,column=0,sticky="e", padx=2)        
        ctk.CTkLabel(edit_window, text="Photo Path:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=5,column=0,sticky="e", padx=2)        

        entry_var = tk.StringVar(value=f"{plant_info['name']}")
        ctk.CTkEntry(edit_window,textvariable=entry_var).grid(row=0, column=1,columnspan=2,sticky="w",padx=5)

        moist_var = tk.StringVar(value=f"{plant_info['care']['moisture']}")
        ctk.CTkComboBox(edit_window, variable=moist_var, values=["daily", "weekly", "twice a week", "monthly"], state="readonly").grid(row=1, column=1,columnspan=2,sticky="w",padx=5)
        light_var = tk.StringVar(value=f"{plant_info['care']['light']}")
        ctk.CTkComboBox(edit_window, variable=light_var, values=["bright", "shady", "bright indirect light"], state="readonly").grid(row=2, column=1,columnspan=2,sticky="w",padx=5)
        temp_var = tk.StringVar(value=f"{plant_info['care']['temperature']}")
        ctk.CTkComboBox(edit_window, variable=temp_var, values=["cooler", "moderate", "warmer"], state="readonly").grid(row=3, column=1,columnspan=2,sticky="w",padx=5)
        substr_var = tk.StringVar(value=f"{plant_info['care']['substrate']}")
        ctk.CTkComboBox(edit_window, variable=substr_var, values=["recommended","well-draining soil"], state="readonly").grid(row=4, column=1,columnspan=2,sticky="w",padx=5)
        photo_var = tk.StringVar(value=f"{plant_info['photo']}")
        ctk.CTkComboBox(edit_window, variable=photo_var, values=[f"{plant_info['photo']}"]).grid(row=5, column=1,columnspan=2,sticky="w",padx=5)
        
        ctk.CTkButton(edit_window,text="Cancel",command=lambda:edit_window.destroy()).grid(row=6,column=0,sticky="we",padx=5)

        ctk.CTkButton(edit_window,text="Delete",command=lambda:self.delete_plant(plant_id, edit_window)).grid(row=6,column=1,sticky="we",padx=5)

        confirm_btn = ctk.CTkButton(edit_window,text="Confirm",command=lambda:self.edit_plant(plant_id,entry_var.get(), moist_var.get(), light_var.get(), temp_var.get(), substr_var.get(), edit_window))
        confirm_btn.grid(row=6,column=2,sticky="we",padx=5)


    def edit_plant(self, plant_id, new_entry, new_moist, new_light, new_temp, new_substrate, close_window):
        '''
        This method serves to update the plant_info.json and to update the main_window while closing the toplevel window
        '''
        with open("images_and_data/plant_info.json", "r") as file:
            data = json.load(file)
        for x in range(len(data["plants"])):
            if data["plants"][x]["id"] == plant_id:
                data["plants"][x]["name"] = new_entry
                data["plants"][x]['care']['moisture'] = new_moist
                data["plants"][x]['care']['light'] = new_light
                data["plants"][x]['care']['temperature'] = new_temp
                data["plants"][x]['care']['substrate'] = new_substrate

        with open("images_and_data/plant_info.json", "w") as file:
            json.dump(data, file, indent=4)

        close_window.destroy()
        self.create_repository_window()


    def delete_plant(self, plant_id, close_window):
        '''
        Deletes a plant from the plant_info.json based on its id, also updates the id's of all plants after deletion
        '''
        with open("images_and_data/plant_info.json", "r") as file:
            data = json.load(file)
        
        #we find the index of the plant
        plant_index = None
        for index, plant in enumerate(data["plants"]):
            if plant["id"] == plant_id:
                plant_index = index
                break
        
        #remove the plant
        if plant_index is not None:
            remove_plant = data["plants"].pop(plant_index)

            #update the indexes
            for plant in data["plants"]:
                if plant["id"] > plant_id:
                    plant["id"] -= 1
        
        #dump it
        with open("images_and_data/plant_info.json", "w") as file:
            json.dump(data, file, indent=4)

        close_window.destroy()
        self.create_repository_window()


    def create_plant_window(self):
        '''
        Opens up a new window using tk.Toplevel (works basically the same as create_edit_window)
        '''
        edit_window = ctk.CTkToplevel(self)
        edit_window.title("Editing")
        edit_window.iconbitmap("images_and_data/leaf_icon.ico")  #has to be a .ico file
        width = self.winfo_width()/2
        height = self.winfo_height()/2
        edit_window.minsize(width,height)
        edit_window.maxsize(width*2,width*2)
        edit_window.geometry(f"{width}x{height}+{int(self.screen_width/2-width/2)}+{int(self.screen_heigth/2-height/1.5)}") #don't know why it doesn't start in the middle, bugs
        edit_window.rowconfigure((0,1,2,3,4,5), weight=1, uniform="a")
        edit_window.columnconfigure((0,1,2), weight=1, uniform="a")

        ctk.CTkLabel(edit_window, text="Name:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=0,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Photo Path:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=1,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Moisture:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=2,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Light:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=3,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Temp:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=4,column=0,sticky="e", padx=2)
        ctk.CTkLabel(edit_window, text="Substrate:", bg_color="transparent", anchor="e", font=(None,14)).grid(row=5,column=0,sticky="e", padx=2)        

        entry_var = tk.StringVar()
        ctk.CTkEntry(edit_window,textvariable=entry_var,placeholder_text="New Plant Name").grid(row=0, column=1,columnspan=2,sticky="w",padx=5)
        photo_var = tk.StringVar(value="Put photo path")
        ctk.CTkComboBox(edit_window, variable=photo_var, values=["images_and_data/placeholder_icon.png"], state="normal").grid(row=1, column=1,columnspan=2,sticky="w",padx=5)
        moist_var = tk.StringVar()
        ctk.CTkComboBox(edit_window, variable=moist_var, values=["daily", "weekly", "twice a week", "monthly"], state="readonly").grid(row=2, column=1,columnspan=2,sticky="w",padx=5)
        light_var = tk.StringVar()
        ctk.CTkComboBox(edit_window, variable=light_var, values=["bright", "shady", "bright indirect light"], state="readonly").grid(row=3, column=1,columnspan=2,sticky="w",padx=5)
        temp_var = tk.StringVar()
        ctk.CTkComboBox(edit_window, variable=temp_var, values=["cooler", "moderate", "warmer"], state="readonly").grid(row=4, column=1,columnspan=2,sticky="w",padx=5)
        substr_var = tk.StringVar()
        ctk.CTkComboBox(edit_window, variable=substr_var, values=["recommended","well-draining soil"], state="readonly").grid(row=5, column=1,columnspan=2,sticky="w",padx=5)

        ctk.CTkButton(edit_window,text="Cancel",command=lambda:edit_window.destroy()).grid(row=6,column=0,sticky="we",padx=5)
        ctk.CTkButton(edit_window,text="Create New",command=lambda:self.create_plant(entry_var.get(), photo_var.get(), moist_var.get(), light_var.get(), temp_var.get(), substr_var.get(), edit_window)).grid(row=6,column=2,sticky="we",padx=5)


    def create_plant(self, name, photo, moist, light, temp, substr, close_window):
        '''
        Creates a new entry in the json file
        '''
        with open("images_and_data/plant_info.json", "r") as file:
            data = json.load(file)
        
        plant_number = len(data["plants"])

        new_id = plant_number+1

        new_entry = {
            "id": new_id,
            "name": name,
            "photo": photo,
            "care": {
                "moisture": moist,
                "light": light,
                "temperature": temp,
                "substrate": substr
            }
        }                    

        data["plants"].append(new_entry)

        with open("images_and_data/plant_info.json", "w") as file:
            json.dump(data, file, indent=4)

        close_window.destroy()
        self.create_repository_window()


    def get_weather_info(self):
        '''
        Gets information about the weather from openmeteo.com (you don't need an api key for this)
        '''
        api = requests.get(f"https://api.open-meteo.com/v1/forecast?{self.coord_var}&hourly=temperature_2m,relativehumidity_2m&forecast_days=1&current_weather=True")
        if api.status_code == 200:
            return api.json()
        else:
            print(f"Request failed with status code {api.status_code}")
            return None


    def show_popup(self, widget, text):
        '''
        Creates a popup window at the widget location with desired text (uses ttk, not ctk)
        '''
        # creating a completely new window
        popup = tk.Toplevel()
        popup.geometry("+{}+{}".format(widget.winfo_rootx() + widget.winfo_width(), widget.winfo_rooty()))
        popup.wm_overrideredirect(True)

        style = ttk.Style()
        style.configure(
            "Popup.TLabel",
            background="#FFFFCC",
            border_radius=8, #this line doesn't work for some reason
            relief="solid", 
            borderwidth=1,
            padding=4,
            bordercolor="#E6E68A"
        )

        label = ttk.Label(popup, text=text, style="Popup.TLabel")
        label.pack(ipadx=5, ipady=2)


        # Schedule the popup to close after 2 seconds
        popup.after(2000, popup.destroy)


    def validate_entry(self, entry_widget):
        '''
        Holds the logic for validating entry fields
        '''
        value = entry_widget.get()
        email_l, name_l, pass_l = get_data()

        if value:
            #checks if the e-mail is correct, if not returns a popup that says so
            if entry_widget == self.email_entry:
                is_valid_email = lambda email: re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email) is not None
                if not is_valid_email(value.lower()):
                    self.email_entry_check.configure(text_color="gray")
                    self.show_popup(entry_widget,"The e-mail address is not valid.")
                elif value.lower() in email_l:
                    self.email_entry_check.configure(text_color="gray")
                    self.show_popup(entry_widget,"This e-mail address is in use.")
                else:
                    self.check_register["email_entry"] = True
                    self.email_entry_check.configure(text_color="green")

            #checks if the username is unique
            if entry_widget == self.name_entry:
                if value.lower() in name_l:
                    self.show_popup(entry_widget,"This username exists.")
                    self.name_entry_check.configure(text_color="gray")
                    self.check_register["name_entry"] = False
                else:
                    self.name_entry_check.configure(text_color="green")
                    self.check_register["name_entry"] = True

            #checks if the password is 
            if entry_widget == self.pass_entry:
                if len(value) < 6:
                    self.show_popup(entry_widget,"Please make your password atleast 6 characters long.")
                    self.check_register["pass_entry"] = False
                    self.pass_entry_check.configure(text_color="gray")
                else:
                    self.pass_entry_check.configure(text_color="green")
                    self.check_register["pass_entry"] = True

            #checks if the passwords are the same
            if entry_widget == self.c_pass_entry:
                if value != self.pass_entry.get():
                    self.show_popup(entry_widget,"Passwords do not match")
                    self.c_pass_entry_check.configure(text_color="gray")
                    self.check_register["c_pass_entry"] = False
                else:
                    self.c_pass_entry_check.configure(text_color="green")
                    self.check_register["c_pass_entry"] = True
            return True
        else:
            self.show_popup(entry_widget,"Please fill out the mandatory field.")
            return False


    def full_image(self, event, original_image, canvas):
        '''
        This method configures the given image to always show itself fully no matter the size of the window
        '''
        canvas_ratio = event.width / event.height
        image_ratio = original_image.size[0] / original_image.size[1]

        #get coords
        if canvas_ratio > image_ratio: #canvas is wider than image
            height = int(event.height)
            width = int(height * image_ratio)

        else: # canvas is narrower than the image
            width = int(event.width)
            height = int(width / image_ratio)

        resized_image = original_image.resize((width,height))
        resized_tk = ImageTk.PhotoImage(resized_image)
        self.resized_images[canvas] = resized_tk

        # Clear canvas and fill with green color then create the new image 
        canvas.delete("all")
        canvas.configure(width=width, height=height)
        canvas.create_image(int(event.width / 2),
                            int(event.height / 2),
                            anchor = "center",
                            image= resized_tk)


    def fill_image(self, event, original_image, canvas):
        '''
        This method makes the image fill the canvas (the image is not shown in full)
        '''

        #current ratio of the event
        canvas_ratio = event.width / event.height
        image_ratio = original_image.size[0] / original_image.size[1]

        #get coords
        if canvas_ratio > image_ratio: #canvas is wider than image
            width = int(event.width)
            height = int(width / image_ratio)
        else:
            height = int(event.height)
            width = int(height * image_ratio)

        resized_image = original_image.resize((width,height))
        resized_tk = ImageTk.PhotoImage(resized_image)
        self.resized_images[canvas] = resized_tk


        canvas.delete("all")
        canvas.configure(width=width, height=height)
        canvas.create_image(int(event.width / 2),
                            int(event.height / 2),
                            anchor = "center",
                            image= resized_tk)


class PlantPanel(ctk.CTkFrame):
    '''
    This class creates a frame that can be animated to move left or right
    '''
    def __init__(self, parent, start_pos, end_pos):
        super().__init__(master=parent)
        self.start_pos = start_pos
        self.end_pos = end_pos
        self.width = 0.6 #always use abs

        self.movetick = 0
        #animation logic
        self.pos = self.start_pos

        #layout
        self.place(relx=self.start_pos,rely=0.2,relwidth=self.width,relheight=0.6)


    def animate_forward(self):
        '''
        Moves the self to the right
        '''

        #if you take the movetick and the self.pos and multiply them you will get 0.7, and that sets the relx,
        #so if you want to change the movespeed of the panels you have to account for this equation to be 0.7 (or like how you want the panels to stick out)
        if self.movetick < 70:
            self.pos -= 0.01
            self.place(relx=self.pos, rely=0.2, relwidth=self.width, relheight=0.6)
            self.movetick += 1
            self.after(10, self.animate_forward)
        else:
            self.start_pos = self.end_pos
            self.movetick = 0


    def animate_backwards(self):
        '''
        moves the self to the left
        '''
        if self.movetick < 70:
            self.pos += 0.01
            self.place(relx=self.pos, rely=0.2, relwidth=self.width, relheight=0.6)
            self.movetick += 1
            self.after(10, self.animate_backwards)
        else:
            self.start_pos = self.end_pos
            self.movetick = 0


#these 2 lines of code set the way all widgets and windows are gonna look like, the app is configured for lightmode
ctk.set_default_color_theme("green")
ctk.set_appearance_mode("light")


#pictures, because these pictures are in buttons they don't need a special function for auto resizing
arrow_l_img = Image.open("images_and_data/arrow_left.png").resize((20,20), Image.LANCZOS)
arrow_l_ctk = ctk.CTkImage(arrow_l_img,arrow_l_img)

arrow_r_img = Image.open("images_and_data/arrow_right.png").resize((20,20), Image.LANCZOS)
arrow_r_ctk = ctk.CTkImage(arrow_r_img,arrow_r_img)

arrow_b_img = Image.open("images_and_data/arrow_back.png").resize((20,20), Image.LANCZOS)
arrow_b_ctk = ctk.CTkImage(arrow_b_img,arrow_b_img)

#the class instance
App(800,800)

    # def stretch_image(self, event, original_image, canvas):
    #     '''
    #     This method is just made for testing certain things out, I kept it, maybe it serves some purpose somewhere else at some point
    #     '''
    #     #size
    #     width = event.width
    #     heigth = event.height

    #     #creating the image
    #     resized_image = original_image.resize((width,heigth))
    #     resized_tk = ImageTk.PhotoImage(resized_image)
    #     # self.resized_images[canvas] = resized_tk

    #     #place on canvas
    #     canvas.delete("all")
    #     canvas.create_image(0,0, image= resized_tk, anchor="nw")
