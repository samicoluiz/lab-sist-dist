# Explicação do Sistema de Banco de Dados Distribuído

Este documento descreve o funcionamento técnico do middleware de banco de dados distribuído, detalhando sua arquitetura, mecanismos de comunicação e estratégias de consistência.

## 1. Arquitetura do Sistema

O sistema é composto por três componentes principais:
- **Middleware (Nós)**: Instâncias de `node.py` que atuam como intermediários entre o cliente e o banco de dados MySQL local.
- **Banco de Dados (Storage)**: Instâncias do MySQL rodando em containers Docker, onde os dados são efetivamente armazenados.
- **Cliente**: Uma aplicação (`client.py`) que envia consultas SQL para qualquer nó do middleware.

Cada nó do middleware possui conhecimento da topologia da rede através de um arquivo `config.json`.

## 2. Comunicação via Sockets

A comunicação entre todos os elementos do sistema é feita utilizando **Sockets TCP (Streaming)**.

- **Protocolo**: TCP (`socket.SOCK_STREAM`) é utilizado para garantir a entrega confiável e ordenada das mensagens.
- **Formato de Dados**: As mensagens são serializadas em formato **JSON**. Isso facilita a interoperabilidade e a expansão do protocolo de comunicação.
- **Escuta e Aceite**: Cada nó mantém uma thread (`executar_servidor`) que escuta em uma porta específica. Quando uma conexão é recebida, uma nova thread é criada para tratar aquela requisição específica (`tratar_cliente`), permitindo concorrência.

## 3. Broadcasting

O **Broadcasting** (difusão) é a técnica onde um nó envia a mesma mensagem para todos os outros nós conhecidos na rede. No sistema, ele é implementado de forma iterativa: o nó percorre sua lista de "vizinhos" e abre uma conexão socket individual com cada um para entregar a mensagem.

O broadcasting é utilizado para:
1. **Heartbeats**: Sinais de "estou vivo" enviados periodicamente.
2. **Replicação**: Difusão de comandos SQL de escrita.
3. **Eleição**: Notificação de novos coordenadores ou início de processo eleitoral.

## 4. Compartilhamento e Replicação de Estado

Para manter o banco de dados sincronizado entre os nós, o sistema utiliza uma estratégia de **Replicação de Escrita com Checksum**:

- **Detecção de Escrita**: O nó que recebe uma query do cliente analisa se ela é um comando de modificação (`INSERT`, `UPDATE`, `DELETE`, etc.).
- **Execução Local**: O comando é primeiro executado no banco de dados MySQL local do nó que recebeu a requisição.
- **Propagação**: Se a execução local for bem-sucedida, o nó gera um **Checksum MD5** do comando SQL e realiza um broadcast de uma mensagem do tipo `REPLICATE` para todos os outros nós.
- **Integridade**: Ao receber uma mensagem de replicação, o nó destino recalcula o checksum. Se coincidir com o enviado, ele aplica o comando em seu próprio banco de dados MySQL. Isso garante que comandos corrompidos durante a transmissão não sejam executados.

## 5. Coordenação e Tolerância a Falhas

O sistema não possui um ponto único de falha centralizado permanentemente. Ele utiliza o **Algoritmo do Valentão (Bully Algorithm)** para eleger um coordenador.

### Eleição (Bully Algorithm)
- Quando um nó percebe que o coordenador atual caiu (falta de heartbeat), ele inicia uma eleição.
- Nós com IDs maiores têm prioridade.
- O nó com o maior ID ativo na rede eventualmente se proclama o novo coordenador e avisa aos demais.

### Detecção de Falhas
- **Heartbeats**: Cada nó envia um sinal de vida a cada 2 segundos.
- **Timeout**: Se um nó não receber sinais de vida de outro nó por mais de 10 segundos, ele o marca como "offline".

## 6. Fluxo de uma Requisição

1. O **Cliente** se conecta a um **Nó X** e envia uma query.
2. O **Nó X** executa a query em seu MySQL local.
3. Se for uma query de **Leitura** (`SELECT`):
   - O resultado é retornado diretamente ao cliente.
4. Se for uma query de **Escrita** (`INSERT`, `UPDATE`, etc.):
   - O **Nó X** envia o comando para todos os outros nós via broadcast.
   - Os outros nós aplicam a mudança em seus bancos locais.
   - O **Nó X** confirma o sucesso ao cliente.

## 7. Consistência e Limitações

Atualmente, o sistema prioriza a **Disponibilidade** em detrimento da **Consistência Forte**. Isso significa que:

- **Falhas de Conexão**: Se um nó estiver offline no momento de uma escrita, ele não receberá a atualização. O sistema atual não possui um "log de operações" para sincronizar nós que retornam de uma falha.
- **Configuração de IPs**: Em um ambiente com múltiplos computadores, **nunca utilize `127.0.0.1` ou `localhost`** no arquivo `ips.txt`. 
    - Se o Nó A configurar o Nó B como `127.0.0.1`, o Nó A tentará enviar dados para si mesmo quando quiser falar com o Nó B.
    - Todos os nós devem usar seus IPs reais de rede (ex: `192.168.x.x`) para que todos possam se enxergar bidirecionalmente.
- **Persistência Docker**: Os bancos de dados MySQL estão configurados sem volumes. Se o container for removido, os dados serão perdidos, causando divergência se apenas um nó for reiniciado.

## 8. Monitoramento

Os logs em `logs/nodeX.log` agora registram falhas de replicação. Se você vir mensagens de erro como `Erro ao enviar REPLICATE`, significa que a rede impediu a sincronização entre os nós.
