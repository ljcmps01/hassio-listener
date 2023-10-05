#include <arduino.h>
#include <SPI.h>
#include <Ethernet.h>
#include <PubSubClient.h>

#include "DHT.h"
#include <ArduinoJson.h>

#include "box_id.h"

#define INTERVALO 3000

#define N_DHT 6

#define DHTPIN1 A0
#define DHTPIN2 A1
#define DHTPIN3 A2
#define DHTPIN4 A3
#define DHTPIN5 A4
#define DHTPIN6 A5

#define DHTTYPE DHT22   

#define WILL_QoS 0
#define WILL_RETAIN 1


boolean conexionExitosa = false;
unsigned long ultimaConexionIntentada = 0;
const unsigned long intervaloReconexion = 5000; // Intervalo entre intentos de reconexión (en milisegundos)


const char* server = "bingolab.local";
// IPAddress server(192, 168, 20, 136);

EthernetClient ethClient;
PubSubClient client(ethClient);

char clientId[16]="arduinoClient";

byte macBuffer[6];


const char* outTopic="testtopic/box_arduino";

// const char* statusTopic="testtopic/box_arduino/status";

// String statusMessage="\{\"box_id\":"+String(BOX_ID)+",\"online\":";
// String birthMessage= statusMessage + "true\}";
// String willMessage= statusMessage + "false\}";

// Inicializo los sensores DHT.
DHT dht[N_DHT]=
{
  {DHTPIN1,DHTTYPE},
  {DHTPIN2,DHTTYPE},
  {DHTPIN3,DHTTYPE},
  {DHTPIN4,DHTTYPE},
  {DHTPIN5,DHTTYPE},
  {DHTPIN6,DHTTYPE}
};


//Funcion de conexion al servidor MQTT
void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    if (!conexionExitosa && (millis() - ultimaConexionIntentada >= intervaloReconexion)) {
      Serial.println("Intentando conectar al servidor MQTT...");
    
      if (Ethernet.begin(macBuffer) == 0){
        Serial.print("Error en la conexion ethernet, reintentando en 5 segundos...");
      }

      else{
        if (client.connect(clientId)) {
          Serial.println("conectado");
          Serial.println(clientId);
          conexionExitosa = true;
        } 
      
        else {
          Serial.print("fallo la conexion, rc=");
          Serial.print(client.state());
          Serial.println(" reintentando en 5 segundos...");
        }
      }
    ultimaConexionIntentada = millis(); // Actualiza el tiempo del último intento de conexión
    }
  }
}

void setup() {
  randomSeed(analogRead(A0));
  int rNum=random(0,999);
  char cRandom[5];
  itoa(rNum,cRandom,6);
  strcat(clientId,cRandom);
  // Serial.println(clientId);
  Serial.begin(9600);
  Serial.print("BOX: ");
  Serial.println(BOX_ID);
  
  for (int i=0;i<N_DHT;i++)
  {
    dht[i].begin();
  } 

  


  byte mac[]= {  0xDE, 0xED, 0xBA, 0xFE, 0xFE, byte(random(0,256)) };
  Ethernet.begin(mac);
  Ethernet.MACAddress(macBuffer);
  for(int i=0;i<6;i++)
  {
    Serial.print(macBuffer[i],HEX);
    Serial.print(" ")
  }
  Serial.println();
  Serial.println(Ethernet.localIP());

  client.setServer(server, 1883);
  
}

void loop() {
  char data[200];
  
  for(int i=0;i<N_DHT;i++)
  {
    if (!client.connected()) {
      reconnect();
    }  

    client.loop();
    Ethernet.maintain();

    Serial.println(i);
    data_JSON(dht[i],BOX_ID,i,data);
    Serial.println(data);
    
    client.publish(outTopic,data);

    delay(INTERVALO);
    
  }
}

void data_JSON(DHT sensor, int box_id, int sensor_index,char *salida)
{
  StaticJsonDocument<100> lectura;
  lectura["box_id"]=box_id;
  lectura["sensor_id"]=sensor_index;
  char data[100];
  
  float temp;
  float hum;
  
  temp=sensor.readTemperature();
  hum=sensor.readHumidity();
  if(isnan(temp)||isnan(hum))
  {
    lectura["temp"]="nan";
    lectura["hum"]="nan";
  }
  else
  {
    lectura["temp"]=temp;    
    lectura["hum"]=hum;    
  }

  serializeJson(lectura,data);
  strcpy(salida,data);
}


