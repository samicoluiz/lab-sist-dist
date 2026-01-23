# Configuração para Acesso Externo (Outras Máquinas)

Este guia explica como permitir que outras máquinas na rede acessem os nós e bancos de dados rodando no WSL.

## Problema

O WSL2 roda em uma rede NAT isolada. Para que outras máquinas possam acessar serviços rodando no WSL, é necessário configurar **port forwarding** do Windows para o WSL.

## Configuração Necessária

### 1. Executar Script de Configuração (Como Administrador)

```powershell
.\configurar_ambiente_completo.ps1
```

Este script configura:

- Port forwarding das portas 3307-3309 (MySQL) e 5000-5002 (Nós)
- Regras de firewall para permitir tráfego externo

### 2. **IMPORTANTE: Reiniciar o Windows**

O port forwarding do Windows só funciona após um reinício completo do sistema.

```powershell
Restart-Computer
```

### 3. Após Reiniciar, Iniciar o Ambiente

```bash
wsl bash -c "cd /mnt/c/Users/s988666302/Documents/Projetos/lab-sist-dist && ./iniciar_ambiente.sh"
```

## Teste de Conectividade

### Da Própria Máquina (192.168.15.6)

```powershell
# Testar MySQL
Test-NetConnection -ComputerName 192.168.15.6 -Port 3307
Test-NetConnection -ComputerName 192.168.15.6 -Port 3308
Test-NetConnection -ComputerName 192.168.15.6 -Port 3309

# Testar Nós
Test-NetConnection -ComputerName 192.168.15.6 -Port 5000
Test-NetConnection -ComputerName 192.168.15.6 -Port 5001
Test-NetConnection -ComputerName 192.168.15.6 -Port 5002
```

### De Outra Máquina

```powershell
.\testar_conectividade_remota.ps1 -TargetIP 192.168.15.6
```

## Arquitetura

```
Máquina Externa (192.168.15.4)
        ↓
Windows (192.168.15.6:5001)
        ↓ [Port Forwarding]
WSL (10.255.255.254:5001)
        ↓
Nó Python escutando em 0.0.0.0:5001
```

## Configurações de Rede

### config.local.json (Usado Localmente no WSL)

Os nós se comunicam entre si via `127.0.0.1`, pois todos rodam no mesmo WSL.

### config.json (Usado por Clientes Externos)

Clientes de outras máquinas usam os IPs externos (192.168.15.x) para se conectar.

## Limitações do Windows/WSL

- **Hairpin NAT não funciona**: A própria máquina Windows não consegue se conectar aos serviços via IP externo (192.168.15.6)
- **Port Forwarding requer reinício**: Após configurar, é necessário reiniciar o Windows
- **Mirrored Mode incompatível**: O modo de rede "Mirrored" do WSL não funciona com Docker

## Troubleshooting

### Port forwarding não funciona

```powershell
# Verificar se está configurado
netsh interface portproxy show all

# Se não aparecer, executar configurar_ambiente_completo.ps1 novamente e REINICIAR
```

### Firewall bloqueando

```powershell
# Verificar regras
Get-NetFirewallRule -DisplayName "*5000*","*5001*","*5002*"

# Adicionar manualmente se necessário
New-NetFirewallRule -DisplayName "Teste Porta 5001" -Direction Inbound -LocalPort 5001 -Protocol TCP -Action Allow
```

### Nós não estão escutando

```bash
# Verificar se estão rodando
wsl bash -c "ps aux | grep node.py"

# Verificar portas
wsl bash -c "ss -tln | grep ':500'"

# Ver logs
wsl bash -c "tail -f /mnt/c/Users/s988666302/Documents/Projetos/lab-sist-dist/logs/node1.log"
```

## Deployment Multi-Máquina

Para rodar nós em máquinas diferentes:

1. **Máquina 192.168.15.6**: Roda Nó 1 (porta 5001, DB 3307)
2. **Máquina 192.168.15.4**: Roda Nó 0 (porta 5000, DB 3309)
3. **Máquina 192.168.15.20**: Roda Nó 2 (porta 5002, DB 3308)

Cada máquina deve:

- Seguir o [GUIA_INSTALACAO_MULTI_MAQUINA.md](GUIA_INSTALACAO_MULTI_MAQUINA.md)
- Usar `config.json` com os IPs reais
- Executar `iniciar_ambiente.sh` que iniciará apenas o nó correspondente ao seu IP
