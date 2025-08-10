from detect_service import trafic_analizer
from detectPet import pet_analizer
from detectGap import gap_analizer
import boto3
import json
import sys
import os
from utils.aws_credentials import AWSCredentials
# Parâmetros de configuração

aws_access_key = AWSCredentials.AWS_ACCESS_KEY_ID
aws_secret_key = AWSCredentials.AWS_SECRET_ACCESS_KEY
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





def lambda_function():  # index, xxx de parâmetros
    # 1) Recebe a mensagem da SQS (string JSON)
    raw_msg = msg()
    data = json.loads(raw_msg)
    print(data)

    # 2) Extrai campos (com defaults seguros)
    video_id = data.get("id")
    file_name = data.get("fileName")
    index = data.get("index", 0)

    if not file_name:
        raise ValueError("Mensagem sem 'fileName'.")

    # 3) Tenta caminho local primeiro
    local_video_dir = "/home/josevaldo/Downloads/Vdebora/115.mp4"
    local_video_path = os.path.join(local_video_dir, file_name)

    source = "local"
    resolved_path = local_video_path

    if not os.path.exists(local_video_path):
        # 4) Fallback para S3 caso o arquivo local não exista
        source = "s3"
        resolved_path = analyzer.s3_service.download_video(file_name)
        if not resolved_path or not os.path.exists(resolved_path):
            raise FileNotFoundError(
                f"Falha ao obter vídeo. Não existe local '{local_video_path}' "
                f"e download S3 retornou inválido: '{resolved_path}'"
            )

    # 5) Monta payload padronizado para o execute()
    video_info = {
        "id": video_id,
        "index": index,
        "source": source,            # 'local' ou 's3'
        "video_path": resolved_path, # caminho local garantido
    }

    print("msg rec.", video_info)

    # 6) Roteia conforme 'index'
    if index == 0:
        # analyzer.execute espera dict -> OK
        analyzer.execute(video_info)

    elif index == 1:
        # estes recebem caminho (string)
        analyzerPet.executePet(resolved_path)

    elif index == 2:
        analyzerGap.executeGap(resolved_path)

    else:
        print(f"[WARN] index desconhecido: {index}")

if __name__ == "__main__":
    lambda_function()