import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar, Style
from pdf2docx import Converter
import threading
import os
import shutil
import zipfile

class PDFtoWordConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Suite PDF: Comprimir, Converter em Word e Remover Marca d'Água")
        master.geometry("600x350")
        master.resizable(False, False)

        self.create_widgets()
        self.pdf_files = []
        self.docx_temp_path = None
        self.zip_temp_path = None

        # Suporte a arrastar e soltar
        try:
            self.master.drop_target_register(tk.DND_FILES)
            self.master.dnd_bind('<<Drop>>', self.drop_file)
        except Exception:
            pass

    def create_widgets(self):
        self.label = tk.Label(self.master, text="Selecione PDF(s) ou arraste para converter:")
        self.label.pack(pady=10)

        btn_frame = tk.Frame(self.master)
        btn_frame.pack()

        self.select_button = tk.Button(btn_frame, text="Selecionar PDF", command=self.select_pdf)
        self.select_button.grid(row=0, column=0, padx=5)

        self.folder_button = tk.Button(btn_frame, text="Converter Pasta Inteira", command=self.select_folder)
        self.folder_button.grid(row=0, column=1, padx=5)

        self.compress_button = tk.Button(btn_frame, text="Comprimir Arquivo", command=self.super_comprimir)
        self.compress_button.grid(row=0, column=2, padx=5)

        self.download_zip_button = tk.Button(btn_frame, text="Baixar Comprimido", command=self.baixar_zip)
        self.download_zip_button.grid(row=0, column=3, padx=5)

        # Estilo personalizado para a barra de progresso
        style = Style(self.master)
        style.theme_use('clam')
        style.configure("custom.Horizontal.TProgressbar",
                        troughcolor='#f0f0f0',
                        bordercolor='#d9d9d9',
                        background='#4CAF50',
                        lightcolor='#6fdc6f',
                        darkcolor='#398439',
                        thickness=20)

        self.progress = Progressbar(self.master, orient="horizontal", length=500,
                                    mode="determinate", style="custom.Horizontal.TProgressbar")
        self.progress.pack(pady=20)

        # Barra de status
        self.status = tk.StringVar()
        self.status.set("Aguardando arquivos.")
        self.status_label = tk.Label(self.master, textvariable=self.status)
        self.status_label.pack()

    def select_pdf(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if files:
            self.pdf_files = list(files)
            self.convert_thread()

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.pdf_files = [
                os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".pdf")
            ]
            if self.pdf_files:
                self.convert_thread()
            else:
                messagebox.showinfo("Nenhum PDF", "Não há arquivos PDF na pasta selecionada.")

    def drop_file(self, event):
        files = self.master.tk.splitlist(event.data)
        self.pdf_files = [f for f in files if f.lower().endswith('.pdf')]
        if self.pdf_files:
            self.convert_thread()
        else:
            messagebox.showwarning("Arquivo inválido", "Por favor, arraste apenas arquivos PDF.")

    def convert_thread(self):
        thread = threading.Thread(target=self.convert_files)
        thread.start()

    def animate_progress(self, step=0):
        if step <= 5:
            self.progress["value"] = step * 20
            self.master.after(100, lambda: self.animate_progress(step + 1))

    def convert_files(self):
        total = len(self.pdf_files)
        for idx, pdf in enumerate(self.pdf_files):
            self.status.set(f"Convertendo {os.path.basename(pdf)} ({idx+1}/{total})")
            self.progress["value"] = 0
            self.master.update_idletasks()

            try:
                docx_file = pdf.replace(".pdf", ".docx")
                cv = Converter(pdf)

                self.animate_progress()
                cv.convert(docx_file, start=0, end=None)
                cv.close()

                self.docx_temp_path = docx_file
                self.progress["value"] = 100
                self.master.update_idletasks()

                # Baixar o arquivo convertido
                self.baixar_arquivo(self.docx_temp_path)

            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao converter {os.path.basename(pdf)}:\n{str(e)}")

        self.status.set("Conversão finalizada.")
        messagebox.showinfo("Concluído", f"{total} arquivo(s) convertido(s) com sucesso!")

    def baixar_arquivo(self, docx_temp_path):
        if not os.path.exists(docx_temp_path):
            messagebox.showerror("Erro", "Arquivo temporário não encontrado.")
            return

        destino = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Documentos do Word", "*.docx")],
            title="Salvar arquivo convertido como"
        )

        if destino:
            try:
                shutil.copy(docx_temp_path, destino)
                os.remove(docx_temp_path)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar ou remover arquivo:\n{str(e)}")

    def super_comprimir(self):
        file_to_compress = filedialog.askopenfilename(title="Selecione o arquivo para comprimir")
        if not file_to_compress:
            return

        zip_path = os.path.splitext(file_to_compress)[0] + "_comprimido.zip"
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_to_compress, arcname=os.path.basename(file_to_compress))
            self.zip_temp_path = zip_path
            messagebox.showinfo("Sucesso", "Arquivo comprimido com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao comprimir arquivo:\n{str(e)}")

    def baixar_zip(self):
        if not self.zip_temp_path or not os.path.exists(self.zip_temp_path):
            messagebox.showwarning("Aviso", "Nenhum arquivo comprimido disponível.")
            return

        destino = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("Arquivos ZIP", "*.zip")],
            title="Salvar arquivo comprimido como"
        )

        if destino:
            try:
                shutil.copy(self.zip_temp_path, destino)
                os.remove(self.zip_temp_path)
                messagebox.showinfo("Sucesso", "Arquivo ZIP salvo e removido da pasta temporária.")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao salvar ou apagar o ZIP:\n{str(e)}")

if __name__ == "__main__":
    try:
        import tkinterdnd2 as tkdnd
        class App(tkdnd.TkinterDnD.Tk, PDFtoWordConverterApp): pass
        root = App()
    except ImportError:
        root = tk.Tk()
        app = PDFtoWordConverterApp(root)

    if not isinstance(root, PDFtoWordConverterApp):
        app = PDFtoWordConverterApp(root)
    root.mainloop()
