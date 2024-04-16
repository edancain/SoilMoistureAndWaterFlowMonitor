from flask import Flask, Response, render_template, request, jsonify
from datetime import datetime, timedelta
#import RPi.GPIO as GPIO
import time
import json

app = Flask(__name__)

# Set GPIO mode
#GPIO.setmode(GPIO.BCM)

# Define GPIO pins
moisture_pin = 17  # Change this to the GPIO pin connected to your soil moisture sensor
flow_pin = 18      # Change this to the GPIO pin connected to your water flow meter
valve_pin = 19     # Change this to the GPIO pin connected to your water valve solenoid

# Setup GPIO pins
##GPIO.setup(moisture_pin, GPIO.IN)
#GPIO.setup(flow_pin, GPIO.IN)
#GPIO.setup(valve_pin, GPIO.OUT)

# Variables for water flow control
water_valve_status = False

# Variables for water flow calculation
flow_frequency = 0
flow_accumulator = 0
last_time = time.time()

# Lists to store data for the last 24 hours
moisture_data_24h = []
flow_data_24h = []

def read_moisture():
    # Read moisture level from sensor
    # You may need to adjust this function depending on your sensor
    #return GPIO.input(moisture_pin)
    return 17

def count_pulse(channel):
    global flow_frequency, flow_accumulator, last_time
    flow_frequency += 1
    flow_accumulator += 1
    if time.time() - last_time >= 3600:  # Update flow rate every hour
        flow_rate = flow_frequency / 7.5  # 7.5 is the number of pulses per liter (adjust as needed)
        print(f"Flow rate: {flow_rate} L/hr")
        # Reset variables
        flow_frequency = 0
        last_time = time.time()
        # Add flow rate to the list for the last 24 hours
        flow_data_24h.append((datetime.now(), flow_rate))
        # Remove old data (older than 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        flow_data_24h = [(t, f) for t, f in flow_data_24h if t >= cutoff_time]

def open_valve():
    global water_valve_status
    #GPIO.output(valve_pin, GPIO.HIGH)
    water_valve_status = True

def close_valve():
    global water_valve_status
    #GPIO.output(valve_pin, GPIO.LOW)
    water_valve_status = False

@app.route('/')
def index():
    moisture_level = read_moisture()
    return render_template('index.html', moisture_level=moisture_level)

@app.route('/stream')
def stream():
    def generate():
        while True:
            moisture_level = read_moisture()
            flow_rate = 5  # Placeholder until we have actual flow rate data
            yield 'data: {}\n\n'.format(json.dumps({'moisture_level': moisture_level, 'flow_rate': flow_rate}))
            time.sleep(1)  # Adjust the delay as needed
    return Response(generate(), mimetype='text/event-stream')

@app.route('/data')
def get_data():
    # Calculate the current flow rate
    current_flow_rate = flow_frequency / 7.5  # Assuming 7.5 pulses per liter, adjust as needed

    # Calculate the average flow rate for the period of data collection
    total_flow_rate = sum(flow[1] for flow in flow_data_24h)
    number_of_data_points = len(flow_data_24h)
    average_flow_rate = total_flow_rate / number_of_data_points if number_of_data_points > 0 else 0

    # Prepare moisture data in the format expected by Plotly
    formatted_moisture_data = [[t.strftime('%Y-%m-%d %H:%M:%S'), level] for t, level in moisture_data_24h]

    # Prepare flow data in the format expected by Plotly
    formatted_flow_data = [[t.strftime('%Y-%m-%d %H:%M:%S'), rate] for t, rate in flow_data_24h]

    return jsonify({
        'moisture_data': formatted_moisture_data,
        'flow_data': formatted_flow_data,
        'current_flow_rate': current_flow_rate,
        'average_flow_rate': average_flow_rate
    })

@app.route('/turn-on-water')
def turn_on_water():
    open_valve()
    return 'Water turned on'

@app.route('/turn-off-water')
def turn_off_water():
    close_valve()
    return 'Water turned off'

if __name__ == '__main__':
    # GPIO.add_event_detect(flow_pin, GPIO.RISING, callback=count_pulse)

    # Dummy data for testing
    import random

    # Clear the existing moisture and flow data
    moisture_data_24h.clear()
    flow_data_24h.clear()

    # Add some dummy flow rate data for testing
    current_time = datetime.now()
    for i in range(24):

        # Generate a random moisture level between 0 and 100 for each hour
        moisture_level = random.randint(0, 100)
        moisture_data_24h.append((current_time - timedelta(hours=i), moisture_level))
        
        # Generate a random flow rate between 0 and 10 for each hour
        flow_rate = random.uniform(0, 10)
        flow_data_24h.append((current_time - timedelta(hours=i), flow_rate))
    # end dummy data

    app.run(host='0.0.0.0', port=9080, debug=True)
