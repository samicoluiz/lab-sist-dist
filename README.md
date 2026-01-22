# Middleware de Banco de Dados Distribuído

Este projeto implementa um middleware em Python para simular um banco de dados distribuído, utilizando múltiplas instâncias do MySQL como nós de armazenamento.

O sistema foi projetado para ser iniciado e configurado de forma automatizada, minimizando o atrito na implantação em diferentes ambientes (Windows, Linux, WSL).

## Funcionalidades Principais

- **Replicação de Escrita**: Operações de escrita (INSERT, UPDATE, DELETE) são replicadas para todos os nós ativos da rede (broadcast).
- **Eleição de Coordenador**: O sistema elege um nó coordenador utilizando o Algoritmo do Valentão (Bully Algorithm) e realiza uma nova eleição se o coordenador falhar.
- **Detecção de Falhas**: Cada nó envia sinais de vida (heartbeats) periodicamente, permitindo que o sistema detecte e reaja a falhas.
- **Integridade de Dados**: A integridade das mensagens replicadas é verificada através de um checksum (MD5).
- **Automação de Ambiente**: Scripts de inicialização e parada para configurar e gerenciar todo o ambiente com um único comando.

## Como Executar o Ambiente

Siga os passos abaixo para configurar e iniciar o projeto.

### Pré-requisitos

- Python 3.8+
- Docker e Docker Compose

### Passo 1: Configurar os Endereços IP

Crie ou edite o arquivo `ips.txt`. Adicione o endereço IP de cada máquina que participará do cluster, um por linha.

**Para testar em uma única máquina (localhost):**
O arquivo `ips.txt` deve conter três linhas, todas com `127.0.0.1`.
```
127.0.0.1
127.0.0.1
127.0.0.1
```

**Para testar em múltiplas máquinas na mesma rede:**
O arquivo deve conter o IP de cada uma das máquinas.
```
192.168.1.10
192.168.1.11
192.168.1.12
```

### Passo 2: Executar o Script de Inicialização

Os scripts de inicialização automatizam tudo: instalam dependências Python, geram o `config.json`, iniciam os contêineres Docker com os bancos de dados e lançam os nós do middleware em segundo plano.

**No Linux ou WSL (Ubuntu, Arch, etc.):**
```bash
# Opcional: Dê permissão de execução ao script (só precisa fazer uma vez)
chmod +x iniciar_ambiente.sh

# Execute o script
./iniciar_ambiente.sh
```

**No Windows (usando PowerShell):**
1.  Abra o **Windows PowerShell**.
2.  Navegue até a pasta do projeto com o comando `cd`.
3.  **Execute o seguinte comando para permitir scripts nesta sessão:**
    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
    ```
4.  Execute o script de inicialização:
    ```powershell
    .\iniciar_ambiente.ps1
    ```

Ao final, os nós estarão rodando em segundo plano. Os logs de cada nó serão salvos em arquivos individuais dentro da pasta `logs/`.

### Passo 3: Interagir com o Banco de Dados

Com o ambiente rodando, você pode usar a interface de terminal (TUI) para enviar comandos SQL. Recomendamos o uso do novo cliente TUI para uma melhor experiência:

```bash
python tui_client.py
```

O `tui_client.py` oferece dois modos:
- **Perfil de Uso**: Seleciona automaticamente o coordenador e permite focar apenas nas queries SQL.
- **Perfil de Teste**: Permite escolher manualmente qual nó receberá a query, ideal para testar falhas e consistência.

Caso prefira o cliente simplificado original:
```bash
python client.py
```

### Passo 4: Parar o Ambiente

Para parar todos os processos (nós e contêineres) e limpar o ambiente, use o script de parada correspondente ao seu sistema operacional:

**No Linux ou WSL:**
```bash
./parar_ambiente.sh
```

**No Windows (PowerShell):**
```powershell
.\parar_ambiente.ps1
```

## Estrutura do Projeto

- `node.py`: Contém a lógica principal de cada nó do middleware, incluindo comunicação, replicação e eleição.
- `client.py`: Uma aplicação de console para enviar queries SQL ao sistema distribuído.
- `docker-compose.yml`: Define as três instâncias do MySQL que servem como nós de armazenamento.
- `configurar.py`: Script Python que gera o arquivo `config.json` com base nos IPs fornecidos.
- `ips.txt`: Arquivo de texto para listar os IPs dos nós a serem configurados.
- `iniciar_ambiente.sh` / `.ps1`: Scripts de orquestração para automatizar a inicialização do ambiente.
- `parar_ambiente.sh` / `.ps1`: Scripts de orquestração para automatizar a parada e limpeza do ambiente.
- `requirements.txt`: Lista as dependências Python do projeto.