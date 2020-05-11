

#include <SPI.h>
#include <avr/wdt.h>
#include "nRF24L01.h"
#include "RF24.h"


//float arr1[64] = {
//  21.00, 21.50, 22.50, 23.50, 25.00, 25.75, 25.75, 28.25, 
//  20.75, 21.50, 22.25, 22.00, 24.00, 26.75, 27.25, 27.00, 
//  20.75, 21.00, 21.50, 23.00, 24.75, 25.50, 26.50, 28.00, 
//  20.75, 20.75, 21.75, 23.00, 24.25, 25.50, 25.50, 26.50,   
//  21.00, 21.00, 21.50, 23.25, 23.75, 24.75, 25.25, 25.75, 
//  19.75, 21.50, 22.25, 23.25, 24.00, 24.00, 24.50, 25.00, 
//  20.50, 20.75, 21.75, 23.00, 24.25, 24.25, 24.00, 24.00, 
//  20.50, 21.50, 21.25, 22.25, 23.25, 23.75, 23.50, 24.75};


float arr1[64] = {
  49.5, 53.8, 59.0, 59.8, 60.3, 59.8, 56.3, 53.0,  
  51.3, 58.8, 60.0, 60.0, 60.3, 60.0, 59.3, 57.0, 
  55.5, 60.3, 60.5, 60.8, 61.0, 60.5, 60.3, 59.5,
  55.5, 60.5, 61.3, 61.5, 61.8, 61.8, 60.8, 60.0,
  53.0, 60.5, 61.5, 61.5, 62.0, 61.5, 60.3, 58.3,
  49.8, 59.0, 61.3, 61.8, 61.8, 61.5, 59.5, 53.5, 
  47.0, 51.8, 58.0, 59.8, 59.3, 57.0, 51.8, 48.5, 
  44.3, 46.5, 48.0, 49.3, 49.5, 48.8, 47.0, 45.5};

//float arr2[64] = {
//  20.50, 21.50, 22.00, 23.00, 24.00, 25.25, 27.25, 28.25, 
//  20.75, 20.75, 21.75, 22.00, 24.00, 25.75, 27.00, 27.50, 
//  20.50, 20.50, 22.00, 22.50, 24.75, 25.00, 26.50, 27.75, 
//  20.50, 21.25, 21.50, 22.75, 23.75, 25.00, 25.75, 26.00, 
//  20.50, 20.75, 21.50, 23.00, 23.75, 24.75, 24.75, 25.00, 
//  20.00, 21.25, 22.25, 23.00, 23.75, 24.25, 24.25, 24.50,   
//  20.50, 21.25, 22.00, 23.25, 24.75, 23.75, 24.00, 24.00, 
//  20.75, 20.75, 22.00, 22.25, 23.25, 23.00, 23.75, 24.00};

float arr2[64] = {
  24.00, 24.50, 25.75, 27.50, 29.50, 30.00, 30.00, 30.00, 
  24.00, 25.00, 26.00, 27.75, 28.25, 28.75, 27.50, 28.50, 
  25.75, 26.75, 28.50, 30.25, 32.25, 31.50, 29.75, 28.75, 
  25.25, 27.50, 32.00, 48.50, 61.75, 57.25, 36.25, 30.50, 
  25.50, 28.50, 39.75, 65.50, 66.00, 67.00, 55.00, 33.00, 
  25.50, 28.50, 42.75, 68.00, 67.75, 68.00, 58.25, 34.25, 
  25.50, 27.25, 33.50, 60.25, 67.75, 66.00, 44.50, 31.75, 
  24.75, 26.00, 28.75, 34.25, 41.25, 39.25, 32.50, 29.00

  
};

//float arr3[64] = {
//  21.50, 21.50, 22.50, 22.75, 25.00, 25.25, 27.00, 28.50, 
//  20.75, 21.25, 21.75, 22.25, 24.25, 26.00, 27.25, 27.25, 
//  20.00, 20.50, 21.50, 22.50, 25.00, 25.25, 26.75, 28.00, 
//  20.75, 21.00, 21.25, 23.00, 23.75, 25.25, 25.50, 26.50, 
//  20.50, 20.75, 21.50, 23.25, 23.75, 24.50, 25.00, 25.50, 
//  20.25, 21.50, 22.00, 23.00, 23.75, 24.25, 24.75, 24.75, 
//  20.00, 21.00, 21.50, 23.00, 24.75, 24.00, 24.25, 24.75, 
//  20.50, 20.25, 22.00, 22.50, 23.75, 23.50, 23.25, 24.25};

