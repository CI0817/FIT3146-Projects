void setup()
{
    Serial.begin(115200);
    while (!Serial)
        ; // This forces the board to wait until the Serial Monitor is open
    Serial.println("Connection successful!");
}

void loop()
{
    Serial.println("Still working...");
    delay(1000);
}