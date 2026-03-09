# 📘 Wandi Vision — Controle Analógico de Servo

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Conda](https://img.shields.io/badge/Conda-Active-brightgreen)](https://docs.conda.io/)

O **Wandi Vision** é um módulo do ecossistema **Wandi Studio** que permite **controlar servos motores a partir de gestos da mão**. Ele interpreta a distância entre o polegar e o dedo indicador em tempo real e converte esse gesto em um ângulo analógico (0° a 180°), enviado via comunicação serial para o microcontrolador.

---

![Wandi Vision Screenshot](https://github.com/eliMassaqui/WandiVision/blob/master/Captura%20de%20ecr%C3%A3%202026-03-09%20132352.png)

---

## 🧠 Arquitetura do Sistema

### Camada de Percepção

* **MediaPipe Hands** — Rastreamento de 1 mão
* Extração da distância entre polegar e indicador
* Normalização da distância para range de 0° a 180°

### Camada de Decisão

* Interpolação linear da distância para ângulo do servo
* Filtragem de jitter (envio apenas se a diferença > 1°)
* Interface visual em tempo real para monitoramento do ângulo

### Camada de Execução

* Comunicação serial @ **115200 bps**
* Envio contínuo de valores inteiros do ângulo (0–180)
* Controle direto do servo motor via Arduino

---

## 🔗 Protocolo de Comunicação (Serial)

| Tipo de dado | Conteúdo | Ação no Arduino       |
| ------------ | -------- | --------------------- |
| Inteiro      | 0 a 180  | Ângulo do servo motor |

📌 O valor enviado é **inteiro** e representa diretamente a posição do servo.

---

## ⚙️ Instalação e Execução

### 1. Criar e ativar ambiente Conda

```bash
conda create -n gestos python=3.10
```

### 2. Instalar dependências

```bash
pip install opencv-python mediapipe pyserial numpy
```

### 3. Executar o módulo

```bash
conda activate gestos
python gestos.py
```

> Obs: Execução fora do ambiente configurado **não é garantida**.

---

## 🧩 Trechos Essenciais — `wandi_vision.py`

### Comunicação Serial com Arduino

```python
BAUD_RATE = 115200
porta_serial = 'COM5'
arduino = serial.Serial(porta_serial, BAUD_RATE, timeout=0.01)
```

### Cálculo do Ângulo a partir da Distância

```python
dist_normalizada = math.hypot(thumb_tip.x - index_tip.x,
                              thumb_tip.y - index_tip.y,
                              thumb_tip.z - index_tip.z)
angulo_raw = np.interp(dist_normalizada, [DIST_MIN_VISUAL, DIST_MAX_VISUAL], [0, 180])
angulo_atual = int(np.clip(angulo_raw, 0, 180))
```

### Envio Seguro do Ângulo

```python
if arduino and abs(angulo_atual - ultimo_angulo_enviado) > 1:
    arduino.write(f"{angulo_atual}\n".encode())
    ultimo_angulo_enviado = angulo_atual
```

---

## 🔌 Firmware Arduino — Controle do Servo

```cpp
#include <Servo.h>

Servo meuServo;
const int pinoServo = 6; // Pino de sinal do servo

void setup() {
  // Inicializa serial na mesma velocidade definida no Python
  Serial.begin(115200);
  
  meuServo.attach(pinoServo);
  
  // Inicializa o servo no meio (90 graus)
  meuServo.write(90);
  
  // Imprime uma mensagem para confirmar o boot (aparece no terminal do Python se ler)
  Serial.println("WandiVision Analogo Iniciado");
}

void loop() {
  // Verifica se há dados chegando na porta serial
  if (Serial.available() > 0) {
    
    // Lê o próximo número inteiro válido que chega pela serial.
    // O Python está enviando "VALOR\n". O parseInt sabe ler isso.
    int angulo = Serial.parseInt();
    
    // Se recebeu um ângulo válido ( parseInt retorna 0 se não encontrar número, 
    // mas 0 é um ângulo válido, então confiamos na lógica do Python)
    
    // Pequena validação de segurança para garantir o range do servo
    if (angulo >= 0 && angulo <= 180) {
      // Move o servo para o ângulo recebido da mão
      meuServo.write(angulo);
    }
  }
}
```

---

## 🔐 Segurança Operacional

* Filtragem de ângulo mínimo para evitar jitter
* Reset automático de posição inicial no boot
* Comunicação serial robusta para falhas de leitura
* Garantia de operação dentro do range do servo (0°–180°)

---

## 📌 Status

✔ Controle gestual do servo motor funcionando
✔ Comunicação serial confiável
✔ Interface visual em tempo real
✔ Arquitetura modular, extensível para outros módulos do Wandi Studio

---

## 🔗 Links e Referências

* [MediaPipe Hands](https://google.github.io/mediapipe/solutions/hands)
* [OpenCV](https://opencv.org/)
* [PySerial](https://pyserial.readthedocs.io/)

---

**Licença:** MIT
