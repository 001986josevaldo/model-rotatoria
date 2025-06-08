import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError

class S3Uploader:
    def __init__(self, aws_access_key, aws_secret_key, region, bucket_name, s3_folder='relatorios'):
        """
        Inicializa o uploader com credenciais da AWS, região, nome do bucket e pasta no S3.
        """
        self.bucket_name = bucket_name
        self.s3_folder = s3_folder
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region
        )

    def upload_file(self, local_file_path, s3_file_name=None):
        """
        Faz upload de um arquivo para o bucket S3.
        """
        if not s3_file_name:
            s3_file_name = os.path.basename(local_file_path)
        s3_key = os.path.join(self.s3_folder, s3_file_name)

        try:
            self.s3_client.upload_file(local_file_path, self.bucket_name, s3_key)
            print(f"✔ Arquivo enviado para s3://{self.bucket_name}/{s3_key}")
            return True
        except FileNotFoundError:
            print("❌ Arquivo local não encontrado.")
        except NoCredentialsError:
            print("❌ Credenciais da AWS não configuradas.")
        except ClientError as e:
            print(f"❌ Erro do cliente AWS: {e}")
        except Exception as e:
            print(f"❌ Erro inesperado: {e}")
        return False
    

# -------------------- EXMPLO DE USO ------------------------------
'''
from s3_uploader import S3Uploader
import os
from datetime import datetime

# Dados
current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
input_name = "video1"
base_name = f"inferencia_{current_time}_{input_name}"

# Caminho local do CSV
output_dir = 'Reports'
os.makedirs(output_dir, exist_ok=True)
local_path = os.path.join(output_dir, f"{base_name}_Relatorio.csv")

# Envio para o S3
uploader = S3Uploader(bucket_name='meu-bucket')
uploader.upload_file(local_path)'''