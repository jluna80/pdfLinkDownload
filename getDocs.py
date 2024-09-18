import os
import re
import requests
import pdfplumber

def extract_links_from_pdf(pdf_path):
    links = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            # Busca el texto "Ver Soporte" y extrae el enlace asociado
            matches = re.findall(r'(Ver soporte)', text)
            print (text)
            for match in matches:
                # Aquí puedes ajustar la lógica para extraer el enlace correcto
                # Por ejemplo, si el enlace está en la misma línea o cerca del texto "Ver Soporte"
                link = extract_link_near_text(text, match)
                if link:
                    links.append(link)
    print("enlace:",matches)
    return links

def extract_link_near_text(text, match):
    # Implementa la lógica para encontrar el enlace cerca del texto "Ver Soporte"
    # Esto puede variar dependiendo de cómo están formateados los PDFs
    # Aquí hay un ejemplo simple que busca un URL en la misma línea
    lines = text.split('\n')
    for line in lines:
        if match in line:
            url_match = re.search(r'(https?://\S+)', line)
            if url_match:
                return url_match.group(0)
    return None

def download_content_from_links(links, output_folder):
    for i, link in enumerate(links):
        response = requests.get(link)
        with open(os.path.join(output_folder, f'content_{i}.pdf'), 'wb') as f:
            f.write(response.content)

def process_pdfs_in_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(folder_path, filename)
            links = extract_links_from_pdf(pdf_path)
            if links:
                output_folder = os.path.join(folder_path, os.path.splitext(filename)[0])
                os.makedirs(output_folder, exist_ok=True)
                download_content_from_links(links, output_folder)

# Ruta de la carpeta que contiene los PDFs
folder_path = './pdf'
process_pdfs_in_folder(folder_path)
