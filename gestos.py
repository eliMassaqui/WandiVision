import cv2
import mediapipe as mp
import serial
import time
import numpy as np
import copy
import math

# --- CONFIGURAÇÃO SERIAL ---
try:
    arduino = serial.Serial('COM5', 9600, timeout=0.1)
    time.sleep(2)
except:
    arduino = None
    print("Arduino não conectado (Rodando simulação)")

# --- CORES ---
C_FUNDO     = (250, 250, 250)
C_TEXTO     = (60, 60, 60)
C_LINHA     = (200, 200, 200)
C_AZUL      = (235, 166, 75)
C_AMARELO   = (80, 200, 245)
C_ATIVO     = (150, 230, 150) # Verde Confirmação
C_DESATIVO  = (240, 240, 240)

# --- MEDIAPIPE ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8, min_tracking_confidence=0.8)

# --- FUNÇÕES VISUAIS ---
def desenhar_texto_centralizado(img, texto, x, y, w, h, fonte, escala, cor, espessura=1):
    tamanho = cv2.getTextSize(texto, fonte, escala, espessura)[0]
    texto_x = x + (w - tamanho[0]) // 2
    texto_y = y + (h + tamanho[1]) // 2
    cv2.putText(img, texto, (texto_x, texto_y), fonte, escala, cor, espessura, cv2.LINE_AA)

def desenhar_botao(img, x, y, w, h, texto, ativo=False, cor_ativa=C_ATIVO):
    cor_fundo = cor_ativa if ativo else C_FUNDO
    cv2.rectangle(img, (x, y), (x + w, y + h), cor_fundo, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), C_LINHA, 1)
    cor_txt = (255, 255, 255) if ativo else C_TEXTO
    espessura = 2 if ativo else 1
    desenhar_texto_centralizado(img, texto, x, y, w, h, cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_txt, espessura)

def desenhar_checkbox(img, x, y, w, h, titulo, checked=False, cor_check=C_TEXTO):
    desenhar_texto_centralizado(img, titulo, x, y, w, 40, cv2.FONT_HERSHEY_SIMPLEX, 0.6, C_TEXTO, 1)
    box_size = 30
    box_x = x + (w - box_size) // 2
    box_y = y + 50
    cv2.rectangle(img, (box_x, box_y), (box_x + box_size, box_y + box_size), C_TEXTO, 2)
    if checked:
        cv2.rectangle(img, (box_x+4, box_y+4), (box_x + box_size-4, box_y + box_size-4), cor_check, -1)

# --- ANALISE ESTRITA DOS DEDOS ---
def get_finger_state(hand, lado):
    """
    Retorna estado [Dedão, Indicador, Médio, Anelar, Mindinho]
    True = Levantado / False = Baixado
    """
    dedos = [False, False, False, False, False]
    tips = [4, 8, 12, 16, 20] 

    # Dedão (Eixo X)
    if lado == "Right":
        if hand.landmark[4].x < hand.landmark[3].x: dedos[0] = True
    else:
        if hand.landmark[4].x > hand.landmark[3].x: dedos[0] = True

    # Outros 4 dedos (Eixo Y - Ponta acima da articulação PIP)
    # Usamos PIP (landmark-2) para garantir que o dedo está esticado mesmo
    for i in range(1, 5):
        if hand.landmark[tips[i]].y < hand.landmark[tips[i] - 2].y:
            dedos[i] = True
    return dedos

