import cv2
from ultralytics import YOLO
from utils.sort import *
from utils.detector_speed import *
from utils.count_vehcicle_class import *
from utils.vehicle_monitoring import MonitoramentoVeiculo,  DetectorLinhaUnica
import time
from datetime import datetime, timedelta
from collections import defaultdict
#from utils.vehicle_counter import DetectorCruzamentoVeiculos123
from utils.line_create import DesenhadorLinhas
from utils.video_converter import VideoConverter
from utils.contarClasses import ContadorEntradas123
from utils.s3_video_service import S3VideoService
from utils.salvarcsvPet import *


class pet_analizer:
    def __init__(self, aws_access_key, aws_secret_key, region, bucket_name):
        self.s3_service = S3VideoService(
            aws_access_key=aws_access_key,
            aws_secret_key=aws_secret_key,
            region=region,
            bucket_name=bucket_name

        )

    def trafic_analyzer(self, input_video, model, output_csv_path, video_base_name):

        FPS = 15  # Definindo a taxa de FPS desejada
        tempo_por_frame = 1.0 / FPS  # Tempo ideal por frame (segundos)

        # inicializa componentes
        detector_velocidade = VelocidadeDetector()
        monitor = MonitoramentoVeiculo()
        contador123 = ContadorEntradas123()
        salvar = salvarcsvPet()
        model = YOLO(model) #"/home/josevaldo/Documentos/ProjDebora/rotatoria_api_service/app/modelos/trafego.pt"
        tracker = Sort(max_age=1000, min_hits=5)  # Rastreador

        # Carrega o vídeo - mantenha esta variável separada
        input_video = input_video #'/home/josevaldo/Documentos/ProjDebora/videos/trafego2.mp4'  # Esta é a string com o caminho
        video = cv2.VideoCapture(input_video)  # Este é o objeto VideoCapture
        fps = video.get(cv2.CAP_PROP_FPS)
        temporizador = TempoVideoPorFrame(fps)



        # -------------------------------------------- OUTPUT PATHs --------------------------------------------------------------------
        # Extrai o nome base do arquivo de entrada (sem extensão)
        input_name = os.path.splitext(os.path.basename(input_video))[0]
        current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")# Obtém a data e hora atual no formato desejado (YYYY-MM-DD_HH-MM-SS)

        # Cria diretórios se não existir
        output_dir = 'Reports'
        output_dir_videos = 'Processed'
        os.makedirs(output_dir, exist_ok=True)  # Cria o diretório se não existir dos relatorios
        os.makedirs(output_dir_videos, exist_ok=True)  # Cria o diretório se não existir dos videos processados

        # Configura o nome base para os arquivos de saída
        base_name = f"{input_name}"
        output_csv_path = os.path.join(output_dir, f"{video_base_name}.csv")
        output_video_path = os.path.join(output_dir_videos, f"{video_base_name}.mp4")

        # -------------------------------------------------------------------------------------------------------------------------------------
        inicio = time.time()  # Marca o tempo inicial

        # Definir o codec e criar o objeto VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')# Use 'mp4v' para o formato MP4
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
        
        def lado_entrada_area(x_anterior, y_anterior, x_atual, y_atual, rect_x1, rect_y1, rect_x2, rect_y2):
            if not (rect_x1 <= x_anterior <= rect_x2 and rect_y1 <= y_anterior <= rect_y2) and \
            (rect_x1 <= x_atual <= rect_x2 and rect_y1 <= y_atual <= rect_y2):

                # Entrou pela esquerda
                if x_anterior < rect_x1:
                    return "esquerda"
                # Entrou pela direita
                elif x_anterior > rect_x2:
                    return "direita"
                # Entrou por cima
                elif y_anterior < rect_y1:
                    return "cima"
                # Entrou por baixo
                elif y_anterior > rect_y2:
                    return "baixo"

            return None  # não entrou ou já estava dentro

        # Coordenadas do retângulo de contagem
        rect_x1, rect_y1 = 270, 290 # 
        rect_x2, rect_y2 = (rect_x1 + 60), (rect_y1 + 60)
    



                # x1, y1, x2, y2
        linhasH = [(rect_x1,rect_y1, rect_x2, rect_y1)] # mesmo y
        linhasV = [(rect_x1, rect_y1, rect_x1, rect_y2)] # mesmo x
        
        
        
        crArray =[]
        total_objetos = 0  # Variável para contar o total de objetos

            # Variável de controle para armazenar a posição anterior
        x2anterior = None  
        tempo_anterior = None  # Inicializa o tempo anterior fora do loop principal
        # Variáveis globais
        ultimo_id = None
        # Dicionário para armazenar o último pet por obj_id
        ultimo_pet_por_id = {}
        contagem_ativa = False
        # Dicionário global para salvar o último pet de cada obj_id
        historico_pets = {}
        # ---------------------------------------------------------------------
        # Lista para armazenar IDs únicos
        lista_veiculos = [] # veiculos que entraram 
        lista_saidas = [] # veiculos que sairam
        tempos_por_id = defaultdict(list)  # Novo dicionário para armazenar os tempos por obj_id
        # Conversão para arquivos de saida
        lista_entrada = []
        # -------------------------------------------------------------------------
        total_anterior = 0  # Variável deve ser declarada fora do loop
        inicio2 = CalcularTempo()  # Inicia o contador automaticamente
        
        tempo_inicio_cruzamento = None
        ultimo_obj_id = None
        ultimo_obj_id_2 = None 
        tempos_entre_cruzamentos = []
        ultimo_intervalo = None 
        historico_cy = {}


        x1Linha, y1Linha, x2Linha, y2LInha = linhasH[0][:4]
        
        x1linhav, y1linhav, x2linhav, y2linhav = linhasV[0][:4]
        lv = x1linhav, y1linhav, x2linhav, y2linhav = linhasV[0][:4]
        lh = x1Linha, y1Linha, x2Linha, y2LInha = linhasH[0][:4]
        detector_de_entrada_V = DetectorLinhaUnica(lv, (0,255,255), 1)
        detector_de_entrada_H = DetectorLinhaUnica(lh, (0,255,255), 1)



        historico_posicoes = {}
        
        ladoanterior = None
        #print('inicio2:', inicio2.tempo_decorrido())
        # Para exibição
        frame_atual = int(video.get(cv2.CAP_PROP_POS_FRAMES))
        tempo_formatado = temporizador.calcular_tempo_formatado(frame_atual)
        print("⏱️ Tempo inicial:", tempo_formatado)

        mensagem_convergencia = None  # Armazena a última mensagem visível
        mensagem_intervalo = None
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
                    if  nomeClass in ["carro", "moto", "caminhao"] and conf > 40:

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
                    continue # Ignora formatos não reconhecidos
                    #raise ValueError("Formato de 'result' não reconhecido.")
                # Converte as coordenadas para inteiros
                x1, y1, x2, y2 = (int(x1)), int(y1), (int(x2)), int(y2)
                w, h = x2 - x1, y2 - y1 # Largura e altura do objeto
                cx,cy = x1+w//2, y1+h//2 # Centro do objeto
                obj_id = int(obj_id)

                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 0), 1)
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
                    f'Vel: {vel}',
                    #f'PET: {pet}'
                ]

                img = detector_velocidade.exibir_texto_na_imagem(img, dados,posicao_inicial,)
                #print('veiculo_existente',veiculo_existente)
                pet = monitor.atualizar_tempo_veiculo(obj_id, x1, y1, img, veiculo_na_area_risco)
                # Verifica se o veículo já foi registrado
                tempo_formatado = inicio2.tempo_decorrido()
                ids.append(obj_id)

                detector_de_entrada_V.verificar_cruzamento(img, cx, cy)
                detector_de_entrada_H.verificar_cruzamento(img, cx, cy)

                # 2. Agora, lado e convergência
                anterior = historico_posicoes.get(obj_id)
                #print('anterior: ',anterior)
                if anterior:
                    lado = lado_entrada_area(anterior[0], anterior[1], x1, y1, rect_x1, rect_y1, rect_x2, rect_y2)
                    #print('lado: ', lado)  lado vai ser para cima ou esquerda

                    if lado:
                        agora = time.time()
                        frame_atual = int(video.get(cv2.CAP_PROP_POS_FRAMES))
                        agoraF = temporizador.calcular_segundos(frame_atual)

                        tempo_video = inicio2.tempo_decorrido()
                        tempo_videoF = temporizador.calcular_segundos(frame_atual)


                        if ladoanterior is None:
                            #frame_atual = int(video.get(cv2.CAP_PROP_POS_FRAMES))
                            print("➡️ Primeiro veículo detectado na área")
                            print(f"ID  do veiculo: {ultimo_obj_id} ou {obj_id}")
                            print(nome_str)

                            tempo_inicio_cruzamento = agora  # Marca o tempo do primeiro
                            tempo_inicio_cruzamentoF2 = agoraF

                            ultimo_obj_id = obj_id
                            ultimo_nome = nome_str
                            ultima_vel = vel
                            print("Tempo por frame: ", tempo_videoF) 


                        elif ladoanterior == lado:
                            print("➡️ Veículos na mesma direção")
                            print(f"ID dos veiculos {ultimo_obj_id} e {obj_id}")
                            print("Tempo por frame: ", tempo_videoF)
                            tempo_inicio_cruzamento = agora  # Atualiza tempo para este novo veículo
                            tempo_inicio_cruzamentoF2 = agoraF

                            ultimo_obj_id = obj_id
                            ultimo_nome = nome_str
                            ultima_vel = vel
                            '''
                            tempo_video = inicio2.tempo_decorrido()
                            frame_atual = int(video.get(cv2.CAP_PROP_POS_FRAMES))
                            # Para cálculo   
                            '''
                            frame_atual = int(video.get(cv2.CAP_PROP_POS_FRAMES))
                            tempo_videoF = temporizador.calcular_segundos(frame_atual)
                            
                            
                        else:
                            frame_atual2 = int(video.get(cv2.CAP_PROP_POS_FRAMES))
                            tempo_videoF2 = temporizador.calcular_segundos(frame_atual2)
                            ultimo_tempo_videoF = tempo_videoF 
                            tempo_video2 = inicio2.tempo_decorrido()

                            intervalo = round(agora - tempo_inicio_cruzamento, 2)
                            intervaloF2 = round(agoraF - tempo_inicio_cruzamentoF2, 2)
                            
                            print("\n↔️ Veículos convergentes")
                            print(f"ID dos veículos {ultimo_obj_id} com {obj_id}")
                            #print(f"⏱️ Tempo entre cruzamento: {intervalo:.2f} segundos")



                            print("Tempo agora2: ", agoraF)
                            print(f"tempo inicio cruazamentoF2", tempo_inicio_cruzamentoF2)




                            print("Tempo por frame: ", tempo_videoF)
                            print(f"⏱️ Tempo entre cruzamento por frame: {intervaloF2:.2f} segundos")

                            
                            mensagem_convergencia = (
                                f"Veiculos convergentes: {ultimo_obj_id} e {obj_id}. PET: {intervaloF2:.2f}s"
                            )


                            # Salva os dados no formato desejado:
                            linha_dados = [
                                tempo_inicio_cruzamentoF2,           # Tempo do frame atual
                                ultimo_obj_id,             # ID anterior
                                ultimo_nome,
                                ultima_vel,
                                #len(lista_entrada) + 1,    # Contador (incremental)
                                
                                tempo_videoF,           # Tempo novamente (pode ser outro se preferir)
                                obj_id,                    # ID atual
                                nome_str,
                                vel,
                                intervaloF2                  # PET (intervalo)
                            ]

                            lista_entrada.append(linha_dados)

                            
                            tempo_inicio_cruzamento = agora
                            tempo_inicio_cruzamentoF2 = agoraF
                            
                            tempo_video = tempo_video2
                            tempo_videoF = tempo_videoF2
                            
                            ultimo_nome = nome_str
                            ultimo_obj_id = obj_id
                            ultima_vel = vel                            
                            #print(f"⏱️ Tempo entre cruzamento do veículo {ultimo_obj_id} com {obj_id}: {ultimo_intervalo:.2f} segundos")
                      
                        ladoanterior = lado
                # Atualiza a posição do veículo atual
                historico_posicoes[obj_id] = (x1, y1)

        





            if cv2.waitKey(1) == 27:
                break

            #cv2.putText(img, f"ID dos veículos {ultimo_obj_id} com {obj_id}", (350, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            if mensagem_convergencia:
                cv2.putText(img, mensagem_convergencia, (350, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)


            # Desenha o retângulo de contagem na imagem
            # Coordenadas do retângulo de contagem
            #rect_x1, rect_y1 = 290, 310 # 
            #rect_x2, rect_y2 = (rect_x1 + 60), (rect_y1 + 60)
            #cv2.line(img, (rect_x1, rect_y1), (rect_x2, rect_y1), (0, 255, 0), 1) # horizontal
            #cv2.line(img, (rect_x1, rect_y1), (rect_x1, rect_y2), (0, 255, 0), 1)
        
            
            cv2.rectangle(img, (rect_x1, rect_y1), (rect_x2, rect_y2), (255, 255, 255), 1)

            # Cria o desenhador e desenha as linhas
            desenhador = DesenhadorLinhas(img)
            #desenhador.desenhar_varias_linhas(linhas)
            if ultimo_intervalo is not None and ultimo_obj_id is not None and ultimo_obj_id_2 is not None:
                cv2.putText(
                    img,
                    f"⏱ Tempo entre {ultimo_obj_id} e {ultimo_obj_id_2}: {ultimo_intervalo:.2f}s",
                    (30, 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

            # Escrever o frame no vídeo
            out.write(img)
            cv2.imshow('PET',img)
            '''
            # Aguarda o tempo necessário para manter os 30 FPS
            tempo_execucao = time.time() - inicio
            if tempo_execucao < tempo_por_frame:
                time.sleep(tempo_por_frame - tempo_execucao)
'''
        
        '''
        #print("Lista veiculos: ", lista_veiculos)
        for obj_id, dados in historico_pets.items():
            lista_entrada.append({
                'id': obj_id,
                'class': dados.get('Class', 'Desconhecido'),
                'time': dados.get('time', 'null'),
                'speed': dados.get('vel', 'null'),
                'pet': dados.get('pet', 'null')
            })
        '''
        if lista_entrada:
            print(lista_entrada)
        else:
            print("Lista vazia.")
        # Salva a contagem final em um CSV com o mesmo nome base
        salvar.salvarcsvPet(lista_entrada, output_csv_path)
        print('historico',historico_pets)
        #print('Lista de saidas: ', lista_saidas)
        video.release()
        out.release()
        cv2.destroyAllWindows()
    
    def executePet(self, xxx):
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
        video_path = os.path.join("Processed", f"{video_base_name}.mp4")
        print('video path', video_path)
        model = "ai_models/trafego.pt"
        #model = "/home/josevaldo/Documentos/ProjDebora/modelos/trafego2.pt"
        
        self.trafic_analyzer(input_video, model, output_csv_path, video_base_name)
        
        VideoConverter.convert_video_to_h264(video_path)

        '''
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
'''