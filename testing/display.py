
from azure.storage.blob import BlobClient
import re
import os
from dotenv import load_dotenv
load_dotenv()


def get_blob_data():

    con_str = os.getenv('con_str')


    blob = BlobClient.from_connection_string(conn_str=con_str, container_name="bustimescontainer", blob_name="bus_times.json")

    blob_data = blob.download_blob()
    blob_contents = blob_data.readall().decode("utf-8")
    cleaned_text = blob_contents.strip()[1:-1]  # Remove the outer square brackets
    lines = cleaned_text.split('",')

    bus_times = []
    for line in lines:
        # Clean each line: Remove leading/trailing spaces and quotes
        line = line.strip().replace('"', '').strip().split(' ')
        bus_times.append(line[-1])
        

    return bus_times


import time
import board
import digitalio
import adafruit_ssd1306


i2c = board.I2C()  # uses board.SCL and board.SDA

# Create the SSD1306 OLED display object
oled = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c)



def scroll_text_show_OLED(oled, text ):
    first_bus = text[0]
    second_bus = text[1]
    third_bus = text[2]
    fourth_bus = text[3]

    oled.text(first_bus, 0, 0)
    scrolling_row = second_bus + ' ' + third_bus + ' ' + fourth_bus
    
    scrolling_row_length = len(scrolling_row) * 6 #check number of pixels is 6 per char

    for i in range (-scrolling_row_length, -128):

        
        oled.text(scrolling_row, i, 16)
        oled.show()
        time.sleep(0.05)


while True:

    text = get_blob_data()
    scroll_text_show_OLED(oled=oled,text=text)




