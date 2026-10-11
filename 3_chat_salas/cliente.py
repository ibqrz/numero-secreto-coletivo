
# Atividade 03 - Exercício 3: Chat de Terminal em Salas (cliente - interface amigável)

import argparse
import os
import re
import socket
import sys
import threading
from datetime import datetime

if os.name == "nt":
    os.system("")                      
USAR_COR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def cor(texto, codigo):
    return f"\033[{codigo}m{texto}\033[0m" if USAR_COR else texto


def azul(t):     return cor(t, "1;36")
def verde(t):    return cor(t, "1;32")
def vermelho(t): return cor(t, "1;31")
def amarelo(t):  return cor(t, "1;33")
def magenta(t):  return cor(t, "1;35")
def cinza(t):    return cor(t, "90")


PALETA = ["32", "33", "34", "35", "36", "91", "92", "93", "94", "95", "96"]


def cor_usuario(nome):
    return cor(nome, "1;" + PALETA[sum(map(ord, nome)) % len(PALETA)])


estado = {
    "etapa": 0,          
    "nome": None,
    "sala": None,
    "aguardando": False, 
}
trava_saida = threading.Lock()
encerrado = threading.Event()

COMANDOS = [
    ("/salas",          "lista as salas ativas e quantas pessoas há em cada"),
    ("/entrar <sala>",  "troca para outra sala (cria se não existir)"),
    ("/usuarios",       "mostra quem está na sua sala"),
    ("/ajuda",          "mostra esta lista"),
    ("/limpar",         "limpa a tela"),
    ("/sair",           "desconecta do chat"),
]
PALAVRAS_DE_COMANDO = {"salas", "entrar", "usuarios", "usuários", "ajuda", "limpar", "sair"}


def hora():
    return datetime.now().strftime("%H:%M")


def prompt():
    if estado["etapa"] == 0:
        return azul("apelido") + " > "
    if estado["etapa"] == 1:
        return azul("sala") + " > "
    return f"{magenta('#' + str(estado['sala']))} {azul(estado['nome'])} > "


def escrever(msg, reexibir_prompt=False):
    with trava_saida:
        if USAR_COR:
            sys.stdout.write("\r\033[K" + msg + "\n")
            if reexibir_prompt and estado["aguardando"]:
                sys.stdout.write(prompt())
            sys.stdout.flush()
        else:
            print(msg, flush=True)


def formatar(linha):
    if linha.startswith("===") or linha.startswith("Digite seu apelido"):
        return None                                     

    m = re.match(r"^\[(.+?)\] (.+?): (.*)$", linha)      
    if m:
        _, autor, texto = m.groups()
        return f"  {cinza(hora())}  {cor_usuario(autor)}: {texto}"

    m = re.match(r"^\* (.+) entrou na sala '(.*)'\.$", linha)
    if m:
        return cinza(f"  → {m.group(1)} entrou na sala")
    m = re.match(r"^\* (.+) saiu da sala '(.*)'\.$", linha)
    if m:
        return cinza(f"  ← {m.group(1)} saiu da sala")

    m = re.match(r"^Você entrou na sala '(.*)'\. Comandos:", linha)
    if m:
        estado["sala"] = m.group(1)
        estado["etapa"] = 2
        return ("\n" + magenta(f"  ╭─ Sala: #{m.group(1)} " + "─" * max(2, 34 - len(m.group(1)))) + "\n"
                + f"  {verde('✓')} Você entrou na sala {magenta('#' + m.group(1))}.\n"
                + f"  {cinza('Escreva e tecle ENTER para conversar. Comandos começam com /  —  digite /ajuda')}\n")

    if linha.startswith("Salas ativas:"):
        itens = re.findall(r"(.+?) \((\d+)\)(?:, |$)", linha[len("Salas ativas:"):].strip())
        linhas = ["", azul("  SALAS ATIVAS")]
        for nome, qtd in itens:
            marca = verde(" ← você está aqui") if nome == estado["sala"] else ""
            pessoas = "pessoa" if qtd == "1" else "pessoas"
            linhas.append(f"   • {magenta('#' + nome)}  {cinza(f'({qtd} {pessoas})')}{marca}")
        return "\n".join(linhas) + "\n"
    if linha.startswith("Nenhuma sala ativa"):
        return cinza("  Nenhuma sala ativa ainda — escolha um nome para criar a primeira!")

    m = re.match(r"^Usuários em '(.*)': (.*)$", linha)
    if m:
        nomes = [n for n in m.group(2).split(", ") if n]
        lista = ", ".join(cor_usuario(n) + (cinza(" (você)") if n == estado["nome"] else "") for n in nomes)
        return f"\n  {azul('NA SALA')} {magenta('#' + m.group(1))} ({len(nomes)}): {lista}\n"

    if linha.startswith("Digite o nome da sala"):
        return amarelo("  Escolha uma sala da lista acima ou digite um nome novo para criá-la.")
    if linha.startswith("Nome de sala inválido"):
        return vermelho("  ✗ Nome de sala inválido. Tente novamente.")
    if linha.startswith("Comando desconhecido") or linha.startswith("Uso:"):
        return vermelho(f"  ✗ {linha}")
    return f"  {linha}"


