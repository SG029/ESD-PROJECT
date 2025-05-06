#include <Ticker.h>
Ticker pulseTicker;

#include <Wire.h>
#include <Adafruit_MLX90614.h>
#include <Adafruit_BMP085.h>
#include "RTClib.h"
#include <OneWire.h>
#include <DallasTemperature.h>

#define MUX_ADDR     0x70
#define MLX_ADDR     0x5A
#define ECG_PIN      A0
#define ECG_LO_PLUS  D5
#define ECG_LO_MINUS D6
#define DS18B20_BUS  D3
#define PULSE_PIN    D7
#define BLINK_PIN    LED_BUILTIN
#define HAPTIC_PIN   D8

Adafruit_MLX90614 mlx;
RTC_DS1307 rtc;
Adafruit_BMP085 bmp;
OneWire oneWire(DS18B20_BUS);
DallasTemperature sensors(&oneWire);

float surfacePressure = 101325.0;
float lastPressure = 0.0;
const float pressureThreshold = 5.0;

int lastBPM = -1;
const int bpmThreshold = 5;

volatile int BPM;
volatile int Signal;
volatile int IBI = 600;
volatile boolean Pulse = false;
volatile boolean QS = false;

volatile int rate[10];
volatile unsigned long sampleCounter = 0;
volatile unsigned long lastBeatTime = 0;
volatile int P = 512;
volatile int T = 512;
volatile int thresh = 525;
volatile int amp = 100;
volatile boolean firstBeat = true;
volatile boolean secondBeat = false;

float maxDepth = 0.0;
bool isBottom = false;
unsigned long bottomStart = 0;
bool decoAlertShown = false;
bool inDecompressionPhase = false;
int decoStopTimeMin = 0;
unsigned long decoStart = 0;
String decoMessage = "";

void tcaselect(uint8_t bus) {
  if (bus > 7) return;
  Wire.beginTransmission(MUX_ADDR);
  Wire.write(1 << bus);
  Wire.endTransmission();
  delayMicroseconds(50);
}

void scanChannel(uint8_t bus) {
  tcaselect(bus);
  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    if (Wire.endTransmission() == 0) {
      Serial.print("0x"); Serial.print(addr, HEX); Serial.print(" ");
    }
  }
  Serial.println();
}

void setup() {
  Serial.begin(115200);
  Wire.begin();

  pinMode(ECG_LO_PLUS, INPUT);
  pinMode(ECG_LO_MINUS, INPUT);
  pinMode(BLINK_PIN, OUTPUT);
  pinMode(HAPTIC_PIN, OUTPUT);
  digitalWrite(HAPTIC_PIN, LOW);

  scanChannel(1); tcaselect(1);
  if (!mlx.begin(MLX_ADDR)) {
    Serial.println("MLX90614 not found");
    while (1);
  }

  scanChannel(0); tcaselect(0);
  if (!rtc.begin()) {
    Serial.println("RTC not found");
    while (1);
  }

  scanChannel(2); tcaselect(2);
  if (!bmp.begin()) {
    Serial.println("BMP180 not found");
    while (1);
  }
  surfacePressure = bmp.readPressure();
  lastPressure = surfacePressure;

  scanChannel(3); tcaselect(3);
  sensors.begin();

  pinMode(PULSE_PIN, INPUT);
  interruptSetup();
}

