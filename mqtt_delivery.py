import utils.json_utilities as json_utilities
import utils.hassio_utils as hass
from systemd import journal

from time import sleep

#test only modules
# import random

config_path = "/home/laboratorio_sv/scripts/hassio-listener/Box_config.json"


mqtt_server = "bingolab.local"
mqtt_port = 1883

journal.send("Abriendo archivo de configuracion")
config_JSON = json_utilities.leerJSON(config_path)

mqtt = hass.MqqtHandler(mqtt_server,mqtt_port)
mqtt.connect()

if(config_JSON != ""):
    journal.send("configuracion cargada exitosamente")
else:
    journal.send("No se pudo leer el archivo")
    exit()

box_topic = "testtopic/box_arduino"

box_listener = hass.BoxListener(box_topic, config_JSON,mqtt)
    
while True:
    box_listener.listener_loop()
    
    sleep(.5)
    
    