float* irCamArr[2] = {arr1,arr2};

RF24 radio(7,8);


uint32_t _seconds = 0;
int _millisTimeout = 1000;
bool isBoilActive = false;
bool isMashActive = false;
bool secondHappend = false;
uint8_t irsendcount = 0;
ISR(TIMER2_COMPA_vect){
  _millisTimeout--;
  if (_millisTimeout ==0){
    _seconds++;
    _millisTimeout=1000;
    secondHappend = true;  
  }
  
  if (secondHappend){
    if (_seconds % 10 == 0){sendFermentData();}
    if (isBoilActive){
      if (_seconds % 5 == 0){sendBoilData();}
    }
    if (isMashActive){
      if (_seconds % 5 == 0) {sendMashData();}
      if (_seconds % 1 == 0) {sendIrCameraData(irCamArr[0]);}  
    }
    secondHappend = false;  
  }
  TCNT1=64910;  //reload timer
}


void configureRadio(){
  Serial.println("configuring radio");
  radio.begin();
  radio.enableDynamicPayloads();
  radio.enableDynamicAck();
  radio.setRetries(5,15);
  radio.setChannel(0x76);
  byte pipe[][5] = {{0xCC,0xCE,0xCC,0xCE,0xCC},{0xE0,0xE0,0xF1,0xF1, 0xE0}};
  radio.openWritingPipe(pipe[0]);
  radio.openReadingPipe(1,pipe[1]);
  radio.failureDetected = false;
  radio.startListening();
  if (radio.isChipConnected()){
    Serial.println("connected");
  }
}

int timerCounter;
void setup(){
  Serial.begin(115200);
  configureRadio();
  pinMode(2, INPUT_PULLUP);
  delay(20);
  attachInterrupt(digitalPinToInterrupt(2), check_radio, FALLING); 
  noInterrupts();

  // disable all interrupts
  TCCR2A = 0;
  TCCR2B = 0;
  // set up interrupt on overflow..
  TCNT2 = 0;   // preload timer
  OCR2A=15624;
  TCCR2A |= (1 << WGM12);
  TCCR2B |= (1 << CS12);// 256 prescaler
  TIMSK2 |= (1 << OCIE2A);   // enable timer overflow interrupt
  interrupts();             // enable all interrupt

  MCUSR = 0;
}



void check_radio(void){
//  Serial.print("Check radio\n");

  bool rx, tx, fail;
  radio.whatHappened(tx,fail,rx);
  
  if (rx || radio.available()){
    uint8_t recieved[5];
    radio.read(&recieved, sizeof(recieved));
    if (recieved[0]==0x06){wdt_enable(WDTO_15MS);}
    else if (recieved[0]==0x05){configureRadio();}
    
    else if(recieved[0]==0x01){ //If recieved mash command
      if (recieved[1]==0x02){stopMash();} //Its a mash stop command
      else if (recieved[1]==0x01){   // Its a mash start command
        uint16_t tempSet = combineTwoBytes(recieved[2], recieved[3]);
        startMash(tempSet);
      }
    }
    else if(recieved[0]==0x02){ //If recieved boil command
      if (recieved[1]==0x02){stopBoil();} //Its a boil stop command
      else if (recieved[1]==0x01){   // Its a boil start command
        uint16_t tempSet = combineTwoBytes(recieved[2], recieved[3]);
        startBoil(tempSet);
      } 
    }
  }
  if (tx){}
  if (fail){}
}

