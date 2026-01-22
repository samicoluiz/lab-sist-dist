# 🚀 Guia de Testes e Demonstração do Banco de Dados Distribuído

Este documento unifica os roteiros de teste para dois cenários de apresentação:

1.  **Máquina Única:** Usando Docker e scripts de automação para simular um ambiente distribuído localmente. Ideal para uma demonstração rápida e controlada.
2.  **Múltiplas Máquinas:** Configurando o ambiente manualmente em diferentes máquinas (físicas ou virtuais) para provar o funcionamento em uma rede real.

---

## Cenário 1: Demonstração em Máquina Única (com Docker)

Este cenário é o mais rápido para apresentar, pois utiliza os scripts de automação que preparam todo o ambiente.

### 1.1 Preparando o Ambiente

Tudo o que você precisa para iniciar o ambiente está contido em um único script.

**Ação:** Abra um terminal PowerShell e execute:
```powershell
.\iniciar_ambiente.ps1
```

**O que acontece neste momento:**
1.  As dependências Python são instaladas.
2.  Os três contêineres Docker (um para cada nó do banco de dados) são iniciados.
3.  O script aguarda os bancos de dados ficarem prontos.
4.  O arquivo `config.json` é gerado com os IPs dos contêineres.
5.  O esquema de tabelas é inicializado em cada banco de dados.
6.  Os três processos do middleware (`node.py`) são iniciados em segundo plano.

**Como observar os nós:**
Para ver o que cada nó está fazendo em tempo real, abra **três terminais** e execute em cada um:

```powershell
# Terminal 1
Get-Content .\logs\node0.log -Wait

# Terminal 2
Get-Content .\logs\node1.log -Wait

# Terminal 3
Get-Content .\logs\node2.log -Wait
```

### 1.2 Demonstração Passo a Passo

Com o ambiente rodando e os logs visíveis, siga os passos abaixo.

#### Passo 1: Verificando a Eleição do Coordenador
**Ação:** Observe os logs.
**Resultado:** O Nó 2 será eleito o coordenador (mensagem: `New Coordinator: 2` nos outros, e `I am the coordinator` nele).
> 🎤 **Ponto da Apresentação:** "O algoritmo do Valentão elege o nó de maior ID como coordenador inicial."

#### Passo 2: Realizando uma Operação de Escrita (INSERT)
**Ação:** Use `python client.py`, conecte-se a qualquer nó (ex: `0`) e execute:
```sql
INSERT INTO users (name, email) VALUES ('Ada Lovelace', 'ada@babbage.com');
```
**Resultado:** O log do Nó 0 mostrará `Transmitting content...`, e os outros `Executing replicated query...`.
> 🎤 **Ponto da Apresentação:** "Operações de escrita são replicadas para todos os nós para garantir a consistência."

#### Passo 3: Verificando a Replicação
**Ação:** Use o `client.py` para executar `SELECT * FROM users;` em cada um dos três nós.
**Resultado:** Todos os nós retornarão o registro de 'Ada Lovelace'.
> 🎤 **Ponto da Apresentação:** "A consulta retorna o mesmo resultado em todos os nós, provando que o cluster está consistente."

#### Passo 4: Demonstrando a Tolerância a Falhas
**Ação:** Derrube o coordenador (Nó 2).
1.  Encontre o PID do Nó 2 (é o terceiro no arquivo `node_pids.tmp`).
    ```powershell
    Get-Content .\node_pids.tmp 
    ```
2.  Encerre o processo.
    ```powershell
    Stop-Process -Id <PID_DO_NO_2>
    ```
**Resultado:** Os logs dos nós 0 e 1 detectarão a falha (`Node 2 is down`) e elegerão o Nó 1 como novo coordenador.
> 🎤 **Ponto da Apresentação:** "Simulamos a falha do coordenador. O sistema detectou e iniciou uma nova eleição, mantendo-se operacional."

#### Passo 5: Verificando a Funcionalidade Pós-Falha
**Ação:** Com o Nó 2 inativo, use o `client.py` para inserir um novo registro em um nó ativo (0 ou 1).
```sql
INSERT INTO users (name, email) VALUES ('Charles Babbage', 'charles@babbage.com');
```
**Resultado:** A escrita funcionará, e um `SELECT` nos nós 0 e 1 mostrará o novo registro.
> 🎤 **Ponto da Apresentação:** "Mesmo com um nó a menos, o cluster continua disponível e consistente, demonstrando alta disponibilidade."

