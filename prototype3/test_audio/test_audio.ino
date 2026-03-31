// #include "DFRobotDFPlayerMini.h"

// DFRobotDFPlayerMini myDFPlayer;

// void setup() {
//   // Start the connection to your laptop
//   Serial.begin(115200);
  
//   // Start the hardware serial connection to the DFPlayer on Pins 0 and 1
//   Serial1.begin(9600);

//   // Wait for the Serial Monitor to open
//   while (!Serial); 

//   Serial.println("Starting up...");

//   // Use Serial1 to talk to the audio module
//   delay(3000);
//   if (!myDFPlayer.begin(Serial1, false, false)) {
//     Serial.println("Error: Check your wiring or the SD card!");
//     while(true); // Stop here on error
//   }

//   Serial.println("DFPlayer is ready!");
  
//   // Set the volume (0 to 30)
//   myDFPlayer.volume(15);

//   delay(500); // Give the chip time to process the volume change
  
//   // Play the first track (001.mp3)
//   myDFPlayer.playFolder(1, 1);

//   // Loop everything inside folder 01
//   // myDFPlayer.loopFolder(1);
// }

// void loop() {
//   // Nothing to do for a simple test
// }


#include "DFRobotDFPlayerMini.h"

DFRobotDFPlayerMini myDFPlayer;

void setup() {
  Serial.begin(115200);   // debug only
  Serial1.begin(9600);    // DFPlayer on D0/D1

  delay(3000);            // give DFPlayer time to boot

  Serial.println("Starting up...");

  if (!myDFPlayer.begin(Serial1, false, false)) {
    Serial.println("DFPlayer init failed.");
    Serial.println("Check TX/RX crossover, SD card, and power.");
    while (true);
  }

  Serial.println("DFPlayer is ready!");

  myDFPlayer.volume(20);
  delay(500);

  myDFPlayer.playFolder(1, 1);   // /01/001.mp3
}

void loop() {
}