def receber(arq):
    try:
        for linha in arq:
            texto = formatar(linha.rstrip("\r\n"))
            if texto is not None:
                escrever(texto, reexibir_prompt=True)
    except (OSError, ValueError):
        pass
    encerrado.set()
    escrever("\n" + vermelho("  ✗ Conexão encerrada pelo servidor. Pressione ENTER para sair."))


def mostrar_banner(host, porta):
    print()
    print(azul("  ╔══════════════════════════════════════════════╗"))
    print(azul("  ║          CHAT DE TERMINAL EM SALAS           ║"))
    print(azul("  ╚══════════════════════════════════════════════╝"))
    print(f"  {verde('● Conectado')} a {host}:{porta}")
    print()
    print(f"  {amarelo('Primeiro, digite o seu apelido e tecle ENTER.')}")
    print()


def mostrar_ajuda():
    linhas = ["", azul("  COMANDOS DO CHAT"), cinza("  " + "─" * 62)]
    for cmd, desc in COMANDOS:
        linhas.append(f"  {amarelo(f'{cmd:<16}')} {desc}")
    linhas += [cinza("  " + "─" * 62),
               "  Qualquer texto que NÃO comece com / é enviado como mensagem",
               "  para as pessoas da sua sala (somente elas recebem).",
               ""]
    escrever("\n".join(linhas))


def limpar_tela():
    if USAR_COR:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()
    else:
        os.system("cls" if os.name == "nt" else "clear")


def apagar_linha_digitada():
    if USAR_COR:
        with trava_saida:
            sys.stdout.write("\033[F")
            sys.stdout.flush()


def main():
    p = argparse.ArgumentParser(description="Cliente - Chat de Terminal em Salas")
    p.add_argument("--host", default="127.0.0.1", help="IP do servidor (padrão: 127.0.0.1)")
    p.add_argument("--porta", type=int, default=5003, help="Porta (padrão: 5003)")
    args = p.parse_args()

    try:
        sock = socket.create_connection((args.host, args.porta))
    except OSError as e:
        print(vermelho(f"\n  ✗ Não foi possível conectar em {args.host}:{args.porta}"))
        print(f"    Motivo: {e}")
        print("    Confira se o servidor está rodando e se o IP/porta estão corretos.")
        sys.exit(1)

    def enviar(texto):
        sock.sendall((texto + "\n").encode("utf-8"))

    arq = sock.makefile("r", encoding="utf-8")
    mostrar_banner(args.host, args.porta)
    threading.Thread(target=receber, args=(arq,), daemon=True).start()

    try:
        while not encerrado.is_set():
            estado["aguardando"] = True
            sys.stdout.write(prompt())
            sys.stdout.flush()
            texto = input().strip()
            estado["aguardando"] = False

            if encerrado.is_set():
                break
            if not texto:
                continue

            if estado["etapa"] == 0:
                estado["nome"] = texto
                estado["etapa"] = 1
                enviar(texto)
                escrever(f"\n  Olá, {cor_usuario(texto)}!")
                continue

            if estado["etapa"] == 1:
                enviar(texto)
                continue

            if texto.startswith("/"):
                cmd, _, resto = texto.partition(" ")
                cmd = cmd.lower()
                if cmd == "/sair":
                    enviar("/sair")
                    break
                elif cmd == "/ajuda":
                    mostrar_ajuda()
                elif cmd == "/limpar":
                    limpar_tela()
                elif cmd in ("/salas", "/usuarios"):
                    enviar(cmd)
                elif cmd == "/entrar":
                    if resto.strip():
                        enviar(f"/entrar {resto.strip()}")
                    else:
                        escrever(vermelho("  ✗ Informe a sala. Exemplo: /entrar geral"))
                else:
                    escrever(vermelho(f"  ✗ Comando '{cmd}' não existe. Digite /ajuda para ver a lista."))
            elif texto.lower() in PALAVRAS_DE_COMANDO:
                escrever(amarelo(f"  ! Comandos começam com /  →  digite  /{texto.lower()}  (esta palavra NÃO foi enviada à sala)"))
            else:
                enviar(texto)
                apagar_linha_digitada()
                escrever(f"  {cinza(hora())}  {azul('Você')}: {texto}")
    except (EOFError, KeyboardInterrupt):
        print()
    except OSError:
        escrever(vermelho("\n  ✗ Conexão perdida com o servidor."))
    finally:
        estado["aguardando"] = False
        sock.close()
        print(cinza("\n  Você saiu do chat. Até logo!"))


if __name__ == "__main__":
    main()