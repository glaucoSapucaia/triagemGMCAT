import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import os
from utils import logger


def iniciar_interface(processar_callback):
    credenciais = {}
    protocolos = []
    cancelar_event = threading.Event()

    def confirmar():
        try:
            credenciais["usuario"] = entry_usuario.get()
            credenciais["senha"] = entry_senha.get()
            credenciais["usuario_sigede"] = entry_usuario_sigede.get()
            credenciais["senha_sigede"] = entry_senha_sigede.get()
            lista = entry_protocolos.get().split(",")
            protocolos.clear()
            protocolos.extend([i.strip() for i in lista if i.strip() != ""])

            if not credenciais["usuario"] or not credenciais["senha"]:
                raise ValueError("Usuário e senha do SIATU são obrigatórios")
            if not credenciais["usuario_sigede"] or not credenciais["senha_sigede"]:
                raise ValueError("Usuário e senha do SIGEDE são obrigatórios")
            if not protocolos:
                raise ValueError("Informe ao menos um protocolo.")

            # Desabilita entradas e botão
            btn_confirmar.config(state="disabled")
            entry_protocolos.config(state="disabled")
            btn_cancelar.config(state="normal")
            status_label.config(text="Processando...")
            cancelar_event.clear()

            # Configura barra de progresso
            progress_bar["maximum"] = len(protocolos)
            progress_bar["value"] = 0

            # Executa em thread separada
            threading.Thread(
                target=lambda: processar_callback(
                    credenciais.copy(),
                    protocolos.copy(),
                    cancelar_event,
                    atualizar_progresso,
                ),
                daemon=True,
            ).start()

        except Exception as e:
            logger.error(f"Erro na interface ao confirmar: {e}")
            messagebox.showerror("Erro", str(e))

    def cancelar():
        cancelar_event.set()
        status_label.config(text="Cancelando processo...")

    def resetar_interface():
        entry_protocolos.config(state="normal")
        entry_protocolos.delete(0, tk.END)
        btn_confirmar.config(state="normal")
        btn_cancelar.config(state="disabled")
        progress_bar["value"] = 0
        status_label.config(text="Pronto para novo processamento.")

    def atualizar_progresso(valor):
        progress_bar["value"] = valor

    def on_fechar():
        if messagebox.askokcancel("Sair", "Deseja realmente encerrar o processamento?"):
            cancelar_event.set()
            root.destroy()

    # Interface
    root = tk.Tk()
    root.title("Triagem de Processos")
    root.geometry("800x600")

    root.protocol("WM_DELETE_WINDOW", on_fechar)

    tk.Label(root, text="Usuário SIGEDE:").grid(
        row=0, column=0, sticky="w", padx=5, pady=5
    )
    entry_usuario_sigede = tk.Entry(root, width=30)
    entry_usuario_sigede.grid(row=0, column=1, padx=5, pady=5)

    tk.Label(root, text="Senha SIGEDE:").grid(
        row=1, column=0, sticky="w", padx=5, pady=5
    )
    entry_senha_sigede = tk.Entry(root, show="*", width=30)
    entry_senha_sigede.grid(row=1, column=1, padx=5, pady=5)

    tk.Label(root, text="Usuário SIATU:").grid(
        row=2, column=0, sticky="w", padx=5, pady=5
    )
    entry_usuario = tk.Entry(root, width=30)
    entry_usuario.grid(row=2, column=1, padx=5, pady=5)

    tk.Label(root, text="Senha SIATU:").grid(
        row=3, column=0, sticky="w", padx=5, pady=5
    )
    entry_senha = tk.Entry(root, show="*", width=30)
    entry_senha.grid(row=3, column=1, padx=5, pady=5)

    tk.Label(
        root,
        text="Protocolo(s) (separados por vírgula e sem espaço - Ex. 7463527921,48302891,2611172):",
    ).grid(row=4, column=0, sticky="w", padx=5, pady=5)
    entry_protocolos = tk.Entry(root, width=50)
    entry_protocolos.grid(row=4, column=1, padx=5, pady=5)

    btn_confirmar = tk.Button(root, text="Confirmar", command=confirmar)
    btn_confirmar.grid(row=5, column=0, sticky="we", padx=5, pady=5)

    btn_cancelar = tk.Button(
        root, text="Cancelar", command=cancelar, fg="red", state="disabled"
    )
    btn_cancelar.grid(row=5, column=1, sticky="we", padx=5, pady=5)

    status_label = tk.Label(root, text="Aguardando entrada...")
    status_label.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

    progress_bar = ttk.Progressbar(
        root, orient="horizontal", length=700, mode="determinate"
    )
    progress_bar.grid(row=7, column=0, columnspan=2, pady=5, padx=5)

    log_area = scrolledtext.ScrolledText(root, width=90, height=20, state="disabled")
    log_area.grid(row=8, column=0, columnspan=2, pady=5, padx=5, sticky="nsew")

    # Ajuste para não perder a rolagem (log area)
    def atualizar_logs():
        try:
            if os.path.exists("Detalhes da Triagem.txt"):
                with open("Detalhes da Triagem.txt", "r", encoding="utf-8") as f:
                    conteudo = f.read()
                log_area.config(state="normal")

                # Checa se o usuário está no final
                pos_atual = log_area.yview()
                esta_no_final = pos_atual[1] == 1.0

                log_area.delete("1.0", tk.END)
                log_area.insert(tk.END, conteudo)
                log_area.config(state="disabled")

                # Mantém scroll no final somente se estava no final
                if esta_no_final:
                    log_area.see(tk.END)
        except Exception as e:
            logger.error(f"Erro ao atualizar logs: {e}")
        root.after(2000, atualizar_logs)

    atualizar_logs()
    return root, resetar_interface, status_label
