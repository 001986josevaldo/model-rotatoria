import cv2
from ultralytics import YOLO
from utils.sort import *
from utils.detector_speed import *
from utils.vehicle_monitoring import *
from utils.count_vehcicle_class import *
from utils.vehicle_monitoring import MonitoramentoVeiculo,  DetectorLinhaUnica
import time
from datetime import datetime
from utils.line_create import DesenhadorLinhas
from utils.s3_video_service import S3VideoService
#import json
from utils.video_converter import VideoConverter
#from utils.salvarcsvPet import RelatorioCSV  # Ajuste o nome conforme seu arquivo .py


class gap_analizer:
    
    def __init__(self, aws_access_key, aws_secret_key, region, bucket_name):
        self.s3_service = S3VideoService(
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            region=region,
            bucket_name=bucket_name

        )
    def trafic_analyzer(self, input_video, model_path, linhas, output_csv_path, video_base_name):

        FPS = 15  # Definindo a taxa de FPS desejada
        tempo_por_frame = 1.0 / FPS  # Tempo ideal por frame (segundos)
        # inicializa componentes
        detector_velocidade = VelocidadeDetector()


        model = YOLO(model_path) #"/home/josevaldo/Documentos/ProjDebora/rotatoria_api_service/app/modelos/trafego.pt"
        
        tracker = Sort(max_age=1000, min_hits=5)  # Rastreador

        # Carrega o vídeo - mantenha esta variável separada
        input_video = input_video #'/home/josevaldo/Documentos/ProjDebora/videos/trafego2.mp4'  # Esta é a string com o caminho
        video = cv2.VideoCapture(input_video)  # Este é o objeto VideoCapture

        # -------------------------------------------- OUTPUT PATHs --------------------------------------------------------------------
        # Extrai o nome base do arquivo de entrada (sem extensão)
        input_name = os.path.splitext(os.path.basename(input_video))[0]
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")# Obtém a data e hora atual no formato desejado (YYYY-MM-DD_HH-MM-SS)

        # Cria diretórios se não existir
        output_dir = 'Reports'
        output_dir_videos = 'Processed'
        os.makedirs(output_dir, exist_ok=True)  # Cria o diretório se não existir dos relatorios
        os.makedirs(output_dir_videos, exist_ok=True)  # Cria o diretório se não existir dos videos processados

        # Configura o nome base para os arquivos de saída




        base_name = video_base_name
        #output_csv_path = os.path.join(output_dir, f"{base_name}_Relatorio.csv")
        output_video_path = os.path.join(output_dir_videos, f"{base_name}.mp4")

        # -------------------------------------------------------------------------------------------------------------------------------------
        inicio = time.time()  # Marca o tempo inicial

        # Definir o codec e criar o objeto VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')# Use 'mp4v','avc1','H264' para o formato MP4
        fps = 30  # Frames por segundo
        frame_size = (840, 472)  # Dimensão do vídeo
        out = cv2.VideoWriter(output_video_path, fourcc, fps, frame_size)
        # -----------------------------------------------------------------------

        # Classes de veículos
        classNames = ["caminhao", "carro", "moto",]

        # Redimensiona o frame para uma largura fixa (ex: 840px), mantendo a proporção
        def redimensionar_frame(frame, largura=840):
            altura = int(frame.shape[0] * (largura / frame.shape[1]))
            return cv2.resize(frame, (largura, altura))
            #print(largura, altura )

        crArray =[]
        total_objetos = 0  # Variável para contar o total de objetos

        Y_LINHA = linhas[0][1]  # acessa o segundo item da primeira tupla (y1)
        x1Linha, y1Linha, x2Linha, y2LInha = linhas[0][:4]
        historico_cy = {}

        tempo_inicio_cruzamento = None
        ultimo_obj_id = None
        ultimo_obj_id_2 = None 
        tempos_entre_cruzamentos = []
        ultimo_intervalo = None 

        while True:
            
            _, img = video.read()
            if img is None:
                print("Erro: Não foi possível abrir o vídeo ou o vídeo chegou ao fim.")
                break
            #tempo_inicio_video = datetime.now()
            
            img = redimensionar_frame(img) # Redimensiona o frame
            
            # Linha 
            xlinha1 = 85
            xlinha2 = xlinha1 + 100
            y1 = 250
            y2 = y1 + 100
            #cv2.line(img, (xlinha1, y1), (xlinha1, y2), (0, 255, 0), 2)
            #cv2.line(img, (xlinha2, y1), (xlinha2, y2), (0, 255, 0), 2)

            # Linha 
            ylinha1 = 150
            ylinha2 = ylinha1 + 100
            x1 = 200
            x2 = x1 + 100
            #cv2.line(img, (x1, ylinha1), (x2, ylinha1), (0, 0, 255), 2)
            #cv2.line(img, (x1, ylinha2), (x2, ylinha2), (0, 0, 255), 2)

            # Detecta veículos
            results = model.predict(img, verbose=False)
            detections = np.empty((0,7))
            #print("detections", results)

            # Inicializa o dicionário para mapear IDs às classes
            id_to_class = {}
            classes = []
            ids = []
            # itera sopbre todos os objetos detectados


            for obj in results:
                dados = obj.boxes
                for x in dados:
                    #conf
                    conf = int(x.conf[0]*100)
                    cls = int(x.cls[0])
                    #print("cls-=> ",cls)
                    nomeClass = classNames[cls]
                    #print(nomeClass)
                    
                    # Verifica classes desejadas
                    if  nomeClass in ["carro", "moto", "caminhao"] and conf > 50:

                        # Coordenadas do bounding box
                        x1, y1, x2, y2 = x.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        w, h = x2 - x1, y2 - y1
                        # Calcula o centro do bounding box
                        cx, cy = x1 + w // 2, y1 + h // 2
                        #cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 2)  

                        # Adiciona a detecção ao tracker
                        crArray = np.array([x1, y1, x2, y2, 0, conf, cls])
                        detections = np.vstack((detections,crArray))

                        # logica dos veiculos na area de risco
                        #if rect_x1 <= x1 <= rect_x2 and rect_y1 <= y1 <= rect_y2:
                        #    contagem_veiculos += 1

            #print("classes: ",classes)
                # Exibir a contagem das classes            
            #print(detections)

            resultTracker = tracker.update2(detections)
            #print("")
            #print(resultTracker)
            tempo1 = time.time()

            for result in resultTracker:
                num_colunas = result.shape[0]
                if len(result) == 5:
                    x1, y1, x2, y2, obj_id = result
                    con = None  # Valor padrão para `con`
                    nomeObjeto = None  # Valor padrão para `resto`
                elif len(result) == 7:
                    x1, y1, x2, y2, obj_id, con, nomeObjeto = result
                else:
                    raise ValueError("Formato de 'result' não reconhecido.")
                # Converte as coordenadas para inteiros
                x1, y1, x2, y2 = (int(x1)), int(y1), (int(x2)), int(y2)
                w, h = x2 - x1, y2 - y1 # Largura e altura do objeto
                cx,cy = x1+w//2, y1+h//2 # Centro do objeto
                obj_id = int(obj_id)

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 1)                
                #cv2.imshow('teste img',img)  
                mapeamento_nomes = {
                0: "Caminhao",
                1: "Carro",
                2: "Moto"
                }
                nome_str = mapeamento_nomes.get(nomeObjeto, "Desconhecido")  # Retorna "Desconhecido" se o valor não estiver no dicionário
                # Garante que nomeObjeto tenha um valor válido
                nomeObjeto = nomeObjeto if nomeObjeto is not None else "desconhecido"
                posicao_inicial = [x2,(y1-20)]

                vel = detector_velocidade.calcular_velocidade(x2,y2, obj_id)     
                dados = [
                    f"Classe: {nome_str}",
                    f"Conf.: {con}%",
                    f"ID: {obj_id}",
                    #f'Vel: {vel}',
                    #f'PET: {pet}'
                ]

                img = detector_velocidade.exibir_texto_na_imagem(img, dados,posicao_inicial,)
                nome_str = mapeamento_nomes.get(nomeObjeto, "Desconhecido")  # Retorna "Desconhecido" se o valor não estiver no dicionário    

                # Para cada veículo rastreado
                cy_anterior = historico_cy.get(obj_id)
                cruzou = (
                    cy_anterior is not None and
                    x1Linha <= cx <= x2Linha and
                    ((cy_anterior < y1Linha <= cy) or (cy_anterior > y1Linha >= cy))
                )
                if cruzou:
                    agora = time.time()
                    cv2.circle(img, (cx,cy), 5, (0, 165, 255), -1)
                    if tempo_inicio_cruzamento is not None and ultimo_obj_id_2 is not None:
                        intervalo = agora - tempo_inicio_cruzamento
                        print(f"Tempo entre cruzamento do veículo {ultimo_obj_id_2} com {obj_id}: {intervalo:.2f} segundos")
                        
                        # Atualiza as variáveis de exibição
                        ultimo_intervalo = intervalo
                        ultimo_obj_id = ultimo_obj_id_2  # anterior
                        ultimo_obj_id_2 = obj_id         # atual

                    else:
                        # Primeira vez apenas
                        ultimo_obj_id_2 = obj_id

                    # Atualiza o tempo de início do próximo intervalo
                    tempo_inicio_cruzamento = agora
                
                # Atualiza posição atual
                historico_cy[obj_id] = cy 

            if cv2.waitKey(1) == 27:
                break


            # Cria o desenhador e desenha as linhas
            desenhador = DesenhadorLinhas(img)
            desenhador.desenhar_varias_linhas(linhas)
            # Mostra sempre o último intervalo registrado, se houver
            if ultimo_intervalo is not None and ultimo_obj_id is not None and ultimo_obj_id_2 is not None:
                cv2.putText(
                    img,
                    f"Tempo entre {ultimo_obj_id} e {ultimo_obj_id_2}: {ultimo_intervalo:.2f}s",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
            # Escrever o frame no vídeo
            out.write(img)
            # visualçização
 
            cv2.imshow('Conflitos de Trafego',img)

            # Aguarda o tempo necessário para manter os 30 FPS
            tempo_execucao = time.time() - inicio
            if tempo_execucao < tempo_por_frame:
                time.sleep(tempo_por_frame - tempo_execucao)




        # Salva a contagem final em um CSV com o mesmo nome base
        #RelatorioCSV.salvar_contagem_csv(lista_veiculos, lista_saidas, output_csv_path)
        video.release()
        out.release()
        cv2.destroyAllWindows()



    def executeGap(self, xxx):
        try:
            print('msg rec.',xxx)
            mensagem = xxx
            #mensagem = json.loads(mensagem)  # Agora é um dict
            
            # --------------------------------- AJUSTADO PARA TESTE -------------------------------------
            #input_video = "/media/josevaldo/E02A-3159/rotatoria_api_service/app/services/videos/rotatoria0.mp4"  
            # ----------------------------------------------------------------------------------------------
            #print('id do video: ',video_id, 's3_video_key',video_key)

            # --------------------------------- TRECHO CORRETO --------------------------------
            video_id = mensagem.get("id")
            video_key = mensagem.get("fileName")
            input_video = self.s3_service.download_video(video_key)
            video_base_name = os.path.splitext(os.path.basename(video_key))[0]  # Ex: "rotatoria"

        except FileNotFoundError as e:
            print(f"Arquivo não encontrado: {e}")
            return
        except RuntimeError as e:
            print(f"Erro ao acessar S3: {e}")
            return
        

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = video_base_name
        output_dir = 'Reports'
        #os.makedirs(output_dir, exist_ok=True)
        output_csv_path = os.path.join(output_dir, f"{base_name}.csv")

        model = "ai_models/trafego.pt"
       
        #model = "/home/josevaldo/Documentos/ProjDebora/modelos/trafego2.pt"

        #print(f"Caminho completo do modelo: {model}")

        linhas = [
            (260, 300, 330, 300, (0, 255, 0)),     
        ]

        VideoConverter.ensure_max_fps(input_video)
        self.trafic_analyzer(input_video, model, linhas, output_csv_path, video_base_name)
        nome_arquivo = os.path.basename(output_csv_path)
        
        video_path = os.path.join("Processed", f"{video_base_name}.mp4")
        
        # convert o video processed
        VideoConverter.convert_video_to_h264(video_path)

        '''     
        #self.s3_service.upload_file(local_file_path=output_csv_path, s3_file_name=nome_arquivo)
        # envia o relatorio
        self.s3_service.upload_file(output_csv_path, 
                                    video_id=video_id,
                                    name=video_key)  # Envia para rotatoria-reports por padrão
        
         # envia o video processado
        self.s3_service.upload_processed_video(
            processed_dir="Processed",
            video_name=f"{video_base_name}.mp4",
            video_id=video_id
        )
        # Apaga os diretorios locais
        self.s3_service.delete_local_directories(
            directories=[
                "Processed",
                "Reports"
            ]
        )
        # deleta o video do s3
        #self.s3_service.delete_video(video_key)
        self.s3_service.cleanup()
       

if __name__ == "__main__":
    gap = gap_analizer()

    # String JSON válida (aspas duplas obrigatórias)
    idfilename = '{"id": 7, "fileName": "testegap"}'

    gap.executeGap(idfilename)
     '''
