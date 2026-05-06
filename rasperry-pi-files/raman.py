from gpiozero import OutputDevice
import threading
import seabreeze.spectrometers as sb
import numpy as np
import pandas as pd
import time
import os



# Connect laser control signal to GPIO port 23
signal = OutputDevice(23)

def power_laser():
    try:
        print("Activating Laser for 30 second integration time")
        signal.on()
        
        time.sleep(15)
        
        print("Deactivating Laser")
        signal.off()
        
    except Exception as e:
                log(f"An error occurred: {e}")
        
    except KeyboardInterrupt:
        # Allows you to stop the script safely with Ctrl+C
        print("Program stopped.")
        
def start_integration():
    devices = sb.list_devices()
    if not devices:
        print("Error: No Ocean Optics device detected.")
        exit()

        spec = sb.Spectrometer(devices[0])

    try:
        # Set Integration Time to 12 Seconds
        
        int_time_us = 12_000_000
        spec.integration_time_micros(int_time_us)
        
        print(f"Integration set to 12s. Capturing spectrum...")
        print("Note: The program will appear paused while the sensor dwells.")

        # Capture Data
        # The .intensities() call blocks the script until the 12s is up
        wavelengths = spec.wavelengths()
        intensities = spec.intensities()

        #Extract Peak Values
        peak_idx = np.argmax(intensities)
        peak_x = wavelengths[peak_idx]
        peak_y = intensities[peak_idx]

        print("-" * 30)
        print(f"Peak Wavelength: {peak_x:.3f} nm")
        print(f"Peak Intensity:  {peak_y:.2f} counts")
        print("-" * 30)

        #Export to CSV
        filename = "peak_data_log.csv"
        output_data = {
            'Wavelength_nm': [round(peak_x, 3)],
            'Intensity_Counts': [round(peak_y, 2)]
        }
        
        df = pd.DataFrame(output_data)
        
        # Check if file exists to determine if we need a header
        file_exists = os.path.isfile(filename)
        df.to_csv(filename, mode='a', index=False, header=not file_exists)
        
        print(f"Success! Data appended to {filename}")

    finally:
        # Always close the connection to prevent hardware hang-ups
        spec.close()
        print("Spectrometer connection closed.")
    
def analysis():
    try:
        laser_thread = threading.Thread(target=power_laser)
        
        laser_thread.start()
        
        start_integration()
        
        laser_thread.join()
            
            
                
    except Exception as e:
                log(f"An error occurred: {e}")
        
if __name__ == "__main__":
    analysis()
