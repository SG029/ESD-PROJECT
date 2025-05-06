#include <SPI.h>
#include <RH_RF95.h>

// Pin mapping (same as receiver)
#define RFM95_CS     PA4  // NSS
#define RFM95_RST    PA2  // Optional
#define RFM95_INT    PB0  // DIO0

#define RF95_FREQ    868.0  // Must match receiver

RH_RF95 rf95(RFM95_CS, RFM95_INT);

void setup() {
  pinMode(RFM95_RST, OUTPUT);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  Serial.begin(9600);
  delay(100);

  // Manual reset LoRa module
  digitalWrite(RFM95_RST, LOW);
  delay(10);
  digitalWrite(RFM95_RST, HIGH);
  delay(10);

  if (!rf95.init()) {
    Serial.println("LoRa init failed. Check wiring!");
    while (1);
  }
  Serial.println("LoRa init OK.");

  if (!rf95.setFrequency(RF95_FREQ)) {
    Serial.println("Failed to set frequency");
    while (1);
  }

  rf95.setTxPower(13, false); // TX power: 5 to 23 dBm
  Serial.println("LoRa Transmitter Ready");
}

void loop() {
  static int counter = 1;
  if (counter <= 30) {
    String message = "Data: " + String(counter);
    Serial.print("Sending: ");
    Serial.println(message);

    rf95.send((uint8_t *)message.c_str(), message.length());
    rf95.waitPacketSent();

    counter++;
  }

  delay(2000); // Wait 2 seconds between messages
}
