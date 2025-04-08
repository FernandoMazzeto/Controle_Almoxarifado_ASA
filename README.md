#**Projeto - Controle Almoxarifado - ASA**
## Como executar:
**1. Clonar o repositório:**
- git clone https://github.com/FernandoMazzeto/Controle_Almoxarifado_ASA.git
- cd Controle_Almoxarifado_ASA
  
**2. Suba os Containers:**
- docker-compose up --build

**3. Acesse a API:**
- http://localhost:8000/docs

**4. Como funciona o envio de pedidos:**
- Crie um pedido via rota POST /pedidos
- Envie o pedido para a fila usando a rota /enviar-pedido/{id}
- Processe o pedido pelo almoxarifado usando a rota /processar-pedido/{id}
