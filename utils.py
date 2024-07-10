import os
import boto3
from botocore.exceptions import ClientError
import io
from io import StringIO
import csv
import requests

# Configuración de logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configura el cliente de S3
s3_client = boto3.client('s3')

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
FILE_NAME = os.environ.get('BD')
BASE_URL = os.environ.get('CMF_BASE_URL')
API_KEY = os.environ.get('CMF_API_KEY')

def obtener_datos_existentes():
    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=FILE_NAME)
        csv_content = response['Body'].read().decode('utf-8')
        csv_reader = csv.reader(StringIO(csv_content), delimiter=';')
        next(csv_reader)  # Saltar la cabecera
        return list(csv_reader)
    except s3_client.exceptions.NoSuchKey:
        logger.info("No existe el archivo. Se creará uno nuevo.")
        return []
    except Exception as e:
        logger.error(f"Error al obtener datos existentes: {e}")
        return []
    
def obtener_datos(endpoint, year, month, day):
    url = f"{BASE_URL}{endpoint}/{year}/{month}/dias/{day}?apikey={API_KEY}&formato=json"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json',
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error obtaining data from {endpoint}: {e}")
        raise


def list_to_csv(data):
    csv_buffer = StringIO()
    csv_writer = csv.writer(csv_buffer, delimiter=';', doublequote=False, quoting=csv.QUOTE_NONE, escapechar=None, quotechar=None)
    
    for row in data:
        csv_writer.writerow(row)
    
    # Obtener el contenido del CSV como string
    csv_string = csv_buffer.getvalue()
    
    return csv_string

def put_csv_to_s3(csv_content):
    # Subir el archivo actualizado a S3
    s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=FILE_NAME, Body=csv_content)
    logger.info("Datos guardados en S3")