# 📘 Wandi Vision — Physical Robot Control

O **Wandi Vision** é o sistema de percepção e controle gestual do **Wandi Robot**.
Ele interpreta gestos bimanuias em tempo real e converte esses gestos em comandos digitais discretos, enviados via comunicação serial diretamente ao robô.
---

## 🧠 Arquitetura do Sistema

### Camada de Percepção

* MediaPipe Hands
* Rastreamento simultâneo das duas mãos
* Extração de estados lógicos dos dedos

### Camada de Decisão

* Combinação bimanual de gestos
* Máquina de estados discreta
* Apenas um comando ativo por vez

### Camada de Execução

* Comunicação Serial @ **115200 bps**
* Protocolo enxuto (**1 byte**)
* Controle direto das saídas digitais do robô

---

## 🔗 Protocolo de Comunicação (Serial)

| Byte | Estado   | Ação no Wandi Robot |
| ---- | -------- | ------------------- |
| '1'  | Duo      | ... |
| '2'  | Together | ... |
| '3'  | Triple   | ... |
| '4'  | Quad     | ... |

📌 Os estados são **mutuamente exclusivos**.

---

## ⚙️ Execução (Obrigatória via Conda)

O sistema **só pode ser executado** dentro do ambiente Conda configurado:

```bash
conda activate gestos
python gestos.py
```

Execução fora desse ambiente **não é suportada**.

---

## 🧩 Trechos Essenciais — `gestos.py`

### Comunicação com o Wandi Robot

```python
BAUD_RATE = 115200
porta_serial = 'COM5'

arduino = serial.Serial(porta_serial, BAUD_RATE, timeout=0.01)
```

Estabelece o canal direto de controle entre o módulo de visão e o robô físico.

---

### Extração de Estados dos Dedos

```python
def get_finger_state(hand, lado):
    dedos = [False]*5
    if lado == "Right":
        dedos[0] = hand.landmark[4].x < hand.landmark[3].x
    else:
        dedos[0] = hand.landmark[4].x > hand.landmark[3].x
    return dedos
```

Converte geometria da mão em estados lógicos binários.

---

### Lógica de Decisão (Estados do Robô)

```python
if esq_ap and dir_ap:
    cmd_atual = 1
elif esq_2d and dir_2d:
    cmd_atual = 4
```

Cada combinação de gestos gera **um único estado operacional** do Wandi Robot.

---

### Envio Seguro do Comando

```python
if cmd_atual != ultimo_cmd:
    arduino.write(str(cmd_atual).encode())
    ultimo_cmd = cmd_atual
```

Evita flood serial e garante transições de estado controladas.

---

## 🔌 Firmware do Wandi Robot — Código Arduino Completo

```cpp
/*
 Wandi Vision - Execution Layer (Wandi Robot)

 Responsabilidades:
 - Receber comandos via Serial
 - Garantir exclusividade das saídas digitais
 - Operar em modo fail-safe
 - Controlar diretamente o hardware do Wandi Robot

 Protocolo:
 - 1 byte por comando ('1' a '4')
 - Baud rate: 115200
*/

// Definição dos pinos de controle do robô
const int PIN_DUO      = 9;   // Comando 1
const int PIN_TOGETHER = 10;  // Comando 2
const int PIN_TRIPLE   = 11;  // Comando 3
const int PIN_QUAD     = 12;  // Comando 4

void setup() {

  // Inicializa comunicação serial
  Serial.begin(115200);

  // Configura pinos como saída
  pinMode(PIN_DUO, OUTPUT);
  pinMode(PIN_TOGETHER, OUTPUT);
  pinMode(PIN_TRIPLE, OUTPUT);
  pinMode(PIN_QUAD, OUTPUT);

  // Estado inicial seguro
  resetPins();
}

void loop() {

  // Aguarda comando vindo do Wandi Vision
  if (Serial.available() > 0) {

    char comando = Serial.read();

    // Garante exclusividade:
    // sempre limpa todos os estados antes de ativar um novo
    resetPins();

    switch (comando) {

      case '1':
        digitalWrite(PIN_DUO, HIGH);
        break;

      case '2':
        digitalWrite(PIN_TOGETHER, HIGH);
        break;

      case '3':
        digitalWrite(PIN_TRIPLE, HIGH);
        break;

      case '4':
        digitalWrite(PIN_QUAD, HIGH);
        break;

      default:
        // Qualquer valor inesperado mantém o robô em estado seguro
        resetPins();
        break;
    }
  }
}

// Função de segurança: desativa todas as saídas
void resetPins() {

  digitalWrite(PIN_DUO, LOW);
  digitalWrite(PIN_TOGETHER, LOW);
  digitalWrite(PIN_TRIPLE, LOW);
  digitalWrite(PIN_QUAD, LOW);
}
```

---

## 🔐 Segurança Operacional

* Nenhum comando contínuo
* Nenhum estado ambíguo
* Reset automático a cada novo comando
* Fail-safe por padrão no robô físico

---

## 📌 Status

✔ Controle gestual do Wandi Robot físico
✔ Comunicação serial estável
✔ Arquitetura extensível
