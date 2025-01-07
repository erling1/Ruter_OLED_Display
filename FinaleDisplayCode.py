import lgpio
import requests
from datetime import datetime
import time
import threading

# --- GPIO Pin Configurations for LCD ---
RS = 26
E = 19
D4 = 13
D5 = 6
D6 = 5
D7 = 11

CHIP = 0  # GPIO chip, 0 for the default chip on Raspberry Pi
HANDLE = lgpio.gpiochip_open(CHIP)  # Open GPIO chip

# --- Initialize GPIO Pins ---
def setup_gpio():
    # Set all the pins as outputs
    lgpio.gpio_claim_output(HANDLE, RS)
    lgpio.gpio_claim_output(HANDLE, E)
    lgpio.gpio_claim_output(HANDLE, D4)
    lgpio.gpio_claim_output(HANDLE, D5)
    lgpio.gpio_claim_output(HANDLE, D6)
    lgpio.gpio_claim_output(HANDLE, D7)

# --- LCD Functions ---
def pulse_enable():
    lgpio.gpio_write(HANDLE, E, 0)
    time.sleep(0.001)
    lgpio.gpio_write(HANDLE, E, 1)
    time.sleep(0.001)
    lgpio.gpio_write(HANDLE, E, 0)
    time.sleep(0.001)

def send_command(cmd):
    lgpio.gpio_write(HANDLE, RS, 0)  # RS = 0 for command mode
    lgpio.gpio_write(HANDLE, D4, cmd & 0x10)
    lgpio.gpio_write(HANDLE, D5, cmd & 0x20)
    lgpio.gpio_write(HANDLE, D6, cmd & 0x40)
    lgpio.gpio_write(HANDLE, D7, cmd & 0x80)
    pulse_enable()
    lgpio.gpio_write(HANDLE, D4, cmd & 0x01)
    lgpio.gpio_write(HANDLE, D5, cmd & 0x02)
    lgpio.gpio_write(HANDLE, D6, cmd & 0x04)
    lgpio.gpio_write(HANDLE, D7, cmd & 0x08)
    pulse_enable()

def send_data(data):
    lgpio.gpio_write(HANDLE, RS, 1)  # RS = 1 for data mode
    lgpio.gpio_write(HANDLE, D4, data & 0x10)
    lgpio.gpio_write(HANDLE, D5, data & 0x20)
    lgpio.gpio_write(HANDLE, D6, data & 0x40)
    lgpio.gpio_write(HANDLE, D7, data & 0x80)
    pulse_enable()
    lgpio.gpio_write(HANDLE, D4, data & 0x01)
    lgpio.gpio_write(HANDLE, D5, data & 0x02)
    lgpio.gpio_write(HANDLE, D6, data & 0x04)
    lgpio.gpio_write(HANDLE, D7, data & 0x08)
    pulse_enable()

def lcd_init():
    send_command(0x33)  # Initialize
    send_command(0x32)  # 4-bit mode
    send_command(0x28)  # 2 lines, 5x8 font
    send_command(0x0C)  # Display on, cursor off
    send_command(0x06)  # Auto-increment cursor
    send_command(0x01)  # Clear display

def lcd_clear():
    send_command(0x01)
    time.sleep(0.002)

def lcd_display_text(text, line=1):
    if line == 1:
        send_command(0x80)  # Move to the first line
    elif line == 2:
        send_command(0xC0)  # Move to the second line
    
    for char in text[:16]:  # LCD can show 16 chars per line
        send_data(ord(char))

# --- Real-Time Bus Data Fetching ---
real_time_url = "https://api.entur.io/journey-planner/v3/graphql"
headers = {"Content-Type": "application/json", 'ET-Client-Name': 'Erling-Project'}
query = """
{
  trip(
    from: {
      place: "NSR:StopPlace:5620",
      name: "Furuset skole, Oslo"
    },
    to: {
      place: "NSR:StopPlace:59516",
      name: "Helsfyr, Oslo"
    },
    numTripPatterns: 4
  ) {
    tripPatterns {
      legs {
        line {
          publicCode
        }
        fromEstimatedCall {
          expectedDepartureTime
        }
      }
    }
  }
}
"""

bus_times = []
bus_names = {
    '100': '100 Oslo Bussterminal',
    '110': '110 Oslo Bussterminal',
    '300': '300 Blystadlia',
    '2N': '2N'
}

def get_data():
    try:
        response = requests.post(real_time_url, json={"query": query}, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Data Fetch Error: {e}")
    return None

def update_bus_times():
    global bus_times
    while True:
        data = get_data()
        if data:
            bus_times.clear()
            try:
                for tripPattern in data['data']['trip']['tripPatterns']:
                    for leg in tripPattern['legs']:
                        line = leg['line']['publicCode']
                        real_time_departure = leg['fromEstimatedCall']['expectedDepartureTime']
                        parsed_time = datetime.fromisoformat(real_time_departure)
                        formatted_time = parsed_time.strftime("%H:%M")
                        bus_times.append(bus_names.get(line, "Unknown") + ' ' + formatted_time)
            except Exception as e:
                print(f"Parsing Error: {e}")
        time.sleep(60)

# --- Display Thread ---
def display_bus_times():
    while True:
        if bus_times:
            lcd_clear()
            lcd_display_text(bus_times[0], line=1)
            if len(bus_times) > 1:
                lcd_display_text(bus_times[1], line=2)
        else:
            lcd_clear()
            lcd_display_text("No Data", line=1)
        time.sleep(5)

# --- Main Program ---
if __name__ == "__main__":
    try:
        setup_gpio()
        lcd_init()
        threading.Thread(target=update_bus_times, daemon=True).start()
        threading.Thread(target=display_bus_times, daemon=True).start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        lgpio.gpiochip_close(HANDLE)  # Close GPIO handle on exit