### 1.3 Encerrando o Ambiente
**Ação:** Para limpar tudo, execute:
```powershell
.\parar_ambiente.ps1
```
---

## Cenário 2: Demonstração em Múltiplas Máquinas

Este cenário prova que o sistema funciona em um ambiente de rede real, sem Docker.

### 2.1 Pré-requisitos e Configuração Manual

**Em cada uma das 3 máquinas:**
- [ ] Clone o repositório do projeto.
- [ ] Instale Python 3.8+.
- [ ] Instale e configure um servidor MySQL 8.0.
- [ ] No MySQL, crie o usuário `root` com senha `root` e dê as permissões necessárias.
- [ ] Crie o banco de dados: `CREATE DATABASE IF NOT EXISTS bd-dist;`.
- [ ] Libere as portas `5000` (para o middleware) e `3306` (para o MySQL) no firewall.
- [ ] Instale as dependências: `pip install -r requirements.txt`.

**Configuração Central:**
1.  Escolha uma máquina para ser a "principal" (onde você rodará o cliente).
2.  Crie o arquivo `ips.txt`, listando os IPs de rede de cada uma das 3 máquinas.
3.  Crie o arquivo `config.json` manualmente, com a seguinte estrutura:
    ```json
    {
      "nodes": [
        {"id": 0, "ip": "192.168.1.10", "port": 5000, "db_port": 3306},
        {"id": 1, "ip": "192.168.1.11", "port": 5000, "db_port": 3306},
        {"id": 2, "ip": "192.168.1.12", "port": 5000, "db_port": 3306}
      ]
    }
    ```
    *Substitua pelos IPs reais de suas máquinas.*

4.  Execute o script de inicialização do banco de dados em **uma** das máquinas (ele se conectará remotamente às outras).
    ```bash
    python init_db.py
    ```

### 2.2 Roteiro de Testes Manuais

**Ação:** Em cada máquina, abra um terminal e inicie o nó correspondente ao seu ID.

```bash
# Na máquina com final de IP .10
python node.py 0

# Na máquina com final de IP .11
python node.py 1

# Na máquina com final de IP .12
python node.py 2
```

Agora, você pode seguir exatamente os mesmos passos da **Seção 1.2 (Demonstração Passo a Passo)**. A lógica é idêntica:
- Observe a eleição do Nó 2.
- Use `python client.py` de qualquer uma das máquinas para inserir dados.
- Observe a replicação nos terminais de cada máquina.
- Para simular a falha, simplesmente use `Ctrl+C` no terminal da máquina do Nó 2.
- Observe a nova eleição e a continuidade do sistema.

---

## 📸 Checklist de Screenshots para Apresentação

| # | Captura | Demonstra |
|---|---------|-----------|
| 1 | 3 terminais (locais ou remotos) com nós rodando | Arquitetura distribuída |
| 2 | Log "New Coordinator: 2" | Bully Algorithm |
| 3 | Log "Node X is down" | Detecção de falha |
| 4 | Log "Transmitting content" + "Checksum" | Replicação + Integridade |
| 5 | Saída do `client.py` com resultado JSON | Interface do cliente |
| 6 | `SELECT` em 3 nós/máquinas com dados idênticos | Consistência de dados |
| 7 | `config.json` com IPs reais (para Cenário 2) | Configurabilidade |

---

## ⚠️ Problemas Conhecidos e Limitações

### 1. Sincronização de Nó Reiniciado
Quando um nó é desligado e religado, ele não recebe os dados que foram inseridos durante sua ausência.
**Solução sugerida**: Implementar um mecanismo de *state transfer* onde um nó que retorna pede ao coordenador um snapshot dos dados atuais.

### 2. Conflitos de Escrita Simultânea
Se dois clientes inserem dados no mesmo momento em nós diferentes, pode haver um conflito de chave primária (auto-increment).
**Solução sugerida**: Usar UUIDs para chaves primárias ou ter o coordenador como ponto central para serializar todas as operações de escrita.

---

## 🏁 Conclusão

O middleware desenvolvido demonstra com sucesso os principais conceitos de sistemas distribuídos:
- ✅ Replicação automática de escritas.
- ✅ Eleição de líder e tolerância a falhas (Bully Algorithm).
- ✅ Detecção de falhas via Heartbeat.
- ✅ Verificação de integridade de dados (MD5).
- ✅ Comunicação via sockets em um ambiente de rede.
- ✅ Configuração flexível para se adaptar a diferentes topologias de rede.
