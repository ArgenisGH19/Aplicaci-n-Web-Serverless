# Aplicación Web Serverless

Gestor de tareas serverless con manejo de fallas (reintentos y estado degradado).
Computación Sustentable, proyecto final.

## Servicios AWS

| Servicio | Uso |
|---|---|
| AWS Lambda (Python 3.12) | Backend `API_Tareas` (GET y POST) |
| Lambda Function URL | Endpoint HTTPS público de la API |
| Amazon DynamoDB | Tabla `TablaTareas` (llave `id`) |

El frontend es `index.html` (HTML y JavaScript), que se abre en el navegador.

## Archivos

- `deploy.py`: crea toda la infraestructura (tabla, Lambda y URL pública).
- `lambda_function.py`: código del backend.
- `index.html`: interfaz con reintentos.

## Despliegue

Requisitos: Learner Lab iniciado, Python 3 y boto3 (en CloudShell ya vienen).

```
git clone https://github.com/ArgenisGH19/Aplicaci-n-Web-Serverless
cd Aplicaci-n-Web-Serverless
python deploy.py
```

El script imprime la URL de la API y la escribe en `index.html`. Abre `index.html` en el navegador.

## Prueba de resiliencia

```
aws lambda put-function-concurrency --function-name API_Tareas --reserved-concurrent-executions 0
aws lambda delete-function-concurrency --function-name API_Tareas
```

El primer comando simula la caída del backend; el segundo lo restaura.

## Limpieza

```
aws lambda delete-function-url-config --function-name API_Tareas
aws lambda delete-function --function-name API_Tareas
aws dynamodb delete-table --table-name TablaTareas
```
