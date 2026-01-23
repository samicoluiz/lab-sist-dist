# Guia de Configuração Multi-Máquina

Este guia explica como configurar e executar o sistema de banco de dados distribuído em **3 máquinas diferentes** usando WSL ou Linux.

## 📋 Pré-requisitos

Em **cada máquina**:

- WSL (Ubuntu) ou Linux
- Docker e Docker Compose instalados
- Python 3.8+
- Conexão de rede entre as máquinas (mesma rede local)
- Portas liberadas no firewall:
  - **5000**: comunicação entre nós
  - **3306**: MySQL (se quiser acessar remotamente)

## 🔧 Configuração Passo a Passo

### 1️⃣ Preparar Todas as Máquinas

Em **todas as 3 máquinas**, clone ou copie o projeto:

```bash
cd ~
git clone <seu-repositorio>
cd lab-sist-dist
```

### 2️⃣ Configurar IPs

Em **todas as 3 máquinas**, edite o arquivo `ips.txt` com os IPs reais:

```bash
nano ips.txt
```

Conteúdo (exemplo com seus IPs):

```
192.168.15.4
192.168.15.6
192.168.15.20
```

**IMPORTANTE**: A ordem dos IPs define o ID de cada nó:

- Linha 1 → Nó 0 (192.168.15.4)
- Linha 2 → Nó 1 (192.168.15.6)
- Linha 3 → Nó 2 (192.168.15.20)

### 3️⃣ Gerar Configuração

Em **todas as 3 máquinas**, gere o arquivo `config.json`:

```bash
python3 configurar.py 192.168.15.4 192.168.15.6 192.168.15.20
```

Isso criará um `config.json` idêntico em todas as máquinas:

```json
{
  "nodes": [
    { "id": 0, "ip": "192.168.15.4", "port": 5000, "db_port": 3306 },
    { "id": 1, "ip": "192.168.15.6", "port": 5000, "db_port": 3306 },
    { "id": 2, "ip": "192.168.15.20", "port": 5000, "db_port": 3306 }
  ]
}
```

### 4️⃣ Iniciar o Ambiente

Em **cada máquina**, execute o script com a flag `--multi-machine`:

```bash
chmod +x iniciar_ambiente.sh
./iniciar_ambiente.sh --multi-machine
```

O script irá:

1. Detectar automaticamente o IP local da máquina
2. Determinar qual nó deve rodar (baseado no `ips.txt`)
3. Iniciar apenas 1 container Docker (MySQL)
4. Inicializar o banco de dados
5. Iniciar apenas o nó correspondente

**Exemplo de saída na Máquina 1 (192.168.15.4):**

```
2026-01-22 10:30:15 - Modo multi-máquina ativado. Detectando nó local...
2026-01-22 10:30:15 - IP local detectado: 192.168.15.4
2026-01-22 10:30:15 - Esta máquina rodará o Nó 0
...
2026-01-22 10:30:45 - Nó 0 iniciado com PID 12345. Logs em logs/node0.log
```

### 5️⃣ Verificar se Está Funcionando

Em qualquer máquina, verifique os logs:

```bash
tail -f logs/node*.log
```

Você deve ver mensagens como:

```
[Nó 0] Iniciado com estratégia de Conexão Sob Demanda na porta DB 3306
[Nó 0] Servidor escutando em 0.0.0.0:5000
[Nó 0] Heartbeat enviado para nó 1
[Nó 0] Heartbeat enviado para nó 2
```

### 6️⃣ Testar Conectividade

Em uma máquina, teste se consegue alcançar os outros nós:

```bash
# Da máquina 1, teste alcançar a máquina 2
nc -zv 192.168.15.6 5000

# Teste alcançar a máquina 3
nc -zv 192.168.15.20 5000
```

## 🖥️ Interagir com o Sistema

Use o cliente de **qualquer máquina**:

```bash
python3 tui_client.py
```

