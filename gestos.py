import cv2
import mediapipe as mp
import serial
import time
import numpy as np
import copy

# --- CONFIGURAÇÃO SERIAL ---
try:
    # Ajuste 'COM5' para a sua porta correta
    arduino = serial.Serial('COM5', 9600, timeout=0.1)
    time.sleep(2)
except:
    arduino = None
    print("Arduino não conectado (Rodando apenas simulação visual)")

# --- PALETA DE CORES (MODO WHITE / MODERNO) ---
# Formato BGR (OpenCV usa Blue-Green-Red)
C_FUNDO     = (250, 250, 250)  # Branco gelo
C_TEXTO     = (60, 60, 60)     # Cinza escuro (mais suave que preto)
C_LINHA     = (200, 200, 200)  # Cinza claro para grades
C_DESTAQUE  = (240, 240, 240)  # Fundo para áreas ativas

# Cores de Ação (Pastel / Moderno)
C_AZUL      = (235, 166, 75)   # Azul suave (Steel Blue invertido BGR)
C_AMARELO   = (80, 200, 245)   # Amarelo/Laranja suave
C_ATIVO     = (150, 230, 150)  # Verde menta para "Sucesso/Ativo"

# --- MEDIAPIPE ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8)

# --- FUNÇÕES AUXILIARES DE DESENHO ---

def desenhar_texto_centralizado(img, texto, x, y, w, h, fonte, escala, cor, espessura=1):
    """Calcula posição para centralizar texto dentro de um retângulo/área"""
    tamanho = cv2.getTextSize(texto, fonte, escala, espessura)[0]
    texto_x = x + (w - tamanho[0]) // 2
    texto_y = y + (h + tamanho[1]) // 2
    cv2.putText(img, texto, (texto_x, texto_y), fonte, escala, cor, espessura, cv2.LINE_AA)

def desenhar_botao(img, x, y, w, h, texto, ativo=False, cor_ativa=C_ATIVO):
    """Desenha uma caixa do grid estilo 'Card'"""
    # Fundo
    cor_fundo = cor_ativa if ativo else C_FUNDO
    cv2.rectangle(img, (x, y), (x + w, y + h), cor_fundo, -1)
    # Borda
    cv2.rectangle(img, (x, y), (x + w, y + h), C_LINHA, 1)
    
    # Texto
    cor_txt = (255, 255, 255) if ativo else C_TEXTO
    espessura = 2 if ativo else 1
    desenhar_texto_centralizado(img, texto, x, y, w, h, cv2.FONT_HERSHEY_SIMPLEX, 0.7, cor_txt, espessura)

def desenhar_checkbox(img, x, y, w, h, titulo, checked=False, cor_check=C_TEXTO):
    """Desenha a seção de objetos com checkbox"""
    # Título da seção
    desenhar_texto_centralizado(img, titulo, x, y, w, 40, cv2.FONT_HERSHEY_SIMPLEX, 0.6, C_TEXTO, 1)
    
    # Caixa do Checkbox
    box_size = 30
    box_x = x + (w - box_size) // 2
    box_y = y + 50
    
    cv2.rectangle(img, (box_x, box_y), (box_x + box_size, box_y + box_size), C_TEXTO, 2)
    
    if checked:
        # Preenchimento se ativo
        cv2.rectangle(img, (box_x+4, box_y+4), (box_x + box_size-4, box_y + box_size-4), cor_check, -1)

# --- FUNÇÃO PRINCIPAL ---

def contar_dedos(hand, lado):
    dedos = 0
    tips = [8, 12, 16, 20] # Pontas dos dedos (menos dedão)

    # Lógica do Dedão (depende do lado da mão)
    if lado == "Right":
        if hand.landmark[4].x < hand.landmark[3].x: dedos += 1
    else:
        if hand.landmark[4].x > hand.landmark[3].x: dedos += 1

    # Outros 4 dedos
    for tip in tips:
        if hand.landmark[tip].y < hand.landmark[tip - 2].y: dedos += 1

    return dedos

