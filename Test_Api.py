import cv2
import numpy as np
import datetime
import time
import os
from pymba import Vimba, Frame, VimbaException
from pathlib import Path
import csv
from Pico_Api import collect_temperature_data  # Import the function from Pico_Api


last_save_time = None
save_interval = 8  # Save every 8 seconds
samplename = "roi_image"  # Name for the saved files
datadir = Path(r'D:\THD Spiegelau project\07.09')  # Directory to save images
temperature_data = []  # List to store temperature data
start_time = datetime.datetime.now()

# CSV file setup
csv_file = datadir / f"{samplename}_temperature_data.csv"
csv_header = ["Timestamp", "Cold Junction Temp (C)", "Channel 1 Temp (C)"]

def save_temperature_data_to_csv(temperature_data, filename=csv_file):
    if not temperature_data:  # Check if there's data to save
        print("No temperature data to save.")
        return

    # Debugging: Print the raw temperature data to the console
    print(f"Raw temperature data: {temperature_data}")

    with open(filename, mode='a', newline='') as file:
        writer = csv.writer(file)
        # Write the temperature data
        for data in temperature_data:
            try:
                time_str = data['time']
                
                # Debugging: Check the type of temperature values before converting
                print(f"Cold junction temp: {data['cold_junction_temp']}, type: {type(data['cold_junction_temp'])}")
                print(f"Channel 1 temp: {data['channel_1_temp']}, type: {type(data['channel_1_temp'])}")
                
                # Ensure temperatures are float
                cold_junction_temp = float(data['cold_junction_temp'])
                channel_1_temp = float(data['channel_1_temp'])
                
                writer.writerow([time_str, cold_junction_temp, channel_1_temp])
            except ValueError as e:
                print(f"Error formatting temperature data: {e}")
                continue  # Skip the faulty row and proceed

    print(f"Temperature data saved to {filename}")

# Open CSV file and write header if not already created
if not csv_file.exists():
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(csv_header)

# Function to set the ROI
def set_roi(camera, width, height, offset_x, offset_y):
    camera.Width = width
    camera.Height = height
    camera.OffsetX = offset_x
    camera.OffsetY = offset_y

# Callback function to display frames continuously
def display_frame(frame: Frame, delay: int = 1) -> None:
    global last_save_time, temperature_data
    start_time_frame = time.time()

    image = frame.buffer_data_numpy()

    try:
        image = cv2.cvtColor(image, cv2.COLOR_BAYER_RG2BGR)  # Convert Bayer to BGR
    except KeyError:
        pass

    print(f"Processing frame ID: {frame.data.frameID}")

    current_time = time.time()
    if last_save_time is None or (current_time - last_save_time) >= save_interval:
        last_save_time = current_time  # Update the last save time

        print(f"Saving frame at {datetime.datetime.now()}")

        try:
            # Collect temperature data
            temperature_data = collect_temperature_data(start_time, num_samples=1)
            # Debug: Print the temperature data received from the API
            print(f"Collected temperature data: {temperature_data}")
        except Exception as e:
            print(f"Error collecting temperature data: {e}")
            temperature_data = []  # Reset temperature data to empty list if an error occurs

        time_stamp = datetime.datetime.now()
        file_name = f"{samplename}_{time_stamp.hour}-{time_stamp.minute}-{time_stamp.second}-{time_stamp.microsecond}.tiff"
        file_path = os.path.join(datadir, file_name)

        print(f"Saving to file path: {file_path}")

        # Save the image
        if not cv2.imwrite(file_path, image):
            print(f"Failed to save image: {file_path}")
        else:
            print(f"Image saved successfully: {file_path}")

        # Save temperature data to CSV
        save_temperature_data_to_csv(temperature_data)

    # Print frame processing time (for debugging purposes)
    print(f"Frame processing time: {time.time() - start_time_frame} seconds")


# Main function
def main():
    # Initialize the Vimba system
    with Vimba() as vimba:
        # Get the first available camera
        camera = vimba.camera(0)  # Selects the first camera

        # Open the camera
        camera.open()

        camera.ExposureAuto = 'Continuous'
        camera.GainAuto = 'Continuous'

        camera.ExposureAutoAlg = 'Mean'
        camera.ExposureAutoMin = 23
        camera.ExposureAutoMax = 9888888
        camera.ExposureAutoOutliers = 0
        camera.ExposureAutoRate = 100
        camera.ExposureAutoTarget = 50

        camera.GainAutoMin = 0
        camera.GainAutoMax = 22
        camera.GainAutoRate = 50

        camera.TriggerSelector = 'FrameStart'
        camera.TriggerSource = 'Software'
        frame_rate = 5
        camera.AcquisitionFrameRateAbs = frame_rate
        print(f"Requested Frame Rate: {frame_rate} FPS")
        print(f"Applied Frame Rate: {camera.AcquisitionFrameRateAbs} FPS")

        

        # Print camera info
        print(f"Max width: {camera.WidthMax}")
        print(f"Max height: {camera.HeightMax}")

        # Set ROI (adjust these values as needed)
        roi_width = 2016  # ROI width
        roi_height = 1828  # ROI height
        roi_offset_x = 1774  # ROI offset from X
        roi_offset_y = 672  # ROI offset from Y

        # Apply the ROI settings to the camera
        set_roi(camera, roi_width, roi_height, roi_offset_x, roi_offset_y)

        # Arm the camera for continuous frame acquisition and set the callback
        camera.arm('Continuous', display_frame)

        # Start the acquisition process
        try:
            # Start frame acquisition
            camera.start_frame_acquisition()
        

            # Keep running until 'q' is pressed in the OpenCV window
            while True:
                # Check for 'q' key press to exit the loop
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        finally:
            # Stop acquisition and disarm the camera
            camera.stop_frame_acquisition()
            camera.disarm()
            cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
