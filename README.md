# Motor de Gestos Python - Interface Neon ==== ANACONDA 🖐️⚡

![OPENCV](https://github.com/eliMassaqui/openCV/blob/master/Captura%20de%20ecr%C3%A3%202026-01-09%20155611.png)
![OPENCV](https://github.com/eliMassaqui/openCV/blob/master/WhatsApp%20Image%202026-01-12%20at%2014.47.34.jpeg)
![OPENCV](https://github.com/eliMassaqui/openCV/blob/master/WhatsApp%20Image%202026-01-12%20at%2014.47.32.jpeg)


Este projeto é um sistema de visão computacional de alta performance que utiliza Mediapipe e OpenCV para rastrear mãos em tempo real com uma interface HUD (Heads-Up Display) estilizada em cores neon.

---

## 🛠️ Tecnologias e Ambiente

* **Python 3.10** (Gerenciado via Anaconda)
* **OpenCV**: Manipulação de frames e renderização de interface.
* **Mediapipe**: Extração de landmarks e processamento de gestos.
* **Numpy**: Operações de matriz.

---

## 📦 Configuração e Execução (Obrigatório)

Para garantir que o modelo funcione com todas as dependências de visão computacional, o uso do ambiente Conda é obrigatório.

### 1. Localização do Projeto

O projeto deve ser executado a partir do diretório de trabalho:

```
C:\Users\UMALAB\Desktop\gestos
```

### 2. Ativação do Ambiente Anaconda

Abra o terminal (Anaconda Prompt ou PowerShell) e execute a ativação do ambiente dedicado:

```powershell
# Ativação do ambiente específico de gestos
conda activate gestos
```

### 3. Execução do Sistema

Após a ativação, execute o motor principal:

```powershell
# Certifique-se de estar na pasta do projeto
cd C:\Users\UMALAB\Desktop\gestos
python gestos.py
```

---

## 🧠 Lógica e Estrutura do Código

O projeto respeita uma lógica rigorosa de detecção baseada na orientação da mão (Esquerda/Direita).

> **Atenção à Identação:** O código utiliza estritamente 4 espaços. Alterações na estrutura de repetição ou condicionais sem respeitar esta regra causarão falhas no loop de processamento do OpenCV.

### Função de Contagem de Dedos

```python
def contar_dedos_pt(landmarks, hand_label):
    dedos = []
    # Lógica do Polegar (Invertida conforme a mão para precisão horizontal)
    if hand_label == "Right":
        dedos.append(landmarks[4].x < landmarks[3].x)
    else:
        dedos.append(landmarks[4].x > landmarks[3].x)

    # Verificação de elevação dos outros 4 dedos (Eixo Y)
    # Comparação entre a ponta (Tip) e a articulação média (PIP)
    for ponta, base in [(8, 6), (12, 10), (16, 14), (20, 18)]:
        dedos.append(landmarks[ponta].y < landmarks[base].y)
    
    return dedos
```

---

# Controle de LEDs via Gestos com Python e Arduino

Este projeto demonstra como controlar LEDs conectados a um Arduino utilizando **gestos de mão detectados pela câmera** via **Python e MediaPipe**, com comunicação serial entre Python e Arduino.

## 📋 Descrição

* Detecção de mãos em tempo real usando **MediaPipe**.
* Contagem de dedos levantados para determinar quantos LEDs acender.
* Comunicação serial com o Arduino para controle dos LEDs.
* LEDs conectados nos pinos **12, 13, 2, 3 e 4**.
* Interface gráfica em Python com HUD neon para visualização do status.

## 🛠 Tecnologias Utilizadas

* Python 3.x
* OpenCV
* MediaPipe
* PySerial
* Arduino IDE / Placas compatíveis

## 🔌 Conexão Arduino

* LEDs conectados aos pinos: **12, 13, 2, 3, 4**.
* GND do Arduino conectado aos LEDs através de resistores adequados (220Ω – 330Ω).
* Comunicação serial configurada na porta **COM5**.

## 💻 Código Arduino

```cpp
int leds[] = {12, 13, 2, 3, 4};
int numLeds = 5;

void setup() {
  Serial.begin(9600);
  for (int i = 0; i < numLeds; i++) {
    pinMode(leds[i], OUTPUT);
    digitalWrite(leds[i], LOW);
  }
}

void loop() {
  if (Serial.available() > 0) {
    int n = Serial.read() - '0';
    if (n >= 0 && n <= numLeds) {
      for (int i = 0; i < numLeds; i++) {
        digitalWrite(leds[i], i < n ? HIGH : LOW);
      }
    }
  }
}
```

## 🐍 Código Python

```python
import cv2
import mediapipe as mp
import serial
import time

arduino = serial.Serial('COM5', 9600)
time.sleep(2)

AZUL_PYTHON = (255, 150, 50)
AMARELO_PYTHON = (0, 255, 255)
BRANCO_PURO = (255, 255, 255)

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils

hands = mp_hands.Hands(max_num_hands=2, min_detection_confidence=0.8, min_tracking_confidence=0.8)
cap = cv2.VideoCapture(0)

def contar_dedos_pt(landmarks, hand_label):
    dedos = []
    if hand_label == "Right":
        dedos.append(landmarks[4].x < landmarks[3].x)
    else:
        dedos.append(landmarks[4].x > landmarks[3].x)
    for ponta, base in [(8,6),(12,10),(16,14),(20,18)]:
        dedos.append(landmarks[ponta].y < landmarks[base].y)
    return dedos

while True:
    ret, frame = cap.read()
    if not ret: break
    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    total_dedos = 0

    if result.multi_hand_landmarks:
        for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
            info_mao = result.multi_handedness[idx].classification[0].label
            dedos = contar_dedos_pt(hand_landmarks.landmark, info_mao)
            total = dedos.count(True)
            total_dedos = max(total_dedos, total)

    arduino.write(str(min(total_dedos,5)).encode())
    cv2.imshow("Gestos Arduino", frame)
    if cv2.waitKey(1) & 0xFF == 27: break

cap.release()
cv2.destroyAllWindows()
arduino.close()
```

## 🚀 Como Usar

1. Conecte os LEDs nos pinos corretos do Arduino.
2. Carregue o código Arduino na placa.
3. Instale as dependências Python: `opencv-python`, `mediapipe`, `pyserial`.
4. Ajuste a porta serial (`COM5`) no código Python.
5. Execute o script Python: `python gestos.py`.
6. Levante os dedos na frente da câmera e veja os LEDs acenderem.

## 🎯 Resultado

* 0 dedos → nenhum LED aceso
* 1 dedo → LED 1 aceso
* 2 dedos → LEDs 1 e 2 acesos
* ...
* 5 dedos → todos os LEDs acesos

## 🙏 Agradecimentos

Agradeço à **Causa-Efeito** pela formação em microcontroladores, que permitiu aplicar os conceitos rapidamente neste projeto prático.

## 📌 Tags

#Arduino #Python #MediaPipe #OpenCV #Gestos #Microcontroladores #Eletrónica #Automação #STEM #Educação #ProjetoHandsOn


| Elemento       | Cor (BGR)       | Descrição                             |
| -------------- | --------------- | ------------------------------------- |
| AZUL_PYTHON    | (255, 150, 50)  | Azul Elétrico para Mão Esquerda       |
| AMARELO_PYTHON | (0, 255, 255)   | Amarelo Fluorescente para Mão Direita |
| BRANCO_PURO    | (255, 255, 255) | Detalhes de HUD e Texto               |
