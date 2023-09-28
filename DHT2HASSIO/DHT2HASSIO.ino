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


//Opciones: 
//"bajo","bouchard","cuadri","entrepiso","fuente",
//"principal","ruleta","vip"
// const char* salas[6]={
//   SALA_SENSOR0,
//   SALA_SENSOR1,
//   SALA_SENSOR2,
//   SALA_SENSOR3,
//   SALA_SENSOR4,
//   SALA_SENSOR5
// };

// const int id[6]={
//   ID_SENSOR0,
//   ID_SENSOR1,
//   ID_SENSOR2,
//   ID_SENSOR3,
//   ID_SENSOR4,
//   ID_SENSOR5
// };

// const char* server = "bingolab.local";
IPAddress server(192, 168, 20, 136);

EthernetClient ethClient;
PubSubClient client(ethClient);

char clientId[16]="arduinoClient";




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
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
  
    if (client.connect(clientId)) {
      // Serial.println("connected");
      Serial.println(clientId);
      // Once connected, publish an announcement...
      // client.publish(statusTopic,birthMessage.c_str(),birthMessage.length(),1);
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
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
  Serial.println(Ethernet.localIP());

  client.setServer(server, 1883);
  
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }  

    client.loop();
  char data[200];
  
  for(int i=0;i<N_DHT;i++)
  {
    Serial.println(i);
    data_JSON(dht[i],BOX_ID,i,data);
    Serial.println(data);
    
    client.publish(outTopic,data);

    delay(INTERVALO);
    client.loop();
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


