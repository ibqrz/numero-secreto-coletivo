
# Atividade 03 - Exercício 1: Jogo do Número Secreto Coletivo (cliente - interface amigável)


import argparse
import os
import re
import socket
import sys
import threading

MIN, MAX = 1, 100

if os.name == "nt":
    os.system("")                     
USAR_COR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def cor(texto, codigo):
    return f"\033[{codigo}m{texto}\033[0m" if USAR_COR else texto


def azul(t):     return cor(t, "1;36")
def verde(t):    return cor(t, "1;32")
def vermelho(t): return cor(t, "1;31")
def amarelo(t):  return cor(t, "1;33")
def cinza(t):    return cor(t, "90")


estado = {
    "nome": None,        
    "lo": MIN, "hi": MAX,  
    "ultimo": None,     
    "tentativas": 0,     
    "vitorias": 0,
    "aguardando": False,
}
trava_saida = threading.Lock()
encerrado = threading.Event()


def prompt():
    if estado["nome"] is None:
        return azul("seu nome") + " > "
    return azul(f"palpite ({estado['lo']}-{estado['hi']})") + " > "


def escrever(msg, reexibir_prompt=False):

    with trava_saida:
        if USAR_COR:
            sys.stdout.write("\r\033[K" + msg + "\n")
            if reexibir_prompt and estado["aguardando"]:
                sys.stdout.write(prompt())
            sys.stdout.flush()
        else:
            print(msg, flush=True)


def resetar_rodada():
    estado["lo"], estado["hi"] = MIN, MAX
    estado["ultimo"] = None
    estado["tentativas"] = 0


def faixa_texto():
    lo, hi = estado["lo"], estado["hi"]
    if lo == hi:
        return f"Só pode ser o {amarelo(str(lo))}!"
    return f"Faixa possível: {amarelo(str(lo))} a {amarelo(str(hi))}"


def formatar(linha):
    if linha.startswith("===") or linha.startswith("Digite seu nome"):
        return None                                    

    if linha == "MAIOR" or linha == "MENOR":
        ult = estado["ultimo"]
        if ult is None:
            return f"  {linha}"
        if linha == "MAIOR":
            estado["lo"] = max(estado["lo"], ult + 1)
            seta = amarelo("▲ MAIOR")
            frase = f"O número secreto é maior que {ult}."
        else:
            estado["hi"] = min(estado["hi"], ult - 1)
            seta = amarelo("▼ MENOR")
            frase = f"O número secreto é menor que {ult}."
        tentativa = f"(tentativa {estado['tentativas']})"
        return f"  {seta}  {frase}\n  {cinza('•')} {faixa_texto()}   {cinza(tentativa)}"

    if linha.startswith("PARABÉNS"):
        estado["vitorias"] += 1
        n = estado["tentativas"]
        return ("\n" + verde("  ╔══════════════════════════════════════╗") + "\n"
                + verde("  ║    ★  PARABÉNS! VOCÊ ACERTOU!  ★     ║") + "\n"
                + verde("  ╚══════════════════════════════════════╝") + "\n"
                + f"  Acertou em {verde(str(n))} tentativa(s). Vitórias nesta sessão: {verde(str(estado['vitorias']))}")

    m = re.match(r"\*\*\* (.+) ACERTOU! O número era (\d+)\.", linha)
    if m:
        vencedor, numero = m.group(1), m.group(2)
        quem = "você" if vencedor == estado["nome"] else vencedor
        return f"\n  {amarelo('🏁 Rodada encerrada!')} Vencedor: {verde(quem)} — o número era {amarelo(numero)}."

    m = re.match(r"--- Nova rodada #(\d+)", linha)
    if m:
        resetar_rodada()
        return (cinza("  " + "─" * 46) + "\n"
                + f"  {azul('NOVA RODADA #' + m.group(1))} — adivinhe o número entre {MIN} e {MAX}!")

    m = re.match(r"Rodada #(\d+):", linha)
    if m:   
        return f"\n  {azul('RODADA #' + m.group(1))} em andamento — adivinhe o número entre {MIN} e {MAX}!\n  {cinza('Digite um número e tecle ENTER. (AJUDA = regras | SAIR = sair)')}"

    if linha.startswith(">>"):
        return cinza(f"  → {linha[2:].strip()}")
    if linha.startswith("<<"):
        return cinza(f"  ← {linha[2:].strip()}")
    if linha.startswith("Entrada inválida") or linha.startswith("Digite um número"):
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
    print(azul("  ║      JOGO DO NÚMERO SECRETO COLETIVO         ║"))
    print(azul("  ╚══════════════════════════════════════════════╝"))
    print(f"  {verde('● Conectado')} a {host}:{porta}")
    print()
    print("  O servidor sorteou um número de 1 a 100. Todos os jogadores")
    print("  tentam descobrir — quem acertar primeiro vence a rodada!")
    print()
    print(f"  {amarelo('Primeiro, digite o seu nome e tecle ENTER.')}")
    print()


