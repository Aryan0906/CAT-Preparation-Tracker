#define LED 13
#define LED1 12
#define MOTOR 11
void setup() {
  pinMode(LED, OUTPUT);
  pinMode(LED1, OUTPUT);
  pinMode(MOTOR, OUTPUT);          
}

void loop() {
  digitalWrite(LED, HIGH);
  digitalWrite(LED1, HIGH);
  digitalWrite(MOTOR, HIGH);
  delay(5000);
  delay(1000);
  delay(1000);
  digitalWrite(LED, LOW);
  digitalWrite(LED1, LOW);
  delay(1000);
  delay(1000);
  delay(5000);
  digitalWrite(MOTOR, LOW);

}

