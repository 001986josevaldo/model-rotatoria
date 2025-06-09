
import boto3
from smart_open import open as smart_open_open
import tempfile
from botocore.exceptions import ClientError, NoCredentialsError
import os
import shutil
import requests
import subprocess

class S3VideoService:
    def __init__(self, aws_access_key, aws_secret_key, region, bucket_name, s3_folder='reports'):
        self.aws_access_key = aws_access_key
        self.aws_secret_key = aws_secret_key
        self.region = region
        self.bucket_name = bucket_name
        self.s3_folder = s3_folder
        self._temp_file = None  # Arquivo temporário local

        self.session = boto3.Session(
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.region
        )
        self.s3 = self.session.client("s3")

    def video_exists(self, video_key):
        try:
            self.s3.head_object(Bucket=self.bucket_name, Key=video_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == "404":
                return False
            else:
                raise

    def get_oldest_video_key(self, prefix=''):
        """
        Retorna a chave (nome) do vídeo mais antigo no bucket S3.
        """
        try:
            response = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            if 'Contents' not in response:
                raise FileNotFoundError("Nenhum arquivo encontrado no bucket.")

            # Ordena os arquivos pela data de modificação (mais antigo primeiro)
            sorted_files = sorted(response['Contents'], key=lambda x: x['LastModified'])
            #nome do vide vai ser passado pela msg que esta sendo recebida pela variavel por exemplo {"id":12,"fileName":"rotatoria2-04-05-2025-1746362982243.mp4"}
            return sorted_files[0]['Key']  # Retorna o nome do mais antigo

        except ClientError as e:
            raise RuntimeError(f"Erro ao listar objetos do bucket: {e}")

    def get_video_key_from_message(self, message_dict):
        """
        Retorna o nome do vídeo com base na mensagem recebida.
        Exemplo de entrada: {"id":12,"fileName":"rotatoria2-04-05-2025-1746362982243.mp4"}
        """
        try:
            file_name = message_dict.get("fileName")
            if not file_name:
                raise ValueError("Chave 'fileName' não encontrada na mensagem.")
            return file_name
        except Exception as e:
            raise RuntimeError(f"Erro ao extrair nome do vídeo da mensagem: {e}")



    def download_video(self, video_key):
        if not self.video_exists(video_key):
            raise FileNotFoundError(f"🎥 Vídeo '{video_key}' não encontrado no bucket '{self.bucket_name}'.")

        s3_uri = f"s3://{self.bucket_name}/{video_key}"
        try:
            self._temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            with smart_open_open(
                s3_uri,
                'rb',
                transport_params={'client': self.s3}
            ) as s3_stream:
                self._temp_file.write(s3_stream.read())
                self._temp_file.flush()
            
            return self._temp_file.name
        except Exception as e:
            print(f"❌ Erro ao baixar vídeo do S3: {e}")
            raise

    def delete_video(self, video_key):
        if not self.video_exists(video_key):
            print(f"⚠️ Vídeo '{video_key}' não encontrado. Nenhuma exclusão realizada.")
            return

        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=video_key)
            print(f"✅ Vídeo '{video_key}' deletado com sucesso do bucket '{self.bucket_name}'")
        except Exception as e:
            print(f"⚠️ Erro ao deletar o vídeo '{video_key}': {e}")

    def cleanup(self):
        if self._temp_file:
            temp_path = self._temp_file.name
            self._temp_file.close()
            os.unlink(temp_path)  # Apaga o arquivo
            self._temp_file = None

    def upload_file(self, 
                    local_file_path, 
                    s3_file_name=None, 
                    destination_bucket="rotatoria-reports",
                    video_id=None,
                    name=None):
        """
        Faz upload de um arquivo para a raiz do bucket S3 especificado (sem pastas)
        e atualiza o status do relatório correspondente via API.
        """
        if not s3_file_name:
            s3_file_name = os.path.basename(local_file_path)

        try:
            
            response = requests.get(
                "http://3.234.193.156:8080/api/report/submit_file",
                params={"fileName": s3_file_name,
                        "bucket": destination_bucket
                }
            ) 
            if response.status_code != 200:
                print(f"❌ Erro ao obter URL assinada: {response.status_code} - {response.text}")
                return False
            data = response.json()
            url = data.get("url")
            name = data.get("fileName")

            with open(local_file_path, 'rb') as f:
                upload_resp = requests.put(
                    url ,
                    data=f,
                    #headers={'Content-Type': "relat/mp4"}
                )

            if upload_resp.status_code == 200:
                print(f"✔ Relatorio '{s3_file_name}' enviado com sucesso.")
                self.atualizar_report_por_id(video_id=video_id, 
                                             name= s3_file_name, 
                                             report_name=name,
                                             status='COMPLETED')
                return True
            
            else:
                print(f"❌ Falha no upload para URL assinada: {upload_resp.status_code}")
                self.atualizar_report_por_id(video_id=video_id, 
                                             name = s3_file_name, 
                                             report_name=name,  
                                             status='FAILED')
                return False
            '''
            print(f"✔ Arquivo enviado para s3://{destination_bucket}/{s3_file_name}")

            # Atualiza o relatório, se info disponível
            if video_id and name:
                self.atualizar_report_por_id(
                    video_id=video_id,
                    name=name,
                    status="COMPLETED"
                )

            return True'''

        except FileNotFoundError:
            print("❌ Arquivo local não encontrado.")
            if video_id and name:
                self.atualizar_report_por_id(
                    video_id=video_id,
                    name=name,
                    status="FAILED"
                )

        except NoCredentialsError:
            print("❌ Credenciais da AWS não configuradas.")

        except ClientError as e:
            print(f"❌ Erro do cliente AWS: {e}")

        except Exception as e:
            print(f"❌ Erro inesperado: {e}")

        return False
    
    @staticmethod
    def convert_video_to_h264(input_video):
        """
        Converte um vídeo para o codec H.264 usando ffmpeg, sobrescrevendo o arquivo original.
        """
        try:
            temp_output = input_video + ".tmp.mp4"
            command = [
                "ffmpeg",
                "-i", input_video,
                "-vcodec", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "medium",
                "-crf", "23",
                temp_output
            ]
            subprocess.run(command, check=True)
            os.replace(temp_output, input_video)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Erro ao converter vídeo para H.264: {e}")
            return False
        