byte IRCount = 0;
void sendIrCameraData(float *arr){
  uint16_t arrsplit[8] = {0};
  
  for (uint8_t i = 0; i<8; i++){
    arrsplit[i] = uint16_t(arr[i+(IRCount*8)]*100);
  }
  
  
  uint8_t data[] = {0x01,0x02, IRCount, 
                  highByte(arrsplit[0]), lowByte(arrsplit[0]),  
                  highByte(arrsplit[1]), lowByte(arrsplit[1]),
                  highByte(arrsplit[2]), lowByte(arrsplit[2]),
                  highByte(arrsplit[3]), lowByte(arrsplit[3]),
                  highByte(arrsplit[4]), lowByte(arrsplit[4]),
                  highByte(arrsplit[5]), lowByte(arrsplit[5]),
                  highByte(arrsplit[6]), lowByte(arrsplit[6]),
                  highByte(arrsplit[7]), lowByte(arrsplit[7])
                  }; 


  radio.stopListening();
  radio.writeFast(&data, sizeof(data));
  radio.txStandBy();
  radio.startListening();
  
  IRCount++;
  if (IRCount ==8){IRCount =0;}
  
}




uint8_t mashArr[300];
uint16_t mashCount = 0;

void startMash(uint16_t tempSet){
  //set boil to temp
  tempSet /= 10;
  isMashActive = true;
  mashCount = 0;

  for (uint8_t i=0; i<60; i++){
    mashArr[i] = (3*i)+20;
    if (mashArr[i] > tempSet){mashArr[i] = tempSet;}
  }
  for (uint16_t i=60; i < 240; i++){mashArr[i] = tempSet;}
  for (uint16_t i=240; i<300; i++ ){
    mashArr[i] = -(3*i)+20;
  }
  
  Serial.print("MASH: ");
  Serial.print(tempSet);
  Serial.print("\n");
}

void stopMash(){
  isMashActive = false;
  mashCount = 0;
  Serial.print("MASH STOPPED \n");
}

void sendMashData(){
  
  uint16_t temp = mashArr[mashCount];
  byte templow = lowByte(temp);
  byte temphigh = highByte(temp);
  uint8_t data[] = {0x01,0x01, temphigh, templow }; 
  mashCount++;
  if (mashCount>=300){mashCount = 0;}
//  Serial.print("\nBoil data sending: ");
//  Serial.print(temp);
  radio.stopListening();
  radio.writeFast(&data, sizeof(data));
  radio.txStandBy();
  radio.startListening();
}


uint8_t boilArr[300];
uint16_t boilCount = 0;

void startBoil(uint16_t tempSet){
  //set boil to temp
  tempSet /= 10;
  isBoilActive = true;
  boilCount = 0;

  for (uint8_t i=0; i<60; i++){
    boilArr[i] = (3*i)+20;
    if (boilArr[i] > tempSet){boilArr[i] = tempSet;}
  }
  for (uint16_t i=60; i < 240; i++){boilArr[i] = tempSet;}
  for (uint16_t i=240; i<300; i++ ){
    boilArr[i] = -(3*i)+20;
  }
  
  Serial.print("BOIL: ");
  Serial.print(tempSet);
  Serial.print("\n");
}

void stopBoil(){
  isBoilActive = false;
  boilCount = 0;
  Serial.print("BOIL STOPPED \n");
}


void sendBoilData(){
  
  uint16_t temp = boilArr[boilCount];
  byte templow = lowByte(temp);
  byte temphigh = highByte(temp);
  uint8_t data[] = {0x02,0x01, temphigh, templow }; 
  boilCount++;
  if (boilCount>=300){boilCount = 0;}
//  Serial.print("\nBoil data sending: ");
//  Serial.print(temp);
  radio.stopListening();
  radio.writeFast(&data, sizeof(data));
  radio.txStandBy();
  radio.startListening();
}

uint16_t temp = 20;
uint16_t g = 10;
uint16_t vol = 300;

void sendFermentData(){
  byte tankid = 3;
  byte templow = lowByte(temp);
  byte temphigh = highByte(temp);
  byte glow = lowByte(g);
  byte ghigh = highByte(g);
  byte vollow = lowByte(vol);
  byte volhigh = highByte(vol);

  uint8_t data[] = {0x03, tankid, temphigh, templow, ghigh, glow, volhigh, vollow};

  radio.stopListening();
  radio.writeFast(&data, sizeof(data));
  radio.txStandBy();
  radio.startListening();
//  temp++;
//  g--;

}



uint16_t combineTwoBytes(byte high, byte low){
  uint16_t combined = high*256;
  combined |= low;
  return combined;
}



void loop() {

//  sendFermentData();
//  delay(1000);
//  if (isBoilActive){
//    sendBoilData();
//  }
//  delay(1000);
}
