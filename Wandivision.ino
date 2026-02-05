/* Robotgames - Wandi Vision 
   Controle Estrito de Saídas Digitais
*/

// Definição dos pinos atualizada
const int PIN_DUO      = 9;  // Comando 1
const int PIN_TOGETHER = 10; // Comando 2
const int PIN_TRIPLE   = 11; // Comando 3
const int PIN_QUAD     = 12; // Comando 4

void setup() {
  Serial.begin(9600);

  pinMode(PIN_DUO, OUTPUT);
  pinMode(PIN_TOGETHER, OUTPUT);
  pinMode(PIN_TRIPLE, OUTPUT);
  pinMode(PIN_QUAD, OUTPUT);

  // Inicializa tudo em nível baixo (OFF)
  resetPins();
}

void loop() {
  if (Serial.available() > 0) {
    char comando = Serial.read();

    // Limpa estados anteriores para garantir exclusividade
    resetPins();

    // Aciona o pino conforme a nova ordem:
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
        // Caso receba '0' ou qualquer outro caractere, mantém tudo OFF
        resetPins();
        break;
    }
  }
}

void resetPins() {
  digitalWrite(PIN_DUO, LOW);
  digitalWrite(PIN_TOGETHER, LOW);
  digitalWrite(PIN_TRIPLE, LOW);
  digitalWrite(PIN_QUAD, LOW);
}