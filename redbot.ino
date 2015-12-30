#include <RedBot.h>


RedBotMotors motors;

String incomingString;
float lastError = 0;
long lastErrorTime = millis();
float integral = 0.0;
float derivative = 0.0;

unsigned int baseSpeed = 50;
float Kp = 50, Ki = 0, Kd = 0;


void setup() {
    Serial.begin(9600);
}


void loop() {
    Serial.println("ready");
    delay(5);

    while (Serial.available() > 0) {
        delay(3);
        char c = Serial.read();
        if (c == '\n') {
            break;
        } else {
            incomingString += c;
        }
    }

    if (incomingString.equals("stop")) {
        motors.brake();
        exit(0);
    }

    long errorTime = millis();
    long iterationTime = errorTime - lastErrorTime;

    float error = atof(incomingString.c_str());

    integral = (error / iterationTime) + integral;
    derivative = (error - lastError) / iterationTime;

    float correction = Kp * error + Ki * integral + Kd * derivative; 

    motors.leftMotor(baseSpeed - correction);
    motors.rightMotor(baseSpeed + correction);

    lastError = error;
    lastErrorTime = errorTime;

    incomingString = "";
}
