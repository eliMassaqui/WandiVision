import cv2
import mediapipe as mp
import serial
import time
import numpy as np
import copy
import math

# --- CONFIGURAÇÃO SERIAL ---
BAUD_RATE = 115200 
porta_serial = 'COM5' 
ultimo_cmd = 0 

try:
    arduino = serial.Serial(porta_serial, BAUD_RATE, timeout=0.01)
    time.sleep(2)
except:
    arduino = None
    print(f"Aviso: Arduino não detectado em {porta_serial}. Modo simulação.")

# --- PALETA DE CORES ---
C_FUNDO       = (250, 250, 250)
C_TEXTO       = (45, 41, 38)
C_LINHA       = (220, 220, 220)
C_BRANCO_PURO  = (255, 255, 255)
C_PRETO       = (0, 0, 0)
C_ROXO        = (230, 50, 140)  # Contorno persistente

# CORES DOS COMANDOS
C_VERDE       = (120, 200, 120)  # Duo (1)
C_AZUL_CMD    = (235, 166, 75)   # Together (2)
C_VERMELHO    = (80, 80, 240)    # Triple (3)
C_AMARELO_CMD  = (80, 200, 245)   # Quad (4)

# --- MEDIAPIPE SETUP ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8, min_tracking_confidence=0.8)

# --- CARREGAR ÍCONE ---
img_logo = cv2.imread('wandi.png', cv2.IMREAD_UNCHANGED)
logo_size = 60

# --- FUNÇÕES DE INTERFACE ---
def desenhar_texto_centralizado(img, texto, x, y, w, h, escala, cor, espessura=1):
    fonte = cv2.FONT_HERSHEY_SIMPLEX
    tamanho = cv2.getTextSize(texto, fonte, escala, espessura)[0]
    tx = x + (w - tamanho[0]) // 2
    ty = y + (h + tamanho[1]) // 2
    cv2.putText(img, texto, (tx, ty), fonte, escala, cor, espessura, cv2.LINE_AA)

def desenhar_botao(img, x, y, w, h, texto, ativo=False, cor_ativa=C_VERDE):
    cor_fundo = cor_ativa if ativo else C_FUNDO
    cv2.rectangle(img, (x, y), (x + w, y + h), cor_fundo, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), C_LINHA, 1)
    cor_txt = (255, 255, 255) if ativo else C_TEXTO
    desenhar_texto_centralizado(img, texto, x, y, w, h, 0.7, cor_txt, 2 if ativo else 1)

def desenhar_caixa_status(img, x, y, w, h, label, cor_fundo, ativo=False):
    cor_contorno = C_ROXO if ativo else C_PRETO
    espessura = 6 if ativo else 2 
    cv2.rectangle(img, (x, y), (x + w, y + h), cor_fundo, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), cor_contorno, espessura)
    cor_fonte = C_PRETO if cor_fundo == C_BRANCO_PURO else C_BRANCO_PURO
    desenhar_texto_centralizado(img, label, x, y, w, h, 0.8, cor_fonte, 2)

def get_finger_state(hand, lado):
    dedos = [False]*5
    tips = [4, 8, 12, 16, 20]
    if lado == "Right": dedos[0] = hand.landmark[4].x < hand.landmark[3].x
    else: dedos[0] = hand.landmark[4].x > hand.landmark[3].x
    for i in range(1, 5):
        dedos[i] = hand.landmark[tips[i]].y < hand.landmark[tips[i]-2].y
    return dedos

