import os
import re
import requests
import pdfplumber
import time
import shutil
# import urllib.parse
from urllib.parse import urlparse, unquote

# Definir una variable global para la ruta
ruta_global = os.path.join(os.getcwd(), "pdf")

def log_mesajes(mensajes, ruta=None, nombre_archivo="log.txt", mostrar_consola=False):
    """
    Crea o actualiza un archivo de log con los mensajes proporcionados.

    Args:
        mensajes (str | list[str]): Mensaje o lista de mensajes a registrar en el log.
        ruta (str, optional): Ruta donde se creará el archivo del log. Si no se especifica, se usará la ruta de ejecución.
        nombre_archivo (str, optional): Nombre del archivo de log. Por defecto es "log.txt".
        mostrar_consola (bool, optional): Si es True, los mensajes también se mostrarán en la consola. Por defecto es False.
    """
    if ruta is None:
        ruta = ruta_global

    # Asegurarse de que la ruta existe
    os.makedirs(ruta, exist_ok=True)

    # Ruta completa del archivo de log
    ruta_completa = os.path.join(ruta, nombre_archivo)

    # Convertir el mensaje a lista si es un string
    if isinstance(mensajes, str):
        mensajes = [mensajes]

    # Obtener la fecha y hora actual
    #timestamp = time.strftime("%y-%m-%d/%H:%M:%S")
    timestamp = time.strftime("%y-%m-%d %H:%M:%S")

    # Abrir el archivo en modo append (crea el archivo si no existe)
    with open(ruta_completa, "a", encoding="utf-8") as log_file:
        for mensaje in mensajes:
            entrada = f"{timestamp}-> {mensaje} \n"
            log_file.write(entrada)
            if mostrar_consola:
                print(entrada.strip())

def copiar_y_renombrar_archivo(ruta_origen, ruta_destino, nuevo_nombre, matiene_original = True):
    # Ejemplo de uso
    # ruta_origen = 'ruta/de/origen/archivo.txt'
    # ruta_destino = 'ruta/de/destino'
    # nuevo_nombre = 'nuevo_nombre.txt'
    # mover_y_renombrar_archivo(ruta_origen, ruta_destino, nuevo_nombre)
    if os.path.exists(ruta_origen):
        try:
            # Crear la ruta completa para el archivo en la nueva ubicación con el nuevo nombre
            ruta_destino_completa = os.path.join(ruta_destino, nuevo_nombre)
            #shutil.move(ruta_origen, ruta_destino_completa)
            if matiene_original:
                shutil.copy(ruta_origen, ruta_destino_completa)
                log_mesajes(f"Archivo copiado y renombrado exitosamente a {ruta_destino_completa}.", ruta_global,
                            "log.txt", True)
            else:
                shutil.move(ruta_origen, ruta_destino_completa)
                log_mesajes(f"Archivo movido exitosamente a {ruta_destino_completa}.", ruta_global, "log.txt", True)
        except Exception as e:
            #print(f"Error al mover y renombrar el archivo: {e}")
            log_mesajes(f"Error al mover y renombrar el archivo: {e}", ruta_global, "log.txt",True)
            log_mesajes(f"Error al mover y renombrar el archivo: {e}", ruta_global, "ERROR.log")
    else:
        log_mesajes("El archivo no existe en la ruta de origen.", ruta_global, "log.txt", True)
        log_mesajes("El archivo no existe en la ruta de origen.", ruta_global, "ERROR.log")

