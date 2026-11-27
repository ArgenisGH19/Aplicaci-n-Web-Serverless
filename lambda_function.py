import json
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('TablaTareas')

def lambda_handler(event, context):
    try:
        if event['requestContext']['http']['method'] == 'POST':
            body = json.loads(event['body'])
            tarea_id = str(uuid.uuid4())
            table.put_item(Item={'id': tarea_id, 'tarea': body['tarea'], 'estado': 'Pendiente'})
            return {"statusCode": 200, "body": json.dumps({"mensaje": "Tarea guardada", "id": tarea_id})}
            
        elif event['requestContext']['http']['method'] == 'GET':
            response = table.scan()
            return {"statusCode": 200, "body": json.dumps(response.get('Items', []))}
            
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