# --- JANELA ---
nome_janela = "Wandi Vision"
cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(nome_janela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    h_cam, w_cam, _ = frame.shape
    try: _, _, sw, sh = cv2.getWindowImageRect(nome_janela)
    except: sw, sh = 1920, 1080
    
    canvas = np.full((sh, sw, 3), C_FUNDO, dtype=np.uint8)
    w_sidebar = int(sw * 0.3)
    w_cam_area = sw - w_sidebar

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    esq_st, dir_st = [False]*5, [False]*5
    p_esq, p_dir = None, None
    m_esq_ok, m_dir_ok = False, False
    h_marks = []

    if result.multi_hand_landmarks:
        for i, hand in enumerate(result.multi_hand_landmarks):
            lado = result.multi_handedness[i].classification[0].label
            st = get_finger_state(hand, lado)
            pos = (hand.landmark[8].x, hand.landmark[8].y)
            if lado == "Left":
                esq_st, p_esq, m_esq_ok = st, pos, True
                cor_sk = C_AZUL_CMD
            else:
                dir_st, p_dir, m_dir_ok = st, pos, True
                cor_sk = C_AMARELO_CMD
            h_marks.append((hand, cor_sk))

    # --- LÓGICA ---
    esq_ap = esq_st[1] and not any(esq_st[2:])
    dir_ap = dir_st[1] and not any(dir_st[2:])
    esq_2d = esq_st[1] and esq_st[2] and not any(esq_st[3:])
    dir_2d = dir_st[1] and dir_st[2] and not any(dir_st[3:])

    cmd_atual = 0 
    if m_esq_ok and m_dir_ok:
        dist = math.hypot(p_esq[0]-p_dir[0], p_esq[1]-p_dir[1]) if p_esq and p_dir else 1.0
        if esq_ap and dir_ap and dist < 0.05: cmd_atual = 2  
        elif esq_ap and dir_ap: cmd_atual = 1                
        elif esq_2d and dir_2d: cmd_atual = 4                
        elif (esq_ap and dir_2d) or (esq_2d and dir_ap): cmd_atual = 3 

    if cmd_atual != 0 and cmd_atual != ultimo_cmd:
        if arduino:
            try: arduino.write(str(cmd_atual).encode())
            except: pass
        ultimo_cmd = cmd_atual

    # --- INTERFACE ---
    cv2.line(canvas, (0, 80), (sw, 80), C_LINHA, 2)
    if img_logo is not None:
        img_rsz = cv2.resize(img_logo, (logo_size, logo_size))
        ly, lx = 10, 30
        if img_rsz.shape[2] == 4:
            alpha = img_rsz[:,:,3]/255.0
            for c in range(3):
                canvas[ly:ly+logo_size, lx:lx+logo_size, c] = \
                img_rsz[:,:,c]*alpha + canvas[ly:ly+logo_size, lx:lx+logo_size, c]*(1-alpha)
        else: canvas[ly:ly+logo_size, lx:lx+logo_size] = img_rsz[:,:,:3]
    
    cv2.putText(canvas, "Wandivision", (110, 55), cv2.FONT_HERSHEY_TRIPLEX, 1.2, C_TEXTO, 2)

    # Botões superiores
    gy, hc, wc = 130, 140, w_sidebar // 2
    desenhar_botao(canvas, 0, gy, wc, hc, "Duo", cmd_atual==1, C_VERDE)
    desenhar_botao(canvas, wc, gy, wc, hc, "Together", cmd_atual==2, C_AZUL_CMD)
    desenhar_botao(canvas, 0, gy+hc, wc, hc, "Triple", cmd_atual==3, C_VERMELHO)
    desenhar_botao(canvas, wc, gy+hc, wc, hc, "Quad", cmd_atual==4, C_AMARELO_CMD)

    # --- STATUS REORGANIZADO (Coluna Azul vs Coluna Branca) ---
    start_y = gy + 3*hc + 40
    box_s = 85 
    gap = 25
    
    # Coluna Esquerda: AZUIS (1 e 3)
    desenhar_caixa_status(canvas, (wc - box_s)//2, start_y, box_s, box_s, "1", C_AZUL_CMD, ultimo_cmd==1)
    desenhar_caixa_status(canvas, (wc - box_s)//2, start_y + box_s + gap, box_s, box_s, "3", C_AZUL_CMD, ultimo_cmd==3)
    
    # Coluna Direita: BRANCAS (2 e 4)
    desenhar_caixa_status(canvas, (wc - box_s)//2 + wc, start_y, box_s, box_s, "2", C_BRANCO_PURO, ultimo_cmd==2)
    desenhar_caixa_status(canvas, (wc - box_s)//2 + wc, start_y + box_s + gap, box_s, box_s, "4", C_BRANCO_PURO, ultimo_cmd==4)

    cv2.line(canvas, (w_sidebar, 80), (w_sidebar, sh), C_TEXTO, 2)

    # Câmera Area
    sc = min((w_cam_area-40)/w_cam, (sh-140)/h_cam)
    nw, nh = int(w_cam*sc), int(h_cam*sc)
    v_rsz = cv2.resize(frame, (nw, nh))
    cx, cy = w_sidebar + (w_cam_area-nw)//2, 100 + ((sh-100)-nh)//2
    canvas[cy:cy+nh, cx:cx+nw] = v_rsz

    for mk, cor in h_marks:
        mk_cp = copy.deepcopy(mk)
        for lm in mk_cp.landmark:
            lm.x, lm.y = (lm.x*nw+cx)/sw, (lm.y*nh+cy)/sh
        mp_draw.draw_landmarks(canvas, mk_cp, mp_hands.HAND_CONNECTIONS, 
            mp_draw.DrawingSpec((255,255,255), 2), mp_draw.DrawingSpec(cor, 4))

    cv2.imshow(nome_janela, canvas)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
if arduino: arduino.close()