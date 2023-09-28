import json
import paho.mqtt.client as mqtt
import logging
from systemd import journal
from time import sleep

mqtt_server = "bingolab.local"
mqtt_port = 1883

# log = logging.getLogger("hassio_utils")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hassio_utils")
logger.addHandler(journal.JournalHandler())


#dev
topic_root = "testtopic/test"
discovery_root = "testtopic/test"

#prod
# topic_root = "bingo"
# discovery_root = "homeassistant"

class HassioSensor:
    #Generar unico por entidad (temperatura y humedad independientes)
    #Testear las propiedad enabled_by_default  y expire_after 
    #Probar si con el atributo device_class se eligen automaticamente las unidades de medida
    def __init__(self, sensor_id:str, sensor_type:str,sensor_unit:str, sala:str):
        
        self.id = f"{sensor_type}_{sensor_id}"
        
        self.unit = sensor_unit
        self.type = sensor_type
        
        self.sala = sala
        
        self.discovery_topic = f'{discovery_root}/sensor/{self.id}/config'
        self.stat_topic = f'{topic_root}/{sensor_id}/{sensor_type}'
        self.availability_topic = f'{topic_root}/{sensor_id}/available'
        
        self.discovery_payload = self.build_discovery_payload(self.type,self.unit)
        
        self.client = mqtt.Client()
        
        self.client.connect(mqtt_server,mqtt_port)
        self.client.on_connect = self.connect_callback
        
    def connect_callback(self,client ,userdata, mid, granted_qos):
        logger.info(f"sensor {self.id} conectado exitosamente")
        logger.info(f"sensor {self.id}:\n\
                    discovery topic: {self.discovery_topic}\n\
                    discovery payload: {self.discovery_payload}\n\n\
                    availability topic: {self.availability_topic}\n\
                    ")
        #Mando el discovery para configurar el sensor
        self.client.publish(self.discovery_topic,self.discovery_payload)
        sleep(.5)
        
        #Habilito el estado del sensor
        self.client.publish(self.availability_topic,"online")
        
        
    
    def build_discovery_payload(self,sensor_type:str,unit_of_meas:str):
        sensor_name=f'{self.id.replace("_"," ")}'
            
        sensor_name=sensor_name.title()
        
        
        discovery_payload = {
            "name":f"{sensor_name}",
            "uniq_id":self.id,
            "stat_t":self.stat_topic,
            "availability_topic":self.availability_topic,
            "optimistic":False,
            "qos":0,
            "retain":True,
            "unit_of_meas":unit_of_meas,
            "device_class":sensor_type,
            "device":{
                "identifiers": self.id,
                "name": sensor_name,
                "model":"DHT22",
                "manufacturer":"Bingo Adrogue SA",
                "suggested_area":self.sala
            }
        }
        parsed_discovery_payload = json.dumps(discovery_payload)
        return parsed_discovery_payload
    
    def send_status(self,value, tries = 3):
        error = False
        err_count=0
        
        while err_count < tries:
            if self.client.is_connected():
                self.client.publish(self.availability_topic,"online",retain=True)
                sleep(.5)
                self.client.publish(self.stat_topic,value,retain=True)
                error = False
                break
            else:
                logger.warning(f"sensor {self.id} no conectado")
                self.client.connect(mqtt_server,mqtt_port)
                error = True
                err_count+=1            
        
        return error
    
class BoxListener:
    def __init__(self,box_topic:str, config_dict:dict):
        self.client = mqtt.Client()
        self.in_topic = box_topic
        self.sensor_dict = dict()
        self.boxes_config = config_dict
        
        self.client.connect(mqtt_server,mqtt_port)
        self.client.subscribe(self.in_topic)
        
        self.client.on_message = self.message_arrive
        
    def message_arrive(self, client, userdata, message:mqtt.MQTTMessage):
        error = False
        payload = json.loads(message.payload)
        
        logger.info(f'se recibio:\n{payload}')
        
        sala,id = get_sensor_info(self.boxes_config,payload["box_id"],payload["sensor_id"])
        
        if id != -1:
            sensor_id = gen_header(sala,id)
            
            if not(sensor_id in self.sensor_dict):
                logger.info(f'Creando sensor:{sensor_id}')

                new_temp_sensor = HassioSensor(sensor_id,"temperature","°C",sala)
                new_hum_sensor = HassioSensor(sensor_id,"humidity","%",sala)
                
                self.sensor_dict.update({
                    sensor_id : {"temperature":new_temp_sensor,
                                "humidity":new_hum_sensor}
                })
                
            logger.info(f'Enviando datos del sensor {sensor_id}')
            self.sensor_dict[sensor_id]["temperature"].send_status(payload["temp"])
            self.sensor_dict[sensor_id]["humidity"].send_status(payload["hum"])
            
        else:
            error = True
            logger.warning(f'no se encontró la informacion de la caja {payload["box_id"]} en el sensor {payload["sensor_id"]}')
        return error
    
    def listener_loop(self):
        if  not(self.client.is_connected()):
            logger.warning(f"escucha desconectada... ")
        self.client.loop()
        
    def sensor_loop(self):
        for sensor in self.sensor_dict:
            for sensor_type in self.sensor_dict[sensor]:
                if  not(self.sensor_dict[sensor][sensor_type].client.is_connected()):
                    logger.warning(f" {self.sensor_dict[sensor][sensor_type].id} DESCONECTADO")
                    
                self.sensor_dict[sensor][sensor_type].client.loop()
            
        
        
        
    
    

    

def gen_header(sala:str,sensor_id:int,beautify=False):
    """genera el nombre del sensor

    Args:
        sala (str): nombre de la sala
        box_id (int): id de la caja
        sensor_id (int): id del sensor
        beautify (bool): Indica si hay que darle formato de nombre o id (capitalizado o no y
        separado por espacio o guion bajo)

    Returns:
        str: nombre generado por la funcion
    """
    name = str()
    separador = "_"
    if beautify:
        sala = sala.capitalize()
        separador = " "
    else:
        sala = sala.replace(" ","_")
    name = separador.join([sala,str(sensor_id)])
    return name

def get_sensor_info(config_JSON:dict,box_id:int,sensor_index:int, verbose=False):
    """busca la informacion del sensor dada la box id y la ubicacion (puerto) del sensor en
    en json de las cajas

    Args:
        config_JSON (dict): json convertido en dict
        box_id (int): id de la caja
        sensor_index (int): indice del puerto del sensor

    Returns:
        tupla(str,int): devuelve una tupla del nombre de la sala y el id del sensor
    """
    sala = ""
    id = -1
    box_key=f'box{box_id}'
    error_msg = ""
    error_flag = False
    if box_key in config_JSON:
        box_info = config_JSON[box_key]
        if sensor_index < min([len(box_info["ids"]),len(box_info["salas"])]):
            sala = box_info["salas"][sensor_index]
            id = box_info["ids"][sensor_index]
        else:
            error_msg = "ERROR: indice sensor fuera de rango"
            
    else:
        error_msg = f"ERROR, box id ({box_key}) no encontrada"
        
    if verbose and error_flag:
        print(error_msg)
    
    return sala,id
