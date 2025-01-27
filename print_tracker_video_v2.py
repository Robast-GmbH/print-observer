import requests
import time
import subprocess
from pathlib import Path
import cv2
import os
from itertools import chain
import numpy as np

x, y = 1820, 705 #Auswertung des Farbtons an dieser Position
fps = 20
folder_name = "Print_Tracker"
range_red = list(chain(range(0, 21), range(340, 361))) # rote Farbwerte (HSV-Modell)
thr = 7 #Threshold für die Anzahl der roten Pixel

def is_usb_drive_mounted():
    try:
        # Execute the mount command and decode the output
        output = subprocess.check_output(['mount']).decode('utf-8')
        return "/media/robast/USB_Drive" in output
    except subprocess.CalledProcessError:
        # If the mount command fails, assume the drive is not mounted
        return False
        
def print_tracker():
    
    print_started = False
    printer_homed = False # Um zu erkennen, dass ein Druck gestartet wird, muss sich der Drucker zuvor in der gehomten Position befinden
    n_mov = 0 # Anzahl der Bilder in denen eine Bewegung erkannt wurde
    n_not_mov = 0 # Anzahl der Bilder in denen keine Bewegung erkannt wurde

    while is_usb_drive_mounted() == True:
        try:
            response = requests.get("http://10.10.13.2:8080/img")
            current_time = time.strftime("%Y-%m-%d_%H_%M_%S")
            file_name = f"3dd_{current_time}.jpg"
            folder_path = f"/media/robast/USB_Drive/imgs/{folder_name}"
            Path(folder_path).mkdir(parents=True, exist_ok=True)
            with open(f"{folder_path}/{file_name}", "wb") as f:
                f.write(response.content)
            img = cv2.imread(f"/media/robast/USB_Drive/imgs/{folder_name}/{file_name}")
            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

            red_pixel = 0 # Anzahl der roten Pixel in einem Bereich von 3x3 Pixeln

            mean_brightness = np.mean(img)
            print(f"Mean brightness: {mean_brightness}")

            if mean_brightness >= 50:

                # Bestimmung der Anzahl an roten Pixeln
                for x_i in range(x-1, x+2):
                    for y_i in range(y-1, y+2):
                        hue, saturation, value = hsv_img[y_i, x_i]
                        if hue in list(range_red):
                            red_pixel += 1

                # Zählen der Bilder, in denen eine Bewegung erkannt wurde
                if red_pixel < thr:
                    n_mov += 1
                    n_not_mov = 0
                    print(f"Bewegung erkannt ({n_mov}x)")  

                # Zählen der Bilder, in denen keine Bewegung erkannt wurde
                elif red_pixel >= thr:
                    n_not_mov += 1
                    n_mov = 0
                    print(f"Keine Bewegung erkannt ({n_not_mov}x)")  

                # Es wurde keine Bewegung erkannt und der Druck wurde noch nicht gestartet -> Das aktuelle Bild wird gelöscht
                if red_pixel >= thr and print_started == False:
                    os.remove(f"/media/robast/USB_Drive/imgs/{folder_name}/{file_name}") 
                    print("Bild wird gelöscht.")
                    printer_homed = True

                # Es hat noch kein Homing stattgefunden -> Das aktuelle Bild wird gelöscht
                elif red_pixel < thr and print_started == False and printer_homed == False:
                    print("Es hat noch kein Homing stattgefunden. Bild wird gelöscht.")

                # Es wurde eine Bewegung in weniger als 5 Bildern hintereinander erkannt -> Es werden alle Bilder bis auf die letzten 4 gelöscht
                elif red_pixel < thr and print_started == False and printer_homed == True and n_mov < 5:
                        img_file = sorted([f for f in os.listdir(folder_path) if f.endswith(('.PNG','.jpg'))])
                        if len(img_file) >= 4:
                            img_file = img_file[:-4]
                            for file in img_file:
                                os.remove(f"/media/robast/USB_Drive/imgs/{folder_name}/{file}")
                
                # Es wurde eine Bewegung in mindestens 5 Bildern hintereinander erkannt -> Die Bilder werden nicht gelöscht, der Druck wurde gestartet
                elif red_pixel < thr and print_started == False and printer_homed == True and n_mov >= 5:
                    print_started = True
                    n_not_mov = 0
                    print("Der Druck wurde gestartet.")

                elif red_pixel < thr and print_started == True and printer_homed == True and n_mov >= 5:
                    print("Der Druck läuft. Das Bild wird gespeichert.")

                # Es wurde keine Bewegung in mindestens 5 Bildern hintereinander erkannt -> Der Druck wurde beendet, das Video wird abgespeichert und die Bilder gelöscht
                elif red_pixel >= thr and print_started == True and n_not_mov >= 5:
                    n_not_mov = 0
                    print("Der Druck wurde beendet.")
                    img_file = sorted([f for f in os.listdir(folder_path) if f.endswith(('.PNG','.jpg'))])
                    print(img_file)
                    first_img = cv2.imread(os.path.join(folder_path,img_file[0]))
                    height, width, _ = first_img.shape
                    video_writer = cv2.VideoWriter("/media/robast/USB_Drive/imgs/Zeitrafferaufnahme_" + current_time + ".avi", cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))

                    for file in img_file:

                        img_path = os.path.join(folder_path, file)
                        img = cv2.imread(img_path)
                        img = cv2.resize(img, (width, height))

                        if img is not None:
                            video_writer.write(img)
                            os.remove(f"/media/robast/USB_Drive/imgs/{folder_name}/{file}")
                            print("Bild hinzugefügt")
                        else:
                            print("Fehler: Ungültiges Bild.")

                    # Writer freigeben
                    video_writer.release()
                    print_started = False
                    print("Das Video wurde abgespeichert und die Bilder gelöscht.")

            else:
                os.remove(f"/media/robast/USB_Drive/imgs/{folder_name}/{file_name}")

        except Exception as e:
            with open("/home/robast/Robast/oak_server/error.log", "a") as f:
                f.write(f"Error: {str(e)}\n")
            time.sleep(2)
            print("Hier")
            continue

        time.sleep(5)
    print("USB Drive is not mounted")


if __name__ == "__main__":
    print_tracker()