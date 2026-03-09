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