#       backend_endpoint="http://3.234.193.156:8080/api/video/submit_file",

    def upload_processed_video(
        self,
        processed_dir,
        video_name=None,
        destination_bucket="rotatoria-processed-videos-bucket",
        video_id=None,

    ):
        """
        Faz upload de um vídeo processado para a raiz do bucket S3 especificado.
        """
        try:
            if not video_name:
                videos = [f for f in os.listdir(processed_dir) if f.endswith(".mp4")]
                if not videos:
                    print("❌ Nenhum vídeo .mp4 encontrado no diretório de processados.")
                    return False
                video_name = videos[0]

            local_file_path = os.path.join(processed_dir, video_name)

            if not os.path.isfile(local_file_path):
                print(f"❌ Arquivo '{local_file_path}' não encontrado.")
                return False
            #response = requests.get(submit_url="http://3.234.193.156:8080/api/video/submit_file", params={"fileName": video_name})
            response = requests.get(
                "http://3.234.193.156:8080/api/video/submit_file",
                params={"fileName": video_name,
                        "isProcessed": True,
                        "bucket": destination_bucket
                
                }
            ) 
            if response.status_code != 200:
                print(f"❌ Erro ao obter URL assinada: {response.status_code} - {response.text}")
                return False
            data = response.json()
            url = data.get("url")

            with open(local_file_path, 'rb') as f:
                upload_resp = requests.put(
                    url ,
                    data=f,
                    headers={'Content-Type': "video/mp4"}
                )

            if upload_resp.status_code == 200:
                print(f"✔ Vídeo '{video_name}' enviado com sucesso.")
                self.atualizar_video_por_id(video_id=video_id, status='COMPLETED')
                return True
            else:
                print(f"❌ Falha no upload para URL assinada: {upload_resp.status_code}")
                self.atualizar_video_por_id(video_id=video_id, status='FAILED')
                return False
    
            print(f"✔ Vídeo enviado para s3://{destination_bucket}/{video_name}")

            self.atualizar_video_por_id(
                video_id=video_id,
                status='COMPLETED'
            )
            return True

        except Exception as e:
            print(f"❌ Erro ao enviar vídeo para o S3: {e}")
            self.atualizar_video_por_id(
                video_id=video_id,
                status='FAILED'
            )
            return False

    def delete_local_directories(self, directories=None):
        """
        Deleta os diretórios locais especificados, incluindo todos os arquivos dentro.
        """
        if directories is None:
            current_script_dir = os.path.dirname(os.path.abspath(__file__))
            directories = [
                os.path.join(current_script_dir, "Processed"),
                os.path.join(current_script_dir, "Reports")
            ]
        
        for dir_path in directories:
            if os.path.exists(dir_path) and os.path.isdir(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    print(f"🧹 Diretório '{dir_path}' deletado com sucesso.")
                except Exception as e:
                    print(f"⚠️ Erro ao deletar '{dir_path}': {e}")
            else:
                print(f"⚠️ Diretório '{dir_path}' não encontrado ou já deletado.")
                


    def atualizar_video_por_id(self,video_id, status):
        """
        Envia uma requisição PATCH para atualizar os dados de um vídeo por ID.

        :param video_id: ID do vídeo a ser atualizado
        :param titulo: Novo título do vídeo
        :param descricao: Nova descrição do vídeo
        :param token: (opcional) Token de autenticação Bearer
        :return: Resposta do servidor (dict ou erro)
        """
        url = f"http://3.234.193.156:8080/api/video/{video_id}"

        payload = {

            "status": status
        }

        headers = {
            "Content-Type": "application/json"
        }
        try:
            response = requests.patch(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"✔ Atualização concluída. Status Code: {response.status_code}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição PATCH: {e}")
            return None
        
    def atualizar_report_por_id(self, video_id, name,report_name, status):
        """
        Envia uma requisição POST para criar um relatório associado a um vídeo.

        :param video_id: ID do vídeo
        :param name: Nome do relatório (ex: nome do arquivo)
        :param status: Status do relatório (padrão: IN_PROGRESS)
        :return: Resposta do servidor ou None em caso de erro
        """
        url = "http://3.234.193.156:8080/api/report"

        payload = {
            "videoId": video_id,
            "fileName": name,
            "status": status,
            "name": report_name,
            
        }

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            print(f"✔ Relatório criado com sucesso. Status Code: {response.status_code}")
  
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro ao criar relatório para o vídeo: {e}")
            return None