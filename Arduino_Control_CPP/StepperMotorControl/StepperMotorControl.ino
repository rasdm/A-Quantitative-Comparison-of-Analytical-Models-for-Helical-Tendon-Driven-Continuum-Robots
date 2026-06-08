#include <Stepper.h>

// --- Pin Definitions ---

// Top hole 1
const int s1_pin1 = 22;
const int s1_pin2 = 24;
const int s1_pin3 = 26;
const int s1_pin4 = 28;

// Top hole 2
const int s2_pin1 = 8;
const int s2_pin2 = 9;
const int s2_pin3 = 10;
const int s2_pin4 = 11;

// Top hole 3
const int s3_pin1 = 32;
const int s3_pin2 = 34;
const int s3_pin3 = 36;
const int s3_pin4 = 38;

const int intervals = 1;

// --- Motor Setup ---
const int stepsPerRev = 2048;

// Initialize the three steppers (Note the pin sequence: 1, 3, 2, 4)
Stepper stepper1(stepsPerRev, s1_pin1, s1_pin3, s1_pin2, s1_pin4);
Stepper stepper2(stepsPerRev, s2_pin1, s2_pin3, s2_pin2, s2_pin4);
Stepper stepper3(stepsPerRev, s3_pin1, s3_pin3, s3_pin2, s3_pin4);

// --- Variables ---
const float r = 1.068; 

void setup() {
  Serial.begin(9600);
  
  stepper1.setSpeed(10);
  stepper2.setSpeed(10);
  stepper3.setSpeed(10);
  
  disableAllMotors();
  
  Serial.println("System Ready.");
  Serial.println("Enter total target values as: dl1,dl2,dl3 (e.g., -0.5,0.5,1)");
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim(); 
    
    if (input.length() == 0) return; 

    int firstComma = input.indexOf(',');
    int secondComma = input.indexOf(',', firstComma + 1);

    if (firstComma > 0 && secondComma > firstComma) {
      
      float dl1 = input.substring(0, firstComma).toFloat();
      float dl2 = input.substring(firstComma + 1, secondComma).toFloat();
      float dl3 = input.substring(secondComma + 1).toFloat();

      Serial.println("\n--------------------------------");
      Serial.print("Received totals -> dl1: "); Serial.print(dl1);
      Serial.print(" | dl2: "); Serial.print(dl2);
      Serial.print(" | dl3: "); Serial.println(dl3);

      // Execute the 10-step sequence with a 1000ms (2 second) delay
      executeIntervalMovement(dl1, dl2, dl3, intervals, 3000);
      
      disableAllMotors();
      Serial.println("Sequence complete. Motors disabled.");
      Serial.println("Waiting for next input...");
      
    } else {
      Serial.println("Invalid format! Please use: dl1,dl2,dl3 (e.g., -0.5,0.5,1)");
    }
  }
}

// --- Custom Functions ---

// Handles the math and execution for moving in slices
void executeIntervalMovement(float d1, float d2, float d3, int intervals, int delayMs) {
  // 1. Calculate total expected radians for the full move
  float totalRad1 = d1 / r;
  float totalRad2 = d2 / r;
  float totalRad3 = d3 / r;

  // 2. Calculate absolute total steps for the full move
  long totalSteps1 = round(totalRad1 * (stepsPerRev / TWO_PI));
  long totalSteps2 = round(totalRad2 * (stepsPerRev / TWO_PI));
  long totalSteps3 = round(totalRad3 * (stepsPerRev / TWO_PI));

  // Keep track of how many steps we have actually taken so far
  long currentStep1 = 0;
  long currentStep2 = 0;
  long currentStep3 = 0;

  Serial.println("Starting multi-step sequence...");

  // 3. Loop through each interval
  for (int i = 1; i <= intervals; i++) {
    
    // Calculate exactly what step we SHOULD be at for this interval (e.g., 1/10th, 2/10ths)
    long targetStep1 = round((float)totalSteps1 * i / intervals);
    long targetStep2 = round((float)totalSteps2 * i / intervals);
    long targetStep3 = round((float)totalSteps3 * i / intervals);

    // Find the difference between where we need to be and where we currently are
    long stepsToMove1 = targetStep1 - currentStep1;
    long stepsToMove2 = targetStep2 - currentStep2;
    long stepsToMove3 = targetStep3 - currentStep3;

    // Print out the current interval's behavior
    Serial.print("Interval "); Serial.print(i); Serial.print("/"); Serial.print(intervals);
    Serial.print(" -> Moving Steps | M1: "); Serial.print(stepsToMove1);
    Serial.print(" | M2: "); Serial.print(stepsToMove2);
    Serial.print(" | M3: "); Serial.println(stepsToMove3);

    // Execute the movement
    stepper1.step(stepsToMove1);
    stepper2.step(stepsToMove2);
    stepper3.step(stepsToMove3);

    // Update our current position tracker
    currentStep1 = targetStep1;
    currentStep2 = targetStep2;
    currentStep3 = targetStep3;

    // Wait the specified delay, except on the very last interval
    if (i < intervals) {
      delay(delayMs);
    }
  }
}

// Disables all 12 pins across the 3 motors
void disableAllMotors() {
  digitalWrite(s1_pin1, LOW); digitalWrite(s1_pin2, LOW);
  digitalWrite(s1_pin3, LOW); digitalWrite(s1_pin4, LOW);
  
  digitalWrite(s2_pin1, LOW); digitalWrite(s2_pin2, LOW);
  digitalWrite(s2_pin3, LOW); digitalWrite(s2_pin4, LOW);
  
  digitalWrite(s3_pin1, LOW); digitalWrite(s3_pin2, LOW);
  digitalWrite(s3_pin3, LOW); digitalWrite(s3_pin4, LOW);
}