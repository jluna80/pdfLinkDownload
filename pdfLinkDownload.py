import os
import re
import requests
import pdfplumber
import time
from urllib.parse import urlparse, unquote

import shutil
import os

def copiar_y_renombrar_archivo(ruta_origen, ruta_destino, nuevo_nombre):
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
            shutil.copy(ruta_origen, ruta_destino_completa)
            print(f"Archivo movido y renombrado exitosamente a {ruta_destino_completa}.")
        except Exception as e:
            print(f"Error al mover y renombrar el archivo: {e}")
    else:
        print("El archivo no existe en la ruta de origen.")

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
    invalid_chars = [':', '°']
    for char in invalid_chars:
        filename = filename.replace(char, '_')
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
        patron = re.compile(rf"{text1}\s*(.*?)\s*{text2}")
        coincidencia = patron.search(texto)
        if coincidencia:
            text_encontrado = coincidencia.group(1).strip()
            return text_encontrado
        else:
            return "No_encontrado"

def download_content_from_links(links, output_folder):
    downloaded_files = []
    for link in links:
        response = requests.get(link)
        # Decodifica la URL y extrae el nombre del archivo
        decoded_link = unquote(link)
        # Extrae el nombre del archivo desde la URL y lo sanitiza
        filename = sanitize_filename(os.path.basename(urlparse(decoded_link ).path))
        file_path = os.path.join(output_folder, filename)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        downloaded_files.append(filename)
        print(filename)
    return downloaded_files

def process_pdfs_in_folder(folder_path, in_folders = True):
    log_entries = []
    inicio_proceso = time.time()
    ahora = time.localtime()
    formato = time.strftime("%Y-%m-%d %H:%M:%S", ahora)
    log_entry = f"\n********************\nHora de inicio: {formato}"
    log_entries.append(log_entry)
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            inicio_pdf = time.time()
            pdf_path = os.path.join(folder_path, filename)
            links = extract_links_from_pdf(pdf_path)
            nombre_proponente = extraer_texto_entre_textos(pdf_path, "Nombre del proponente", "Razón social")
            codigo_equipo = extraer_texto_entre_textos(pdf_path, "Código Tipo Equipo / Mobiliario:", "Nombre del Equipamiento:")
            nombre_equipo = extraer_texto_entre_textos(pdf_path, "Nombre del Equipamiento:", "Código Tipo Equipo / Mobiliario:")
            print(f"Nombre del proponente: {nombre_proponente}")
            print(f"Código Tipo Equipo / Mobiliario: {codigo_equipo}")
            print(filename, "Cantidad de docs: ", len(links))
            if links:
                if in_folders:
                    output_folder = os.path.join(folder_path, nombre_proponente + "\\" +  os.path.splitext(filename)[0]+f"_{nombre_equipo}_{codigo_equipo}")
                else:
                    output_folder = os.path.join(folder_path, os.path.splitext(filename)[0])
                os.makedirs(output_folder, exist_ok=True)
                downloaded_files = download_content_from_links(links, output_folder)
                if in_folders:
                    copiar_y_renombrar_archivo(pdf_path, output_folder, filename[:-4]+f"_{nombre_equipo}_{codigo_equipo}.pdf")
                fin_pdf = time.time()
                formato_hms = elapsed_time(fin_pdf - inicio_pdf)
                log_entry = f"{filename} Cantidad de docs: {len(downloaded_files)}\nTiempo en procesar este pdf {formato_hms} segundos\n" + "\n".join(downloaded_files)
                log_entries.append(log_entry)
    # Escribe el log en un archivo
    fin_proceso = time.time()
    ahora = time.localtime()
    formato = time.strftime("%Y-%m-%d %H:%M:%S", ahora)
    formato_hms = elapsed_time(fin_proceso - inicio_proceso)
    log_entry = f"Hora de fin: {formato}\nTiempo total {formato_hms} (H:M:S) "
    log_entries.append(log_entry)
    with open(os.path.join(folder_path, 'log.txt'), 'a', encoding='utf-8') as log_file:
        log_file.write("\n\n".join(log_entries))

# Ruta de la carpeta que contiene los PDFs
folder_path = './pdf'
# folder_path = 'C:/Users/josel/Icarus/TI - Documentos/Proyectos/Iem-pro/La Serena/G4_MC-licitacion1/Ofertas_MC_G4'
# folder_path = 'G:/Mi unidad/PDF-lrll/COMERCIALIZADORA P&E SOLUCIONES INDUSTRIALES SPA'

print("Procesando carpeta: ", folder_path)
inicio = time.time()
ahora = time.localtime()
formato = time.strftime("%Y-%m-%d %H:%M:%S", ahora)
print("Hora de inicio: ", formato)
process_pdfs_in_folder(folder_path)
fin = time.time()
ahora = time.localtime()
formato = time.strftime("%Y-%m-%d %H:%M:%S", ahora)
print("Hora de Fin: ", formato)
formato_hms = elapsed_time(fin - inicio)
print(f"La función tardó {formato_hms} (H:M:S) en ejecutarse.")
