from detect_service import trafic_analizer
from detectPet import pet_analizer
from detectGap import gap_analizer
import boto3
import json
import sys
import os
from aws_credentials import AWSCredentials

# Parâmetros de configuração

aws_access_key = AWSCredentials.AWS_ACCESS_KEY_ID
aws_secret_key = AWSCredentials.AWS_SECRET_ACCESS_KEY
print(aws_access_key)
print(aws_secret_key)
region = "us-east-1"
bucket_name = "rotatoria-videos-bucket"
bucket_name_processed_videos = "rotatoria-processed-videos-bucket" 
bucket_name_reports = "rotatoria-reports" 

def msg():
    # Crie o cliente SQS
    sqs = boto3.client(
        'sqs',
        region_name='us-east-1',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key
        )
   
    # URL da sua fila SQS
    queue_url = 'ttps://sqs.us-east-1.amazonaws.com/179629269134/rotatoria-lambda-processed-videos-queue'
    # Recebe a mensagem
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10  # Long polling (melhora performance)
    )

    # Verifica se recebeu alguma mensagem
    messages = response.get('Messages', [])
    #messages = {"id": 7,"fileName": "rotatoria2-04-05-2025-1746383596192.mp4", "index": 2}
    # -------------  somente para teste 
    #messages = idfilename = '{"id": 7, "fileName": "testegap"}'
    
    if not messages:
        print("Nenhuma mensagem na fila.")
        sys.exit()
    
    else:
        for message in messages:
            #print("Mensagem recebida:", message['Body'])
            return message['Body']

            # Após processar, exclua a mensagem para que ela não volte à fila
            receipt_handle = message['ReceiptHandle']
            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=receipt_handle
            )
            print("Mensagem excluída.")
              
#https://sqs.us-east-1.amazonaws.com/179629269134/rotatoria-lambda-processed-videos-queue

# Inicializa o objeto da classe trafic_analizer com as credenciais
analyzer = trafic_analizer(
    aws_access_key=aws_access_key,
    aws_secret_key=aws_secret_key,
    region=region,
    bucket_name=bucket_name
)
analyzerPet = pet_analizer(
    aws_access_key=aws_access_key,
    aws_secret_key=aws_secret_key,
    region=region,
    bucket_name=bucket_name
)
analyzerGap = gap_analizer(
    aws_access_key=aws_access_key,
    aws_secret_key=aws_secret_key,
    region=region,
    bucket_name=bucket_name
)

def lambda_function(): # index, xxx de paramentros    
    #idfileName = msg()
    idfileName = '{"id": 7,"fileName": "parte_014.mp4", "index": 1}'
    print(idfileName)
    idfileName = json.loads(idfileName)

 
    if idfileName["index"] == 0:
        analyzer.execute(idfileName)

    elif idfileName["index"] == 1:
        analyzerPet.executePet(idfileName)

    elif idfileName["index"] == 2:
        analyzerGap.executeGap(idfileName)

if __name__== "__main__":
    lambda_function()

# {"id": 7,"fileName": "rotatoria2-04-05-2025-1746383596192.mp4", "index": 2}
