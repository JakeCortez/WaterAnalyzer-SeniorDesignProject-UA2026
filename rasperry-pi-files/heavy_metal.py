import os
import time
import requests
import csv
import json
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


# Network Settings
SSID = "Insta Ramen"
PASSWORD = "12345678" 
ESP32_BASE_URL = "http://192.168.4.1"

OUTPUT_FILE = "heavy_metals.csv"

def read_text(path):
   url = ESP32_BASE_URL + path
   print(f"GET {url}")
   with urlopen(url, timeout=10) as response:
       text = response.read().decode("utf-8")
   print(text.strip())
   return text
def read_json(path):
   text = read_text(path)
   return json.loads(text)

def download_csv(path, output_file):
   with urlopen(ESP32_BASE_URL + path, timeout=10) as response:
       text = response.read().decode("utf-8")

   with open(output_file, "w", newline="") as file:
       file.write(text)

   return list(csv.reader(text.splitlines()))

def set_wifi(state):
    """state: 'up' to connect with password, 'down' to disconnect"""
    if state == 'up':
        print(f"Connecting to {SSID}...")
        # This command connects using the password
        cmd = f"nmcli device wifi connect '{SSID}' password '{PASSWORD}'"
        os.system(cmd)
    else:
        print(f"Disconnecting from {SSID}...")
        # This drops the specific connection
        cmd = f"nmcli connection down '{SSID}'"
        os.system(cmd)
        cmd = f"nmcli connection delete '{SSID}'"
        os.system(cmd)
    
    time.sleep(6) # Handshaking buffer
            
def run_analysis_session():
   try:
       set_wifi('up')
       
       print("Checking ESP32 connection...")
       read_text("/ping")

       print("Starting CV run on ESP32...")
       read_json("/run_cv")

       while True:
           status = read_json("/status")
           state = status.get("status")
           remaining = status.get("seconds_remaining", 0)

           if state == "complete":
               break

           print(f"Running CV: {remaining} seconds remaining")
           time.sleep(2)

       rows = download_csv("/data.csv", OUTPUT_FILE)
       print(f"Saved {OUTPUT_FILE}")
       print(rows)


   except HTTPError as error:
       print(f"ESP32 returned HTTP error {error.code}: {error.reason}")
       print(error.read().decode("utf-8", errors="replace"))
   except URLError as error:
       print("Could not reach the ESP32.")
       print("Make sure the Pi is connected to the ESP32 Wi-Fi network.")
       print(f"Details: {error.reason}")
   except TimeoutError:
       print("Timed out while waiting for the ESP32.")


   finally:
        # 5. Disconnect to free up the Pi's WiFi
        set_wifi('down')
        print("Connection closed. Pi is back to idle.")

if __name__ == "__main__":
    run_analysis_session()
    

