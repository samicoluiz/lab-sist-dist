# 🧪 Roteiro de Testes - Middleware de Banco de Dados Distribuído

Este documento descreve os testes para demonstrar o funcionamento do middleware em máquinas reais.

---

## 📋 Pré-requisitos

### Em cada máquina:
- [ ] Python 3.8+ instalado
- [ ] MySQL 8.0 rodando
- [ ] Usuário MySQL: `root` / Senha: `root`
- [ ] Database `bd-dist` criado
- [ ] Tabela `users` inicializada (`python init_db.py`)
- [ ] Arquivo `config.json` com IPs reais
- [ ] Porta 5000 e 3306 liberadas no firewall

### Comandos de preparação:
```bash
# Em cada máquina
pip install mysql-connector-python

# Criar database (no MySQL)
CREATE DATABASE IF NOT EXISTS bd-dist;

# Inicializar tabela
python init_db.py
```

---

## 🎯 TESTE 1: Eleição de Coordenador (Bully Algorithm)

### Objetivo
Demonstrar que o algoritmo do Valentão elege corretamente o nó com maior ID.

### Passos

| Ordem | Máquina | Comando | Resultado Esperado |
|-------|---------|---------|-------------------|
| 1 | A | `python node.py 0` | "I am the coordinator" |
| 2 | B | `python node.py 1` | "New Coordinator: 1" em A e B |
| 3 | C | `python node.py 2` | "New Coordinator: 2" em A, B e C |

### Screenshot sugerido
Captura dos 3 terminais mostrando a eleição convergindo para Nó 2.

---

## 🎯 TESTE 2: Heartbeat e Detecção de Falha

### Objetivo
Mostrar que nós inativos são detectados e nova eleição é disparada.

### Passos

| Ordem | Ação | Resultado |
|-------|------|-----------|
| 1 | Com 3 nós rodando, encerre o Nó 2 (Ctrl+C) | - |
| 2 | Aguarde 10-15 segundos | Logs: "Node 2 is down" em A e B |
| 3 | Observe a eleição | "New Coordinator: 1" |

### Screenshot sugerido
Terminal do Nó 0 ou 1 mostrando detecção de falha + nova eleição.

---

## 🎯 TESTE 3: Replicação de Escrita

### Objetivo
Provar que operações de escrita são replicadas para todos os nós.

### Passos

1. Execute o cliente em qualquer máquina:
   ```bash
   python client.py
   ```

2. Selecione o Nó 0 e execute:
   ```sql
   INSERT INTO users (name, email) VALUES ('Maria Silva', 'maria@empresa.com');
   ```

3. Observe os terminais:
   - **Nó 0**: "WRITE operation. Transmitting content..."
   - **Nó 1 e 2**: "Executing replicated query from Node 0"

4. Verifique em cada nó:
   ```sql
   SELECT * FROM users;
   ```

### Resultado esperado
Todos os 3 nós retornam o registro da Maria Silva.

---

## 🎯 TESTE 4: Verificação de Checksum (Integridade)

### Objetivo
Demonstrar que o hash MD5 é calculado e verificado.

### O que observar
Ao enviar um INSERT, o log mostra:
```
[Node 0] Checksum: a1b2c3d4e5f6...
[Node 1] Executing replicated query from Node 0
```

O checksum garante que dados corrompidos seriam rejeitados.

---

## 🎯 TESTE 5: Balanceamento de Carga

### Objetivo
Demonstrar distribuição de requisições entre nós.

### Passos

1. Execute o cliente:
   ```bash
   python client.py
   ```

2. Escolha opção `a` (Auto) 10 vezes executando:
   ```sql
   SELECT * FROM users;
   ```

3. Observe a distribuição nos terminais dos nós.

### Resultado esperado
Requisições distribuídas aproximadamente igual (~3-4 por nó).

---

## 🎯 TESTE 6: Consistência de Dados

### Objetivo
Verificar que todos os nós têm dados idênticos.

### Passos

