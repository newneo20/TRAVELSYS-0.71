import pandas as pd
import os
from colorama import Fore, Style, init
import unicodedata
import re

# Inicializar colorama para colores en consola
init(autoreset=True)

# Definir colores más sugerentes
COLORES = {
    'EXITO': Fore.GREEN,
    'ERROR': Fore.RED,
    'ADVERTENCIA': Fore.YELLOW,
    'INFO': Fore.BLUE,
    'RESUMEN': Fore.MAGENTA,
    'DETALLE': Fore.CYAN
}

# Obtener la ruta del directorio donde está el script
script_dir = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(script_dir, 'Traslados.xlsx')

# Definir las reglas de sustitución (Asegurarse de que las claves estén en mayúsculas)
REGLAS_SUSTITUCION = {
    'AEPTO': 'AEROPUERTO',
    'GV': 'GUARDALAVACA',
    'GVACA': 'GUARDALAVACA',
    'H.': 'HOTEL',
    'H': 'HOTEL',
    'HOT.': 'HOTEL',
    'HOT': 'HOTEL',
    'HTL': 'HOTEL',
    'HTLES': 'HOTELES',
    'HTLS.': 'HOTELES',
    'HTLS': 'HOTELES',
    'JOSE MARTI NO. 3': 'AEROPUERTO JOSE MARTI TERMINAL 3',
    'JOSE MARTI NO.1 Y 2': 'AEROPUERTO JOSE MARTI TERMINAL 1 Y 2',
    'JOSE MARTI NO.5 (WAJAY)': 'AEROPUERTO JOSE MARTI TERMINAL 5 (WAJAY)',
    'PTO': 'PUNTO',
    'S SANTOS': 'SANCTI SPIRITUS',
    'SANTIAGO AEROPUERTO': 'AEROPUERTO SANTIAGO DE CUBA',
    'STA': 'SANTA',
    'STGO': 'SANTIAGO',
    'STO': 'SANTO'
}

def eliminar_caracteres_especiales(texto):
    """
    Elimina tildes, diéresis, puntos y espacios al final de la cadena.
    """
    if not isinstance(texto, str):
        return texto  # Evitar errores si el valor no es una cadena
    # Normalizar texto para eliminar acentos y diéresis
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    # Eliminar puntos
    texto = texto.replace('.', '')
    # Eliminar espacios al final
    texto = texto.rstrip()
    return texto

def aplicar_sustituciones(texto, reglas):
    """
    Aplica las sustituciones definidas en el diccionario de reglas dentro de cualquier parte del texto.
    """
    if not isinstance(texto, str):
        return texto  # Evitar errores si el valor no es una cadena
    original_texto = texto
    for clave, valor in reglas.items():
        # Crear un patrón que encuentre la clave dentro del texto, incluso si está en medio de otras palabras
        patron = re.compile(re.escape(clave), re.IGNORECASE)
        texto = patron.sub(valor, texto)
    if original_texto != texto:
        print(COLORES['INFO'] + f"SUSTITUCIÓN: '{original_texto}' => '{texto}'")
    return texto

def cargar_documento():
    """
    CARGA EL ARCHIVO EXCEL 'TRASLADOS.XLSX' DESDE EL DIRECTORIO DEL SCRIPT.
    
    RETURNS:
        pd.ExcelFile: Objeto ExcelFile si el archivo existe.
        None: Si el archivo no se encuentra o ocurre un error.
    """
    try:
        if os.path.exists(file_path):
            print(COLORES['EXITO'] + "DOCUMENTO CARGADO CORRECTAMENTE DESDE: " + file_path.upper())
            return pd.ExcelFile(file_path)
        else:
            print(COLORES['ERROR'] + "ERROR: NO SE ENCONTRÓ EL ARCHIVO 'TRASLADOS.XLSX' EN EL DIRECTORIO ACTUAL.".upper())
            return None
    except Exception as e:
        print(COLORES['ERROR'] + f"ERROR AL CARGAR EL DOCUMENTO: {e}".upper())
        return None

def transformar_a_mayusculas():
    """
    CONVIERTE LAS COLUMNAS DE TIPO STRING A MAYÚSCULAS EN TODAS LAS HOJAS DEL ARCHIVO EXCEL,
    APLICA SUSTITUICIONES ESPECÍFICAS, ELIMINA CARACTERES ESPECIALES, CUENTA LOS CAMBIOS
    REALIZADOS Y GUARDA EL ARCHIVO MODIFICADO.
    """
    try:
        excel_data = pd.read_excel(file_path, sheet_name=None)
    except Exception as e:
        print(COLORES['ERROR'] + f"ERROR AL LEER EL ARCHIVO EXCEL: {e}".upper())
        return

    resumen_cambios = {}

    for sheet_name, sheet_data in excel_data.items():
        cambios_por_columna = {}
        columnas_objeto = sheet_data.select_dtypes(include=['object']).columns

        for col in columnas_objeto:
            original_unique = sheet_data[col].nunique(dropna=False)
            # Convertir a mayúsculas
            sheet_data[col] = sheet_data[col].astype(str).str.upper()

            # Aplicar sustituciones si la columna es 'ORIGEN' o 'DESTINO' (incluyendo variantes plurales)
            if col.upper() in ['ORIGEN', 'ORIGENES', 'DESTINO', 'DESTINOS']:
                # Primero, aplicar las sustituciones
                sheet_data[col] = sheet_data[col].apply(lambda x: aplicar_sustituciones(x, REGLAS_SUSTITUCION))
                # Luego, eliminar caracteres especiales
                sheet_data[col] = sheet_data[col].apply(lambda x: eliminar_caracteres_especiales(x))
            
            nuevo_unique = sheet_data[col].nunique(dropna=False)
            cambios = nuevo_unique - original_unique
            cambios_por_columna[col] = cambios

        resumen_cambios[sheet_name] = cambios_por_columna
        excel_data[sheet_name] = sheet_data

    output_file_path = os.path.join(script_dir, "Traslados_MAYUSCULAS.xlsx")
    try:
        with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
            for sheet_name, sheet_data in excel_data.items():
                sheet_data.to_excel(writer, sheet_name=sheet_name, index=False)
        print(COLORES['ADVERTENCIA'] + f"DOCUMENTO GUARDADO COMO: {output_file_path}".upper())
    except Exception as e:
        print(COLORES['ERROR'] + f"ERROR AL GUARDAR EL ARCHIVO EXCEL: {e}".upper())
        return

    # Mostrar resumen de cambios
    for sheet, cambios in resumen_cambios.items():
        print(COLORES['DETALLE'] + f"\nRESUMEN DE CAMBIOS EN LA HOJA: {sheet}".upper())
        for col, count in cambios.items():
            print(COLORES['RESUMEN'] + f"   - COLUMNA '{col}': {count} MODIFICACIONES.".upper())

if __name__ == "__main__":
    documento = cargar_documento()
    if documento:
        transformar_a_mayusculas()
    else:
        print(COLORES['ERROR'] + "NO SE PUDO PROCESAR EL DOCUMENTO.".upper())
