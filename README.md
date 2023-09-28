# Hassio Listener

Servicio que funciona como interfaz entre la informacion de sensores DHT22 enviada por un Arduino Uno para que sean reconocidos por Home Assistant

## To Do

Actualmente se genera un cuello de botella en la recepcion de mensajes MQTT

La estructura actual se compone por 2 clientes por sensor, lo que seria 12 clientes por caja, probablemente esto este generando el problema, ya que se debe mantener la conexion de cada cliente

Mejorar el manejo de clientes mqtt, probar con generar un unico cliente para todos los sensores.
