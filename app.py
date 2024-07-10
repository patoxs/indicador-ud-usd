import os
from datetime import datetime, timedelta
from io import StringIO
import logging
from utils import obtener_datos_existentes, obtener_datos, list_to_csv, put_csv_to_s3
import boto3
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import csv

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración
S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')
FILE_NAME = os.environ.get('BD')
HOUR = os.environ.get('HORA')
MINUTE = os.environ.get('MINUTE')

# Configura el cliente de S3
s3_client = boto3.client('s3')
    
def guardar_datos():
    logger.info(f"Executing data saving")
    try:
        today = datetime.today()
        formatted_date = today.strftime("%d-%m-%Y")

        # Obtener datos existentes
        existing_data = obtener_datos_existentes()

        # Verificar si ya existen datos para hoy
        if existing_data[-1][0] == formatted_date:
            logger.warning(f"Data already exists for {formatted_date}. No new data will be saved.")
            return

        uf_value = None
        dolar_value = None
        logger.info(f"NONE: uf:{uf_value} - dolar:{dolar_value}")
        # Obtener datos de UF
        data_uf = obtener_datos('uf', today.year, today.month, today.day)
        if 'CodigoError' not in data_uf:
            uf_value = data_uf['UFs'][0]['Valor']
        else:
            logger.warning(f"There is no UF data for {formatted_date}: {data_uf.get('Mensaje', 'No data available')}")

        # Obtener datos de Dólar
        data_dolar = obtener_datos('dolar', today.year, today.month, today.day)
        if 'CodigoError' not in data_dolar:
            dolar_value = data_dolar['Dolares'][0]['Valor']
        else:
            logger.warning(f"There is no UF data for {formatted_date}: {data_dolar.get('Mensaje', 'No data available')}")

        logger.info(f"INFOINFO uf:{uf_value} - dolar:{dolar_value}")

        # Si no hay datos nuevos, usar los últimos valores conocidos
        if uf_value is None or dolar_value is None:
            if existing_data:
                last_data = existing_data[-1]
                uf_value = uf_value or last_data[4]
                dolar_value = dolar_value or last_data[5]
                logger.info(f"Using the latest known values for {formatted_date}")
            else:
                logger.error(f"No data available for {formatted_date} and no previous data found")
                return

        # Preparar los nuevos datos
        new_row = [formatted_date, today.day, today.month, today.year, uf_value, dolar_value]

        logger.info(f"new row: {new_row}")

        existing_data.append(new_row)

        logger.info(f"lista: {existing_data}")
        csv_content = list_to_csv(existing_data)
        logger.info(f"csv content: {csv_content}")
        put_csv_to_s3(csv_content)

    except requests.RequestException as e:
        logger.error(f"Error al obtener datos de la API: {e}")
    except Exception as e:
        logger.error(f"Error al guardar datos: {e}")

def recuperar_datos(currency, year, month, day):
    if currency not in ['uf', 'dolar']:
        return jsonify({"error": "Moneda no soportada"}), 400

    try:
        response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=FILE_NAME)
        csv_content = response['Body'].read().decode('utf-8')
        csv_reader = csv.reader(StringIO(csv_content), delimiter=';')
        next(csv_reader)  # Saltar la cabecera

        requested_date = datetime(year, month, day)
        requested_date_str = requested_date.strftime("%d-%m-%Y")
        
        matching_row = None
        last_row = None

        for row in csv_reader:
            last_row = row
            if row[0] == requested_date_str:
                matching_row = row
                break

        if matching_row:
            date_obj = datetime.strptime(matching_row[0], "%d-%m-%Y")
            value = matching_row[4] if currency == 'uf' else matching_row[5]
        elif last_row:
            # Si no se encuentra la fecha exacta, usar el último valor disponible
            date_obj = datetime.strptime(last_row[0], "%d-%m-%Y")
            value = last_row[4] if currency == 'uf' else last_row[5]
            logger.warning(f"No se encontraron datos para {requested_date_str}. Usando el último valor disponible del {date_obj.strftime('%Y-%m-%d')}.")
        else:
            return jsonify({"error": "No se encontraron datos"}), 404

        return jsonify({
            f"{currency.capitalize()}es": [
                {
                    "Valor": value,
                    "Fecha": date_obj.strftime("%Y-%m-%d")
                }
            ]
        })
    except Exception as e:
        logger.error(f"Error al recuperar datos: {e}")
        return jsonify({"error": "No se encontraron datos"}), 404

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"message": "Is a live"}), 200

@app.route('/guardar', methods=['PUT'])
def put_guardar_datos():
    guardar_datos()
    return jsonify({"message": "Datos guardados en S3 manualmente"})

@app.route('/<currency>/<int:year>/<int:month>/dias/<int:day>', methods=['GET'])
def get_recuperar_datos(currency, year, month, day):
    return recuperar_datos(currency, year, month, day)


# Configurar APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=guardar_datos, trigger='cron', hour=HOUR, minute=MINUTE)
scheduler.start()

# Cerrar el scheduler al terminar la aplicación
import atexit
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True)