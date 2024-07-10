# API de Valores UF y Dólar

Este repositorio contiene una API desarrollada en Python utilizando Flask, diseñada para obtener el valor de la UF y el valor del dólar para el día actual, desde la CMF (https://api.cmfchile.cl/) y almacenarlos en un archivo CSV. Este archivo CSV es alojado en un bucket S3. La aplicación está configurada para ser desplegada en un contenedor Docker y puede ser utilizada en un clúster EKS.

## Características Principales
- **API en Flask**: Obtiene los valores actuales de la UF y el dólar desde la API de la CMF.
- **Almacenamiento en S3**: Guarda el archivo CSV en un bucket S3.
- **Docker**: Incluye un Dockerfile para crear un contenedor de la aplicación.
- **Despliegue en EKS**: Preparada para ser utilizada en un clúster EKS.

## Instrucciones para Ejecutar la Aplicación
1. Clonar el repositorio:
    ```bash
    git clone <url-del-repositorio>
    ```
2. Navegar al directorio del proyecto:
    ```bash
    cd <nombre-del-repositorio>
    ```
3. Crear y activar un entorno virtual (opcional pero recomendado):
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
4. Instalar las dependencias:
    ```bash
    pip install -r requirements.txt
    ```
5. Definir las variables de entorno en un archivo `.env` basado en el archivo `.env.sample`:
    ```
    S3_BUCKET_NAME=nombre-del-bucket-s3
    CMF_API_KEY=api-key-cmf-valida
    CMF_BASE_URL=https://api.cmfchile.cl/api-sbifv3/recursos_api/
    BD=nombre-file.csv
    ```
6. Ejecutar la aplicación:
    ```bash
    python3 app.py
    ```

## Docker
Para construir y ejecutar la aplicación en un contenedor Docker de forma local:
1. Construir la imagen Docker:
    ```bash
    sudo docker buildx build --platform linux/amd64 -t nombre-imagen . --load
    ```
2. Ejecutar el contenedor:
    ```bash
    docker run -d --env-file .env nombre-imagen
    ```

## Variables de Entorno
- `S3_BUCKET_NAME`: Nombre del bucket S3.
- `CMF_API_KEY`: API key válida para la CMF.
- `CMF_BASE_URL`: URL base de la API de la CMF.
- `BD`: Nombre del archivo CSV.

## Contribuciones
Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request.

## Licencia
Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
