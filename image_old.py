import datetime
import time
from pymba import Vimba, Frame, VimbaException
import cv2
from pathlib import Path

PIXEL_FORMATS_CONVERSIONS = {
    'BayerRG8': cv2.COLOR_BAYER_RG2RGB,
}

saveframe_count = 8  # Save every N-th frame
datadir = Path(r'D:\THD Spiegelau project\04.09')
samplename = '06_03'
frame_counter = 0

ROI_SELECTED = False  # Flag to indicate if ROI is selected
roi = None  # Store the selected ROI

def display_frame(frame: Frame, delay: int = 1) -> None:
    global frame_counter, ROI_SELECTED, roi
    start_time = time.time()  # Measure frame processing start time

    # Get a copy of the frame data
    image = frame.buffer_data_numpy()

    # Convert color space if necessary
    try:
        image = cv2.cvtColor(image, PIXEL_FORMATS_CONVERSIONS[frame.pixel_format])
    except KeyError:
        pass

    # Print the frame ID to track frame acquisition
    print(f"Processing frame ID: {frame.data.frameID}, frame_counter: {frame_counter}")

    # Save every saveframe_count-th frame
    if frame.data.frameID % saveframe_count == 0:
        print(f"Saving frame {frame_counter} (frame ID: {frame.data.frameID})")

        # If ROI is selected, crop the full-size image based on the ROI
        if ROI_SELECTED and roi is not None:
            x, y, w, h = roi
            cropped_image = image[y:y+h, x:x+w]
            # Save the cropped image with a timestamp
            time_stamp = datetime.datetime.now()
            outputfile = f"{samplename}_{time_stamp.hour}-{time_stamp.minute}-{time_stamp.second}-{time_stamp.microsecond}.tiff"
            cv2.imwrite(str(datadir / outputfile), cropped_image)
        else:
            # Save the full image if no ROI is selected
            outputfile = f'{samplename}_{frame_counter:06d}.tiff'
            cv2.imwrite(str(datadir / outputfile), image)
        frame_counter += 1
    else:
        print(f"Skipping frame {frame.data.frameID} (not every {saveframe_count}th frame)")

    # Print the processing time for the current frame
    print(f"Frame processing time: {time.time() - start_time} seconds")

def select_roi_on_resized_image(frame: Frame) -> tuple:
    # Get a copy of the frame data
    image = frame.buffer_data_numpy()

    # Convert color space if necessary
    try:
        image = cv2.cvtColor(image, PIXEL_FORMATS_CONVERSIONS[frame.pixel_format])
    except KeyError:
        pass

    # Resize image for easier ROI selection
    resized_image = cv2.resize(image, (800, 600))

    # Let the user select the ROI on the resized image
    roi = cv2.selectROI("Select ROI", resized_image, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Select ROI")

    # Scale the ROI back to the original full image size
    x, y, w, h = roi
    original_height, original_width = image.shape[:2]
    scale_x = original_width / 800
    scale_y = original_height / 600
    roi_full_size = (int(x * scale_x), int(y * scale_y), int(w * scale_x), int(h * scale_y))

    return roi_full_size

def main():
    global ROI_SELECTED, roi
    with Vimba() as vimba:
        camera = vimba.camera(0)
        camera.open()

        # Reset image format
        camera.OffsetX = 0
        camera.OffsetY = 0
        camera.Height = camera.HeightMax
        camera.Width = camera.WidthMax

        # Set auto exposure and gain
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
        camera.AcquisitionFrameRateAbs = 1  # Adjust this as needed

        # Arm the camera and acquire a single frame for ROI selection
        camera.arm('SingleFrame')
        try:
            frame = camera.acquire_frame()
            roi = select_roi_on_resized_image(frame)  # Get the ROI from the user
            ROI_SELECTED = True  # Set the flag that ROI is selected
        except Exception as e:
            print(f"Error during ROI selection: {e}")
            camera.disarm()
            return

        camera.disarm()

        # Arm the camera again for continuous acquisition
        camera.arm('Continuous', display_frame)
        camera.start_frame_acquisition()
        key = 'e'

        # Main loop
        try:
            while key != 'c':
                key = input("the cam is on")
        except KeyboardInterrupt:
            print("Acquisition interrupted by user")

        camera.stop_frame_acquisition()
        camera.disarm()
        camera.close()

if __name__ == '__main__':
    main()
