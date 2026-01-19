#facomp/s8 #distributed-systems/laboratory 
#workload 

Equipe:
- Luiz Antonio Leite 
- Max Jose Lobato 
- Wesley Pontes (saiu) 

## comando 
Desenvolver um middleware para disponibilizar um banco de dados distribuídos baseado no SGBD MySQL. O middleware deverá ser desenvolvido baseado nas seguintes premissas:
- Pode ser desenvolvido em qualquer linguagem de programação;
- Deverá ser executado em pelo menos 03 máquinas diferentes;
- Usar o SGBD MySQL;
- A comunicação entre os nós do banco de dados distribuídos deverá ocorrer através de sockets;
- Desenvolver protocolo para troca de informações entre as diversas máquinas;
- Possibilidade de configurar os nós do DDB através de IPs de cada máquina;
- O DDB deverá seguir as premissas de uma DDM homogêneo autônomo;
- Todas as alterações efetuadas em um dos nós do DDB deverá ser replicada em todos os outros nós da rede;
- Preferencialmente poderá ter um coordenador. Porém, caso o coordenador falhe, deverá ter algum algoritmo para a eleição de um novo coordenador;
- O tipo de comunicação deverá ser determinado: broadcast, unicast, multicast;
- Garantir que as operações sigam as propriedades ACID;
- Todos os nós do DDB deverão informar periodicamente que estão ativos no DDB;
- Usar um mecanismo do tipo checksum para verificar a integridade dos dados recebidos;
- Garantir que não haja sobrecarga de nós no DDB, ou seja, que as requisições possam ser distribuídas entre os nós da rede;
- Cada nó deverá infomar as queries que foram requisitadas para ele e informar o conteúdo que será transmitido;
- Para acessar o DDB deverá ser criada uma aplicação com interface simples para executar queries. Cada retorno de queries deverá informar o resultado e o nó do DDB em que foi executada. 

## resposta 

O middleware foi desenvolvido em **Python**, utilizando **Sockets** para comunicação e **MySQL** como SGBD, orquestrado via Docker. Abaixo, detalho como cada requisito foi atendido:

1.  **Linguagem e SGBD**: Implementado em Python (`node.py`), utilizando `mysql-connector` para gerenciar 3 instâncias de MySQL 8.0 rodando em containers Docker distintos.
2.  **Arquitetura Distribuída**: O sistema roda em 3 nós (simulados em portas diferentes: 5000, 5001, 5002), configuráveis via arquivo `config.json` (IP/Porta), caracterizando um DDB Homogêneo Autônomo.
3.  **Comunicação e Protocolo**: A troca de mensagens ocorre via Sockets TCP com payloads em JSON. Tipos de mensagens incluem `CLIENT_QUERY`, `REPLICATE`, `HEARTBEAT` e `ELECTION`.
4.  **Replicação e Integridade**:
    *   Toda operação de escrita (INSERT/UPDATE/DELETE) recebida por um nó é executada localmente e imediatamente difundida (**Broadcast**) para os demais nós.
    *   A integridade é verificada via **Checksum (MD5)** do comando SQL. Se o hash calculado pelo receptor diferir do enviado, a operação é rejeitada.
5.  **Tolerância a Falhas e Coordenação**:
    *   **Heartbeat**: Threads dedicadas enviam sinais de vida a cada 2s. Se um nó silencia, é marcado como inativo.
    *   **Eleição (Bully Algorithm)**: Se o coordenador falha, o algoritmo do Valentão é acionado. O nó ativo com maior ID assume a coordenação.
6.  **Concorrência e ACID**: O MySQL local garante ACID por transação. O middleware coordena a atomicidade distribuída replicando a escrita para todos os nós vivos.
7.  **Balanceamento e Interface**:
    *   O cliente (`client.py`) possui um modo "Auto" que seleciona aleatoriamente (`random`) um nó para enviar a query, distribuindo a carga.
        *   Logs detalhados no console informam query recebida, nó executor e dados de replicação.

### Guia de Deploy em Máquinas Reais

Para executar este middleware em 3 máquinas físicas diferentes (ex: Máquina A, B e C), siga este roteiro:

1.  **Configuração de Rede**:
    *   Assegure que as máquinas estejam na mesma rede (LAN ou VPN).
    *   Anote o IP de cada uma (ex: Máquina A: `192.168.1.10`, Máquina B: `192.168.1.11`, Máquina C: `192.168.1.12`).

2.  **Configuração do MySQL (Em cada máquina)**:
    *   Edite o `my.cnf` (Linux) ou `my.ini` (Windows) para permitir conexões externas:
        ```ini
        bind-address = 0.0.0.0
        ```
    *   Crie o usuário com permissão de acesso remoto:
        ```sql
        CREATE USER 'root'@'%' IDENTIFIED BY 'root';
        GRANT ALL PRIVILEGES ON *.* TO 'root'@'%';
        FLUSH PRIVILEGES;
        ```

3.  **Atualização do `config.json`**:
    *   O mesmo arquivo deve estar presente em todas as máquinas.
    *   Atualize os IPs para os reais e padronize as portas (ex: use porta 5000 para o middleware e 3306 para o banco em todas).
    ```json
    {
        "nodes": [
        {"id": 0, "ip": "192.168.1.10", "port": 5000, "db_port": 3306},
        {"id": 1, "ip": "192.168.1.11", "port": 5000, "db_port": 3306},
        {"id": 2, "ip": "192.168.1.12", "port": 5000, "db_port": 3306}
        ]
    }
    ```

4.  **Firewall**:
    *   Libere as portas TCP 5000 (comunicação do middleware) e 3306 (MySQL) no firewall de cada máquina.

5.  **Execução**:
    *   **Máquina A**: Execute `python node.py 0`
    *   **Máquina B**: Execute `python node.py 1`
    *   **Máquina C**: Execute `python node.py 2`

Desta forma, o sistema deixará de usar o loopback (`127.0.0.1`) e passará a operar em uma rede real distribuída.




[[2025-12-06]]
`creation_date:202512062001`
