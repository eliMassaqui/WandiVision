import cv2
import mediapipe as mp
import serial
import time
import numpy as np
import math

# --- CONFIGURAÇÃO SERIAL ---
BAUD_RATE = 115200 
porta_serial = 'COM5'

try:
    arduino = serial.Serial(porta_serial, BAUD_RATE, timeout=0.01)
    time.sleep(2) 
    print(f"Conectado ao Arduino em {porta_serial}")
except:
    arduino = None
    print(f"Aviso: Arduino não detectado em {porta_serial}. Modo simulação.")

# --- PALETA DE CORES ---
C_FUNDO       = (250, 250, 250)
C_TEXTO       = (45, 41, 38)
C_LINHA_UI    = (220, 220, 220)
C_PRETO       = (0, 0, 0)
C_ROXO        = (230, 50, 140)
C_LINHA_DEDOS = (255, 0, 0)   # Azul
C_PONTOS_DEDOS = (0, 255, 255) # Amarelo

# --- MEDIAPIPE SETUP ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# --- VARIÁVEIS DE CONTROLE ---
ultimo_angulo_enviado = -1
DIST_MIN_VISUAL = 0.03
DIST_MAX_VISUAL = 0.25

def desenhar_texto_centralizado(img, texto, x, y, w, h, escala, cor, espessura=1):
    fonte = cv2.FONT_HERSHEY_SIMPLEX
    tamanho = cv2.getTextSize(texto, fonte, escala, espessura)[0]
    tx = x + (w - tamanho[0]) // 2
    ty = y + (h + tamanho[1]) // 2
    cv2.putText(img, texto, (tx, ty), fonte, escala, cor, espessura, cv2.LINE_AA)

# --- JANELA E CÂMERA ---
nome_janela = "Wandi Vision - Controle Analogo"
cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
# Ativa tela cheia
cv2.setWindowProperty(nome_janela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret or frame is None: 
        continue
        
    frame = cv2.flip(frame, 1)
    h_cam, w_cam, _ = frame.shape
    
    # Obter tamanho real da janela (importante para o resize dinâmico)
    rect = cv2.getWindowImageRect(nome_janela)
    if rect and rect[2] > 0:
        _, _, sw, sh = rect
    else:
        sw, sh = 1280, 720 # Fallback inicial

    # Criar fundo
    canvas = np.full((sh, sw, 3), C_FUNDO, dtype=np.uint8)
    w_sidebar = int(sw * 0.25)
    w_cam_area = sw - w_sidebar

    # --- LÓGICA DE REDIMENSIONAMENTO (Onde ocorria o erro) ---
    # Garantimos que sc nunca seja zero ou negativo
    sc = max(0.01, min((w_cam_area - 60) / w_cam, (sh - 120) / h_cam))
    nw, nh = max(1, int(w_cam * sc)), max(1, int(h_cam * sc))
    
    # Centralização do frame na área da direita
    cx = w_sidebar + (w_cam_area - nw) // 2
    cy = 80 + ((sh - 80) - nh) // 2

    v_rsz = cv2.resize(frame, (nw, nh))

    # Processamento MediaPipe
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    angulo_atual = 90
    ponto_polegar_canvas = None
    ponto_indicador_canvas = None

    if result.multi_hand_landmarks:
        hand_landmarks = result.multi_hand_landmarks[0]
        thumb_tip = hand_landmarks.landmark[4]
        index_tip = hand_landmarks.landmark[8]

        dist_normalizada = math.hypot(thumb_tip.x - index_tip.x, 
                                      thumb_tip.y - index_tip.y,
                                      thumb_tip.z - index_tip.z)

        angulo_raw = np.interp(dist_normalizada, [DIST_MIN_VISUAL, DIST_MAX_VISUAL], [0, 180])
        angulo_atual = int(np.clip(angulo_raw, 0, 180))

        ponto_polegar_canvas = (int(thumb_tip.x * nw + cx), int(thumb_tip.y * nh + cy))
        ponto_indicador_canvas = (int(index_tip.x * nw + cx), int(index_tip.y * nh + cy))

    # --- ENVIO SERIAL ---
    if arduino and abs(angulo_atual - ultimo_angulo_enviado) > 1:
        try:
            arduino.write(f"{angulo_atual}\n".encode())
            ultimo_angulo_enviado = angulo_atual
        except:
            pass

    # --- UI RENDERING ---
    # Sidebar e divisores
    cv2.line(canvas, (0, 60), (sw, 60), C_LINHA_UI, 2)
    cv2.putText(canvas, "Wandivision: Servo Control", (20, 40), cv2.FONT_HERSHEY_TRIPLEX, 1.0, C_TEXTO, 2)
    cv2.line(canvas, (w_sidebar, 60), (w_sidebar, sh), C_LINHA_UI, 2)
    
    # Display do Ângulo
    desenhar_texto_centralizado(canvas, "ANGULO SERVO", 0, 80, w_sidebar, 40, 0.6, C_TEXTO, 1)
    cor_angulo = (0, int(np.interp(angulo_atual, [0, 180], [255, 0])), int(np.interp(angulo_atual, [0, 180], [0, 255])))
    cv2.rectangle(canvas, (20, 130), (w_sidebar-20, 250), C_PRETO, 2)
    desenhar_texto_centralizado(canvas, f"{angulo_atual}", 20, 130, w_sidebar-40, 120, 3.0, cor_angulo, 5)

    # Barra de Progresso
    bar_y, bar_w = 350, 40
    bar_h = sh - bar_y - 60
    cv2.rectangle(canvas, (w_sidebar//2 - 20, bar_y), (w_sidebar//2 + 20, bar_y + bar_h), C_LINHA_UI, -1)
    p_fill = int(np.interp(angulo_atual, [0, 180], [0, bar_h]))
    cv2.rectangle(canvas, (w_sidebar//2 - 20, bar_y + bar_h - p_fill), (w_sidebar//2 + 20, bar_y + bar_h), cor_angulo, -1)
    
    # Colocar frame da câmera no canvas
    canvas[cy:cy+nh, cx:cx+nw] = v_rsz

    # Desenho dos pontos (Azul e Amarelo)
    if ponto_polegar_canvas and ponto_indicador_canvas:
        cv2.line(canvas, ponto_polegar_canvas, ponto_indicador_canvas, C_LINHA_DEDOS, 4, cv2.LINE_AA)
        cv2.circle(canvas, ponto_polegar_canvas, 12, C_PONTOS_DEDOS, -1, cv2.LINE_AA)
        cv2.circle(canvas, ponto_indicador_canvas, 12, C_PONTOS_DEDOS, -1, cv2.LINE_AA)

    cv2.imshow(nome_janela, canvas)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
if arduino: arduino.close()