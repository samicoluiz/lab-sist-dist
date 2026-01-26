# 📘 Guia de Conformidade e Demonstração: Middleware DDB

Este guia serve como roteiro para apresentar o projeto, conectando cada requisito da atividade aos trechos específicos do código e explicando como demonstrar as funcionalidades na prática.

---

## 1. Arquitetura e Configuração

### Requisito: Execução em 3 Máquinas & Configuração de IPs
*   **Descrição:** O sistema deve rodar em pelo menos 3 máquinas e permitir configuração via IP.
*   **Onde ver no código:**
    *   Arquivo: `config.json` (ou `config.local.json`).
    *   Código: Classe `No.carregar_configuracao` em `node.py`.
*   **Como Demonstrar:**
    1.  Abra o arquivo `config.json` e mostre a lista `nodes` com IPs e portas configurados.
    2.  Mostre os 3 terminais rodando os nós (`python node.py 0`, `1`, `2`).

### Requisito: SGBD MySQL & DDM Homogêneo Autônomo
*   **Descrição:** Usar MySQL e garantir que cada nó seja independente (autônomo).
*   **Onde ver no código:**
    *   Arquivo: `node.py` -> `self.config_bd`.
    *   Código: Cada instância cria sua própria conexão (`mysql.connector.connect`) com o banco local.
*   **Como Demonstrar:**
    1.  Conecte-se manualmente a um dos bancos MySQL (via Workbench ou CLI) e mostre a tabela (vazia ou com dados).
    2.  Faça o mesmo em outra instância para provar que são bancos fisicamente separados.

---

## 2. Comunicação e Protocolo

### Requisito: Sockets & Protocolo Próprio
*   **Descrição:** Comunicação via Sockets e protocolo definido.
*   **Onde ver no código:**
    *   Arquivo: `node.py`.
    *   Socket: Método `enviar_msg` utiliza `socket.socket(socket.AF_INET, socket.SOCK_STREAM)`.
    *   Protocolo: Mensagens em JSON com campo `type` (`CLIENT_QUERY`, `REPLICATE`, `HEARTBEAT`).
*   **Como Demonstrar:**
    1.  Observe os logs no terminal quando um nó inicia.
    2.  Destaque mensagens como `Mensagem recebida: REPLICATE` ou `Mensagem recebida: CLIENT_QUERY`.

### Requisito: Checksum (Integridade)
*   **Descrição:** Verificar a integridade dos dados recebidos.
*   **Onde ver no código:**
    *   Arquivo: `node.py`.
    *   Código: Função `calcular_checksum` (usa MD5). O receptor recalcula o hash e compara com o recebido.
*   **Como Demonstrar:**
    1.  Aponte para a validação no código: `if self.calcular_checksum(...) != msg['checksum']:`.
    2.  Nos logs de execução, mostre a linha: `Replicando Checksum: <hash_md5>`.

---

## 3. Funcionalidades Críticas (Apresentação ao Vivo)

### Requisito: Replicação de Dados (Broadcast)
*   **Descrição:** Alterações (INSERT/UPDATE/DELETE) em um nó devem ser replicadas em todos.
*   **Onde ver no código:**
    *   Arquivo: `node.py` -> `executar_query`.
    *   Código: Detecta escrita e chama `realizar_broadcast`.
*   **🧪 DEMONSTRAÇÃO:**
    1.  Abra o cliente: `python client.py`.
    2.  Conecte no **Nó 0**.
    3.  Execute: `INSERT INTO users (name, email) VALUES ('Demo', 'demo@teste.com');`
    4.  Desconecte e conecte no **Nó 2**.
    5.  Execute: `SELECT * FROM users WHERE email = 'demo@teste.com';`
    6.  **Resultado:** O dado inserido no Nó 0 aparecerá na consulta do Nó 2.

### Requisito: Balanceamento de Carga (Sem Sobrecarga)
*   **Descrição:** Distribuir requisições entre os nós para evitar sobrecarga.
*   **Onde ver no código:**
    *   Arquivo: `client.py`.
    *   Código: Opção **"a: Auto"** usa `random.randint` para escolher o nó de destino.
*   **🧪 DEMONSTRAÇÃO:**
    1.  No `client.py`, escolha a opção **"a: Auto"**.
    2.  Faça 3 a 5 consultas simples seguidas (ex: `SELECT 1`).
    3.  Observe os terminais dos servidores. Você verá que **nós diferentes** imprimiram "Executando Query", provando a distribuição.

### Requisito: Tolerância a Falhas e Eleição (Coordenador)
*   **Descrição:** Eleição de novo coordenador caso o atual falhe (Algoritmo Bully/Valentão).
*   **Onde ver no código:**
    *   Arquivo: `node.py`.
    *   Código: Thread `monitorar_nos` detecta falha e `iniciar_eleicao` executa o algoritmo.
*   **🧪 DEMONSTRAÇÃO (O "Grand Finale"):**
    1.  No cliente, use a opção 'c' para descobrir quem é o Coordenador atual (ex: Nó 2).
    2.  Vá ao terminal do **Coordenador (Nó 2)** e encerre o processo (Ctrl+C).
    3.  Observe os logs dos nós restantes (0 e 1).
    4.  Em aprox. 10s, aparecerá:
        *   `[Nó X] Nó 2 offline`
        *   `Iniciando eleição...`
        *   `Novo Coordenador: 1` (O nó de maior ID restante assume).

### Requisito: ACID e Logs
*   **Descrição:** Garantir propriedades ACID e informar operações.
*   **Onde ver no código:**
    *   ACID Local: Uso de `conn.commit()` do MySQL.
    *   Logs: `print()` no `node.py` informando Query, Nó executor e Conteúdo.
*   **Como Demonstrar:**
    1.  Aponte para o terminal rodando o `node.py`.
    2.  Cada linha impressa é evidência do requisito de log ("informar query requisitada e conteúdo transmitido").

---

## Resumo Rápido de Comandos

1.  **Iniciar Nós:**
    *   Terminal 1: `python node.py 0`
    *   Terminal 2: `python node.py 1`
    *   Terminal 3: `python node.py 2`

2.  **Iniciar Cliente:**
    *   Terminal 4: `python client.py`
