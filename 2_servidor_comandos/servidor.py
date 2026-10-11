
# Atividade 03 - Exercício 2: Servidor de Comandos (servidor)

import argparse
import socket
import threading
import unicodedata
from datetime import datetime

AJUDA = (
    "Comandos disponíveis: SOMAR n1 n2 | SUBTRAIR n1 n2 | MULTIPLICAR n1 n2 | "
    "DIVIDIR n1 n2 | HORA | DATA | INVERTER palavra | VOGAL palavra | "
    "CONSOANTE palavra | AJUDA | SAIR"
)


def formatar(n):
    if float(n).is_integer():
        return str(int(n))
    return str(round(n, 10))


def letra_base(c):
    return unicodedata.normalize("NFD", c)[0].lower()


def eh_vogal(c):
    return c.isalpha() and letra_base(c) in "aeiou"


def eh_consoante(c):
    return c.isalpha() and letra_base(c) not in "aeiou"


def numeros(args):
    if len(args) != 2:
        raise ValueError("informe exatamente dois números.")
    try:
        return float(args[0].replace(",", ".")), float(args[1].replace(",", "."))
    except ValueError:
        raise ValueError("os argumentos devem ser números.")


def processar(linha):
    partes = linha.strip().split()
    if not partes:
        return "ERRO: comando vazio. Digite AJUDA."
    cmd, args = partes[0].upper(), partes[1:]

    try:
        if cmd == "SOMAR":
            a, b = numeros(args)
            return formatar(a + b)
        if cmd == "SUBTRAIR":
            a, b = numeros(args)
            return formatar(a - b)
        if cmd == "MULTIPLICAR":
            a, b = numeros(args)
            return formatar(a * b)
        if cmd == "DIVIDIR":
            a, b = numeros(args)
            if b == 0:
                return "ERRO: divisão por zero."
            return formatar(a / b)
        if cmd == "HORA":
            return datetime.now().strftime("%H:%M")
        if cmd == "DATA":
            return datetime.now().strftime("%d/%m/%Y")
        if cmd in ("INVERTER", "VOGAL", "CONSOANTE"):
            if len(args) != 1:
                return f"ERRO: uso correto -> {cmd} [PALAVRA]"
            palavra = args[0]
            if cmd == "INVERTER":
                return palavra[::-1]
            if cmd == "VOGAL":
                return "".join(c for c in palavra if eh_vogal(c))
            return "".join(c for c in palavra if eh_consoante(c))
        if cmd == "AJUDA":
            return AJUDA
    except ValueError as e:
        return f"ERRO: {e}"
    return f"ERRO: comando '{cmd}' desconhecido. Digite AJUDA."


def tratar_cliente(sock, addr):
    print(f"[SERVIDOR] Cliente conectado: {addr}")
    arq = sock.makefile("r", encoding="utf-8")
    try:
        sock.sendall(("Servidor de Comandos pronto. " + AJUDA + "\n").encode("utf-8"))
        for linha in arq:
            linha = linha.strip()
            if linha.upper() == "SAIR":
                break
            print(f"[SERVIDOR] {addr} -> {linha}")
            resposta = processar(linha)
            sock.sendall((resposta + "\n").encode("utf-8"))
    except OSError:
        pass
    finally:
        print(f"[SERVIDOR] Cliente desconectado: {addr}")
        sock.close()


def main():
    p = argparse.ArgumentParser(description="Servidor de Comandos")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--porta", type=int, default=5002)
    args = p.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.host, args.porta))
    srv.listen()
    print(f"[SERVIDOR] Escutando em {args.host}:{args.porta}")
    try:
        while True:
            sock, addr = srv.accept()
            threading.Thread(target=tratar_cliente, args=(sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Encerrando.")
    finally:
        srv.close()


if __name__ == "__main__":
    main()
