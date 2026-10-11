
# Atividade 03 - Exercício 3: Chat de Terminal em Rede Local (servidor)

import argparse
import socket
import threading

trava = threading.RLock()
salas = {}         


class Conexao:
    def __init__(self, sock, addr):
        self.sock = sock
        self.addr = addr
        self.nome = f"{addr[0]}:{addr[1]}"
        self.sala = None
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


def listar_salas():
    with trava:
        if not salas:
            return "Nenhuma sala ativa ainda (digite um nome para criar a primeira)."
        return "Salas ativas: " + ", ".join(f"{n} ({len(c)})" for n, c in sorted(salas.items()))


def enviar_sala(sala, msg, excluir=None):
    with trava:
        for c in list(salas.get(sala, [])):
            if c is not excluir:
                c.enviar(msg)


def sair_da_sala(conn):
    with trava:
        sala = conn.sala
        if sala is None:
            return
        salas[sala].remove(conn)
        if not salas[sala]:
            del salas[sala]         
        conn.sala = None
    enviar_sala(sala, f"* {conn.nome} saiu da sala '{sala}'.")


def entrar_na_sala(conn, sala):
    sair_da_sala(conn)
    with trava:
        salas.setdefault(sala, []).append(conn)
        conn.sala = sala
    conn.enviar(f"Você entrou na sala '{sala}'. Comandos: /salas /entrar <sala> /usuarios /sair")
    enviar_sala(sala, f"* {conn.nome} entrou na sala '{sala}'.", excluir=conn)
    print(f"[SERVIDOR] {conn.nome} -> sala '{sala}'")


def tratar_cliente(conn):
    conn.enviar("=== CHAT DE TERMINAL ===")
    conn.enviar("Digite seu apelido:")
    nome = conn.receber()
    if nome is None:
        conn.fechar()
        return
    if nome.strip():
        conn.nome = nome.strip()

    conn.enviar(listar_salas())
    conn.enviar("Digite o nome da sala que deseja entrar (será criada se não existir):")
    sala = conn.receber()
    while sala is not None and not sala.strip():
        conn.enviar("Nome de sala inválido. Tente novamente:")
        sala = conn.receber()
    if sala is None:
        conn.fechar()
        return
    entrar_na_sala(conn, sala.strip())

    while True:
        linha = conn.receber()
        if linha is None:
            break
        linha = linha.strip()
        if not linha:
            continue
        if linha.startswith("/"):
            cmd, _, resto = linha.partition(" ")
            cmd = cmd.lower()
            if cmd == "/sair":
                break
            elif cmd == "/salas":
                conn.enviar(listar_salas())
            elif cmd == "/entrar":
                if resto.strip():
                    entrar_na_sala(conn, resto.strip())
                else:
                    conn.enviar("Uso: /entrar <sala>")
            elif cmd == "/usuarios":
                with trava:
                    nomes = ", ".join(c.nome for c in salas.get(conn.sala, []))
                conn.enviar(f"Usuários em '{conn.sala}': {nomes}")
            else:
                conn.enviar("Comando desconhecido. Use /salas /entrar <sala> /usuarios /sair")
        else:
            enviar_sala(conn.sala, f"[{conn.sala}] {conn.nome}: {linha}", excluir=conn)

    sair_da_sala(conn)
    print(f"[SERVIDOR] {conn.nome} desconectou.")
    conn.fechar()


def main():
    p = argparse.ArgumentParser(description="Servidor - Chat de Terminal em Salas")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--porta", type=int, default=5003)
    args = p.parse_args()

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((args.host, args.porta))
    srv.listen()
    print(f"[SERVIDOR] Escutando em {args.host}:{args.porta}")
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