void loop() {
  tcaselect(1);
  float amb = mlx.readAmbientTempC();
  float obj = mlx.readObjectTempC();

  tcaselect(0);
  DateTime now = rtc.now();

  tcaselect(2);
  float pressure = bmp.readPressure();

  float depth = (pressure - surfacePressure) / 9806.65;
  depth = max(depth, 0.0f);

  tcaselect(3);
  sensors.requestTemperatures();
  float Celsius = sensors.getTempCByIndex(0);

  bool ecgConnected = !(digitalRead(ECG_LO_PLUS) == 1 || digitalRead(ECG_LO_MINUS) == 1);
  int ecgValue = ecgConnected ? analogRead(ECG_PIN) : -1;

  int bpmToPrint = QS ? BPM : -1;
  int signalToPrint = Signal;

  if (bpmToPrint > 0 && abs(bpmToPrint - lastBPM) > bpmThreshold) {
    digitalWrite(HAPTIC_PIN, HIGH); delay(200); digitalWrite(HAPTIC_PIN, LOW);
    lastBPM = bpmToPrint;
  }

  QS = false;

  if (abs(pressure - lastPressure) > pressureThreshold) {
    digitalWrite(HAPTIC_PIN, HIGH); delay(200); digitalWrite(HAPTIC_PIN, LOW);
    Serial.println(">>> DECO STOP TRIGGERED: Sudden Pressure Change <<<");

    Serial.print("AmbTemp: "); Serial.print(amb); Serial.print(" C, ");
    Serial.print("ObjTemp: "); Serial.print(obj); Serial.print(" C, ");
    Serial.print("Pressure: "); Serial.print(pressure); Serial.print(" Pa, ");
    Serial.print("Depth: "); Serial.print(depth, 2); Serial.print(" m, ");
    Serial.print("WaterTemp: ");
    Serial.print(Celsius != DEVICE_DISCONNECTED_C ? String(Celsius) : "NaN"); Serial.print(" C, ");
    Serial.print("ECG: "); Serial.print(ecgValue); Serial.print(", ");
    Serial.print("BPM: "); Serial.print(bpmToPrint); Serial.print(", ");
    Serial.print("Signal: "); Serial.print(signalToPrint); Serial.print(", ");
    Serial.print("DECO_MSG: "); Serial.println(decoMessage);

    for (int i = 0; i < 3; i++) {
      digitalWrite(BLINK_PIN, HIGH); digitalWrite(HAPTIC_PIN, HIGH); delay(200);
      digitalWrite(BLINK_PIN, LOW);  digitalWrite(HAPTIC_PIN, LOW);  delay(200);
    }
  }

  lastPressure = pressure;

  if (depth > 10.0) {
    if (!isBottom) {
      isBottom = true;
      bottomStart = millis();
      maxDepth = depth;
      decoMessage = "";
      decoAlertShown = false;
    } else {
      if (depth > maxDepth) maxDepth = depth;
    }
  } else {
    if (isBottom) {
      isBottom = false;
      unsigned long bottomDurationMin = (millis() - bottomStart) / 60000;

      if (maxDepth > 18 && bottomDurationMin > 30) {
        decoStopTimeMin = map(bottomDurationMin, 30, 60, 3, 10);
        decoMessage = "DECO_STOP_5m_" + String(decoStopTimeMin) + "min";
        decoStart = millis();
        inDecompressionPhase = true;
      } else {
        decoMessage = "NO_DECO_STOP";
        inDecompressionPhase = false;
      }
    }
  }

  if (inDecompressionPhase && depth < 6.0 && depth > 4.0) {
    unsigned long elapsedMin = (millis() - decoStart) / 60000;
    if (!decoAlertShown) {
      Serial.println(">>> DECOMPRESSION STOP <<<");
      Serial.println(decoMessage);
      for (int i = 0; i < 6; i++) {
        digitalWrite(BLINK_PIN, HIGH); digitalWrite(HAPTIC_PIN, HIGH); delay(300);
        digitalWrite(BLINK_PIN, LOW);  digitalWrite(HAPTIC_PIN, LOW);  delay(300);
      }
      decoAlertShown = true;
    }
    if (elapsedMin >= decoStopTimeMin) {
      inDecompressionPhase = false;
      Serial.println(">>> DECO STOP COMPLETE <<<");
      for (int i = 0; i < 4; i++) {
        digitalWrite(HAPTIC_PIN, HIGH); delay(100);
        digitalWrite(HAPTIC_PIN, LOW); delay(100);
      }
    }
  }

  Serial.print(amb); Serial.print(", ");
  Serial.print(obj); Serial.print(", ");
  Serial.print(pressure); Serial.print(", ");
  Serial.print(depth, 2); Serial.print(", ");
  Serial.print(Celsius != DEVICE_DISCONNECTED_C ? String(Celsius) : "NaN"); Serial.print(", ");
  Serial.print(ecgValue); Serial.print(", ");
  Serial.print(bpmToPrint); Serial.print(", ");
  Serial.print(signalToPrint); Serial.print(", ");
  Serial.println(decoMessage);

  delay(1000);
}

void interruptSetup() {
  pulseTicker.attach_ms(2, pulseSensorPoll);
}

void pulseSensorPoll() {
  Signal = analogRead(PULSE_PIN);
  sampleCounter += 2;
  int N = sampleCounter - lastBeatTime;

  if ((Signal < thresh) && (N > (IBI / 5) * 3)) {
    if (Signal < T) T = Signal;
  }

  if ((Signal > thresh) && (Signal > P)) {
    P = Signal;
  }

  if ((N > 250) && (Signal > thresh) && !Pulse && (N > (IBI / 5) * 3)) {
    Pulse = true;
    IBI = sampleCounter - lastBeatTime;
    lastBeatTime = sampleCounter;

    if (secondBeat) {
      secondBeat = false;
      for (int i = 0; i <= 9; i++) rate[i] = IBI;
    }

    if (firstBeat) {
      firstBeat = false;
      secondBeat = true;
      return;
    }

    word runningTotal = 0;
    for (int i = 0; i <= 8; i++) {
      rate[i] = rate[i + 1];
      runningTotal += rate[i];
    }

    rate[9] = IBI;
    runningTotal += rate[9];
    runningTotal /= 10;
    BPM = 60000 / runningTotal;
    QS = true;
  }

  if ((Signal < thresh) && Pulse) {
    Pulse = false;
    amp = P - T;
    thresh = amp / 2 + T;
    P = thresh;
    T = thresh;
  }

  if (N > 2500) {
    thresh = 512;
    P = 512;
    T = 512;
    lastBeatTime = sampleCounter;
    firstBeat = true;
    secondBeat = false;
  }
}