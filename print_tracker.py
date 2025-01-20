import requests
import time
import subprocess
from pathlib import Path


def is_usb_drive_mounted():
    try:
        # Execute the mount command and decode the output
        output = subprocess.check_output(['mount']).decode('utf-8')
        return "/media/robast/USB_Drive" in output
    except subprocess.CalledProcessError:
        # If the mount command fails, assume the drive is not mounted
        return False
        
def print_tracker():
    while is_usb_drive_mounted() == True:
        try:
            response = requests.get("http://10.10.13.2:8080/img")
            current_time = time.strftime("%Y-%m-%d_%H_%M_%S")
            file_name = f"3dd_{current_time}.jpg"
            # Create a new folder with the current date as the name
            folder_name = time.strftime("%Y-%m-%d")
            folder_path = f"/media/robast/USB_Drive/imgs/{folder_name}"
            Path(folder_path).mkdir(parents=True, exist_ok=True)
            with open(f"{folder_path}/{file_name}", "wb") as f:
                f.write(response.content)
        except Exception as e:
            with open("/home/robast/Robast/oak_server/error.log", "a") as f:
                f.write(f"Error: {str(e)}\n")
            time.sleep(2)
            continue
        time.sleep(5)
    print("USB Drive is not mounted")

        
if __name__ == "__main__":
    print_tracker()
    

