import os
import io
import time
from datetime import datetime
#Revisamos que tengamos todas las librerias instaladas y si no las instalamos
try:
    import zipfile
    import shutil
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2 import service_account
    from tqdm import tqdm
    from tkinter import *
except ImportError:
    os.system('pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib zipfile36 pytest-shutil tqdm==2.2.3 tkintertable')
    import zipfile
    import shutil
    from tqdm import tqdm
    from tkinter import *
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2 import service_account

#Limpiamos la consola
os.system('cls' if os.name == 'nt' else 'clear')

master = Tk()
#Damos un nombre a la ventana
master.title("Descargas Drive")
#Definimos el tamaño de la ventana
master.geometry("400x300")

#Funcion para cerrar la ventana
def close_window():
    master.destroy()

#Solicita los datos de la carpeta a descargar
def solicitar_datos():
    folder_id = folder_id_entry.get()
    folder_path = folder_path_entry.get()
    folder_id_entry.delete(0, END)
    folder_path_entry.delete(0, END)
    return imprimir_datos(folder_id, folder_path)

#Imprimos los datos obtenidos en una tabla
def imprimir_datos(folder_id, folder_path):
    Label(master, text="ID de la carpeta:").grid(row=0, column=0)
    Label(master, text=folder_id).grid(row=0, column=1)

    Label(master, text="Ruta de la carpeta:").grid(row=1, column=0)
    Label(master, text=folder_path).grid(row=1, column=1)

Label(master, text="ID de la carpeta:").grid(row=0, column=0)
folder_id_entry = Entry(master)
folder_id_entry.grid(row=0, column=1)

Label(master, text="Ruta de la carpeta:").grid(row=1, column=0)
folder_path_entry = Entry(master)
folder_path_entry.grid(row=1, column=1)

Button(master, text="Aceptar", command=solicitar_datos).grid(row=2, column=0, columnspan=2, pady=10)

Button(master, text="Salir", command=close_window).grid(row=3, column=0, columnspan=2, pady=10)

mainloop()

#Llamamos a la funcion para solicitar los datos
def main():
    solicitar_datos(
        folder_id_entry.get(),
        folder_path_entry.get()
    )

    imprimir_datos(
        folder_id_entry.get(),
        folder_path_entry.get()
    )

#Iniciamos el proyecto
if __name__ == '__main__':
    main()

#Funcion para descargar los archivos
# def descargar_archivos():
#     #Lemos archivo credenciales.txt y de ahi obtenemos las rutas para el json y el id de la carpeta y la carpeta local
#     with open('configuracion.txt', 'r') as file:
#         lines = file.readlines()
#         SERVICE_ACCOUNT_FILE = lines[0].strip()
#         FOLDER_IDS = [fid.strip() for fid in lines[1].strip().split(',') if fid.strip()]
#         OUTPUT_DIR = lines[2].strip()
#         ZIP_OUTPUT = lines[3].strip()

#     # Leemos el contenido de la dirección de credenciales y buscamos el archivo JSON
#     credenciales_json = SERVICE_ACCOUNT_FILE
#     if not os.path.isfile(credenciales_json) or not credenciales_json.endswith('.json'):
#         raise FileNotFoundError(f"El archivo de credenciales no es válido: {credenciales_json}")
#     else:
#         print("🔑 Cargando credenciales...")
#         SERVICE_ACCOUNT_FILE = credenciales_json
#         SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
#         credentials = service_account.Credentials.from_service_account_file(
#             SERVICE_ACCOUNT_FILE, scopes=SCOPES)
#         service = build('drive', 'v3', credentials=credentials)
#         print("✅ Credenciales cargadas.")

#     # Crear las carpetas si no existen
#     os.makedirs(ZIP_OUTPUT, exist_ok=True)
#     os.makedirs(OUTPUT_DIR, exist_ok=True)

#     print("✅ Configuración completada.")
#     print("🚀 Descargando archivos...")

#     for folder_id in FOLDER_IDS:
#         files = get_files_in_folder(folder_id, service)
#         for file in tqdm(files, desc=f"Descargando archivos de la carpeta {folder_id}"):
#             file_id = file['id']
#             file_name = file['name']
#             file_path = os.path.join(OUTPUT_DIR, file_name)
#             mime_type = file['mimeType']

#             if mime_type == 'application/vnd.google-apps.shortcut':
#                 target_id = file['shortcutDetails']['targetId']
#                 target_file = service.files().get(
#                     fileId=target_id,
#                     fields='id, name, mimeType, modifiedTime'
#                 ).execute()
#                 if target_file['mimeType'] == 'application/vnd.google-apps.folder':
#                     process_folder(target_id, os.path.join(OUTPUT_DIR, target_file['name']), service, processed_folders, files_downloaded_counter)
#                 else:
#                     download_file(target_id, target_file['name'], OUTPUT_DIR, service, mime_type=target_file['mimeType'])
#                     files_downloaded_counter[0] += 1
#                 continue

#             if mime_type == 'application/vnd.google-apps.folder':
#                 process_folder(file_id, os.path.join(OUTPUT_DIR, file_name), service, processed_folders, files_downloaded_counter)
#             else:
#                 download_file(file_id, file_name, OUTPUT_DIR, service, mime_type=mime_type)
#                 files_downloaded_counter[0] += 1

#     print(f"✅ Descarga completada. Se descargaron {files_downloaded_counter[0]} archivos en {time.time() - start_time:.2f} segundos.")
#     print("🚀 Comprimiendo archivos...")

#     zip_directory(OUTPUT_DIR, ZIP_OUTPUT + "/descargas.zip")
#     print("✅ Archivos comprimidos en descargas.zip.")

#     print("🚀 Listo para descargar en la carpeta descargas.zip.")

#     close_window()

# #Funcion para descargar un archivo
# def download_file(file_id, file_name, output_dir, service, mime_type=None):
#     request = service.files().get_media(fileId=file_id)
#     file_path = os.path.join(output_dir, file_name)
#     if mime_type == 'application/vnd.google-apps.folder':
#         return
#     with open(file_path, 'wb') as file:
#         downloader = MediaIoBaseDownload(file, request)
#         done = False
#         while done is False:
#             status, done = downloader.next_chunk()
#             print(f"📥 Descargando {file_name} ({status.progress() * 100:.2f}%)")

# #Funcion para descargar una carpeta
# def process_folder(folder_id, output_dir, service, processed_folders, files_downloaded_counter):
#     if folder_id in processed_folders:
#         return
#     processed_folders.add(folder_id)
#     files = get_files_in_folder(folder_id, service)
#     for file in files:
#         file_id = file['id']
#         file_name = file['name']
#         mime_type = file['mimeType']
#         if mime_type == 'application/vnd.google-apps.folder':
#             process_folder(file_id, os.path.join(output_dir, file_name), service, processed_folders, files_downloaded_counter)
#         else:
#             download_file(file_id, file_name, output_dir, service, mime_type=mime_type)
#             files_downloaded_counter[0] += 1

# #Funcion para obtener los archivos de una carpeta
# def get_files_in_folder(folder_id, service):
#     query = f"'{folder_id}' in parents and trashed=false"
#     files = []
#     page_token = None
#     while True:
#         response = service.files().list(
#             q=query,
#             spaces='drive',
#             fields='nextPageToken, files(id, name, mimeType, modifiedTime)',
#             pageToken=page_token
#         ).execute()
#         files.extend(response.get('files', []))
#         page_token = response.get('nextPageToken')
#         if not page_token:
#             break
#     return files