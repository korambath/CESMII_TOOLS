#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_ADXL345_U.h>

/* Assign a unique ID to this sensor at the same time */
//Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345);
//Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(clock,miso,mosi,cs);
//Adafruit_ADXL345_Unified(uint8_t clock, uint8_t miso, uint8_t mosi, uint8_t cs, int32_t sensorID = -1);

//SCK = Connect the SCL pin to Digital #13 but any pin can be used later
//MISO = Connect the SDO pin to Digital #12 but any pin can be used later
//MOSI = Connect the SDA pin to Digital #11 but any pin can be used later
//CS = Connect the CS pin Digital #10 but any pin can be used later
//Vin = Connect Vin to the power supply, 3V or 5V is fine. Use the same voltage that the microcontroller logic is based off of. For most Arduinos, that is 5V
//GND = Connect GND to common power/data ground

#define ADXL_SCK 13      
#define ADXL_MISO 12
#define ADXL_MOSI 11
#define ADXL_CS 10

//Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(12345); // For I2C
Adafruit_ADXL345_Unified accel = Adafruit_ADXL345_Unified(ADXL_SCK,ADXL_MISO,ADXL_MOSI,ADXL_CS); // For SPI


void displaySensorDetails(void)
{
  sensor_t sensor;
  accel.getSensor(&sensor);
  Serial.println("------------------------------------");
  Serial.print  ("Sensor:       "); Serial.println(sensor.name);
  Serial.print  ("Driver Ver:   "); Serial.println(sensor.version);
  Serial.print  ("Unique ID:    "); Serial.println(sensor.sensor_id);
  Serial.print  ("Max Value:    "); Serial.print(sensor.max_value); Serial.println(" m/s^2");
  Serial.print  ("Min Value:    "); Serial.print(sensor.min_value); Serial.println(" m/s^2");
  Serial.print  ("Resolution:   "); Serial.print(sensor.resolution); Serial.println(" m/s^2");
  Serial.println("------------------------------------");
  Serial.println("");
  delay(500);
}


void setup(void) 
{
  Serial.begin(9600);
  Serial.println("ADXL345 Accelerometer Calibration"); 
  Serial.println("");
  
  /* Initialise the sensor */
  if(!accel.begin())
  {
    /* There was a problem detecting the ADXL345 ... check your connections */
    Serial.println("Ooops, no ADXL345 detected ... Check your wiring!");
    while(1);
  }
  accel.setDataRate(ADXL345_DATARATE_1600_HZ);
  /* Set the range to whatever is appropriate for your project */
  accel.setRange(ADXL345_RANGE_16_G);

  // accel.setRange(ADXL345_RANGE_8_G);
  // accel.setRange(ADXL345_RANGE_4_G);
  // accel.setRange(ADXL345_RANGE_2_G);
  
  /* Display some basic information on this sensor */
  displaySensorDetails(); 
  
  Serial.print  ("Sensor Data Rate:       ");
  Serial.println(accel.getDataRate());
  Serial.print  ("Sensor Data Range:       ");
  Serial.println(accel.getRange());     
  delay(1000);
}

void loop(void)
{
    //Serial.println("Type key when ready..."); 
    //while (!Serial.available()){}  // wait for a character
    
    /* Get a new sensor event */ 
    

    sensors_event_t accelEvent;  
    accel.getEvent(&accelEvent);



    //Serial.println(accelEvent.acceleration.x);
    //Serial.println(accelEvent.acceleration.y);
    //Serial.println(accelEvent.acceleration.z);

    /* UNCOMMENT TO VIEW X Y Z ACCELEROMETER VALUES */  
    //Serial.print(accelEvent.acceleration.x);
    //Serial.print(", ");
    //Serial.print(accelEvent.acceleration.y);
    //Serial.print(", ");
    Serial.println(accelEvent.acceleration.z);


    //delay(500);
    /*
    while (Serial.available())
    {
      Serial.read();  // clear the input buffer
    }
    */
}
