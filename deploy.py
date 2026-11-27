import boto3
import time
import zipfile
import os

# --- CONFIGURACIÓN ---
# PEGA AQUÍ EL ARN DE TU LABROLE QUE BUSCASTE EN EL PASO 1
LAB_ROLE_ARN = "arn:aws:iam::258891373326:role/LabRole" 
REGION = "us-east-1"
# ---------------------

print("Iniciando despliegue de infraestructura. Esto tomará unos 2-3 minutos...")

# 1. Crear tabla en DynamoDB
dynamodb = boto3.client('dynamodb', region_name=REGION)
try:
    print("Creando tabla DynamoDB 'TablaTareas'...")
    dynamodb.create_table(
        TableName='TablaTareas',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )
    # Esperar a que la tabla exista
    waiter = dynamodb.get_waiter('table_exists')
    waiter.wait(TableName='TablaTareas')
    print("Tabla creada exitosamente.")
except dynamodb.exceptions.ResourceInUseException:
    print("La tabla ya existe. Omitiendo...")

# 2. Empaquetar y Crear Lambda
print("Empaquetando Lambda...")
with zipfile.ZipFile('lambda_deploy.zip', 'w') as zipf:
    zipf.write('lambda_function.py')

lambda_client = boto3.client('lambda', region_name=REGION)
print("Desplegando función Lambda...")
try:
    response_lambda = lambda_client.create_function(
        FunctionName='API_Tareas',
        Runtime='python3.12',
        Role=LAB_ROLE_ARN,
        Handler='lambda_function.py.lambda_handler',
        Code={'ZipFile': open('lambda_deploy.zip', 'rb').read()},
        Timeout=10
    )
    time.sleep(5) # Esperar a que asimile el rol
except lambda_client.exceptions.ResourceConflictException:
    print("La función Lambda ya existe. Omitiendo...")

# 3. Crear Function URL (API Gateway Serverless)
print("Configurando Endpoint Público (Function URL)...")
try:
    response_url = lambda_client.create_function_url_config(
        FunctionName='API_Tareas',
        AuthType='NONE',
        Cors={'AllowOrigins': ['*'], 'AllowMethods': ['*']}
    )
    api_url = response_url['FunctionUrl']
    
    # Dar permisos públicos
    lambda_client.add_permission(
        FunctionName='API_Tareas',
        StatementId='FunctionURLAllowPublicAccess',
        Action='lambda:InvokeFunctionUrl',
        Principal='*',
        FunctionUrlAuthType='NONE'
    )
    print(f"\n¡ÉXITO! TU API URL ES: {api_url}")
    print("-> PEGA ESTA URL en la variable API_URL de tu archivo index.html")
except Exception as e:
    print(f"Error al crear URL (o ya existe): {e}")

print("\nPasos finales:")
print("1. Pon la URL en tu index.html")
print("2. Abre index.html en tu navegador. ¡El proyecto está funcionando!")