1. Insira 5 registros via Nó 0:
   ```sql
   INSERT INTO users (name, email) VALUES ('User1', 'u1@test.com');
   INSERT INTO users (name, email) VALUES ('User2', 'u2@test.com');
   INSERT INTO users (name, email) VALUES ('User3', 'u3@test.com');
   INSERT INTO users (name, email) VALUES ('User4', 'u4@test.com');
   INSERT INTO users (name, email) VALUES ('User5', 'u5@test.com');
   ```

2. Execute SELECT em cada nó individualmente:
   ```sql
   SELECT * FROM users;
   ```

### Resultado esperado
Todos os nós retornam exatamente os mesmos 5 registros.

---

## 🎯 TESTE 7: Recuperação de Falha do Coordenador

### Objetivo
Mostrar tolerância a falhas do sistema.

### Passos

| Ordem | Ação | Resultado |
|-------|------|-----------|
| 1 | Desligar Nó 2 (coordenador) | - |
| 2 | Aguardar detecção | "Node 2 is down" |
| 3 | Observar eleição | Nó 1 vira coordenador |
| 4 | Enviar INSERT para Nó 0 | Operação funciona normalmente |
| 5 | SELECT em Nó 0 e 1 | Dados consistentes |

---

## 🎯 TESTE 8: Comunicação Entre Máquinas Diferentes

### Objetivo
Provar que funciona com IPs reais (não localhost).

### Configuração (config.json)
```json
{
  "nodes": [
    {"id": 0, "ip": "192.168.1.10", "port": 5000, "db_port": 3306},
    {"id": 1, "ip": "192.168.1.11", "port": 5000, "db_port": 3306},
    {"id": 2, "ip": "192.168.1.12", "port": 5000, "db_port": 3306}
  ]
}
```

### Passos
1. Execute `python node.py X` em cada máquina (X = 0, 1, 2)
2. Execute `python client.py` de qualquer máquina
3. Envie queries para nós em IPs diferentes

### Resultado esperado
Comunicação cross-network funcionando.

---

## 🤖 Script de Demonstração Automatizado

Execute o script que criei para testes automáticos:

```bash
python demo_tests.py
```

Este script executa:
- ✅ Verificação de conectividade
- ✅ Teste de replicação INSERT
- ✅ Teste de balanceamento de carga
- ✅ Teste de consistência
- ✅ Teste de UPDATE/DELETE replicados

---

## 📸 Checklist de Screenshots para Apresentação

| # | Captura | Demonstra |
|---|---------|-----------|
| 1 | 3 terminais com nós rodando | Arquitetura distribuída |
| 2 | Log "New Coordinator: 2" | Bully Algorithm |
| 3 | Log "Node X is down" | Detecção de falha |
| 4 | Log "Transmitting content" + "Checksum" | Replicação + Integridade |
| 5 | Client.py com resultado JSON | Interface do cliente |
| 6 | SELECT em 3 nós com dados iguais | Consistência |
| 7 | config.json com IPs reais | Configurabilidade |
| 8 | Saída do demo_tests.py | Testes automatizados |

---

## ⚠️ Problemas Conhecidos

### 1. Sincronização de Nó Reiniciado
Quando um nó é desligado e religado, ele não recebe os dados que foram inseridos durante sua ausência.

**Solução sugerida**: Implementar sincronização inicial (snapshot) ao reconectar.

### 2. Conflitos de Escrita Simultânea
Se dois clientes inserem no mesmo momento em nós diferentes, pode haver conflito de ID auto-increment.

**Solução sugerida**: Usar UUID ou coordenador para serializar escritas.

---

## 🏁 Conclusão

O middleware demonstra:
- ✅ Replicação automática de escritas
- ✅ Eleição de líder (Bully Algorithm)
- ✅ Heartbeat e detecção de falhas
- ✅ Verificação de integridade (MD5)
- ✅ Balanceamento de carga
- ✅ Comunicação via sockets
- ✅ Configuração flexível via JSON