# Setup Janela
nome_janela = "Wandi Vision Strict"
cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(nome_janela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    h_cam, w_cam, _ = frame.shape
    
    # Layout responsivo
    try:
        _, _, sw, sh = cv2.getWindowImageRect(nome_janela)
    except:
        sw, sh = 1920, 1080
    
    canvas = np.full((sh, sw, 3), C_FUNDO, dtype=np.uint8)
    w_sidebar = int(sw * 0.30)
    w_camera_area = sw - w_sidebar

    # Processamento
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    # Variáveis de Estado
    dedos_esq = [False]*5
    dedos_dir = [False]*5
    ponta_esq = None # Coordenada Ponta Indicador
    ponta_dir = None # Coordenada Ponta Indicador
    mao_esq_ok = False
    mao_dir_ok = False
    
    hand_landmarks_to_draw = []

    if result.multi_hand_landmarks:
        for i, hand in enumerate(result.multi_hand_landmarks):
            lado = result.multi_handedness[i].classification[0].label
            states = get_finger_state(hand, lado)
            
            # Coordenada da ponta do indicador (Landmark 8)
            px = hand.landmark[8].x
            py = hand.landmark[8].y

            if lado == "Left":
                dedos_esq = states
                ponta_esq = (px, py)
                mao_esq_ok = True
                cor = C_AZUL
            else:
                dedos_dir = states
                ponta_dir = (px, py)
                mao_dir_ok = True
                cor = C_AMARELO
                
            hand_landmarks_to_draw.append((hand, cor))

    # =========================================================
    # LÓGICA RESTRITA E INTELIGENTE
    # =========================================================

    # 1. Definir "Posturas" para cada mão individualmente
    # Nota: states[1]=Ind, [2]=Med, [3]=Anel, [4]=Min
    
    # Postura "Apontar" (Só indicador UP, resto DOWN)
    # Ignoramos o dedão (states[0]) para ser mais ergonômico, ou incluímos se quiser super estrito
    esq_apontar = dedos_esq[1] and not dedos_esq[2] and not dedos_esq[3] and not dedos_esq[4]
    dir_apontar = dedos_dir[1] and not dedos_dir[2] and not dedos_dir[3] and not dedos_dir[4]

    # Postura "Dois Dedos" (Indicador + Médio UP, Anelar + Mindinho DOWN)
    esq_dois = dedos_esq[1] and dedos_esq[2] and not dedos_esq[3] and not dedos_esq[4]
    dir_dois = dedos_dir[1] and dedos_dir[2] and not dedos_dir[3] and not dedos_dir[4]

    # Estados Finais (Mutuamente Exclusivos)
    cmd_duo = False
    cmd_together = False
    cmd_triple = False
    cmd_quad = False

    # Só processa se ambas as mãos estiverem na tela
    if mao_esq_ok and mao_dir_ok:
        
        # Verificar contato (Distância entre pontas dos indicadores)
        distancia = 100 # valor alto padrão
        if ponta_esq and ponta_dir:
            distancia = math.hypot(ponta_esq[0] - ponta_dir[0], ponta_esq[1] - ponta_dir[1])
        
        tocando = distancia < 0.05 # Threshold de toque (5% da tela)

        # HIERARQUIA DE DECISÃO (if - elif - elif)
        
        # CASO 1: TOGETHER
        # Requisito: Ambos em postura de "Apontar" E se tocando
        if esq_apontar and dir_apontar and tocando:
            cmd_together = True
            
        # CASO 2: DUO
        # Requisito: Ambos em postura de "Apontar", mas NÃO se tocando
        elif esq_apontar and dir_apontar and not tocando:
            cmd_duo = True
            
        # CASO 3: QUAD
        # Requisito: Ambas as mãos com postura "Dois Dedos" (2 + 2 = 4)
        # Verificação estrita: Anelares e mindinhos devem estar baixados
        elif esq_dois and dir_dois:
            cmd_quad = True
            
        # CASO 4: TRIPLE
        # Requisito: Uma mão "Apontar" e a outra "Dois Dedos" (1 + 2 = 3)
        elif (esq_apontar and dir_dois) or (esq_dois and dir_apontar):
            cmd_triple = True

    # --- OBJETOS (CHECKBOXES) ---
    # Independentes dos comandos centrais, mas também estritos (Anelar/Min OFF)
    check_azul = esq_dois  # Mão Esq fazendo "V" limpo
    check_branco = dir_dois # Mão Dir fazendo "V" limpo

    # --- ARDUINO ---
    valor_serial = 0
    if cmd_together: valor_serial = 4
    elif cmd_quad:   valor_serial = 3
    elif cmd_triple: valor_serial = 2
    elif cmd_duo:    valor_serial = 1
    
    if arduino:
        try: arduino.write(str(valor_serial).encode())
        except: pass

    # ==========================
    # DESENHO (Visual White Mode)
    # ==========================
    
    # Cabeçalho
    cv2.line(canvas, (0, 80), (sw, 80), C_LINHA, 2)
    cv2.circle(canvas, (60, 40), 30, C_TEXTO, 2)
    desenhar_texto_centralizado(canvas, "Icon", 30, 10, 60, 60, cv2.FONT_HERSHEY_SIMPLEX, 0.4, C_TEXTO)
    cv2.putText(canvas, "Wandivision", (110, 55), cv2.FONT_HERSHEY_TRIPLEX, 1.2, C_TEXTO, 2, cv2.LINE_AA)

    # Sidebar
    desenhar_texto_centralizado(canvas, "Comandos", 0, 80, w_sidebar, 50, cv2.FONT_HERSHEY_COMPLEX, 0.8, C_TEXTO)
    cv2.line(canvas, (0, 130), (w_sidebar, 130), C_LINHA, 1)

    grid_y = 130
    h_cell = 150
    w_cell = w_sidebar // 2

    # Botões Grid (Apenas um acende por vez devido à lógica if/elif)
    desenhar_botao(canvas, 0, grid_y, w_cell, h_cell, "Duo", cmd_duo)
    desenhar_botao(canvas, w_cell, grid_y, w_cell, h_cell, "Together", cmd_together, C_AMARELO)
    desenhar_botao(canvas, 0, grid_y + h_cell, w_cell, h_cell, "Triple", cmd_triple)
    desenhar_botao(canvas, w_cell, grid_y + h_cell, w_cell, h_cell, "Quad", cmd_quad)

    # Checkboxes Objetos
    y_obj = grid_y + (h_cell * 2)
    cv2.line(canvas, (0, y_obj), (w_sidebar, y_obj), C_LINHA, 1)
    
    desenhar_checkbox(canvas, 0, y_obj, w_cell, h_cell, "Obj. Azuis", check_azul, C_AZUL)
    desenhar_checkbox(canvas, w_cell, y_obj, w_cell, h_cell, "Obj. Brancos", check_branco, C_AMARELO)

    cv2.line(canvas, (w_sidebar, 80), (w_sidebar, sh), C_TEXTO, 2)

    # Área Câmera
    scale = min((w_camera_area - 40) / w_cam, (sh - 140) / h_cam)
    nw, nh = int(w_cam * scale), int(h_cam * scale)
    video_resized = cv2.resize(frame, (nw, nh))
    
    cam_x = w_sidebar + (w_camera_area - nw) // 2
    cam_y = 100 + ((sh - 100) - nh) // 2

    cv2.rectangle(canvas, (cam_x-10, cam_y-10), (cam_x+nw+10, cam_y+nh+10), (230, 230, 230), -1)
    cv2.rectangle(canvas, (cam_x-10, cam_y-10), (cam_x+nw+10, cam_y+nh+10), C_LINHA, 1)
    canvas[cam_y:cam_y + nh, cam_x:cam_x + nw] = video_resized

    # Mãos sobre o vídeo
    if hand_landmarks_to_draw:
        for hand_mk, cor in hand_landmarks_to_draw:
            hand_map = copy.deepcopy(hand_mk)
            for lm in hand_map.landmark:
                lm.x = (lm.x * nw + cam_x) / sw
                lm.y = (lm.y * nh + cam_y) / sh
            mp_draw.draw_landmarks(canvas, hand_map, mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2),
                mp_draw.DrawingSpec(color=cor, thickness=4))

    # Debug Discreto
    debug_text = f"CMD: {valor_serial}"
    cv2.putText(canvas, debug_text, (cam_x, cam_y + nh + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (180,180,180), 1)

    if cv2.waitKey(1) & 0xFF == 27: break
    cv2.imshow(nome_janela, canvas)

cap.release()
cv2.destroyAllWindows()
if arduino: arduino.close()