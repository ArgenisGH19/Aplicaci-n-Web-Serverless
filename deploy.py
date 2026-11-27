"""
Despliegue de la aplicación serverless (Infraestructura como Código con boto3).
Crea: tabla DynamoDB, función Lambda y su Function URL pública.
Uso:  python deploy.py
"""
import re
import time
import zipfile

import boto3
from botocore.exceptions import ParamValidationError

REGION = "us-east-1"
TABLA = "TablaTareas"
FUNCION = "API_Tareas"

# El LabRole existe en todas las cuentas del Learner Lab; solo cambia el ID de cuenta.
cuenta = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
LAB_ROLE_ARN = f"arn:aws:iam::{cuenta}:role/LabRole"

print("Iniciando despliegue de infraestructura. Esto tomará unos 2-3 minutos...")

# 1. Tabla en DynamoDB
dynamodb = boto3.client("dynamodb", region_name=REGION)
try:
    print(f"Creando tabla DynamoDB '{TABLA}'...")
    dynamodb.create_table(
        TableName=TABLA,
        KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 1, "WriteCapacityUnits": 1},
    )
    dynamodb.get_waiter("table_exists").wait(TableName=TABLA)
    print("Tabla creada exitosamente.")
except dynamodb.exceptions.ResourceInUseException:
    print("La tabla ya existe. Omitiendo...")

# 2. Empaquetar y crear la función Lambda
print("Empaquetando Lambda...")
with zipfile.ZipFile("lambda_deploy.zip", "w") as zipf:
    zipf.write("lambda_function.py")

lambda_client = boto3.client("lambda", region_name=REGION)
print("Desplegando función Lambda...")
try:
    with open("lambda_deploy.zip", "rb") as f:
        lambda_client.create_function(
            FunctionName=FUNCION,
            Runtime="python3.12",
            Role=LAB_ROLE_ARN,
            Handler="lambda_function.lambda_handler",  # archivo.función (sin ".py")
            Code={"ZipFile": f.read()},
            Timeout=10,
        )
    time.sleep(5)  # esperar a que asimile el rol
except lambda_client.exceptions.ResourceConflictException:
    print("La función Lambda ya existe. Omitiendo...")

# 3. Function URL pública
print("Configurando endpoint público (Function URL)...")
try:
    api_url = lambda_client.create_function_url_config(
        FunctionName=FUNCION,
        AuthType="NONE",
        Cors={"AllowOrigins": ["*"], "AllowMethods": ["*"]},
    )["FunctionUrl"]
except lambda_client.exceptions.ResourceConflictException:
    api_url = lambda_client.get_function_url_config(FunctionName=FUNCION)["FunctionUrl"]
    print("La Function URL ya existe.")


def permiso(sid, **extra):
    try:
        lambda_client.add_permission(
            FunctionName=FUNCION, StatementId=sid, Principal="*", **extra
        )
    except lambda_client.exceptions.ResourceConflictException:
        pass  # el permiso ya existe


# Una URL pública con AuthType NONE necesita los DOS permisos; con solo el primero responde 403.
permiso(
    "FunctionURLAllowPublicAccess",
    Action="lambda:InvokeFunctionUrl",
    FunctionUrlAuthType="NONE",
)
try:
    permiso(
        "FunctionURLInvokeAllowPublicAccess",
        Action="lambda:InvokeFunction",
        InvokedViaFunctionUrl=True,
    )
except ParamValidationError:
    print("Tu boto3 es antiguo. Actualiza con 'pip install -U boto3' o ejecuta:")
    print(
        f"aws lambda add-permission --function-name {FUNCION} "
        "--statement-id FunctionURLInvokeAllowPublicAccess "
        "--action lambda:InvokeFunction --principal '*' --invoked-via-function-url"
    )

# 4. Escribir la URL en index.html (si el archivo está en esta carpeta)
try:
    with open("index.html", encoding="utf-8", newline="") as f:
        html = f.read()
    html = re.sub(r'const API_URL = ".*?";', lambda m: f'const API_URL = "{api_url}";', html)
    with open("index.html", "w", encoding="utf-8", newline="") as f:
        f.write(html)
    print("index.html actualizado con la URL de la API.")
except FileNotFoundError:
    print("No se encontró index.html. Pega la URL manualmente en API_URL.")

print(f"\n¡ÉXITO! TU API URL ES: {api_url}")
print("Abre index.html en tu navegador. ¡El proyecto está funcionando!")