def elapsed_time(tiempo_transcurrido):
    # Convertir la diferencia a H:M:S
    horas = int(tiempo_transcurrido // 3600)
    minutos = int((tiempo_transcurrido % 3600) // 60)
    segundos = int(tiempo_transcurrido % 60)
    # Formatear la salida
    formato_hms = f"{horas:02}:{minutos:02}:{segundos:02}"
    return formato_hms

def sanitize_filename(filename):
    # Reemplaza los caracteres no válidos
    invalid_chars = [':', '°', '/', '\\']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Eliminar saltos de línea
    filename = filename.replace('\n', ' ').replace('\r', ' ')
    return filename

def extract_links_from_pdf(pdf_path):
    links = set()  # Usamos un set para evitar duplicados
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for annot in page.annots:
                if 'uri' in annot:
                    uri = annot['uri']
                    links.add(uri)  # Añadimos al set
    return list(links)  # Convertimos el set a lista para devolverlo

def extraer_texto_entre_textos(ruta_pdf,text1,text2):
    with pdfplumber.open(ruta_pdf) as pdf:
        pagina = pdf.pages[0]  # Obtener la primera página
        texto = pagina.extract_text()
        # Expresión regular para encontrar el texto entre las dos frases
        patron = re.compile(rf"{text1}\s*(.*?)\s*{text2}", re.DOTALL)
        coincidencia = patron.search(texto)
        #coincidencias = patron.findall(texto)
        if coincidencia:
            text_encontrado = coincidencia.group(1).strip()
            return text_encontrado
        else:
            return "No_encontrado"

def download_content_from_links(links, output_folder):
    downloaded_files = []
    for link in links:
        # Decodifica la URL y extrae el nombre del archivo
        decoded_link = unquote(link)
        # sanitized_link = urllib.parse.quote(link, safe=':/') # Esta opcion sanitiza los acentos y me falla por que algunas url tiene acentos.
        sanitized_link = link.replace("+", "%2B")
        # Extrae el nombre del archivo desde la URL y lo sanitiza
        filename = sanitize_filename(os.path.basename(urlparse(decoded_link ).path))
        file_path = os.path.join(output_folder, filename)
        #Evitamos descargar archivos ya descargados pero siempre descargo los anexos por que no se sus nombres.
        if not os.path.exists(file_path) or filename.isdigit():
            response = requests.get(sanitized_link)
            if response.status_code == 200:
                #obtengo el nombre del anexo ya que el filename siempre seria un numero.
                if filename.isdigit():
                    content_disposition = response.headers.get('Content-Disposition')
                    filename = content_disposition.split('filename=')[1]
                    if filename.startswith('"') or filename.startswith("'"):
                        filename = filename[1:-1]
                    filename = filename.encode('latin1').decode('utf-8')
                    filename = sanitize_filename(os.path.basename(filename))
                    file_path = os.path.join(output_folder, filename)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                log_mesajes(f"Descarga de Archivo: {filename}", ruta_global, "log.txt", True)
            else:
                log_mesajes(f"Descarga de Archivo: (http response error {response.status_code}) ruta: {sanitized_link}", ruta_global, "ERROR.log")
                log_mesajes(f"Descarga de Archivo: (http response error {response.status_code}) ruta: {sanitized_link}", ruta_global,
                            "log.txt",True)
        else:
            filename = filename + " (omitido)"
        downloaded_files.append(filename)
    return downloaded_files

def process_pdfs_in_folder(folder_path, in_folders = True):
    log_entries = []
    inicio_proceso = time.time()
    ahora = time.localtime()
    # formato = time.strftime("%Y-%m-%d %H:%M:%S", ahora)
    # log_entry = f"\n********************\nHora de inicio: {formato}"
    # log_entries.append(log_entry)
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            inicio_pdf = time.time()
            pdf_path = os.path.join(folder_path, filename)
            links = extract_links_from_pdf(pdf_path)
            nombre_proponente = extraer_texto_entre_textos(pdf_path, "Nombre del proponente", "Razón social")
            codigo_equipo = extraer_texto_entre_textos(pdf_path, "Código Tipo Equipo / Mobiliario:", "Nombre del Equipamiento:")
            nombre_equipo = extraer_texto_entre_textos(pdf_path, "Nombre del Equipamiento:", "Marca:")
            nombre_proponente = sanitize_filename(nombre_proponente)
            codigo_equipo = sanitize_filename(codigo_equipo)
            nombre_equipo = sanitize_filename(nombre_equipo)
            #print(f"Nombre del proponente: {nombre_proponente}")
            log_entries = [ f"Archivo en proceso {filename}",
                            f"Nombre del proponente: {nombre_proponente}",
                            f"Nombre del equipo: {nombre_equipo}",
                            f"Código Tipo Equipo / Mobiliario: {codigo_equipo}",
                            f"Cantidad de docs: {len(links)}"]
            log_mesajes(log_entries, ruta_global, "log.txt", True)
            if links:
                if in_folders:
                    output_folder = os.path.join(folder_path, nombre_proponente + "\\" +  os.path.splitext(filename)[0]+f"_{nombre_equipo}_{codigo_equipo}")
                else:
                    output_folder = os.path.join(folder_path, os.path.splitext(filename)[0])
                os.makedirs(output_folder, exist_ok=True)
                downloaded_files = download_content_from_links(links, output_folder)
                if in_folders:
                    copiar_y_renombrar_archivo(pdf_path, output_folder, filename[:-4]+f"_{nombre_equipo}_{codigo_equipo}.pdf")
                    destino_dir = os.path.dirname(f'{folder_path}\\pdfProcesados\\')  # Crear el directorio de destino si no existe
                    if not os.path.exists(destino_dir):
                        os.makedirs(destino_dir)
                    copiar_y_renombrar_archivo(pdf_path, destino_dir, filename, False ) #guarda los pdf procesados en otra carpeta que debe existir
                fin_pdf = time.time()
                formato_hms = elapsed_time(fin_pdf - inicio_pdf)
                #log_entry = f"{filename} Cantidad de docs: {len(downloaded_files)}\nTiempo en procesar este pdf {formato_hms} segundos\n" + "\n".join(downloaded_files)
                log_entries = [f"Cantidad de docs descargados: {len(downloaded_files)}",
                               f"Tiempo en procesar este pdf {formato_hms} segundos"]
                log_mesajes(log_entries, ruta_global, "log.txt", True)

# Ruta de la carpeta que contiene los PDFs


#ruta_global = 'C:\\Users\\josel\\Icarus\\TI - Documentos\\Proyectos\\Iem-pro\\La Serena\\G4_MC-licitacion1\\Ofertas_MC_G4'
#ruta_global = 'C:\\Users\\josel\\Icarus\\EEMM-MC-MNC - Copia Ofertas Recibidas'
#ruta_global = 'G:\\Mi unidad\\PDF-lrll\\COMERCIALIZADORA P&E SOLUCIONES INDUSTRIALES SPA'

folder_path = ruta_global
mensajes = [
    "-----------------------------------",
    "    Inicio proceso de ejecución    ",
    "-----------------------------------"
]
log_mesajes(mensajes, folder_path, "log.txt",True)
log_mesajes(f"Procesando carpeta: {folder_path}", folder_path, "log.txt",True)
inicio = time.time()
log_mesajes(f"Parte el análisis de los documentos", folder_path, "log.txt",True)
process_pdfs_in_folder(folder_path)
fin = time.time()
log_mesajes(f"Termina el análisis de los documentos:", folder_path, "log.txt",True)
formato_hms = elapsed_time(fin - inicio)
log_mesajes(f"El proceso tardó {formato_hms} (H:M:S) en ejecutarse.", folder_path, "log.txt",True)