import os
import conf
import re
import requests
import pdfplumber
import time
import shutil
import json

# import urllib.parse
from urllib.parse import urlparse, unquote

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
        ruta = conf.ruta_global

    # Asegurarse de que la ruta existe
    os.makedirs(ruta, exist_ok=True)

    # Ruta completa del archivo de log
    ruta_completa = os.path.join(ruta, nombre_archivo)

    # Convertir el mensaje a lista si es un string
    if isinstance(mensajes, str):
        mensajes = [mensajes]

    # Obtener la fecha y hora actual
    # timestamp = time.strftime("%y-%m-%d/%H:%M:%S")
    timestamp = time.strftime("%y-%m-%d %H:%M:%S")

    # Abrir el archivo en modo append (crea el archivo si no existe)
    with open(ruta_completa, "a", encoding="utf-8") as log_file:
        for mensaje in mensajes:
            entrada = f"{timestamp}-> {mensaje} \n"
            log_file.write(entrada)
            if mostrar_consola:
                print(entrada.strip())

def copiar_y_renombrar_archivo(ruta_origen, ruta_destino, nuevo_nombre, matiene_original=True):
    # Ejemplo de uso
    # ruta_origen = 'ruta/de/origen/archivo.txt'
    # ruta_destino = 'ruta/de/destino'
    # nuevo_nombre = 'nuevo_nombre.txt'
    # mover_y_renombrar_archivo(ruta_origen, ruta_destino, nuevo_nombre)
    if os.path.exists(ruta_origen):
        try:
            # Crear la ruta completa para el archivo en la nueva ubicación con el nuevo nombre
            ruta_destino_completa = os.path.join(ruta_destino, nuevo_nombre)
            # shutil.move(ruta_origen, ruta_destino_completa)
            if matiene_original:
                shutil.copy(ruta_origen, ruta_destino_completa)
                log_mesajes(f"Archivo copiado y renombrado exitosamente a {ruta_destino_completa}.", conf.ruta_global,
                            "log.txt", True)
            else:
                shutil.move(ruta_origen, ruta_destino_completa)
                log_mesajes(f"Archivo movido exitosamente a {ruta_destino_completa}.", conf.ruta_global, "log.txt", True)
        except Exception as e:
            # print(f"Error al mover y renombrar el archivo: {e}")
            log_mesajes(f"Error al mover y renombrar el archivo: {e}", conf.ruta_global, "log.txt", True)
            log_mesajes(f"Error al mover y renombrar el archivo: {e}", conf.ruta_global, "ERROR.log")
    else:
        log_mesajes("El archivo no existe en la ruta de origen.", conf.ruta_global, "log.txt", True)
        log_mesajes("El archivo no existe en la ruta de origen.", conf.ruta_global, "ERROR.log")

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

def extraer_texto_entre_textos(ruta_pdf, text1, text2):
    with pdfplumber.open(ruta_pdf) as pdf:
        pagina = pdf.pages[0]  # Obtener la primera página
        texto = pagina.extract_text()
        # Expresión regular para encontrar el texto entre las dos frases
        patron = re.compile(rf"{text1}\s*(.*?)\s*{text2}", re.DOTALL)
        coincidencia = patron.search(texto)
        # coincidencias = patron.findall(texto)
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
        filename = sanitize_filename(os.path.basename(urlparse(decoded_link).path))
        file_path = os.path.join(output_folder, filename)
        # Evitamos descargar archivos ya descargados pero siempre descargo los anexos por que no se sus nombres.
        if not os.path.exists(file_path) or filename.isdigit():
            response = requests.get(sanitized_link)
            if response.status_code == 200:
                # obtengo el nombre del anexo ya que el filename siempre seria un numero.
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
                log_mesajes(f"Descarga de Archivo: {filename}", conf.ruta_global, "log.txt", True)
                downloaded_files.append(filename)
            else:
                log_mesajes(f"Descarga de Archivo: (http response error {response.status_code}) ruta: {sanitized_link}",
                            conf.ruta_global, "ERROR.log")
                log_mesajes(f"Descarga de Archivo: (http response error {response.status_code}) ruta: {sanitized_link}",
                            conf.ruta_global,"log.txt", True)
        else:
            filename = filename + " (omitido)"
            downloaded_files.append(filename)
    return downloaded_files

