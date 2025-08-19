import customtkinter as ctk
import sqlite3
import tkinter as tk
from tkinter import messagebox

# Layout
PALETA = {
    "fundo": "#190B09",
    "input": "#CAA495",
    "botao": "#AC755C",
    "botao_hover": "#794734",
    "texto": "#45251B",
}

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("green")

# Banco de Dados
con = sqlite3.connect("despesas.db")
cur = con.cursor()
cur.execute("""
    CREATE TABLE IF NOT EXISTS transacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        descricao TEXT,
        valor REAL
    )
""")
con.commit()

# Variável para controlar edição
transacao_editando = None

# Funções 
def atualizar_saldo():
    cur.execute("SELECT SUM(valor) FROM transacoes")
    total = cur.fetchone()[0]
    total = total if total else 0
    saldo_label.configure(
        text=f"Saldo: R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
        text_color="green" if total >= 0 else "red"
    )

def carregar_transacoes():
    lista.delete(0, "end")
    cur.execute("SELECT * FROM transacoes ORDER BY id DESC")
    for row in cur.fetchall():
        lista.insert("end", f"{row[0]} - {row[1]} | {row[2]}: R$ {row[3]:,.2f}"
                     .replace(",", "X").replace(".", ",").replace("X", "."))

def limpar_campos():
    """Limpa todos os campos e sai do modo edição"""
    global transacao_editando
    desc_entry.delete(0, "end")
    valor_entry.delete(0, "end")
    tipo_var.set("Receita")
    lista.selection_clear(0, "end")
    transacao_editando = None
    botao_adicionar.configure(text="Adicionar")

def ao_selecionar_item(event):
    """Função chamada quando um item da lista é selecionado"""
    global transacao_editando
    
    selecao = lista.curselection()
    if not selecao:
        return
    
    try:
        item = lista.get(selecao[0])
        # Formato: "ID - TIPO | DESCRIÇÃO: R$ VALOR"
        partes = item.split(" | ")
        transacao_id = int(partes[0].split(" - ")[0])
        tipo_info = partes[0].split(" - ")[1]  # Pega o TIPO
        desc_valor = partes[1].split(": R$ ")
        descricao = desc_valor[0]  # Pega a DESCRIÇÃO
        valor_texto = desc_valor[1].replace(".", "").replace(",", ".")  # Converte o valor
        
        # Preenche os campos
        tipo_var.set(tipo_info)
        desc_entry.delete(0, "end")
        desc_entry.insert(0, descricao)
        valor_entry.delete(0, "end")
        # Remove o sinal negativo para despesas na exibição
        valor_numerico = abs(float(valor_texto))
        valor_entry.insert(0, f"{valor_numerico:.2f}".replace(".", ","))
        
        # Entra no modo edição
        transacao_editando = transacao_id
        botao_adicionar.configure(text="Atualizar")
        
    except:
        pass  # Ignora erros de parsing

def adicionar_ou_atualizar_transacao():
    global transacao_editando
    
    tipo = tipo_var.get()
    desc = desc_entry.get()
    try:
        valor = float(valor_entry.get().replace(",", "."))
    except ValueError:
        messagebox.showerror("Erro", "Digite um valor numérico válido.")
        return
    
    if tipo == "Despesa":
        valor = -abs(valor)
    else:
        valor = abs(valor)

    if transacao_editando:
        # Atualizar transação existente
        cur.execute("UPDATE transacoes SET tipo=?, descricao=?, valor=? WHERE id=?", 
                    (tipo, desc, valor, transacao_editando))
        con.commit()
        messagebox.showinfo("Sucesso", "Transação atualizada com sucesso!")
    else:
        # Adicionar nova transação
        cur.execute("INSERT INTO transacoes (tipo, descricao, valor) VALUES (?, ?, ?)", 
                    (tipo, desc, valor))
        con.commit()
        messagebox.showinfo("Sucesso", "Transação adicionada com sucesso!")
    
    limpar_campos()
    carregar_transacoes()
    atualizar_saldo()

def excluir_transacao():
    selecao = lista.curselection()
    if not selecao:
        messagebox.showwarning("Aviso", "Selecione uma transação para excluir.")
        return
    
    resposta = messagebox.askyesno("Confirmar", "Tem certeza que deseja excluir esta transação?")
    if not resposta:
        return
        
    item = lista.get(selecao[0])
    transacao_id = int(item.split(" - ")[0])
    cur.execute("DELETE FROM transacoes WHERE id=?", (transacao_id,))
    con.commit()
    messagebox.showinfo("Sucesso", "Transação excluída com sucesso!")
    
    limpar_campos()
    carregar_transacoes()
    atualizar_saldo()

def atualizar():
    """Função para atualizar a lista e o saldo"""
    limpar_campos()
    carregar_transacoes()
    atualizar_saldo()

# Interface 
root = ctk.CTk()
root.title("💰 Gerenciador de Despesas")
root.geometry("600x600")
root.configure(fg_color=PALETA["fundo"])

# Frame superior - saldo
saldo_label = ctk.CTkLabel(root, text="Saldo: R$ 0,00", font=("Times New Roman", 22, "bold"))
saldo_label.pack(pady=10)

# Frame de inputs
frame_inputs = ctk.CTkFrame(root, fg_color=PALETA["input"], corner_radius=12)
frame_inputs.pack(pady=10, padx=20)

tipo_var = ctk.StringVar(value="Receita")
ctk.CTkRadioButton(frame_inputs, text="Receita", variable=tipo_var, value="Receita",
                   fg_color=PALETA["botao"], hover_color=PALETA["botao_hover"]).grid(row=0, column=0, padx=10, pady=10)
ctk.CTkRadioButton(frame_inputs, text="Despesa", variable=tipo_var, value="Despesa",
                   fg_color=PALETA["botao"], hover_color=PALETA["botao_hover"]).grid(row=0, column=1, padx=10, pady=10)

desc_entry = ctk.CTkEntry(frame_inputs, placeholder_text="Descrição", width=200)
desc_entry.grid(row=1, column=0, padx=10, pady=10)
valor_entry = ctk.CTkEntry(frame_inputs, placeholder_text="Valor (R$)", width=150)
valor_entry.grid(row=1, column=1, padx=10, pady=10)

botao_adicionar = ctk.CTkButton(frame_inputs, text="Adicionar", command=adicionar_ou_atualizar_transacao,
                               fg_color=PALETA["botao"], hover_color=PALETA["botao_hover"])
botao_adicionar.grid(row=2, column=0, pady=10, padx=5)

ctk.CTkButton(frame_inputs, text="Limpar", command=limpar_campos,
              fg_color=PALETA["botao"], hover_color=PALETA["botao_hover"]).grid(row=2, column=1, pady=10, padx=5)

# Lista de transações (tkinter.Listbox)
lista = tk.Listbox(root, width=80, height=12, bg=PALETA["input"], fg=PALETA["texto"],
                   font=("Times New Roman", 18), selectbackground=PALETA["botao_hover"])
lista.pack(pady=10)
lista.bind("<<ListboxSelect>>", ao_selecionar_item)

# Frame para botões inferiores
frame_botoes = ctk.CTkFrame(root, fg_color="transparent")
frame_botoes.pack(pady=10)

# Botão excluir
ctk.CTkButton(frame_botoes, text="Excluir Selecionado", command=excluir_transacao,
              fg_color=PALETA["botao"], hover_color=PALETA["botao_hover"]).pack(pady=5)

# Inicialização
carregar_transacoes()
atualizar_saldo()

root.mainloop()