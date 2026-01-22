import socket
import json
import sys
import random
import os
import time

# Tenta importar bibliotecas específicas para cada SO
try:
    import msvcrt
    SISTEMA = "windows"
except ImportError:
    import termios
    import tty
    SISTEMA = "unix"

# Cores ANSI
class Cores:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def exibir_banner():
    banner = f'''\
{Cores.OKCYAN}{Cores.BOLD}
  _____  _____ ____  _   _ _   _ ______ 
 |  __ \|_   _/ __ \| \ | | \ | |  ____|
 | |  | | | || |  | |  \| |  \| | |__   
 | |  | | | || |  | | . ` | . ` |  __|  
 | |__| |_| || |__| | |\  | |\  | |____ 
 |_____/|_____\____/|_| \_|_| \_|______|                                        
 {Cores.ITALIC}Distributed Intelligent Object Network Node Exchange{Cores.ENDC}
'''
    print(banner)

def get_key():
    """Captura uma tecla de forma multiplataforma."""
    if SISTEMA == "windows":
        ch = msvcrt.getch()
        if ch in [b'\x00', b'\xe0']:
            ch = msvcrt.getch()
            if ch == b'H': return "UP"
            if ch == b'P': return "DOWN"
        if ch == b'\r': return "ENTER"
        if ch == b'q': return "q"
        return str(ch)
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
            if ch == '\x1b': # Sequência de escape (setas)
                ch = sys.stdin.read(2)
                if ch == '[A': return "UP"
                if ch == '[B': return "DOWN"
            if ch == '\r' or ch == '\n': return "ENTER"
            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def menu_interativo(opcoes, titulo):
    selecionado = 0
    while True:
        limpar_tela()
        exibir_banner()
        print(f"{Cores.BOLD}{titulo}{Cores.ENDC}\n")
        
        for i, opcao in enumerate(opcoes):
            prefixo = f"{Cores.OKGREEN}> " if i == selecionado else "  "
            cor = Cores.OKGREEN if i == selecionado else ""
            print(f"{prefixo}{cor}{opcao}{Cores.ENDC}")
        
        print(f"\n{Cores.WARNING}(Use as setas ↑ ↓ e pressione Enter){Cores.ENDC}")
        
        key = get_key()
        if key == "UP":
            selecionado = (selecionado - 1) % len(opcoes)
        elif key == "DOWN":
            selecionado = (selecionado + 1) % len(opcoes)
        elif key == "ENTER":
            return selecionado
        elif key == "q":
            return -1

def _enviar_requisicao(ip, porta, mensagem, timeout=3.0):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            s.connect((ip, porta))
            s.sendall(json.dumps(mensagem).encode())
            dados = s.recv(16384)
            if dados: return json.loads(dados.decode())
    except Exception: pass
    return None

def encontrar_coordenador(nos):
    for no in nos:
        resposta = _enviar_requisicao(no['ip'], no['port'], {'type': 'GET_COORDINATOR'}, timeout=0.5)
        if resposta and resposta.get('status') == 'success':
            return resposta.get('coordinator_id')
    return None

def formatar_resultado(resultado):
    if resultado.get('status') == 'success':
        data = resultado.get('data')
        print(f"\n{Cores.OKGREEN}[Nó {resultado.get('node')}]: OK{Cores.ENDC}")
        if data:
            colunas = data[0].keys()
            header = " | ".join([f"{Cores.BOLD}{c}{Cores.ENDC}" for c in colunas])
            print("-" * 40)
            print(header)
            print("-" * 40)
            for row in data:
                print(" | ".join([str(row[c]) for c in colunas]))
            print("-" * 40)
        else:
            print(f"{Cores.OKBLUE}Comando executado.{Cores.ENDC}")
    else:
        print(f"\n{Cores.FAIL}[ERRO]: {resultado.get('message')}{Cores.ENDC}")

def perfil_uso(nos):
    limpar_tela()
    exibir_banner()
    print(f"{Cores.OKGREEN}--- MODO DIONNE: OPERAÇÃO DIRETA ---{Cores.ENDC}\n")
    
    while True:
        id_coord = encontrar_coordenador(nos)
        alvo = next((n for n in nos if n['id'] == id_coord), nos[0]) if id_coord is not None else nos[0]
        label = f"Coord {alvo['id']}" if id_coord is not None else f"Nó {alvo['id']}"

        try:
            sql = input(f"{Cores.BOLD}{Cores.OKCYAN}DIONNE @ {label} > {Cores.ENDC}")
            if sql.lower() in ['q', 'exit', 'sair']: break
            if not sql: continue

            res = _enviar_requisicao(alvo['ip'], alvo['port'], {'type': 'CLIENT_QUERY', 'sql': sql})
            if res: formatar_resultado(res)
            else: print(f"{Cores.FAIL}Falha na conexão.{Cores.ENDC}")
        except KeyboardInterrupt:
            break

def perfil_teste(nos):
    while True:
        opcoes = [f"Nó {n['id']} ({n['ip']}:{n['port']})" for n in nos]
        opcoes.extend(["Balanceamento Aleatório", "Automático (Coordenador)", "Voltar"])
        
        escolha = menu_interativo(opcoes, "--- MODO DIONNE: TESTES E DEPURAÇÃO ---")
        
        if escolha == -1 or escolha == len(opcoes) - 1: break
        
        no_alvo = None
        if escolha < len(nos):
            no_alvo = nos[escolha]
        elif escolha == len(nos):
            no_alvo = random.choice(nos)
        elif escolha == len(nos) + 1:
            id_coord = encontrar_coordenador(nos)
            no_alvo = next((n for n in nos if n['id'] == id_coord), nos[0])
        
        if no_alvo:
            print(f"\n{Cores.OKCYAN}Conectado ao Nó {no_alvo['id']}{Cores.ENDC}")
            try:
                sql = input(f"SQL > ")
                if sql:
                    res = _enviar_requisicao(no_alvo['ip'], no_alvo['port'], {'type': 'CLIENT_QUERY', 'sql': sql})
                    if res: formatar_resultado(res)
                    else: print(f"{Cores.FAIL}Erro.{Cores.ENDC}")
                input("\n[Pressione Enter]")
            except KeyboardInterrupt:
                break

def principal():
    try:
        with open('config.json', 'r') as f: nos = json.load(f)['nodes']
    except:
        print("Erro: config.json não encontrado."); return

    while True:
        opcoes = ["Modo Normal", "Modo Debug", "Sair"]
        escolha = menu_interativo(opcoes, "BEM-VINDO À DIONNE")
        
        if escolha == 0: perfil_uso(nos)
        elif escolha == 1: perfil_teste(nos)
        else: break

if __name__ == "__main__":
    principal()
