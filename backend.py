#!/usr/bin/python3

'''
    Networking code for ENGS21, Dartmouth College
    Allen Ma
    May 2020
'''

import eventlet
import paho.mqtt.client as mqtt
from flask import Flask, render_template, request
from flask_socketio import SocketIO
import json
import datetime
import threading
from rgbmatrix import RGBMatrix, RGBMatrixOptions, graphics
import time
from queue import Queue

# queue to pass data to led thread
q = Queue()

# dunno why I need this
eventlet.monkey_patch()

# Don't forget to change the variables for the MQTT broker!
mqtt_username = "<hash your username!>"
mqtt_password = "<hash your password!!>"
mqtt_topic = "engs21"
mqtt_web_topic = "web/engs21"
# static IP of raspberry pi
mqtt_broker_ip = "<static ip for raspberry pi>"

# flask app
app = Flask(__name__)

filename = input("LOG file what is the filename?? must be .txt")

socketio = SocketIO(app)

# Global variables
counter = 0
sensor_on = True

debug = False


'''
    Flask stuff
'''
@app.route("/")
def main():
    return render_template("main_mqttflask.html")


@socketio.on('publish')
def handle_publish(json_str):
    data = json.loads(json_str)
    client.publish(data['topic'], data['message'], data['qos'])

''' PATHO MQTT callback '''
def on_message(client, userdata, message):

    topic = message.topic
    msg_txt = message.payload.decode()

#     print("message received topic: {}, txt: {}".format(topic, msg_txt))
#
     # both the web/engs21 and engs21 provide the same message
    counter_logic(topic, msg_txt)

    data = dict(
        count=counter,
        sensor_on=sensor_on,
    )


    # update the count immediately
    socketio.emit('mqtt_update', data=data)

    # update the LED
    q.put(counter)

    with open(filename, "a") as f:
        print("{0}, {1}, {2}, {3}".format(datetime.datetime.now(), counter, msg_txt, topic), file=f)

''' PATHO MQTT CALLBACK '''
def on_connect(client, userdata, flags, rc):
    print("starting MQTT subscriber")
    # subscribe to topics
    client.subscribe('engs21')
    client.subscribe('web/engs21')

''' PATHO MQTT CALLBACK '''
def on_disconnect(client, userdata):
    client.loop_stop()

''' Utility function '''
def counter_logic(topic, msg_txt):

    global counter
    global sensor_on

    if topic == "web/engs21":
        if msg_txt == "zero":
            counter = 0
        elif msg_txt == "up":
            counter += 1
        elif msg_txt == "down":
            counter -= 1
        elif msg_txt == "toggle":
            sensor_on = not sensor_on
        elif msg_txt == "connect":
            print("connection to web dashboard")
        else:
            if debug:
                print("msg_txt not recognized: ", msg_txt)

    if topic == "engs21" and sensor_on:
        if msg_txt == "up":
            counter += 1
        elif msg_txt == "down":
            # allow negative for now
            counter -= 1
        else:
            if debug:
                print("msg_txt not recognized: ", msg_txt)


''' Threading stuff '''


class LEDThread(threading.Thread):

	def __init__(self, queue, args=(), kwargs=None):
		threading.Thread.__init__(self, args=(), kwargs=None)
		self.queue = queue
		self.daemon = True
		self.options = RGBMatrixOptions()
		self.options.rows = 32
		self.options.cols = 64
		self.options.chain_length = 1
		self.options.parallel = 1
		self.options.hardware_mapping = "adafruit-hat"
		self.matrix = RGBMatrix(options = self.options)
		self.font = graphics.Font()
		self.font.LoadFont("./fonts/10x20.bdf")
		self.red = graphics.Color(255, 0, 0)
		self.blue = graphics.Color(255, 255, 255)
		self.green = graphics.Color(0, 255, 0)
		self.offscreen_canvas = self.matrix.CreateFrameCanvas()

	def run(self):
		count_str = str(counter)
		graphics.DrawText(self.matrix, self.font, self.options.rows // 2, self.options.cols // 2, self.blue, count_str)

		while True:
			val = self.queue.get()
			self.updateLED(val)

	def updateLED(self, val):
		self.offscreen_canvas.Clear()
		count_str = str(val)
		if val >= 10:
			graphics.DrawText(self.offscreen_canvas, self.font, self.options.rows // 2, self.options.cols // 2 - 14, self.red, "STOP")
		else:
			graphics.DrawText(self.offscreen_canvas, self.font, self.options.rows // 2, self.options.cols // 2 - 14, self.green, "GO")
		graphics.DrawText(self.offscreen_canvas, self.font, self.options.rows // 2 + 7, self.options.cols // 2, self.blue, count_str)
		self.offscreen_canvas = self.matrix.SwapOnVSync(self.offscreen_canvas)



''' MQTT stuff '''

def mqtt_client_startup():
    # Here, we are telling the client which functions are to be run
    # on connecting, and on receiving a message
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    # Once everything has been set up, we can (finally) connect to the broker
    # 1883 is the listener port that the MQTT broker is using
    client.connect(mqtt_broker_ip, 1883)

    # Once we have told the client to connect, let the client object run itself
    # this creates a new thread
    client.loop_start()




'''
    MQTT stuff
'''
# start the mqtt_thread
client = mqtt.Client()
# Set the username and password for the MQTT client
client.username_pw_set(mqtt_username, mqtt_password)
mqtt_client_startup()

# start a new thread to run the led display
led_thread = LEDThread(q)
led_thread.start()


# set your desired port here
if __name__ == '__main__':
    socketio.run(app, host=mqtt_broker_ip, port=8099, use_reloader=False, debug=True)