def process_pdfs_in_folder(folder_path, orderBy="equipo"):
    log_entries = []
    downloaded_files = []
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
            # Para filtrar y bajar solo el anexo que me intereza
            # links = [cadena for cadena in links if "anexo8G3" in cadena]
            nombre_proponente = extraer_texto_entre_textos(pdf_path, "Nombre del proponente", "Razón social")
            codigo_equipo = extraer_texto_entre_textos(pdf_path, "Código Tipo Equipo / Mobiliario:",
                                                       "Nombre del Equipamiento:")
            nombre_equipo = extraer_texto_entre_textos(pdf_path, "Nombre del Equipamiento:", "Marca:")
            nombre_proponente = sanitize_filename(nombre_proponente)
            codigo_equipo = sanitize_filename(codigo_equipo)
            nombre_equipo = sanitize_filename(nombre_equipo)
            # print(f"Nombre del proponente: {nombre_proponente}")
            log_entries = [f"Archivo en proceso {filename}",
                           f"Nombre del proponente: {nombre_proponente}",
                           f"Nombre del equipo: {nombre_equipo}",
                           f"Código Tipo Equipo / Mobiliario: {codigo_equipo}",
                           f"Cantidad de docs: {len(links)}"]
            log_mesajes(log_entries, conf.ruta_global, "log.txt", True)
            if links:
                match orderBy:
                    case "proponente":
                        #output_folder = os.path.join(folder_path, nombre_proponente + "\\" + os.path.splitext(filename)[0] + f"_{nombre_equipo}_{codigo_equipo}")
                        output_folder = os.path.join(folder_path,f"Ofertas_xProponente\\{nombre_proponente}\\{os.path.splitext(filename)[0]}{nombre_equipo}_{codigo_equipo}")
                        in_folders = True
                    case "equipo":
                        output_folder = os.path.join(folder_path,f"Ofertas_xEquipo\\{codigo_equipo}_{nombre_equipo}\\{nombre_proponente}_{os.path.splitext(filename)[0]}")
                        in_folders = True
                    case _:
                        output_folder = os.path.join(folder_path, f"Ofertas\\{os.path.splitext(filename)[0]}")
                        in_folders = False
                os.makedirs(output_folder, exist_ok=True)
                #descarga los archivos en enlaces
                downloaded_files = download_content_from_links(links, output_folder)
                # Coloca una copia del pdf de oferta en la carpeta donde estan todo los archivos desacargados
                copiar_y_renombrar_archivo(pdf_path, output_folder,filename[:-4] + f"_{nombre_equipo}_{codigo_equipo}.pdf")
                # Crear el directorio de destino si no existe
                destino_dir = os.path.dirname(f'{folder_path}\\pdfProcesados\\')
                if not os.path.exists(destino_dir):
                    os.makedirs(destino_dir)
                # guarda los pdf procesados en otra carpeta que debe existir
                copiar_y_renombrar_archivo(pdf_path, destino_dir, filename,False)

                fin_pdf = time.time()
                formato_hms = elapsed_time(fin_pdf - inicio_pdf)
                # log_entry = f"{filename} Cantidad de docs: {len(downloaded_files)}\nTiempo en procesar este pdf {formato_hms} segundos\n" + "\n".join(downloaded_files)
                log_entries = [f"Cantidad de docs descargados: {len(downloaded_files)}",
                               f"Tiempo en procesar este pdf {formato_hms} segundos"]
                log_mesajes(log_entries, conf.ruta_global, "log.txt", True)

