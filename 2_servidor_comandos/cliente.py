
# Atividade 03 - Exercício 2: cliente do Servidor de Comandos (interface amigável)

import argparse
import difflib
import os
import socket
import sys

COMANDOS = {
    "SOMAR":       ("SOMAR [NUM1] [NUM2]",       "SOMAR 8 5",              "13"),
    "SUBTRAIR":    ("SUBTRAIR [NUM1] [NUM2]",    "SUBTRAIR 10 17",         "-7"),
    "MULTIPLICAR": ("MULTIPLICAR [NUM1] [NUM2]", "MULTIPLICAR 5 13",       "65"),
    "DIVIDIR":     ("DIVIDIR [NUM1] [NUM2]",     "DIVIDIR 7 2",            "3.5"),
    "HORA":        ("HORA",                      "HORA",                   "10:21"),
    "DATA":        ("DATA",                      "DATA",                   "29/09/2026"),
    "INVERTER":    ("INVERTER [PALAVRA]",        "INVERTER distribuída",   "adíubirtsid"),
    "VOGAL":       ("VOGAL [PALAVRA]",           "VOGAL programação",      "oaaão"),
    "CONSOANTE":   ("CONSOANTE [PALAVRA]",       "CONSOANTE paralela",     "prll"),
}

if os.name == "nt":
    os.system("")                     
USAR_COR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def cor(texto, codigo):
    return f"\033[{codigo}m{texto}\033[0m" if USAR_COR else texto


def azul(t):     return cor(t, "1;36")
def verde(t):    return cor(t, "1;32")
def vermelho(t): return cor(t, "1;31")
def amarelo(t):  return cor(t, "33")
def cinza(t):    return cor(t, "90")


def mostrar_ajuda():
    print()
    print(azul("  COMANDOS DISPONÍVEIS"))
    print(cinza("  " + "─" * 74))
    print(f"  {'COMO USAR':<28}{'EXEMPLO':<24}{'RESPOSTA'}")
    print(cinza("  " + "─" * 74))
    for uso, exemplo, resultado in COMANDOS.values():
        print(f"  {uso:<28}{amarelo(exemplo):<{24 + (len(amarelo('')) if USAR_COR else 0)}}{resultado}")
    print(cinza("  " + "─" * 74))
    print("  Regras:")
    print("   • Primeiro o NOME do comando, depois os valores, separados por ESPAÇO.")
    print("   • Maiúsculas ou minúsculas tanto faz (somar = SOMAR).")
    print("   • Não use vírgula entre os números: SOMAR 1 2 (e não 1, 2).")
    print(f"   • {azul('AJUDA')} mostra esta tela  |  {azul('SAIR')} encerra o programa.")
    print()


def mostrar_banner(host, porta):
    print()
    print(azul("  ╔══════════════════════════════════════════════╗"))
    print(azul("  ║        CLIENTE - SERVIDOR DE COMANDOS        ║"))
    print(azul("  ╚══════════════════════════════════════════════╝"))
    print(f"  {verde('● Conectado')} a {host}:{porta}")
    mostrar_ajuda()


def dica_de_erro(comando, resposta):
    if "zero" in resposta:
        return
    nome = comando.split()[0].upper()
    if nome in COMANDOS:
        print(amarelo(f"   Dica: use no formato  {COMANDOS[nome][0]}   →   exemplo: {COMANDOS[nome][1]}"))
        return
    sugestao = difflib.get_close_matches(nome, COMANDOS, n=1, cutoff=0.6)
    if sugestao:
        print(amarelo(f"   Dica: você quis dizer {sugestao[0]}?  Exemplo: {COMANDOS[sugestao[0]][1]}"))
    else:
        print(amarelo("   Dica: comece pelo NOME do comando, depois os valores. Ex.: SOMAR 23 24"))
        print(amarelo("         Digite AJUDA para ver todos os comandos."))


def main():
    p = argparse.ArgumentParser(description="Cliente - Servidor de Comandos")
    p.add_argument("--host", default="127.0.0.1", help="IP do servidor (padrão: 127.0.0.1)")
    p.add_argument("--porta", type=int, default=5002, help="Porta (padrão: 5002)")
    args = p.parse_args()

    try:
        sock = socket.create_connection((args.host, args.porta))
    except OSError as e:
        print(vermelho(f"\n  ✗ Não foi possível conectar em {args.host}:{args.porta}"))
        print(f"    Motivo: {e}")
        print("    Confira se o servidor está rodando e se o IP/porta estão corretos.")
        sys.exit(1)

    arq = sock.makefile("r", encoding="utf-8")
    arq.readline()                         
    mostrar_banner(args.host, args.porta)

    try:
        while True:
            comando = input(azul("comando") + " > ").strip()
            if not comando:
                continue
            if comando.upper() == "AJUDA":
                mostrar_ajuda()
                continue

            sock.sendall((comando + "\n").encode("utf-8"))
            if comando.upper() == "SAIR":
                break

            resposta = arq.readline()
            if not resposta:
                print(vermelho("  ✗ O servidor encerrou a conexão."))
                break
            resposta = resposta.rstrip()
            if resposta.startswith("ERRO"):
                print(vermelho(f"  ✗ {resposta}"))
                dica_de_erro(comando, resposta)
            else:
                print(f"  {verde('✓ Resposta:')} {resposta}")
            print()
    except (EOFError, KeyboardInterrupt):
        print()
    except OSError:
        print(vermelho("\n  ✗ Conexão perdida com o servidor."))
    finally:
        sock.close()
        print(cinza("  Conexão encerrada. Até logo!"))


if __name__ == "__main__":
    main()