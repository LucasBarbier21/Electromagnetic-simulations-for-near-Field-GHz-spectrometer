import tkinter as tk
from tkinter import ttk
from datetime import datetime
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import mplcursors
from io import StringIO

# Function to fetch hydrological observation data
def fetch_hydro_data(station_code, start_date, end_date):
    base_url = "https://hubeau.eaufrance.fr/api/v1/hydrometrie/observations_tr.csv"
    params = {
        "date_debut_obs": start_date,
        "date_fin_obs": end_date,
        "code_entite": station_code,
        "grandeur_hydro": "Q",
        "timestep": 10,
    }

    try:
        response = requests.get(base_url, params=params)
        if response.status_code == 200:
            csv_data = response.content.decode('utf-8')
            df = pd.read_csv(StringIO(csv_data), sep=';')
            return df
        else:
            print("Error:", response.text)
            return None
    except Exception as e:
        print("An error occurred:", e)
        return None
    
# Function to handle button click event
def get_data():
    station_code = stations[station_var.get()]
    start_date = start_date_var.get()
    end_date = end_date_var.get()
    data = fetch_hydro_data(station_code, start_date, end_date)
    print("Response : ok")
    if data is not None and not data.empty:
        hydro_data_array = data.values
        hydro_data_array = convert_matrix_structure(hydro_data_array)
        Data_extract = extract(hydro_data_array)
        print('Extraction:ok')
        Data_extract_smoothed = centered_moving_average(Data_extract[1], window_size=(int(len(Data_extract[1])/10)+1))
        print("Smooth:ok")
        time_data = Data_extract[0]
        time_values, x_labels, min_date = adaptative_time(time_data)
        
        # Clear previous plot frame if exists
        if plot_frame.winfo_children():
            for child in plot_frame.winfo_children():
                child.destroy()
                        
        # Create a frame to hold the canvas and toolbar
        plot_frame.grid(row=5, column=0, columnspan=2)
        
        # Plot
        plt.plot([min_date + pd.Timedelta(seconds=t) for t in time_values], Data_extract_smoothed[:len(time_values)])
        plt.xlabel('Time')
        plt.xticks(rotation=45, ha='right')
        plt.ylabel('Data')
        plt.title('Adaptive Scale Plot')
        
        # Embed plot in Tkinter
        canvas = FigureCanvasTkAgg(plt.gcf(), master=plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Add matplotlib toolbar for zoom and pan functionalities
        toolbar = NavigationToolbar2Tk(canvas, plot_frame)
        toolbar.update()
        toolbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add cursor toggle button
        toggle_button = tk.Button(plot_frame, text="Toggle Cursor", command=toggle_cursor)
        toggle_button.pack()
        print("plot:ok")

        
# Function to toggle mplcursors
def toggle_cursor():
    global cursor_on
    cursor_on = not cursor_on
    if cursor_on:
        mpl_cursor = mplcursors.cursor(plt.gcf(), hover=True)
        print("cursor:on")
    else:
        mpl_cursor = mplcursors.cursor(plt.gcf(), hover=False)
        print("cursor:off")


# Sample station database (Replace with actual data)
stations = {
    "Arceau": "U122401001",
    "Cessey-sur-Tille": "U122402001",
    "Crecey-sur-Tille": "U1204010"
}

# Function to convert matrix structure
def convert_matrix_structure(matrix):
    new_matrix = []
    for row in matrix:
        new_row = []
        for item in row:
            if isinstance(item, str):
                new_row.append(item)
            elif isinstance(item, float):
                new_row.append(float(item))
            elif isinstance(item, int):
                new_row.append(int(item))
            else:
                new_row.append(item)
        new_matrix.append(new_row)
    return new_matrix

# Function to extract data
def extract(data_array):
    Data = [[],[]]
    for i in range(len(data_array)):
        Data[0].append(data_array[i][7])
        Data[1].append(data_array[i][8])
    return Data

# Function for centered moving average
def centered_moving_average(data, window_size):
    half_window = window_size // 2
    # Pad the data symmetrically using reflection padding
    padded_data = np.pad(data, half_window, mode='reflect')
    # Apply centered moving average
    smoothed_data = np.convolve(padded_data, np.ones(window_size) / window_size, mode='valid')
    return smoothed_data

# Function for adaptive time
def adaptative_time(time_data):
    parsed_dates = [datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ') for date_str in time_data]
    min_date = min(parsed_dates)
    max_date = max(parsed_dates)
    date_range = max_date - min_date
    if date_range.days >= 365:
        x_labels = [date.strftime('%b %Y') for date in parsed_dates]
    elif date_range.days >= 28:
        x_labels = [date.strftime('%d %b') for date in parsed_dates]
    else:
        x_labels = [date.strftime('%H:%M') for date in parsed_dates]
    unique_dates = []
    unique_x_labels = []
    for i, date in enumerate(parsed_dates):
        if date not in unique_dates:
            unique_dates.append(date)
            unique_x_labels.append(x_labels[i])
    time_values = sorted([(date - min_date).total_seconds() for date in unique_dates])
    return time_values, unique_x_labels, min_date

# Set initial cursor state
cursor_on = False

# Create the main window
root = tk.Tk()
root.title("Hydrological Observation Data Viewer")

# Calculate screen width and height
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Set window width and height
window_width = 800   # Adjust as needed
window_height = 600  # Adjust as needed

# Calculate x and y coordinates for centering the window
x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)

# Set window geometry
root.geometry(f"{window_width}x{window_height}+{x}+{y}")


# Station selection
station_label = tk.Label(root, text="Select Station:")
station_label.grid(row=0, column=0, padx=(window_width//3, 10), pady=10)

station_var = tk.StringVar(root)
station_dropdown = ttk.Combobox(root, textvariable=station_var, values=list(stations.keys()), width=25)
station_dropdown.grid(row=0, column=1, padx=(10, 200), pady=10)

# Date selection
start_date_label = tk.Label(root, text="Start Date:")
start_date_label.grid(row=1, column=0, padx=(window_width//3, 10), pady=10)

start_date_var = tk.StringVar(root, value=datetime.now().strftime("%Y-%m-%d"))
start_date_entry = tk.Entry(root, textvariable=start_date_var, width=25)
start_date_entry.grid(row=1, column=1, padx=(10, 200), pady=10)

end_date_label = tk.Label(root, text="End Date:")
end_date_label.grid(row=2, column=0, padx=(window_width//3, 10), pady=10)

end_date_var = tk.StringVar(root, value=datetime.now().strftime("%Y-%m-%d"))
end_date_entry = tk.Entry(root, textvariable=end_date_var, width=25)
end_date_entry.grid(row=2, column=1, padx=(10, 200), pady=10)

# Button to fetch data
fetch_button = tk.Button(root, text="Fetch Data", command=get_data, width=50)
fetch_button.grid(row=3, column=0, columnspan=2, padx=220, pady=10)

mpl_cursor = mplcursors.cursor(plt.gcf())

# Create a frame to hold the plot
plot_frame = tk.Frame(root)

# Run the main event loop
root.mainloop()
