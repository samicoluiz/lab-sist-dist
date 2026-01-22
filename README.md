# Distributed Database Middleware

Este projeto implementa um middleware para um banco de dados distribuído homogêneo autônomo baseado em MySQL.

## Requisitos

- Python 3.x
- MySQL Server (3 instâncias)
- Biblioteca `mysql-connector-python`

## Configuração

O arquivo `config.json` contém os IPs e portas dos nós do middleware e dos bancos de dados MySQL correspondentes.

```json
{
  "nodes": [
    {"id": 0, "ip": "127.0.0.1", "port": 5000, "db_port": 3306},
    {"id": 1, "ip": "127.0.0.1", "port": 5001, "db_port": 3307},
    {"id": 2, "ip": "127.0.0.1", "port": 5002, "db_port": 3308}
  ]
}
```

## Como Executar

1. **Subir os Bancos de Dados**:
   Certifique-se de ter 3 instâncias do MySQL rodando nas portas configuradas (3306, 3307, 3308).
   Se tiver Docker instalado, você pode usar:
   ```bash
   docker compose up -d
   ```

2. **Inicializar as Tabelas**:
   Execute o script de inicialização para criar a tabela de teste em todos os nós:
   ```bash
   python init_db.py
   ```

3. **Iniciar os Nós do Middleware**:
   Abra 3 terminais e execute um nó em cada:
   ```bash
   # Terminal 1
   python node.py 0
   
   # Terminal 2
   python node.py 1
   
   # Terminal 3
   python node.py 2
   ```

4. **Executar a Aplicação Cliente**:
   Use o cliente para enviar queries ao bd-dist:
   ```bash
   python client.py
   ```

## Funcionalidades Implementadas

- **Comunicação por Sockets**: Protocolo JSON customizado.
- **Replicação**: Operações de escrita (INSERT, UPDATE, DELETE, etc.) são replicadas para todos os nós ativos.
- **Eleição de Coordenador**: Algoritmo do Valentão (Bully Algorithm).
- **Heartbeat**: Detecção periódica de falhas.
- **Integridade**: Verificação por checksum (MD5) dos dados transmitidos.
- **Balanceamento de Carga**: Cliente pode escolher o nó ou usar o modo 'Auto' (Random).
- **Propriedades ACID**: Garantidas localmente pelo MySQL e distribuídas via replicação síncrona simples.
- **Logging**: Cada nó informa detalhadamente as queries recebidas e o conteúdo transmitido.
