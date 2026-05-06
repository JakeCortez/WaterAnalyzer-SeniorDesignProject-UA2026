import socket
import os
import threading
import phosphates
import heavy_metal
import raman
import plotdata
import motor
from datetime import datetime
import time

base_dir = os.path.dirname(os.path.abspath(__file__))
message_to_send = os.path.join(base_dir, "data.txt")
file_to_send = os.path.join(base_dir, "contaminants_plot.png")

def log(message):
    # Adds a timestamp to every server-side print statement
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    
def start_esp32():
    log("Starting ESP32 communication...")
    heavy_metal.run_analysis_session()
    log("Heavy Metal Analysis complete.")
    
def start_phosphates():
    log("Starting phosphate Analysis...")
    motor.dip()
    phosphates.analysis()
    log("Phosphate Analysis Complete.")
    
def start_raman():
    log("Starting raman Analysis...")
    raman.analysis()
    log("Raman Analysis Complete.")

    
def start_server():
    host = '0.0.0.0' 
    port = 65432
    socket.setdefaulttimeout(600) # wait up to ten minutes for a response

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        log(f"Server listening on {host}:{port}")
        
        while True:
            conn, addr = s.accept()
            with conn:
                log(f"Connected by {addr}")
                try:
                    data = conn.recv(1024).decode('utf-8')
                    
                    if data == "Download":
                        if os.path.exists(file_to_send):
                            log(f"Sending {file_to_send}...")
                            with open(file_to_send, 'rb') as f:
                                conn.sendall(f.read())
                            log("File transfer complete.")
                        else:
                            log("Error: File not found.")
                            conn.sendall(b"ERROR: File not found")
                    
                    elif data == "Start_Analysis":
                        log("Analysis signal received. Spawning background threads...")
                        conn.sendall(b"Analysis in Progress...")
                        # Define the threads
                        t1 = threading.Thread(target=start_esp32)
                        t2 = threading.Thread(target=start_phosphates)
                        t3 = threading.Thread(target=start_raman)
                        
                        # Start all threads in parallel
                        t1.start()
                        t2.start()
                        t3.start()
                        
                        # Wait for all threads to complete
                        log("Waiting for all analysis threads to finish...")
                        t1.join()
                        t2.join()
                        t3.join()
                        
                        
                        log("All analyses complete. Sending data to client.")
                        
                        
                        
                        # Now send the actual data file (or a success message)
                        if os.path.exists(message_to_send):
                            with open(message_to_send, 'rb') as f:
                                conn.sendall(f.read())
                        else:
                            conn.sendall(b"Analysis Complete but invalid file.")
                        
                    else:
                        log(f"Unrecognized command")
                        conn.sendall(b"Error: Invalid Command")
                except Exception as e:
                    log(f"An error occurred: {e}")

if __name__ == "__main__":
    start_server()
