import cv2
import mediapipe as mp
import serial
import time
import numpy as np
import copy

# --- SERIAL ---
try:
    arduino = serial.Serial('COM5', 9600, timeout=0.1)
    time.sleep(2)
except:
    arduino = None
    print("Arduino não conectado")

# --- CORES ---
FUNDO = (248, 249, 250)
BRANCO = (255, 255, 255)
BORDA = (220, 220, 220)
TEXTO = (45, 41, 38)

AZUL = (255, 150, 50)
AMARELO = (0, 255, 255)

# --- MEDIAPIPE ---
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8)

cap = cv2.VideoCapture(0)

nome_janela = "Wandi Vision"
cv2.namedWindow(nome_janela, cv2.WINDOW_NORMAL)
cv2.setWindowProperty(nome_janela, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

# --- CONTAR DEDOS ---
def contar_dedos(hand, lado):
    dedos = 0
    tips = [8, 12, 16, 20]

    if lado == "Right":
        if hand.landmark[4].x < hand.landmark[3].x:
            dedos += 1
    else:
        if hand.landmark[4].x > hand.landmark[3].x:
            dedos += 1

    for tip in tips:
        if hand.landmark[tip].y < hand.landmark[tip - 2].y:
            dedos += 1

    return dedos

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape

    try:
        _, _, sw, sh = cv2.getWindowImageRect(nome_janela)
    except:
        sw, sh = 1920, 1080

    canvas = np.full((sh, sw, 3), FUNDO, dtype=np.uint8)

    scale = min((sw - 40) / w, (sh - 140) / h)
    nw, nh = int(w * scale), int(h * scale)
    video = cv2.resize(frame, (nw, nh))

    xo = (sw - nw) // 2
    yo = 100

    cv2.rectangle(canvas, (xo - 5, yo - 5), (xo + nw + 5, yo + nh + 5), BRANCO, -1)
    cv2.rectangle(canvas, (xo - 5, yo - 5), (xo + nw + 5, yo + nh + 5), BORDA, 1)
    canvas[yo:yo + nh, xo:xo + nw] = video

    rgb = cv2.cvtColor(video, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    dedos_esq = 0
    dedos_dir = 0

    if result.multi_hand_landmarks:
        for i, hand in enumerate(result.multi_hand_landmarks):
            lado = result.multi_handedness[i].classification[0].label
            dedos = contar_dedos(hand, lado)

            if lado == "Left":
                dedos_esq = dedos
            else:
                dedos_dir = dedos

            cor = AZUL if lado == "Left" else AMARELO

            hand_map = copy.deepcopy(hand)
            for lm in hand_map.landmark:
                lm.x = (lm.x * nw + xo) / sw
                lm.y = (lm.y * nh + yo) / sh

            mp_draw.draw_landmarks(
                canvas, hand_map, mp_hands.HAND_CONNECTIONS,
                mp_draw.DrawingSpec(color=BRANCO, thickness=2),
                mp_draw.DrawingSpec(color=cor, thickness=4)
            )

    valor = (dedos_esq * 5) + dedos_dir
    leds = min(valor // 5, 4)

    if arduino:
        try:
            arduino.write(str(leds).encode())
        except:
            pass

    cv2.putText(canvas, f"MAO ESQ: {dedos_esq}", (40, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, AZUL, 2)

    cv2.putText(canvas, f"MAO DIR: {dedos_dir}", (300, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, AMARELO, 2)

    cv2.putText(canvas, f"VALOR: {valor}  |  LEDS: {leds}", (600, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 1, TEXTO, 2)

    if cv2.waitKey(1) & 0xFF == 27:
        break

    cv2.imshow(nome_janela, canvas)

cap.release()
cv2.destroyAllWindows()
if arduino:
    arduino.close()
