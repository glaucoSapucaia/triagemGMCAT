from utils import logger
import tkinter as tk
from tkinter import messagebox


def iniciar_interface():
    try:
        credenciais = {}
        protocolos = []

        def confirmar():
            try:
                credenciais["usuario"] = entry_usuario.get()
                credenciais["senha"] = entry_senha.get()
                credenciais["usuario_sigede"] = entry_usuario_sigede.get()
                credenciais["senha_sigede"] = entry_senha_sigede.get()
                lista = entry_protocolos.get().split(",")
                protocolos.extend([i.strip() for i in lista if i.strip() != ""])

                # Validações básicas
                if not credenciais["usuario"] or not credenciais["senha"]:
                    raise ValueError("Usuário e senha do SIATU são obrigatórios")

                if not credenciais["usuario_sigede"] or not credenciais["senha_sigede"]:
                    raise ValueError("Usuário e senha do SIGEDE são obrigatórios")

                if not protocolos:
                    raise ValueError("Informe ao menos um protocolo.")

                root.destroy()
            except Exception as e:
                logger.error(f"Erro na interface ao confirmar: {e}")
                messagebox.showerror("Erro", str(e))

        root = tk.Tk()
        root.title("Triagem de Processos")

        # Credenciais SIGEDE
        tk.Label(root, text="Usuário SIGEDE:").grid(row=0, column=0)
        entry_usuario_sigede = tk.Entry(root)
        entry_usuario_sigede.grid(row=0, column=1)

        tk.Label(root, text="Senha SIGEDE:").grid(row=1, column=0)
        entry_senha_sigede = tk.Entry(root, show="*")
        entry_senha_sigede.grid(row=1, column=1)

        # Credenciais principais
        tk.Label(root, text="Usuário SIATU:").grid(row=2, column=0)
        entry_usuario = tk.Entry(root)
        entry_usuario.grid(row=2, column=1)

        tk.Label(root, text="Senha SIATU:").grid(row=3, column=0)
        entry_senha = tk.Entry(root, show="*")
        entry_senha.grid(row=3, column=1)

        # Protocolo(s)
        tk.Label(root, text="Protocolo(s) (separados por vírgula):").grid(
            row=4, column=0
        )
        entry_protocolos = tk.Entry(root, width=40)
        entry_protocolos.grid(row=4, column=1)

        tk.Button(root, text="Confirmar", command=confirmar).grid(
            row=5, column=0, columnspan=2
        )

        root.mainloop()
        return credenciais, protocolos
    except Exception as e:
        logger.error(f"Erro crítico na interface: {e}")
        raise
