# Guia de Deployment Multi-Máquina

Este guia explica como configurar e executar o sistema distribuído em 3 máquinas Windows diferentes.

## Arquitetura

- **Máquina 1 (192.168.15.4)**: Nó 0 + MySQL DB1 (porta 3309)
- **Máquina 2 (192.168.15.6)**: Nó 1 + MySQL DB2 (porta 3307) 
- **Máquina 3 (192.168.15.20)**: Nó 2 + MySQL DB3 (porta 3308)

## Pré-requisitos em Cada Máquina

1. **Windows 10/11** com WSL2 (se for usar WSL) ou PowerShell
2. **Docker Desktop** instalado e rodando
3. **Python 3.8+** instalado
4. **Git** (para clonar o projeto)

## Instalação - Passo a Passo

### Em CADA uma das 3 máquinas:

#### 1. Clonar ou Copiar o Projeto

```powershell
git clone <repositorio>
cd lab-sist-dist
```

Ou copie a pasta completa via rede/USB.

#### 2. Configurar o IP da Máquina

Copie o arquivo `.env` correspondente:

**Máquina 192.168.15.4:**
```powershell
Copy-Item .env.maquina1 .env
```

**Máquina 192.168.15.6:**
```powershell
# O arquivo .env já está configurado com MY_IP=192.168.15.6
```

**Máquina 192.168.15.20:**
```powershell
Copy-Item .env.maquina3 .env
```

#### 3. Verificar o arquivo ips.txt

O arquivo `ips.txt` deve conter os 3 IPs (já está configurado):
```
192.168.15.4
192.168.15.6
192.168.15.20
```

#### 4. Configurar Port Forwarding (se usar WSL)

**Apenas necessário se usar WSL2**. Execute como Administrador:

```powershell
.\configurar_ambiente_completo.ps1
```

Depois **REINICIE o Windows**.

#### 5. Configurar Firewall

Abra as portas necessárias no firewall:

```powershell
# Execute como Administrador
New-NetFirewallRule -DisplayName "MySQL Nó" -Direction Inbound -LocalPort 3307,3308,3309 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "Nós Middleware" -Direction Inbound -LocalPort 5000,5001,5002 -Protocol TCP -Action Allow
```

#### 6. Iniciar o Ambiente

**No Windows (PowerShell):**
```powershell
.\iniciar_ambiente.ps1
```

**No WSL:**
```bash
sudo ./iniciar_ambiente.sh
```

O script detectará automaticamente o IP da máquina e iniciará **apenas o nó correspondente**.

## Verificação

### Verificar Nó Rodando

```powershell
# Ver processos Python
Get-Process python | Where-Object {$_.CommandLine -like '*node.py*'}
```

### Testar Conectividade

**Da própria máquina:**
```powershell
# Testar MySQL local
Test-NetConnection -ComputerName localhost -Port 3307

# Testar nó local
Test-NetConnection -ComputerName localhost -Port 5001
```

**De outra máquina:**
```powershell
# Testar conectividade com a máquina 192.168.15.6
Test-NetConnection -ComputerName 192.168.15.6 -Port 5001
Test-NetConnection -ComputerName 192.168.15.6 -Port 3307
```

## Testar o Sistema

Após todas as 3 máquinas estarem rodando, teste com o cliente:

```powershell
python client.py
```

O cliente mostrará os 3 nós disponíveis e você poderá enviar queries para qualquer um deles.

## Troubleshooting

### "IP local não encontrado em ips.txt"

- Verifique o arquivo `.env` está configurado corretamente
- Confirme que o IP em `.env` corresponde a um dos IPs em `ips.txt`

### "Falha na conexão com o nó"

- Verifique se o firewall está configurado em ambas as máquinas
- Teste conectividade com `Test-NetConnection`
- Verifique se o nó está rodando: `Get-Process python`

### Port forwarding não funciona (WSL)

- **REINICIE o Windows** após executar `configurar_ambiente_completo.ps1`
- Verifique se está configurado: `netsh interface portproxy show all`

### Nós não conseguem se comunicar

- Verifique se os IPs em `ips.txt` estão corretos
- Teste ping entre as máquinas: `ping 192.168.15.6`
- Verifique logs em `logs/node*.log`

## Parar o Ambiente

```powershell
.\parar_ambiente.ps1
```

Ou no WSL:
```bash
sudo ./parar_ambiente.sh
```

## Logs

Os logs de cada nó ficam em:
- `logs/node0.log`
- `logs/node1.log`
- `logs/node2.log`

Para ver logs em tempo real:
```powershell
Get-Content logs\node1.log -Tail 20 -Wait
```

## Comandos Úteis

```powershell
# Ver portas escutando
netstat -ano | findstr ":5001"

# Ver contêineres Docker
docker ps

# Reiniciar Docker
Restart-Service docker

# Ver IPs da máquina
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like '192.168.*'}
```
