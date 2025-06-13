import cv2
from ultralytics import YOLO
from utils.sort import *
from utils.detector_speed import VelocidadeDetector
from utils.vehicle_monitoring import *
from utils.count_vehcicle_class import *
from utils.vehicle_monitoring import MonitoramentoVeiculo,  DetectorLinhaUnica
import time
from datetime import datetime
from utils.line_create import DesenhadorLinhas
from utils.s3_video_service import S3VideoService
import json
#from utils.s3Uploader import S3Uploader

class trafic_analizer:
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
        monitor = MonitoramentoVeiculo()

        model = YOLO(model_path) #"/home/josevaldo/Documentos/ProjDebora/rotatoria_api_service/app/modelos/trafego.pt"
        #model = YOLO("/media/josevaldo/E02A-3159/rotatoria_api_service/app/services/ai_models/trafego.pt")
        
        # desse jeito da certo
        #model = YOLO("/home/josevaldo/Documentos/ProjDebora/modelos/trafego.pt")
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
            frame = cv2.resize(frame, (largura, altura))
            #print(largura, altura )
            return frame

        # Função para verificar se um veículo está na área de risco
        def veiculo_na_area_risco(x1, y1):
            return rect_x1 <= x1 <= rect_x2 and rect_y1 <= y1 <= rect_y2

        # Coordenadas do retângulo de contagem
        rect_x1, rect_y1 = 270, 300
        rect_x2, rect_y2 = 330, 350

        crArray =[]
        total_objetos = 0  # Variável para contar o total de objetos

            # Variável de controle para armazenar a posição anterior
        x2anterior = None  
        tempo_anterior = None  # Inicializa o tempo anterior fora do loop principal


        # Atribuindo linhas aos objetos diretamente usando a lista 'linhas'
        linhaA, linhaB, LinhaSaidaA, LinhaSaidaB, LinhaSaidaC, LinhaSaidaD = [linha[:4] for linha in linhas]
        detectorAB = ContadorVeiculos(linhaA, linhaB) # do arquivo contarClasees.py
        contadorEntradas = ContadorVeiculos(linhaA, linhaB)
        detector_de_entrada_B = DetectorLinhaUnica(linhaB, (0,255,255), 1)
        detector_de_entrada_A = DetectorLinhaUnica(linhaA, (0,255,255), 1)
        detector_de_saida_A = DetectorLinhaUnica(LinhaSaidaA, (0,255,255), 1)
        detector_de_saida_B = DetectorLinhaUnica(LinhaSaidaB, (0,255,255), 1)
        detector_de_saida_C = DetectorLinhaUnica(LinhaSaidaC, (0,255,255), 1)
        detector_de_saida_D = DetectorLinhaUnica(LinhaSaidaD, (0,255,255), 1)

        # Lista para armazenar IDs únicos
        lista_veiculos = [] # veiculos que entraram 
        lista_saidas = [] # veiculos que sairam

        # -------------------------------------------------------------------------
        total_anterior = 0  # Variável deve ser declarada fora do loop
        inicio2 = CalcularTempo()  # Inicia o contador automaticamente
        #print('inicio2:', inicio2.tempo_decorrido())

        while True:
            
            _, img = video.read()
            if img is None:
                print("Erro: Não foi possível abrir o vídeo ou o vídeo chegou ao fim.")
                break
            #tempo_inicio_video = datetime.now()
            
            img = redimensionar_frame(img) # Redimensiona o frame

            # Inicializa a contagem de veículos dentro do retângulo
            contagem_veiculos = 0
            
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
            results = model(img, stream=True, verbose=False)
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
                    if  nomeClass in ["carro", "moto", "caminhao"] and conf > 70:

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
            
                # veículo que CRUZA a linha B 
                caminhao, carro, moto = detectorAB.verificar_cruzamento_linha_id_obj(cx, cy, obj_id, nomeObjeto)
            
                # Garante que nomeObjeto tenha um valor válido
                nomeObjeto = nomeObjeto if nomeObjeto is not None else "desconhecido"
                # ----------------------------------------------------------------
                # Chama o método para atualizar o tempo que o veículo passou na area de risco PET 
                #monitor.atualizar_tempo_veiculo(obj_id, x1, y1, img, veiculo_na_area_risco)

                # exibir id na imagem
                #cv2.putText(img, str(obj_id), (x2, y2), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1)
                ids.append(obj_id)

                posicao_inicial = [x2,(y1-20)]
                vel = detector_velocidade.calcular_velocidade(x2,y2, obj_id)     
                dados = [
                    f"Classe: {nome_str}",
                    f"Conf.: {con}%",
                    f"ID: {obj_id}",
                    f'Vel: {vel}'
                ]
                img = detector_velocidade.exibir_texto_na_imagem(img, dados,posicao_inicial,)

                # ----------------------- ENTRADAS --------------------------------
                cruzou, img = detector_de_entrada_B.verificar_cruzamento(img, cx, cy)  # Ponto (250,210) está abaixo da linha y=200  
                if cruzou:
                    #print('inicio123:', inicio2.tempo_decorrido())
                    tempo_formatado = inicio2.tempo_decorrido()
                    EB = 'EB'
                        # Verifica se o veículo já foi registrado
                    if not any(veic['id'] == obj_id for veic in lista_veiculos):
                        # Adiciona um novo dicionário com todas as informações
                        lista_veiculos.append({
                            'id': obj_id,
                            'class': nome_str,  # "carro", "moto", "caminhao"
                            #'cx': cx,  # Coordenada X do centro (opcional)
                            #'cy': cy,  # Coordenada Y do centro (opcional)
                            'time': tempo_formatado,
                            'speed': vel,
                            'EB': EB
                        })
                        #print(f"Novo registro - ID: {obj_id}, Tipo: {nomeObjeto}")
                
                cruzou, img = detector_de_entrada_A.verificar_cruzamento(img, cx, cy)  # Ponto (250,210) está abaixo da linha y=200
                if cruzou:
                    tempo_formatado = inicio2.tempo_decorrido() 
                    EA = 'EA'
                    if not any(veic['id'] == obj_id for veic in lista_veiculos):
                        # Adiciona um novo dicionário com todas as informações
                        lista_veiculos.append({
                            'id': obj_id,
                            'class': nome_str,  # "carro", "moto", "caminhao"
                            #'cx': cx,  # Coordenada X do centro (opcional)
                            #'cy': cy,  # Coordenada Y do centro (opcional)
                            'time': tempo_formatado,
                            'speed': vel,
                            'EB': EA
                        })
                # ---------- SAIDAS ------------------------------------
                cruzou, img = detector_de_saida_C.verificar_cruzamento(img, cx, cy)  # Ponto (250,210) está abaixo da linha y=200
                if cruzou:
                    tempo_formatado = inicio2.tempo_decorrido() 
                    SC = 'SC'
                    # Verifica se o veículo já foi registrado
                    if not any(
                        (veic['id'] == obj_id and veic.get('Saida'
                        '') == SC)  # Verifica se já tem EB = 'EB'
                        for veic in lista_saidas
                    ):
                        # Adiciona um novo dicionário com todas as informações
                        lista_saidas.append({
                            'id': obj_id,
                            'class': nome_str,  # "carro", "moto", "caminhao"
                            #'cx': cx,  # Coordenada X do centro (opcional)
                            #'cy': cy,  # Coordenada Y do centro (opcional)
                            'time': tempo_formatado,
                            'speed': vel,
                            'Saida': SC
                        })

                cruzou, img = detector_de_saida_A.verificar_cruzamento(img, cx, cy)  # Ponto (250,210) está abaixo da linha y=200
                if cruzou:
                    tempo_formatado = inicio2.tempo_decorrido()   
                    SA = 'SA'
                        # Verifica se o veículo já foi registrado
                    if not any(
                        (veic['id'] == obj_id and veic.get('Saida') == SA)  # Verifica se já tem EB = 'SA'
                        for veic in lista_saidas
                    ):
                        lista_saidas.append({
                            'id': obj_id,
                            'class': nome_str,  # "carro", "moto", "caminhao"
                            #'cx': cx,  # Coordenada X do centro (opcional)
                            #'cy': cy,  # Coordenada Y do centro (opcional)
                            'time': tempo_formatado,
                            'speed': vel,
                            'Saida': SA
                        })
                cruzouB, img = detector_de_saida_B.verificar_cruzamento(img, cx, cy)  # Ponto (250,210) está abaixo da linha y=200
                if cruzouB:
                    tempo_formatado = inicio2.tempo_decorrido() 
                    SB = 'SB'
                    # Verifica se o veículo já foi registrado
                    if not any(
                        (veic['id'] == obj_id and veic.get('Saida') == SB)  # Verifica se já tem EB = 'SA'
                        for veic in lista_saidas
                    ):
                        lista_saidas.append({
                            'id': obj_id,
                            'class': nome_str,  # "carro", "moto", "caminhao"
                            #'cx': cx,  # Coordenada X do centro (opcional)
                            #'cy': cy,  # Coordenada Y do centro (opcional)
                            'time': tempo_formatado,
                            'speed': vel,
                            'Saida': SB
                        })
                        
                # -----------------
                cruzouD, img = detector_de_saida_D.verificar_cruzamento(img, cx, cy)  # Ponto (250,210) está abaixo da linha y=200
                if cruzouD:
                    tempo_formatado = inicio2.tempo_decorrido() 
                    SD = 'SD'
                    # Verifica se o veículo já foi registrado
                    if not any(
                        (veic['id'] == obj_id and veic.get('Saida') == SD)  # Verifica se já tem EB = 'SA'
                        for veic in lista_saidas
                    ):
                        lista_saidas.append({
                            'id': obj_id,
                            'class': nome_str,  # "carro", "moto", "caminhao"
                            #'cx': cx,  # Coordenada X do centro (opcional)
                            #'cy': cy,  # Coordenada Y do centro (opcional)
                            'time': tempo_formatado,
                            'speed': vel,
                            'Saida': SD
                        })

                # ---------------------- CONTAGEM DOS VEICULOS QUE ENTRAM NO CENARIO PELA ENTRADA A E ENTRADA B ----------------
                contadorA = contadorEntradas.verificar_cruzamento_linhaA(cx, cy, obj_id)
                contadorB = contadorEntradas.verificar_cruzamento_linhaB(cx, cy, obj_id)               

            coordenadas = [(cx,cy)]
            
            # Loop para processar cada objeto
            for obj_id, classe, (cx, cy) in zip(ids, classes, coordenadas):
                # Verificar cruzamentos
                contadorEntradas.verificar_cruzamento_linhaA(cx, cy, obj_id)
                contadorEntradas.verificar_cruzamento_linhaB(cx, cy, obj_id)

            # Exibe a contagem total de veículos
            total = len(contadorEntradas.get_contadorA())+ len(contadorEntradas.get_contadorB())
            if total_anterior != total:     
                #print(f"Total Aprox. Veiculos: {total}")
                for i in range(3):
                    print("Processando" + "." * (i + 1), end="\r", flush=True)
                    time.sleep(0.5)
                total_anterior = total

            if cv2.waitKey(1) == 27:
                break

            # Desenha o retângulo de contagem na imagem
            #cv2.rectangle(img, (rect_x1, rect_y1), (rect_x2, rect_y2), (255, 255, 255), 1)
            # Exibe a contagem de veículos dentro do retângulo
            #cv2.putText(img, f"Area de risco (PET): {contagem_veiculos}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 1)
            cv2.putText(img, f"Entrada A: {len(contadorEntradas.get_contadorA())}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
            cv2.putText(img, f"Entrada B: {len(contadorEntradas.get_contadorB())}", (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,127 , 255), 2)  
            # Desenhar a linha A azul

            # Cria o desenhador e desenha as linhas
            desenhador = DesenhadorLinhas(img)
            desenhador.desenhar_varias_linhas(linhas)

            # Escrever o frame no vídeo
            out.write(img)
            # visualçização
            #cv2.imshow('Conflitos de Trafego',img)

            # Aguarda o tempo necessário para manter os 30 FPS
            tempo_execucao = time.time() - inicio
            if tempo_execucao < tempo_por_frame:
                time.sleep(tempo_por_frame - tempo_execucao)

        # Salva a contagem final em um CSV com o mesmo nome base
        contadorEntradas.salvar_contagem_csv(lista_veiculos, lista_saidas, output_csv_path)
        #print("Lista entrada: ", lista_veiculos)
        #print('Lista de saidas: ', lista_saidas)
        video.release()
        out.release()
        cv2.destroyAllWindows()

    def execute(self, xxx):
        try:
            print('msg rec.',xxx)
            mensagem = xxx
            #mensagem = json.loads(mensagem)  # Agora é um dict
            video_id = mensagem.get("id")
            video_key = mensagem.get("fileName")
            #print('id do video: ',video_id, 's3_video_key',video_key)

            #video_key = self.s3_service.get_video_key_from_message(mensagem)
            input_video = self.s3_service.download_video(video_key)
            video_base_name = os.path.splitext(os.path.basename(video_key))[0]  # Ex: "rotatoria"

        except FileNotFoundError as e:
            print(f"Arquivo não encontrado: {e}")
            return
        except RuntimeError as e:
            print(f"Erro ao acessar S3: {e}")
            return
        
        #input_video = "/home/josevaldo/Documentos/ProjDebora/videos/rotatoria.mp4"
        #video_base_name = "rotatoria123"
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = video_base_name
        output_dir = 'Reports'
        #os.makedirs(output_dir, exist_ok=True)
        output_csv_path = os.path.join(output_dir, f"{base_name}.csv")

        model = "ai_models/trafego.pt"
        #model = "/home/josevaldo/Documentos/ProjDebora/modelos/trafego2.pt"

        #print(f"Caminho completo do modelo: {model}")

        linhas = [
            (250, 60, 360, 60, (255, 0, 0)),
            (200, 220, 200, 390, (255, 0, 0)),
            (100, 100, 100, 200, (0, 255, 0)),
            (270, 430, 400, 430, (0, 255, 0)),
            (800, 170, 800, 330, (0, 255, 0)),
            (380, 60, 480, 60, (0, 255, 0)),
        ]

        self.trafic_analyzer(input_video, model, linhas, output_csv_path, video_base_name)

        nome_arquivo = os.path.basename(output_csv_path)
        
        video_path = os.path.join("Processed", f"{video_base_name}.mp4")
        # convert o video processed
        self.s3_service.convert_video_to_h264(video_path)

        #self.s3_service.upload_file(local_file_path=output_csv_path, s3_file_name=nome_arquivo)
        '''
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
        )'''
        # deleta o video do s3
        #self.s3_service.delete_video(video_key)
        self.s3_service.cleanup()