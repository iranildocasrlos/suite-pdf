import streamlit as st
import os
import zipfile
import fitz  # PyMuPDF
from PIL import Image
from pdf2docx import Converter
import io

# Aplica tema escuro e estilo
st.set_page_config(page_title="Suite PDF", layout="centered")

st.markdown("""
    <style>
    body {
        color: white;
        background-color: #0e1117;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 10px 24px;
    }
    .stProgress > div > div > div > div {
        background-color: #4CAF50;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🧰 Suite PDF - Comprimir, Converter em Word e Remover Marca d'Água")

# --- Funções auxiliares ---
def converter_pdf_para_word(pdf_path, output_path):
    

    cv = Converter(pdf_path)
    cv.convert(output_path, start=0, end=None)
    cv.close()

def remover_marca_dagua(pdf_path, output_path, texto="Exemplo de Marca D'água"):
    doc = fitz.open(pdf_path)
    for page in doc:
        for img in page.get_images(full=True):
            xref = img[0]
            page.delete_image(xref)
        for inst in page.search_for(texto):
            page.delete_text(inst)
    doc.save(output_path)

def comprimir_pdf(pdf_path):
    output_path = os.path.splitext(pdf_path)[0] + "_comprimido.pdf"
    doc = fitz.open(pdf_path)

    # Otimização das imagens
    for page in doc:
        images = page.get_images(full=True)
        for img in images:
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image_pil = Image.open(io.BytesIO(image_bytes))
                image_pil = image_pil.convert("RGB")
                
                # Salva a imagem com compressão para reduzir o tamanho
                buffer = io.BytesIO()
                image_pil.save(buffer, format="JPEG", quality=50)  # Aumente a compressão ajustando o valor de qualidade
                new_image_bytes = buffer.getvalue()
                
                # Atualiza a imagem no PDF
                doc.update_image(xref, new_image_bytes)
            except Exception as e:
                continue

    # Salva o documento comprimido
    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return output_path

def criar_zip_com_pdf(pdf_path):
    zip_path = os.path.splitext(pdf_path)[0] + "_comprimido.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(pdf_path, arcname=os.path.basename(pdf_path))
    return zip_path

# --- Abas ---
aba = st.tabs(["📄 PDF para Word", "💧 Remover Marca d'Água", "🗜️ Comprimir Arquivo"])

# --- Aba 1: PDF para Word ---
with aba[0]:
    st.header("📄 Converter PDF para Word")
    uploaded_pdf = st.file_uploader("Faça upload de um arquivo PDF", type="pdf")
    if uploaded_pdf:
        with st.spinner("Convertendo PDF para DOCX..."):
            with open("temp.pdf", "wb") as f:
                f.write(uploaded_pdf.read())
            converter_pdf_para_word("temp.pdf", "output.docx")
            st.success("Conversão concluída!")
            with open("output.docx", "rb") as f:
                st.download_button("📥 Baixar Word", f, file_name="convertido.docx")
            os.remove("temp.pdf")
            os.remove("output.docx")

# --- Aba 2: Remover Marca d'Água ---
with aba[1]:
    st.header("💧 Remover Marca d'Água")
    uploaded_watermark_pdf = st.file_uploader("Upload do PDF com marca d'água", type="pdf", key="watermark")
    watermark_text = st.text_input("Texto da marca d'água para remover", "Exemplo de Marca D'água")

    if uploaded_watermark_pdf and watermark_text:
        with st.spinner("Removendo marca d'água..."):
            with open("marca.pdf", "wb") as f:
                f.write(uploaded_watermark_pdf.read())
            remover_marca_dagua("marca.pdf", "sem_marca.pdf", watermark_text)
            st.success("Marca d'água removida com sucesso!")
            with open("sem_marca.pdf", "rb") as f:
                st.download_button("📥 Baixar PDF sem marca", f, file_name="sem_marca.pdf")
            os.remove("marca.pdf")
            os.remove("sem_marca.pdf")

# --- Aba 3: Comprimir Arquivo ---
with aba[2]:
    st.header("🗜️ Comprimir Arquivo (ZIP)")
    file_to_compress = st.file_uploader("Upload de um PDF", type=["pdf"], key="zipper")

    if file_to_compress:
        with st.spinner("Comprimindo PDF com otimização de imagens..."):
            with open("temp_input.pdf", "wb") as f:
                f.write(file_to_compress.read())
            # Comprimir o PDF
            pdf_comprimido = comprimir_pdf("temp_input.pdf")
            # Criar arquivo ZIP contendo o PDF comprimido
            zip_file = criar_zip_com_pdf(pdf_comprimido)
            st.success("PDF comprimido e arquivo ZIP gerado com sucesso!")
            with open(zip_file, "rb") as f:
                st.download_button("📥 Baixar ZIP", f, file_name=os.path.basename(zip_file))
            os.remove("temp_input.pdf")
            os.remove(pdf_comprimido)
            os.remove(zip_file)
