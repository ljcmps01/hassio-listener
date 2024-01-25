import os
import subprocess
import argparse

from default_config import server_ip

arduino_cli_path ="bin/arduino-cli.exe"
exit = ""
box_id = ""

def listar_puertos_com():
    # Ejecutar el comando arduino-cli para listar los puertos COM disponibles
    resultado = subprocess.check_output([arduino_cli_path, 'board', 'list'], universal_newlines=True)
    
    # Dividir las líneas de salida en una lista
    lineas = resultado.split('\n')
    
    # Filtrar las líneas que contienen información sobre los puertos COM
    puertos_com = [linea.split()[0] for linea in lineas if 'COM' in linea]
    
    return puertos_com

def compilar_sketch(ruta_sketch):
    # Ejecutar el comando arduino-cli para compilar el sketch
    proceso_compilacion = subprocess.Popen([arduino_cli_path, 'compile', '--verbose', '-b', 'arduino:avr:uno', ruta_sketch], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    
    print("Compilando el sketch...")
    
    
    for linea in proceso_compilacion.stdout:
        print(linea.strip())
        
    proceso_compilacion.wait()
    
    print("Compilación completada.")

def cargar_sketch(ruta_sketch, puerto_com):
    # Ejecutar el comando arduino-cli para cargar el sketch en el Arduino UNO
    proceso_carga = subprocess.Popen([arduino_cli_path, 'upload', '--verbose', '-p', puerto_com, '-b', 'arduino:avr:uno', ruta_sketch], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    
    print(f"Cargando el sketch en {puerto_com}...")
    
    for linea in proceso_carga.stdout:
        print(linea.strip())
        
    proceso_carga.wait()
    print("Carga completada.")
    
def crear_header(box_id,server_ip):
    with open("box_id.h","w") as header_id:
        valor = f"#define BOX_ID {str(box_id)}\n#define SERVER_IP {server_ip.replace('.',',')}\n"
        header_id.write(valor)
        
        print(f"Header generado exitosamente, se cargó:\n{valor}")

if __name__ == "__main__":
    # Ruta al directorio del sketch de Arduino
    ruta_sketch = 'DHT2HASSIO.ino'
    
    parser = argparse.ArgumentParser(description='Compila y carga el sketch de las cajas maestras Arduino.')
    parser.add_argument('--id','-i', type=int, help='ID de la caja')

    args = parser.parse_args()

    if args.id:
        box_id = args.id

    while exit=="":
        # Listar los puertos COM disponibles
        puertos_com = listar_puertos_com()
        
        box_id_flag=True

        if not puertos_com:
            print("No se encontraron puertos COM disponibles.")
            exit = input("Presione enter para reintentar, otra tecla para salir\n")
        else:
            print(f"Direccion IP: {server_ip}")
            print("Puertos COM disponibles:")
            for i, puerto in enumerate(puertos_com):
                print(f"{i+1}: {puerto}")

            # Elegir un puerto COM
            seleccion = int(input("Elija un puerto COM (1-{0}, ingrese 0 para salir o -1 para modificar IP): ".format(len(puertos_com))))
            

            if 1 <= seleccion <= len(puertos_com):
                
                # Si no se ingreso el id por la linea de comandos, ahora se le pregunta al usuario por su valor
                while box_id_flag:
                    if type(box_id) is int:
                        crear_header(box_id,server_ip)
                        box_id_flag = False
                        box_id = ""
                    
                    else:
                        input_id = input("Ingrese id de la caja: \n")
                        if input_id.isdecimal():
                            box_id = int(input_id)
                       
                            
                puerto_elegido = puertos_com[seleccion - 1]
                print(f"Compilando y cargando en {puerto_elegido}...")
                
                # Compilar el sketch
                compilar_sketch(ruta_sketch)

                # Cargar el sketch en el Arduino UNO
                cargar_sketch(ruta_sketch, puerto_elegido)
            elif seleccion == 0:
                exit = "exit"
            
            elif seleccion == -1:
                server_ip=input("ingrese nueva ip del servidor: ")
            else:
                print("Selección no válida.")
