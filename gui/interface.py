from utils import logger

import tkinter as tk
from tkinter import messagebox


def iniciar_interface():
    try:
        credenciais = {}
        indices = []

        def confirmar():
            try:
                credenciais["usuario"] = entry_usuario.get()
                credenciais["senha"] = entry_senha.get()
                lista = entry_indices.get().split(",")
                indices.extend([i.strip() for i in lista if i.strip() != ""])

                if not credenciais["usuario"] or not credenciais["senha"]:
                    raise ValueError("Usuário e senha são obrigatórios")

                if not indices:
                    raise ValueError("Informe ao menos um índice")

                root.destroy()
            except Exception as e:
                logger.error(f"Erro na interface ao confirmar: {e}")
                messagebox.showerror("Erro", str(e))

        root = tk.Tk()
        root.title("Triagem de Estagiários")

        tk.Label(root, text="Usuário:").grid(row=0, column=0)
        entry_usuario = tk.Entry(root)
        entry_usuario.grid(row=0, column=1)

        tk.Label(root, text="Senha:").grid(row=1, column=0)
        entry_senha = tk.Entry(root, show="*")
        entry_senha.grid(row=1, column=1)

        tk.Label(root, text="Índices (separados por vírgula):").grid(row=2, column=0)
        entry_indices = tk.Entry(root, width=40)
        entry_indices.grid(row=2, column=1)

        tk.Button(root, text="Confirmar", command=confirmar).grid(
            row=3, column=0, columnspan=2
        )

        root.mainloop()
        return credenciais, indices
    except Exception as e:
        logger.error(f"Erro crítico na interface: {e}")
        raise
