# Hassio Listener

Servicio que funciona como interfaz entre la informacion de sensores DHT22 enviada por un Arduino Uno para que sean reconocidos por Home Assistant

## To Do

* [DHT2HASSIO] Ver si se puede ingresar la ip del servidor por hostname y no necesariamente por ip
* [DHT2HASSIO] Avisar al usuario que la compilacion y/o la carga falló
* [DHT2HASSIO] Capacidad de cambiar la ip del servidor desde linea de comando y desde cli

* [mqtt_delivery] Revisar funcionamiento en caso de que el listener reciba info de un sensor no configurado en el json
* [mqtt_delivery] Añadir funcion de rediscovery si el servidor HA envia una mensaje de nacimiento (indicando que el servidor acaba de iniciar)
