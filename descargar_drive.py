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
except ImportError:
    os.system('pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib zipfile36 pytest-shutil tqdm==2.2.3')
    import zipfile
    import shutil
    from tqdm import tqdm
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
    from google.oauth2 import service_account

#Limpiamos la consola
os.system('cls' if os.name == 'nt' else 'clear')
for i in tqdm(range(100)):
    time.sleep(0.1)


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_files_in_folder(folder_id, drive_service, max_retries=3):
    query = f"'{folder_id}' in parents and trashed=false"
    files = []
    page_token = None
    while True:
        for attempt in range(1, max_retries + 1):
            try:
                response = drive_service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, modifiedTime, shortcutDetails)',
                    pageToken=page_token
                ).execute()
                break
            except Exception as e:
                print(f"⚠️ Error al listar archivos en la carpeta {folder_id} (Intento {attempt}/{max_retries}): {e}")
                if attempt == max_retries:
                    print(f"❌ No se pudo obtener la lista de la carpeta {folder_id}.")
                    return files
                # time.sleep(5)
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken')
        if not page_token:
            break
    return files

def download_file(file_id, file_name, folder_path, drive_service, mime_type=None, max_retries=3):
    if mime_type and mime_type.startswith('application/vnd.google-apps'):
        export_mime_types = {
            'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.google-apps.drawing': 'image/png'
        }
        export_mime = export_mime_types.get(mime_type, 'application/pdf')
        request = drive_service.files().export_media(fileId=file_id, mimeType=export_mime)
        ext_map = {
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
            'image/png': '.png',
            'application/pdf': '.pdf'
        }
        file_name += ext_map.get(export_mime, '.pdf')
    else:
        request = drive_service.files().get_media(fileId=file_id)

    ensure_dir(folder_path)
    file_path = os.path.join(folder_path, file_name)

    for attempt in range(1, max_retries + 1):
        try:
            with io.FileIO(file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        print(f"Descargando {file_name}... {int(status.progress() * 100)}%")
            print(f"✅ Descarga completada: {file_name}")
            break
        except Exception as e:
            print(f"⚠️ Error al descargar {file_name} (Intento {attempt}/{max_retries}): {e}")
            if attempt == max_retries:
                print(f"❌ No se pudo descargar {file_name}.")
            # else:
                # time.sleep(5)

def process_folder(folder_id, folder_path, drive_service, processed_folders, files_downloaded_counter):
    if folder_id in processed_folders:
        return
    processed_folders.add(folder_id)

    print(f"📂 Procesando carpeta: {folder_path}")
    ensure_dir(folder_path)
    files = get_files_in_folder(folder_id, drive_service)

    for file in tqdm(files, desc="Descargando archivos"):  
        file_id = file['id']
        file_name = file['name']
        mime_type = file['mimeType']

        if mime_type == 'application/vnd.google-apps.shortcut':
            target_id = file['shortcutDetails']['targetId']
            target_file = drive_service.files().get(
                fileId=target_id,
                fields='id, name, mimeType, modifiedTime'
            ).execute()
            if target_file['mimeType'] == 'application/vnd.google-apps.folder':
                process_folder(target_id, os.path.join(folder_path, target_file['name']), drive_service, processed_folders, files_downloaded_counter)
            else:
                download_file(target_id, target_file['name'], folder_path, drive_service, mime_type=target_file['mimeType'])
                files_downloaded_counter[0] += 1
            continue

        if mime_type == 'application/vnd.google-apps.folder':
            process_folder(file_id, os.path.join(folder_path, file_name), drive_service, processed_folders, files_downloaded_counter)
        else:
            download_file(file_id, file_name, folder_path, drive_service, mime_type=mime_type)
            files_downloaded_counter[0] += 1

def zip_directory(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder_path)
                zipf.write(file_path, arcname)

def main():
    start_time = time.time()
    print("🚀 Script iniciado...")

    #Lemos archivo credenciales.txt y de ahi obtenemos las rutas para el json y el id de la carpeta y la carpeta local
    with open('configuracion.txt', 'r') as file:
        lines = file.readlines()
        SERVICE_ACCOUNT_FILE = lines[0].strip()
        FOLDER_IDS = [fid.strip() for fid in lines[1].strip().split(',') if fid.strip()]
        OUTPUT_DIR = lines[2].strip()
        ZIP_OUTPUT = lines[3].strip()

    # Leemos el contenido de la dirección de credenciales y buscamos el archivo JSON
    credenciales_json = SERVICE_ACCOUNT_FILE
    if not os.path.isfile(credenciales_json) or not credenciales_json.endswith('.json'):
        raise FileNotFoundError(f"El archivo de credenciales no es válido: {credenciales_json}")
    else:
        print("🔑 Cargando credenciales...")
        SERVICE_ACCOUNT_FILE = credenciales_json
        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=credentials)
        print("✅ Credenciales cargadas.")

    # Crear las carpetas si no existen
    os.makedirs(ZIP_OUTPUT, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("✅ Configuración completada.")

    #Revisamos si las carpetas existen
    if not os.path.exists(ZIP_OUTPUT):
        print(f"📂 La carpeta {ZIP_OUTPUT} no existe. Creando...")
        os.makedirs(ZIP_OUTPUT)
        print(f"📂 Carpeta {ZIP_OUTPUT} creada.")
    if not os.path.exists(OUTPUT_DIR):
        print(f"📂 La carpeta {OUTPUT_DIR} no existe. Creando...")
        os.makedirs(OUTPUT_DIR)
        print(f"📂 Carpeta {OUTPUT_DIR} creada.")

    # Borrar carpeta anterior
    if os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    ensure_dir(OUTPUT_DIR)
    ensure_dir(ZIP_OUTPUT)

    processed_folders = set()
    files_downloaded_counter = [0]

    for folder_id in FOLDER_IDS:
        process_folder(folder_id, OUTPUT_DIR, service, processed_folders, files_downloaded_counter)

    zip_name = f"descarga_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(ZIP_OUTPUT, zip_name)
    print("📦 Creando ZIP...")
    zip_directory(OUTPUT_DIR, zip_path)
    print(f"📦 ZIP creado: {zip_path}")

    end_time = time.time()
    print(f"✅ Script completado en {end_time - start_time:.2f} segundos")

if __name__ == '__main__':
    main()    