# Setup Janela
nome_janela = "Wandi Vision Interface"
cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(nome_janela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break

    frame = cv2.flip(frame, 1)
    h_cam, w_cam, _ = frame.shape

    # 1. Configurar Tamanho da Tela (Canvas)
    try:
        _, _, sw, sh = cv2.getWindowImageRect(nome_janela)
    except:
        sw, sh = 1920, 1080 # Fallback

    canvas = np.full((sh, sw, 3), C_FUNDO, dtype=np.uint8)

    # 2. Definir Layout (Sidebar 30% | Câmera 70%)
    w_sidebar = int(sw * 0.30)
    w_camera_area = sw - w_sidebar
    
    # --- PROCESSAMENTO VISUAL (MediaPipe) ---
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    dedos_esq = 0
    dedos_dir = 0
    mao_esq_detectada = False
    mao_dir_detectada = False
    hand_landmarks_to_draw = []

    if result.multi_hand_landmarks:
        for i, hand in enumerate(result.multi_hand_landmarks):
            lado = result.multi_handedness[i].classification[0].label
            dedos = contar_dedos(hand, lado)

            if lado == "Left":
                dedos_esq = dedos
                mao_esq_detectada = True
                cor_mao = C_AZUL
            else:
                dedos_dir = dedos
                mao_dir_detectada = True
                cor_mao = C_AMARELO
            
            # Guardar para desenhar depois sobre a câmera redimensionada
            hand_landmarks_to_draw.append((hand, cor_mao))

    total_dedos = dedos_esq + dedos_dir
    duas_maos = mao_esq_detectada and mao_dir_detectada

    # --- COMUNICAÇÃO ARDUINO ---
    valor_arduino = (dedos_esq * 5) + dedos_dir
    leds = min(valor_arduino // 5, 4)
    
    if arduino:
        try:
            arduino.write(str(leds).encode())
        except:
            pass

    # ==========================================
    # DESENHANDO A INTERFACE (Baseado no Esboço)
    # ==========================================

    # --- HEADER GERAL ---
    cv2.line(canvas, (0, 80), (sw, 80), C_LINHA, 2)
    
    # Ícone (Círculo)
    cv2.circle(canvas, (60, 40), 30, C_TEXTO, 2)
    desenhar_texto_centralizado(canvas, "Icon", 30, 10, 60, 60, cv2.FONT_HERSHEY_SIMPLEX, 0.4, C_TEXTO)
    
    # Título "Wandivision"
    cv2.putText(canvas, "Wandivision", (110, 55), cv2.FONT_HERSHEY_TRIPLEX, 1.2, C_TEXTO, 2, cv2.LINE_AA)

    # --- SIDEBAR (ESQUERDA) ---
    # Título "Comandos"
    desenhar_texto_centralizado(canvas, "Comandos", 0, 80, w_sidebar, 50, cv2.FONT_HERSHEY_COMPLEX, 0.8, C_TEXTO)
    cv2.line(canvas, (0, 130), (w_sidebar, 130), C_LINHA, 1)

    # Grid de Comandos (Coordenadas relativas à sidebar)
    grid_y_start = 130
    cell_h = 150 # Altura de cada célula
    half_w = w_sidebar // 2

    # Linha 1: Duo | Together
    desenhar_botao(canvas, 0, grid_y_start, half_w, cell_h, "Duo", total_dedos == 2)
    desenhar_botao(canvas, half_w, grid_y_start, half_w, cell_h, "Together", duas_maos, C_AMARELO)

    # Linha 2: Triple | Quad
    desenhar_botao(canvas, 0, grid_y_start + cell_h, half_w, cell_h, "Triple", total_dedos == 3)
    desenhar_botao(canvas, half_w, grid_y_start + cell_h, half_w, cell_h, "Quad", total_dedos == 4)

    # Linha 3: Objetos Azuis | Objetos Brancos (Checkboxes)
    y_objs = grid_y_start + (cell_h * 2)
    cv2.line(canvas, (0, y_objs), (w_sidebar, y_objs), C_LINHA, 1) # Separador
    
    # Checkbox Azul (Esquerda)
    desenhar_checkbox(canvas, 0, y_objs, half_w, cell_h, "Obj. Azuis", mao_esq_detectada, C_AZUL)
    
    # Checkbox Branco (Direita/Amarelo)
    desenhar_checkbox(canvas, half_w, y_objs, half_w, cell_h, "Obj. Brancos", mao_dir_detectada, C_AMARELO)

    # Divisória Vertical Principal
    cv2.line(canvas, (w_sidebar, 80), (w_sidebar, sh), C_TEXTO, 2)

    # --- ÁREA DA CÂMERA (DIREITA) ---
    
    # Título "Camera Area" (Aparece se não houver vídeo, ou acima dele)
    # Vamos calcular o tamanho do vídeo para caber na área direita mantendo aspect ratio
    scale = min((w_camera_area - 40) / w_cam, (sh - 140) / h_cam)
    nw, nh = int(w_cam * scale), int(h_cam * scale)
    
    # Redimensiona o vídeo
    video_resized = cv2.resize(frame, (nw, nh))
    
    # Centraliza na área direita
    cam_x = w_sidebar + (w_camera_area - nw) // 2
    cam_y = 100 + ((sh - 100) - nh) // 2

    # Desenha borda decorativa da câmera
    padding = 10
    cv2.rectangle(canvas, (cam_x - padding, cam_y - padding), (cam_x + nw + padding, cam_y + nh + padding), (230, 230, 230), -1)
    cv2.rectangle(canvas, (cam_x - padding, cam_y - padding), (cam_x + nw + padding, cam_y + nh + padding), C_LINHA, 1)

    # Cola o vídeo no canvas
    canvas[cam_y:cam_y + nh, cam_x:cam_x + nw] = video_resized

    # --- DESENHO DOS SKELETONS (Mapeados para a nova posição) ---
    if hand_landmarks_to_draw:
        for hand_mk, cor in hand_landmarks_to_draw:
            # Precisamos clonar e remapear as coordenadas para a posição do vídeo na tela
            hand_map = copy.deepcopy(hand_mk)
            for lm in hand_map.landmark:
                # Transforma de normalizado (0-1) para pixels do vídeo redimensionado + offset da posição
                lm.x = (lm.x * nw + cam_x) / sw
                lm.y = (lm.y * nh + cam_y) / sh
            
            mp_draw.draw_landmarks(
                canvas, hand_map, mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=(255, 255, 255), thickness=2),
                mp_draw.DrawingSpec(color=cor, thickness=4)
            )

    # Overlay de Informação Técnica (Discreta no canto da câmera)
    info_text = f"Esq: {dedos_esq} | Dir: {dedos_dir} | LED Val: {valor_arduino}"
    cv2.putText(canvas, info_text, (cam_x, cam_y + nh + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, C_TEXTO, 1, cv2.LINE_AA)

    # Exibir "Camera Area" placeholder texto se quiser seguir estritamente o desenho
    desenhar_texto_centralizado(canvas, "Camera Area", w_sidebar, 80, w_camera_area, 50, cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150,150,150))

    # --- FINALIZAÇÃO ---
    if cv2.waitKey(1) & 0xFF == 27: # ESC para sair
        break

    cv2.imshow(nome_janela, canvas)

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()