def download_files(links, token, output_folder,fileName,fileExtension):
    downloaded_files = []
    tenat = conf.tenat
    headers = {
        "User-Agent": "JFL/0.0.1",
        "X-Tenant": tenat,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    for link in links:
        # Decodifica la URL y extrae el nombre del archivo
        decoded_link = unquote(link)
        ofertNumber = sanitize_filename(os.path.basename(urlparse(decoded_link).path))
        filename = f"{fileName}{ofertNumber}.{fileExtension}"
        file_path = os.path.join(output_folder, filename)
        if not os.path.exists(file_path):
            response = requests.get(link, headers=headers)
            if response.status_code == 200:
                content_disposition = response.headers.get('Content-Disposition')
                if not os.path.exists(output_folder):
                    os.makedirs(output_folder)
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                log_mesajes(f"Descarga de Archivo: {filename}", conf.ruta_global, "log.txt", True)
                downloaded_files.append(filename)
            else:
                log_mesajes(f"Descarga de Archivo: (http response error {response.status_code}) ruta: {link}",
                            conf.ruta_global, "ERROR.log")
                log_mesajes(f"Descarga de Archivo: (http response error {response.status_code}) ruta: {link}",
                            conf.ruta_global, "log.txt", True)
        else:
            log_mesajes(f"Descarga de Archivo: {filename} Omitida",
                            conf.ruta_global, "log.txt", True)
            downloaded_files.append(filename)
    return downloaded_files

def get_login_token():
    response = requests.post(conf.logingUrl, headers=conf.headers, data=json.dumps(conf.data))
    if response.status_code == 200:
        response_json = response.json()
        token = response_json.get("plain-text-token")
        if token:
            return {"token":token}
        else:
            return {"error":"El token no se encontró en la respuesta."}
    else:
        return {"error":f"Error al intentar login Status Code: {response.status_code}"}

inicio = time.time()
folder_path = conf.ruta_global
mensajes = [
    "-----------------------------------",
    "    Inicio proceso de ejecución    ",
    "-----------------------------------"
]
log_mesajes(mensajes, folder_path, "log.txt", True)
log_mesajes(f"Procesando carpeta: {folder_path}", folder_path, "log.txt", True)
log_mesajes(f"Parte el análisis de los documentos", folder_path, "log.txt", True)
# Proceso para obtener los pdf
oferts = []
oferts = [1309,1343,1356,624,643,644,649,650,651,652,653,654,704,705,706,735,737,739,740,741,744,745,746,747,750,751,752,753,754,755,756,757,758,759,760,761,765,766,767,768,769,770,773,774,777,782,804,874,876,897,901,1032,1121,1202,1205,1207,1208,1233,1237,1239,1240,1516,1603,1619,1634,1645,1649,1077,1746,1759,720,721,722,723,724,792,812,813,816,845,846,857,875,612,1040,1042,1044,1045,1046,1047,1049,1050,1052,1053,1360,573,579,580,574,1265,578,661,663,664,665,666,667,668,669,670,630,633,636,638,680,681,694,695,716,717,878,883,1033,1034,1038,1039,1072,584,585,586,587,588,590,591,593,603,604,605,607,641,1288,631,879,881,1048,1055,1058,1059,1062,1063,1064,1065,1066,1067,1068,1069,1070,1071,1073,1078,1081,1082,1084,1085,1086,1087,1088,1089,1090,1091,1092,1093,1094,1096,1103,1106,1117,1119,1124,1125,1126,1127,1129,1131,1132,1134,1135,1137,1138,1139,1140,1141,1142,1144,1145,1146,1156,1162,1182,1186,1209,1210,1214,1215,1216,1227,1230,1232,1236,1243,1273,1279,1294,1303,1320,825,826,827,828,829,831,832,833,834,835,836,838,841,842,844,778,779,780,781,784,786,787,788,1395,1467,1473,1491,1496,1497,1498,1499,1500,1501,1535,1554,1560,1563,1569,1575,1580,1582,1599,1612,1154,1159,1169,1286,1292,1306,1318,1350,1351,1352,1353,1355,1407,1164,1196,1263,1266,1277,1293,671,676,882,1188,1464,1511,1536,715,727,1212,1219,1220,1222,1223,1224,1231,1235,1257,1262,1488,793,801,850,851,854,860,861,866,868,869,1133,1157,1315,1370,1434,1463,1505,1513,805,806,807,809,810,811,999,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1013,1014,1015,1016,1017,1019,1020,1028,1029,1051,1061,1364,1429,1430,870,960,994,998,1025,1095,1107,1118,885,886,887,888,890,892,893,894,961,1022,1023,1174,1180,1189,1192,1256,1297,1299,1302,1307,1308,1310,1311,1312,1313,1377,1379,1380,1381,1382,1383,1387,1388,1389,1390,1391,1392,1393,1394,1097,1098,1099,1100,1102,1358,1366,1367,1369,1371,1372,1373,1374,1375,1376,1396,1398,1399,1400,1401,1402,1456,1462,1465,1472,1506,1526,1551,1559,1562,1566,1567,1570,1573,1577,1605,1622,1629,1632,1637,1639,1642,1644,1646,1648,1657,1663,1670,1708,1109,1111,1225,1327,1328,1331,1332,1333,1334,1335,1432,1433,1190,1211,1246,1247,1251,1258,1260,1503,1469,1504,1548,1552,1557,1558,1561,1585,1595,1596,1597,1321,1368,1431,1435,1436,1438,1439,1440,1442,1443,1444,1445,1446,1447,1448,1449,1450,1451,1453,1454,1455,1485,1486,1510,1301,1415,1416,1417,1418,1419,1420,1421,1422,1424,1425,1426,1427,1428,1397,1411,1512,1523,1540,1542,1543,1547,1556,1565,1571,1576,1588,1590,1591,1707,571,577,615,627,655,656,657,658,730,731,732,814,815,848,864,873,899,900,902,903,904,905,907,908,909,910,911,912,913,916,917,918,919,920,921,922,923,924,925,926,927,928,929,930,931,932,933,934,935,936,937,938,939,940,941,942,943,944,945,946,947,948,949,950,951,952,953,954,955,956,958,959,962,963,964,965,966,967,968,969,970,971,972,973,974,975,976,977,978,979,980,981,982,983,984,985,986,987,988,989,990,991,992,993,1275,1304,1314,1329,1330,1363,1468,1518,1519,1520,1521,1522,1525,1527,1528,1529,1530,1531,1532,1533,1534,1537,1541,1544,1572,1574,1578,1581,1584,1586,1587,1589,1592,1593,1594,1601,1610,1611,1614,1616,1617,1618,1620,1623,1624,1625,1626,1628,1631,1635,1640,1641,1667,1672,1675,1678,1682,1685,1688,1691,1694,1696,1709,1714,1718,1724,1725,1727,1729,1731,1733,1736,1740,1743,1745,1748,1751,1752,1754,1760,1762,1763,1765,1197,1198,1199,1200,1201,1203,1204,1348,1471,616,626,1165,1167,1170,1172,1229,1238,1268,1269,1280,1284,1285,1290,1291,1295,1336,1337,1357,1365,1404,1405,1406,1409,1441,1461,1476,1492,1493,1494,1495,1538,1545,1546,1550,1564,1568,1579,1583,617,618,632,1171,1175,1177,1178,1181,1183,1184,1228,1252,1253,1254,645,677,1036,1361,1474,1104,1105,1607,1669,1693,1711,1507,1549,1647,1650,1651,1654,1655,1660,1661,1668,1674,1677,1681,1684,1686,1689,1692,1695,1699,1700,1702,1703,1705,1710,1712,1715,1717,1721,1726,1734,1738,1741,1744,1749,1600,1609,1615,1621,1627,1630,1633,1636,1643,1652,1656,1658,1659,1662,1665,1666,1671,1673,1676,1680,1683,1687,1690,1697,1698,1701,1704,1706,1713,1716,1719,1720,1723,1728,1730,1732,1735,1737,1739,1742,1747,1750,1753,1755,1756,1757,1758,1761,1764,1766,1767]
#oferts = [765,766,767,768,769,770,773,774,777,782,804,874,876,897,901,1032,1121,1202,1205,1207,1208,1233,1237,1239,1240,1516,1603,1619,1634,1645,1649,1077,1746,1759,720,721,722,723,724,792,812,813,816,845,846,857,875,612,1040,1042,1044,1045,1046,1047,1049,1050,1052,1053,1360,573,579,580,574,1265,578,661,663,664,665,666,667,668,669,670,630,633,636,638,680,681,694,695,716,717,878,883,1033,1034,1038,1039,1072,584,585,586,587,588,590,591,593,603,604,605,607,641,1288,631,879,881,1048,1055,1058,1059,1062,1063,1064,1065,1066,1067,1068,1069,1070,1071,1073,1078,1081,1082,1084,1085,1086,1087,1088,1089,1090,1091,1092,1093,1094,1096,1103,1106,1117,1119,1124,1125,1126,1127,1129,1131,1132,1134,1135,1137,1138,1139,1140,1141,1142,1144,1145,1146,1156,1162,1182,1186,1209,1210,1214,1215,1216,1227,1230,1232,1236,1243,1273,1279,1294,1303,1320,825,826,827,828,829,831,832,833,834,835,836,838,841,842,844,778,779,780,781,784,786,787,788,1395,1467,1473,1491,1496,1497,1498,1499,1500,1501,1535,1554,1560,1563,1569,1575,1580,1582,1599,1612,1154,1159,1169,1286,1292,1306,1318,1350,1351,1352,1353,1355,1407,1164,1196,1263,1266,1277,1293,671,676,882,1188,1464,1511,1536,715,727,1212,1219,1220,1222,1223,1224,1231,1235,1257,1262,1488,793,801,850,851,854,860,861,866,868,869,1133,1157,1315,1370,1434,1463,1505,1513,805,806,807,809,810,811,999,1002,1003,1004,1005,1006,1007,1008,1009,1010,1011,1013,1014,1015,1016,1017,1019,1020,1028,1029,1051,1061,1364,1429,1430,870,960,994,998,1025,1095,1107,1118,885,886,887,888,890,892,893,894,961,1022,1023,1174,1180,1189,1192,1256,1297,1299,1302,1307,1308,1310,1311,1312,1313,1377,1379,1380,1381,1382,1383,1387,1388,1389,1390,1391,1392,1393,1394,1097,1098,1099,1100,1102,1358,1366,1367,1369,1371,1372,1373,1374,1375,1376,1396,1398,1399,1400,1401,1402,1456,1462,1465,1472,1506,1526,1551,1559,1562,1566,1567,1570,1573,1577,1605,1622,1629,1632,1637,1639,1642,1644,1646,1648,1657,1663,1670,1708,1109,1111,1225,1327,1328,1331,1332,1333,1334,1335,1432,1433,1190,1211,1246,1247,1251,1258,1260,1503,1469,1504,1548,1552,1557,1558,1561,1585,1595,1596,1597,1321,1368,1431,1435,1436,1438,1439,1440,1442,1443,1444,1445,1446,1447,1448,1449,1450,1451,1453,1454,1455,1485,1486,1510,1301,1415,1416,1417,1418,1419,1420,1421,1422,1424,1425,1426,1427,1428,1397,1411,1512,1523,1540,1542,1543,1547,1556,1565,1571,1576,1588,1590,1591,1707,571,577,615,627,655,656,657,658,730,731,732,814,815,848,864,873,899,900,902,903,904,905,907,908,909,910,911,912,913,916,917,918,919,920,921,922,923,924,925,926,927,928,929,930,931,932,933,934,935,936,937,938,939,940,941,942,943,944,945,946,947,948,949,950,951,952,953,954,955,956,958,959,962,963,964,965,966,967,968,969,970,971,972,973,974,975,976,977,978,979,980,981,982,983,984,985,986,987,988,989,990,991,992,993,1275,1304,1314,1329,1330,1363,1468,1518,1519,1520,1521,1522,1525,1527,1528,1529,1530,1531,1532,1533,1534,1537,1541,1544,1572,1574,1578,1581,1584,1586,1587,1589,1592,1593,1594,1601,1610,1611,1614,1616,1617,1618,1620,1623,1624,1625,1626,1628,1631,1635,1640,1641,1667,1672,1675,1678,1682,1685,1688,1691,1694,1696,1709,1714,1718,1724,1725,1727,1729,1731,1733,1736,1740,1743,1745,1748,1751,1752,1754,1760,1762,1763,1765,1197,1198,1199,1200,1201,1203,1204,1348,1471,616,626,1165,1167,1170,1172,1229,1238,1268,1269,1280,1284,1285,1290,1291,1295,1336,1337,1357,1365,1404,1405,1406,1409,1441,1461,1476,1492,1493,1494,1495,1538,1545,1546,1550,1564,1568,1579,1583,617,618,632,1171,1175,1177,1178,1181,1183,1184,1228,1252,1253,1254,645,677,1036,1361,1474,1104,1105,1607,1669,1693,1711,1507,1549,1647,1650,1651,1654,1655,1660,1661,1668,1674,1677,1681,1684,1686,1689,1692,1695,1699,1700,1702,1703,1705,1710,1712,1715,1717,1721,1726,1734,1738,1741,1744,1749,1600,1609,1615,1621,1627,1630,1633,1636,1643,1652,1656,1658,1659,1662,1665,1666,1671,1673,1676,1680,1683,1687,1690,1697,1698,1701,1704,1706,1713,1716,1719,1720,1723,1728,1730,1732,1735,1737,1739,1742,1747,1750,1753,1755,1756,1757,1758,1761,1764,1766,1767]
# oferts = [146, 339, 6, 354, 101, 88, 355, 102, 356, 103, 148, 357, 149, 262, 358, 119, 105, 426, 93, 145, 243, 272, 330,
#            359, 106, 143, 360, 107, 141, 274, 341, 361, 186, 75, 189, 244, 245, 276, 338, 345, 348, 206, 246, 255, 268,
#            283, 349, 370, 384, 207, 247, 273, 284, 296, 373, 391, 430, 231, 285, 297, 377, 227, 298, 378, 397, 299, 232,
#            275, 286, 233, 287, 311, 444, 251, 295, 300, 380, 220, 248, 277, 288, 308, 374, 433, 237, 313, 381, 301, 382,
#            411, 302, 383, 416, 289, 312, 228, 304, 386, 229, 303, 385, 418, 305, 421, 290, 291, 307, 458, 317, 342, 394,
#            187, 362, 120, 121, 122, 123, 109, 363, 124, 260, 201, 364, 392, 461, 170, 365, 111, 367, 112, 113, 368, 114,
#            369, 181, 372, 292, 242, 293, 306, 375, 460, 125, 387, 462, 115, 150, 379, 116, 151, 388, 117, 325, 326, 309,
#            327, 409, 279, 328, 413, 486, 329, 414, 344, 415, 89, 393, 90, 403, 171, 183, 154, 408, 155, 417, 128, 464,
#            218, 465, 129, 184, 118, 131, 132, 133, 134, 135, 136, 91, 137, 95, 96, 259, 98, 99, 94, 353, 352, 366, 351,
#            202, 182, 280, 337, 459, 447, 376, 264]
oferts = [574,571,573]

if len(oferts):
    ofertsLinks = [conf.getOfertUrl + str(ofert) for ofert in oferts]
    excelLinks = [conf.getExcelUrl + str(ofert) for ofert in oferts]
    token = get_login_token()
    if token.get('token') :
        log_mesajes("loging exitoso", conf.ruta_global, "log.txt", True)
        ofertFiles = download_files(ofertsLinks, token.get('token'), folder_path, "Oferta", "pdf")
        excelFiles = download_files(excelLinks, token.get('token'), f"{folder_path}\\EETT", "Eett", "xlsx")
        log_mesajes(f"PDF obtenidos/ofertas: {len(ofertFiles)}/{len(oferts)}", conf.ruta_global, "log.txt", True)
        log_mesajes(f"XLSX obtenidos/ofertas: {len(excelFiles)}/{len(oferts)}", conf.ruta_global, "log.txt", True)
    else:
        log_mesajes(token.get('error'), conf.ruta_global, "log.txt", True)
        log_mesajes(token.get('error'), conf.ruta_global, "ERROR.log", False)

# Procesa de los pdf descargados anterior mente o que se encuentren en la carpta
process_pdfs_in_folder(folder_path, "equipo")
#process_pdfs_in_folder(folder_path, "sinCarpetas")
#process_pdfs_in_folder(folder_path, "proponente")
fin = time.time()
log_mesajes(f"Termina el análisis de los documentos:", folder_path, "log.txt", True)
formato_hms = elapsed_time(fin - inicio)
log_mesajes(f"El proceso tardó {formato_hms} (H:M:S) en ejecutarse.", folder_path, "log.txt", True)
