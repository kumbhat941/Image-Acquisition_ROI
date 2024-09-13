import cv2
import numpy as np
import datetime
import time
import os
from pymba import Vimba, Frame, VimbaException
from pathlib import Path

last_save_time = None
save_interval = 8  # Save every 8 seconds
samplename = "roi_image"  # Name for the saved files
datadir = Path(r'D:\THD Spiegelau project\07.09')  # Directory to save images

# Function to set the ROI
def set_roi(camera, width, height, offset_x, offset_y):
    camera.Width = width
    camera.Height = height
    camera.OffsetX = offset_x
    camera.OffsetY = offset_y

# Callback function to display frames continuously
def display_frame(frame: Frame, delay: int = 1) -> None:
    global last_save_time

    start_time_frame = time.time()
    image = frame.buffer_data_numpy()

    try:
        image = cv2.cvtColor(image, cv2.COLOR_BAYER_RG2BGR)  # Convert Bayer to BGR
    except KeyError:
        pass

    # Print frame ID (for debugging purposes)
    print(f"Processing frame ID: {frame.data.frameID}")

    # Get current time
    current_time = time.time()

    # Check if 8 seconds have passed since the last save
    if last_save_time is None or (current_time - last_save_time) >= save_interval:
        last_save_time = current_time  # Update the last save time

        print(f"Saving frame at {datetime.datetime.now()}")

        # Generate the timestamp and file name
        time_stamp = datetime.datetime.now()
        file_name = f"{samplename}_{time_stamp.hour}-{time_stamp.minute}-{time_stamp.second}-{time_stamp.microsecond}.tiff"
        file_path = os.path.join(datadir, file_name)

        print(f"Saving to file path: {file_path}")

        # Save the image
        if not cv2.imwrite(file_path, image):
            print(f"Failed to save image: {file_path}")
        else:
            print(f"Image saved successfully: {file_path}")

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
