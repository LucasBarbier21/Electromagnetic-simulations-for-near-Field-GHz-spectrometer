import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO
from datetime import datetime
import mplcursors

def fetch_hydro_observation_data(start_date, end_date, station_code):
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

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Load the CSV data into a Pandas DataFrame
            csv_data = response.content.decode('utf-8')
            df = pd.read_csv(StringIO(csv_data), sep=';')
            print("CSV:ok")
            return df
        else:
            # If the request was unsuccessful, print the error message
            print("Error:", response.text)
            return None

    except Exception as e:
        # Handle any exceptions
        print("An error occurred:", e)
        return None

def extract(data_array):
    Data = [[],[]]
    for i in range(len(data_array)):
        Data[0].append(data_array[i][7])
        Data[1].append(data_array[i][8])
    return Data

def convert_matrix_structure(matrix):
    new_matrix = []
    for row in matrix:
        new_row = []
        for item in row:
            if isinstance(item, str):
                new_row.append(item)
            elif isinstance(item, float):
                new_row.append(float(item))  # Convert float strings to float
            elif isinstance(item, int):
                new_row.append(int(item))  # Convert integer strings to integer
            else:
                new_row.append(item)
        new_matrix.append(new_row)
    return new_matrix

# Set the start and end dates for the data retrieval
start_date = "2024-03-16T00:00:00.000Z"
end_date = "2024-04-13T00:06:00.00Z"
station_code = "U122401001"

# Call the function to fetch hydrological observation data for the specified time range and station
hydro_data = fetch_hydro_observation_data(start_date, end_date, station_code)

# Check if the DataFrame is not empty
if hydro_data is not None and not hydro_data.empty:
    # Display the DataFrame (optional)
    print("Hydro_data:ok")
else:
    # Print a message indicating no data retrieved
    print("No data retrieved.")

# Convert DataFrame to matrix
hydro_data_array_dataframe = hydro_data.values
hydro_data_array = convert_matrix_structure(hydro_data_array_dataframe)

Data_extract = extract(hydro_data_array)

def centered_moving_average(data, window_size):
    half_window = window_size // 2
    # Pad the data symmetrically using reflection padding
    padded_data = np.pad(data, half_window, mode='reflect')
    # Apply centered moving average
    smoothed_data = np.convolve(padded_data, np.ones(window_size) / window_size, mode='valid')
    return smoothed_data

Data_extract_smoothed = centered_moving_average(Data_extract[1], window_size=(int(len(Data_extract[1])/10)+1))

def adaptative_time(time_data):
    # Parse time data and extract components
    parsed_dates = [datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ') for date_str in time_data]

    # Determine the range of time covered by the data
    min_date = min(parsed_dates)
    max_date = max(parsed_dates)
    date_range = max_date - min_date

    # Decide the appropriate format for x-axis labels based on the range
    if date_range.days >= 365:  # If data covers more than a year
        x_labels = [date.strftime('%b %Y') for date in parsed_dates]
    elif date_range.days >= 28:  # If data covers more than a month
        x_labels = [date.strftime('%d %b') for date in parsed_dates]
    else:  # If data covers less than a month
        x_labels = [date.strftime('%H:%M') for date in parsed_dates]

    # Keep track of unique dates
    unique_dates = []
    unique_x_labels = []
    for i, date in enumerate(parsed_dates):
        if date not in unique_dates:
            unique_dates.append(date)
            unique_x_labels.append(x_labels[i])

    # Convert datetime objects to numerical values representing elapsed time in seconds
    time_values = sorted([(date - min_date).total_seconds() for date in unique_dates])
    return time_values, unique_x_labels, min_date

time_data = Data_extract[0]
time_values, x_labels, min_date = adaptative_time(time_data)

# Debugging: Print lengths of time_values and Data_extract_smoothed
print("Length of time_values:", len(time_values))
print("Length of Data_extract_smoothed:", len(Data_extract_smoothed))

# Plot
plt.plot([min_date + pd.Timedelta(seconds=t) for t in time_values], Data_extract_smoothed[:len(time_values)])
plt.xlabel('Time')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Data')
plt.title('Adaptive Scale Plot')
mplcursors.cursor()
plt.show()

print("Plot:ok")
