#include <RedBot.h>


RedBotMotors motors;
RedBotSensor leftIR = RedBotSensor(A3);
RedBotSensor centerIR = RedBotSensor(A6);
RedBotSensor rightIR = RedBotSensor(A7);

String command;
float lastError = 0;
long lastErrorTime = millis();
float integral = 0.0;
float derivative = 0.0;

const unsigned int rBaseSpeed = 85;
const unsigned int lBaseSpeed = 95;
const float Ku = rBaseSpeed + 95, Tu = 20;
const float Kp = 0.6 * Ku;
const float Ki = 2.0 * Kp / Tu;
const float Kd = (Kp * Tu) / 8.0;

const unsigned short IR_THRESH = 500;


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
			command += c;
		}
	}

	if (command.equals("stop")) {
		motors.brake();
		exit(0);
	}

	long errorTime = millis();
	long iterationTime = errorTime - lastErrorTime;

	float error = atof(command.c_str());

	bool onCenter = centerIR.read() > IR_THRESH;
	bool onLeft = leftIR.read() > IR_THRESH;
	bool onRight = rightIR.read() > IR_THRESH;
	if (onCenter && (onLeft || onRight)) {
		error = 0.4 * error;
	}

	integral = (error / iterationTime) + integral;
	derivative = (error - lastError) / iterationTime;

	float correction = Kp * error + Ki * integral + Kd * derivative; 
	Serial.println(correction);

	motors.leftMotor((int) (correction - lBaseSpeed));
	motors.rightMotor((int) (rBaseSpeed + correction));

	lastError = error;
	lastErrorTime = errorTime;

	command = "";

	delay(40);
}
