#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>

constexpr int BME_SCK = 13;
constexpr int BME_MISO = 12;
constexpr int BME_MOSI = 11;
constexpr int BME_CS = 10;
constexpr float SEALEVELPRESSURE_HPA = 1013.25f;
constexpr unsigned long DELAY_TIME = 500;
constexpr int SERIAL_BAUD_RATE = 9600;

Adafruit_BME280 bme; // I2C

void setup() {
    Serial.begin(SERIAL_BAUD_RATE);
    while (!Serial); // Wait for Serial to be ready

    if (!initializeSensor()) {
        Serial.println("Failed to initialize BME280 sensor.");
        while (1) delay(10); // Halt if the sensor is not found
    }

    Serial.println("BME280 initialized successfully.");
}

void loop() { 
    printMQTTValues();
    delay(DELAY_TIME);
}

bool initializeSensor() {
    unsigned status = bme.begin();
    if (!status) {
        Serial.print("Could not find a valid BME280 sensor. Check wiring, address, or sensor ID!\n");
        Serial.print("SensorID was: 0x");
        Serial.println(bme.sensorID(), 16);
        return false;
    }
    return true;
}

void printMQTTValues() {
    Serial.print(bme.readTemperature());
    Serial.print(",");
    Serial.print(bme.readPressure() / 100.0F); // Convert to hPa
    Serial.print(",");
    Serial.print(bme.readAltitude(SEALEVELPRESSURE_HPA));
    Serial.print(",");
    Serial.println(bme.readHumidity());
}

void printValues() {
    Serial.print("Temperature = ");
    Serial.print(bme.readTemperature());
    Serial.println(" °C");

    Serial.print("Pressure = ");
    Serial.print(bme.readPressure() / 100.0F);
    Serial.println(" hPa");

    Serial.print("Approx. Altitude = ");
    Serial.print(bme.readAltitude(SEALEVELPRESSURE_HPA));
    Serial.println(" m");

    Serial.print("Humidity = ");
    Serial.print(bme.readHumidity());
    Serial.println(" %");

    Serial.println();
}
