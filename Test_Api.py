import cv2
import numpy as np
from pymba import Vimba, Frame

# Function to set the ROI
def set_roi(camera, width, height, offset_x, offset_y):
    camera.Width = width
    camera.Height = height
    camera.OffsetX = offset_x
    camera.OffsetY = offset_y

# Callback function to display frames continuously
def display_frame(frame: Frame):
    # Get the image data as a NumPy array
    image = frame.buffer_data_numpy()

    # Convert the image from Bayer to BGR format for OpenCV
    image = cv2.cvtColor(image, cv2.COLOR_BAYER_RG2BGR)

    # Resize the image to fit on the screen (reduce size for display)
    screen_res = 1280, 720  # Set your screen resolution here (width, height)
    scale_width = screen_res[0] / image.shape[1]
    scale_height = screen_res[1] / image.shape[0]
    scale = min(scale_width, scale_height)
    window_width = int(image.shape[1] * scale)
    window_height = int(image.shape[0] * scale)

    # Resize the image to fit in the window
    resized_image = cv2.resize(image, (window_width, window_height))

    # Display the resized image in a window
    cv2.imshow('Captured Image', resized_image)

    # Wait briefly for the 'q' key to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        return  # Exit on pressing 'q'

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
        camera.ExposureAutoRate = 50
        camera.ExposureAutoTarget = 25

        camera.GainAutoMin = 0
        camera.GainAutoMax = 22
        camera.GainAutoRate = 50

        camera.TriggerSelector = 'FrameStart'
        camera.TriggerSource = 'Software'

        

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
