// Pulse Sensor Definitions
#define PULSE_PIN A0       // The only analog input on NodeMCU
#define THRESHOLD 550      // Adjust based on your sensor (400-600 typical)
#define SAMPLE_WINDOW 1000 // Update BPM every second (matches Python expectation)

// LED Indicator Pins (optional)
#define LED_PIN D4         // Onboard LED on NodeMCU (inverted logic)
#define BEAT_LED D1        // External LED for heartbeat visualization

unsigned long lastBeat = 0;
int bpm = 0;
int beatCount = 0;
unsigned long sampleStart = 0;
bool beatDetected = false;

void setup() {
  // Initialize pins
  pinMode(PULSE_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  pinMode(BEAT_LED, OUTPUT);
  digitalWrite(LED_PIN, HIGH); // Turn off onboard LED (inverted)
  
  // Start serial communication
  Serial.begin(9600);
  while (!Serial); // Wait for serial connection on native USB
  
  sampleStart = millis();
  
  // Print CSV header (only if you want to log to serial monitor)
  // Serial.println("Timestamp,Signal,BPM,BeatDetected");
}

void loop() {
  int signal = analogRead(PULSE_PIN);
  unsigned long currentTime = millis();
  bool isBeat = false;

  // Beat detection with debounce
  if (signal > THRESHOLD && !beatDetected && (currentTime - lastBeat) > 300) {
    beatDetected = true;
    beatCount++;
    lastBeat = currentTime;
    isBeat = true;
    digitalWrite(BEAT_LED, HIGH); // Flash LED on beat
    Serial.print("PEAK:");        // For Python's beat detection
    Serial.println(signal);
  } 
  else if (signal < THRESHOLD) {
    beatDetected = false;
    digitalWrite(BEAT_LED, LOW);
  }

  // Calculate and send data every second (matches Python's expectation)
  if (currentTime - sampleStart >= SAMPLE_WINDOW) {
    bpm = beatCount * 60;  // Convert to BPM
    
    // Send data in CSV format: Timestamp,Signal,BPM,BeatFlag
    Serial.print("DATA:");  // Prefix for Python to identify
    Serial.print(currentTime);
    Serial.print(",");
    Serial.print(signal);
    Serial.print(",");
    Serial.print(bpm);
    Serial.print(",");
    Serial.println(isBeat ? "1" : "0");

    // Blink onboard LED
    digitalWrite(PC_13, LOW);
    delay(50);
    digitalWrite(PC_13, HIGH);

    // Reset counters
    beatCount = 0;
    sampleStart = currentTime;
  }

  delay(10);  // Small delay for stability
}