def mostrar_ajuda():
    escrever("\n".join([
        "",
        azul("  COMO JOGAR"),
        cinza("  " + "─" * 46),
        f"  • Digite um número de {MIN} a {MAX} e tecle ENTER.",
        f"  • {amarelo('▲ MAIOR')}: o número secreto é maior que o seu palpite.",
        f"  • {amarelo('▼ MENOR')}: o número secreto é menor que o seu palpite.",
        "  • Quando alguém acertar, todos são avisados e começa nova rodada.",
        f"  • {azul('AJUDA')} mostra esta tela  |  {azul('SAIR')} encerra o jogo.",
        cinza("  " + "─" * 46),
    ]))


def main():
    p = argparse.ArgumentParser(description="Cliente - Jogo do Número Secreto")
    p.add_argument("--host", default="127.0.0.1", help="IP do servidor (padrão: 127.0.0.1)")
    p.add_argument("--porta", type=int, default=5001, help="Porta (padrão: 5001)")
    args = p.parse_args()

    try:
        sock = socket.create_connection((args.host, args.porta))
    except OSError as e:
        print(vermelho(f"\n  ✗ Não foi possível conectar em {args.host}:{args.porta}"))
        print(f"    Motivo: {e}")
        print("    Confira se o servidor está rodando e se o IP/porta estão corretos.")
        sys.exit(1)

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
            if texto.lower() in ("sair", "/sair"):
                break

            if estado["nome"] is None:
                estado["nome"] = texto
                sock.sendall((texto + "\n").encode("utf-8"))
                escrever(f"\n  Olá, {verde(texto)}! Bem-vindo(a) ao jogo.")
                continue

            if texto.lower() in ("ajuda", "/ajuda"):
                mostrar_ajuda()
                continue

      
            try:
                palpite = int(texto)
            except ValueError:
                escrever(vermelho(f"  ✗ '{texto}' não é um número. Digite um inteiro de {MIN} a {MAX} (ou AJUDA / SAIR)."))
                continue
            if not MIN <= palpite <= MAX:
                escrever(vermelho(f"  ✗ O número deve estar entre {MIN} e {MAX}."))
                continue
            if not estado["lo"] <= palpite <= estado["hi"]:
                escrever(amarelo(f"  ! Você já sabe que o número está entre {estado['lo']} e {estado['hi']}."))

            estado["ultimo"] = palpite
            estado["tentativas"] += 1
            sock.sendall((str(palpite) + "\n").encode("utf-8"))
    except (EOFError, KeyboardInterrupt):
        print()
    except OSError:
        escrever(vermelho("\n  ✗ Conexão perdida com o servidor."))
    finally:
        estado["aguardando"] = False
        sock.close()
        print(cinza(f"\n  Fim de jogo, {estado['nome'] or 'jogador'}! Vitórias nesta sessão: {estado['vitorias']}. Até logo!"))


if __name__ == "__main__":
    main()