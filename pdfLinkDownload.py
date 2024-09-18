import os
import re
import requests
import pdfplumber
from urllib.parse import urlparse, unquote

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

def process_pdfs_in_folder(folder_path):
    log_entries = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            links = extract_links_from_pdf(pdf_path)
            print(filename, "Cantidad de docs: ", len(links))
            if links:
                output_folder = os.path.join(folder_path, os.path.splitext(filename)[0])
                os.makedirs(output_folder, exist_ok=True)
                downloaded_files = download_content_from_links(links, output_folder)
                log_entry = f"{filename} Cantidad de docs: {len(downloaded_files)}\n" + "\n".join(downloaded_files)
                log_entries.append(log_entry)
    # Escribe el log en un archivo
    with open(os.path.join(folder_path, 'log.txt'), 'w', encoding='utf-8') as log_file:
        log_file.write("\n\n".join(log_entries))

# Ruta de la carpeta que contiene los PDFs
folder_path = './pdf'
# folder_path = 'G:/Mi unidad/PDF-lrll/COMERCIALIZADORA P&E SOLUCIONES INDUSTRIALES SPA'
print("Procesando carpeta: ", folder_path)
process_pdfs_in_folder(folder_path)