## 🛑 Parar o Ambiente

Em **cada máquina**:

```bash
./parar_ambiente.sh
```

## 🔥 Problemas Comuns e Soluções

### ❌ Erro: "IP local não encontrado em ips.txt"

**Causa**: O IP da máquina não corresponde ao listado em `ips.txt`

**Solução**:

```bash
# Verifique o IP da sua máquina
ip addr show | grep "inet "

# Atualize ips.txt com o IP correto
nano ips.txt
```

### ❌ Nós não se comunicam

**Causa**: Firewall bloqueando porta 5000

**Solução no WSL/Ubuntu**:

```bash
# No Windows, libere a porta no Windows Defender Firewall
# Ou desabilite temporariamente para testar

# No Linux
sudo ufw allow 5000/tcp
```

### ❌ Docker não expõe porta 3306 externamente

**Causa**: Docker dentro do WSL não está fazendo bind em 0.0.0.0

**Solução**: O `docker-compose.yml` já está configurado corretamente:

```yaml
ports:
  - "0.0.0.0:3306:3306"
```

Se ainda não funcionar, reinicie o Docker:

```bash
sudo systemctl restart docker
```

### ❌ Erro: "Connection refused" ao conectar entre nós

**Verificações**:

1. **Nó está rodando?**

   ```bash
   ps aux | grep "node.py"
   ```

2. **Porta está aberta?**

   ```bash
   netstat -tulpn | grep 5000
   ```

3. **Teste manual de conexão**:
   ```bash
   telnet 192.168.15.6 5000
   ```

## 🎯 Modo Local (Teste em 1 Máquina)

Para testar tudo em 1 máquina apenas (sem `--multi-machine`):

```bash
# ips.txt deve ter:
127.0.0.1
127.0.0.1
127.0.0.1

# Gerar config
python3 configurar.py 127.0.0.1 127.0.0.1 127.0.0.1

# Iniciar SEM a flag --multi-machine
./iniciar_ambiente.sh
```

Isso iniciará os 3 nós simultaneamente na mesma máquina.

## 📊 Arquitetura Multi-Máquina

```
┌─────────────────────┐      ┌─────────────────────┐      ┌─────────────────────┐
│   Máquina 1         │      │   Máquina 2         │      │   Máquina 3         │
│  192.168.15.4       │      │  192.168.15.6       │      │  192.168.15.20      │
├─────────────────────┤      ├─────────────────────┤      ├─────────────────────┤
│  Nó 0 (porta 5000)  │◄────►│  Nó 1 (porta 5000)  │◄────►│  Nó 2 (porta 5000)  │
│        ▲            │      │        ▲            │      │        ▲            │
│        │            │      │        │            │      │        │            │
│        ▼            │      │        ▼            │      │        ▼            │
│  MySQL (porta 3306) │      │  MySQL (porta 3306) │      │  MySQL (porta 3306) │
└─────────────────────┘      └─────────────────────┘      └─────────────────────┘
```

## ✅ Checklist de Implantação

- [ ] Docker e Docker Compose instalados em todas as máquinas
- [ ] Python 3.8+ instalado
- [ ] Projeto copiado para todas as máquinas
- [ ] `ips.txt` configurado com IPs reais (mesma ordem em todas)
- [ ] `config.json` gerado com IPs corretos
- [ ] Firewall liberado (porta 5000)
- [ ] `iniciar_ambiente.sh --multi-machine` executado em todas
- [ ] Logs verificados (`tail -f logs/node*.log`)
- [ ] Teste de conectividade entre nós realizado

## 🚀 Próximos Passos

Após tudo funcionando:

1. Execute `python3 tui_client.py` em qualquer máquina
2. Insira dados e veja a replicação acontecendo
3. Pare um nó (`./parar_ambiente.sh`) e observe a eleição de novo coordenador
4. Reinicie o nó e veja ele se reintegrar ao cluster
