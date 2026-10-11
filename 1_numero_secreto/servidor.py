
# Atividade 03 - Exercício 1: Jogo do Número Secreto Coletivo (servidor)

import argparse
import random
import socket
import threading

MIN, MAX = 1, 100

trava = threading.RLock()      
jogadores = []                
segredo = random.randint(MIN, MAX)
rodada = 1


class Conexao:
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.nome = f"{addr[0]}:{addr[1]}"
        self.arq = sock.makefile("r", encoding="utf-8")
        self.lock_envio = threading.Lock()   

    def enviar(self, msg):
        try:
            with self.lock_envio:
                self.sock.sendall((msg + "\n").encode("utf-8"))
        except OSError:
            pass

    def receber(self):
        try:
            linha = self.arq.readline()
        except (OSError, ValueError):
            return None
        return linha.rstrip("\r\n") if linha else None

    def fechar(self):
        try:
            self.sock.close()
        except OSError:
            pass


def broadcast(msg):
    with trava:
        for j in list(jogadores):
            j.enviar(msg)


def nova_rodada():
    global segredo, rodada
    with trava:
        segredo = random.randint(MIN, MAX)
        rodada += 1
        print(f"[SERVIDOR] Rodada {rodada} iniciada. (número secreto: {segredo})")
    broadcast(f"--- Nova rodada #{rodada}! Adivinhe o número entre {MIN} e {MAX} ---")


def tratar_cliente(conn):
    conn.enviar("=== JOGO DO NÚMERO SECRETO COLETIVO ===")
    conn.enviar("Digite seu nome:")
    nome = conn.receber()
    if nome is None:
        conn.fechar()
        return
    if nome.strip():
        conn.nome = nome.strip()

    with trava:
        jogadores.append(conn)
    print(f"[SERVIDOR] {conn.nome} entrou ({len(jogadores)} jogador(es)).")
    broadcast(f">> {conn.nome} entrou no jogo.")
    conn.enviar(f"Rodada #{rodada}: adivinhe o número entre {MIN} e {MAX}.")

    while True:
        linha = conn.receber()
        if linha is None:
            break
        try:
            palpite = int(linha.strip())
        except ValueError:
            conn.enviar("Entrada inválida. Digite um número inteiro.")
            continue
        if not MIN <= palpite <= MAX:
            conn.enviar(f"Digite um número entre {MIN} e {MAX}.")
            continue

        with trava:
            if palpite == segredo:
                conn.enviar("PARABÉNS! VOCÊ ACERTOU!")
                broadcast(f"*** {conn.nome} ACERTOU! O número era {palpite}. Rodada encerrada. ***")
                nova_rodada()
            elif palpite < segredo:
                conn.enviar("MAIOR")
            else:
                conn.enviar("MENOR")

    with trava:
        if conn in jogadores:
            jogadores.remove(conn)
    print(f"[SERVIDOR] {conn.nome} saiu.")
    broadcast(f"<< {conn.nome} saiu do jogo.")
    conn.fechar()


def main():
    p = argparse.ArgumentParser(description="Servidor - Jogo do Número Secreto")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--porta", type=int, default=5001)
    args = p.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.host, args.porta))
    srv.listen()
    print(f"[SERVIDOR] Escutando em {args.host}:{args.porta}")
    print(f"[SERVIDOR] Rodada {rodada} iniciada. (número secreto: {segredo})")

    try:
        while True:
            sock, addr = srv.accept()
            threading.Thread(target=tratar_cliente, args=(Conexao(sock, addr),), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[SERVIDOR] Encerrando.")
    finally:
        srv.close()


if __name__ == "__main__":
    main()
