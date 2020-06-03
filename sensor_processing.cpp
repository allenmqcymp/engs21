/*
 * Allen Ma, Musab Shakeel, Michael Cullen, Kane Hall
 * ENGS21 Dartmouth College
 * Spring 2020
 */
//#include <Bounce2.h> // Used for "debouncing" the pushbutton
#include <ESP8266WiFi.h> // Enables the ESP8266 to connect to the local network (via WiFi)
#include <PubSubClient.h> // Allows us to connect to, and publish to the MQTT broker

const int ledPin = 0; // This code uses the built-in led for visual feedback that the button has been pressed
const int sensorPin = 13; // Connect your button to pin #13

// WiFi
// Make sure to update this for your own WiFi network!
// use secrets.h to hash the password and username
const char* ssid = "<wifi ssid>";
const char* wifi_password = "<wifi-password>";

// MQTT
// Make sure to update this for your own MQTT Broker!
// not sure about this
const char* mqtt_server = "<insert MQTT server address>";
const char* mqtt_topic = "engs21";
const char* mqtt_username = "<mqtt username>";
const char* mqtt_password = "<mqtt password>";
// The client id identifies the ESP8266 device. Think of it a bit like a hostname (Or just a name, like Greg).
const char* clientID = "entrance_sensor";

// Initialise the Pushbutton Bouncer object
//Bounce bouncer = Bounce();

// Initialise the WiFi and MQTT Client objects
WiFiClient wifiClient;
PubSubClient client(mqtt_server, 1883, wifiClient); // 1883 is the listener port for the Broker

void setup() {
  pinMode(ledPin, OUTPUT);
  pinMode(sensorPin, INPUT);

  // Switch the on-board LED off to start with
  digitalWrite(ledPin, HIGH);

  // Setup pushbutton Bouncer object
//  bouncer.attach(sensorPin);
//  bouncer.interval(100);

  // Begin Serial on 115200
  // Remember to choose the correct Baudrate on the Serial monitor!
  // This is just for debugging purposes
  Serial.begin(9600);

  Serial.print("Connecting to ");
  Serial.println(ssid);

  // Connect to the WiFi
  WiFi.begin(ssid, wifi_password);

  // Wait until the connection has been confirmed before continuing
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  // Debugging - Output the IP Address of the ESP8266
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

  // Connect to MQTT Broker
  // client.connect returns a boolean value to let us know if the connection was successful.
  // If the connection is failing, make sure you are using the correct MQTT Username and Password (Setup Earlier in the Instructable)
  if (client.connect(clientID, mqtt_username, mqtt_password)) {
    Serial.println("Connected to MQTT Broker!");
  }
  else {
    Serial.println("Connection to MQTT Broker failed...");
  }
  
}

int state = 0;
int val;
int falling_edge_time = 0;
int rising_edge_time = 0;
int time_since_last_high;

void loop() {
  // Update button state
  // This needs to be called so that the Bouncer object can check if the button has been pressed

  val = digitalRead(sensorPin);

  if (state == 0 && val == HIGH) {
    rising_edge_time = millis();
    time_since_last_high = rising_edge_time - falling_edge_time;
    state = 1;

    if (time_since_last_high > 300) {

        // Turn light on when button is pressed down
        // (i.e. if the state of the button rose from 0 to 1 (not pressed to pressed))
        digitalWrite(ledPin, LOW);
    
        // PUBLISH to the MQTT Broker (topic = mqtt_topic, defined at the beginning)
        // Here, "Button pressed!" is the Payload, but this could be changed to a sensor reading, for example.
        if (client.publish(mqtt_topic, "up")) {
          Serial.println("Debug message: Sensor tripped!!");
        }
        // Again, client.publish will return a boolean value depending on whether it succeeded or not.
        // If the message failed to send, we will try again, as the connection may have broken.
        else {
          Serial.println("Message failed to send. Reconnecting to MQTT Broker and trying again");
          client.connect(clientID, mqtt_username, mqtt_password);
          delay(10); // This delay ensures that client.publish doesn't clash with the client.connect call
          client.publish(mqtt_topic, "up");
        }
    }
  }
  else if (state == 1 && val == LOW) {
//    // Turn light off when button is released
//    // i.e. if state goes from high (1) to low (0) (pressed to not pressed)
//    digitalWrite(ledPin, HIGH);
      state = 0;
      falling_edge_time = millis();    
  }
}
