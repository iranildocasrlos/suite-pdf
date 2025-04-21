import streamlit as st
import os
import zipfile
import fitz  # PyMuPDF
from PIL import Image
from pdf2docx import Converter
import io
import pandas as pd
import re
import requests
from streamlit_lottie import st_lottie
import time





 # Lista de verificações virus PDF
# Função para verificar conteúdo do PDF (scripts, anexos, objetos)
def verificar_malware_em_pdf(caminho_pdf):
    resultado = {
        "scripts_encontrados": [],
        "anexos_suspeitos": [],
        "obj_suspeitos": [],
        "acoes_automaticas": [],
        "urls_detectadas": [],
    }

    doc = fitz.open(caminho_pdf)

    for page in doc:
        # Verificar URLs
        links = page.get_links()
        for link in links:
            if "uri" in link:
                resultado["urls_detectadas"].append(link["uri"])

    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text("text")
        if "/JS" in text or "/JavaScript" in text:
            resultado["scripts_encontrados"].append(f"Script JavaScript encontrado na página {i+1}")

    # Verificar ações automáticas
    if "OpenAction" in doc.metadata or "/AA" in doc.metadata:
        resultado["acoes_automaticas"].append("Ação automática detectada ao abrir o PDF")

    # Verificar objetos suspeitos
    for obj in doc:
        if isinstance(obj, fitz.Page):
            continue
        obj_str = str(obj)
        if any(palavra in obj_str for palavra in ["Launch", "EmbeddedFiles", "/AA", "/JS", "JavaScript"]):
            resultado["obj_suspeitos"].append(f"Objeto suspeito: {obj_str[:100]}...")

    return resultado


# Função para descrever o que foi encontrado
def descrever_item(item, tipo):
    if tipo == "scripts":
        return f"Script encontrado: {item}. Pode ser um script que tenta explorar vulnerabilidades conhecidas para executar código arbitrário ou roubar informações."
    elif tipo == "anexos":
        return f"Anexo encontrado: {item}. Anexos podem conter executáveis disfarçados ou arquivos maliciosos que tentam ser executados automaticamente."
    elif tipo == "objetos":
        return f"Objeto suspeito encontrado: {item}. Isso pode ser um objeto PDF embutido que tenta realizar ações inesperadas ou contém código malicioso."
    return "Descrição não disponível."



#animação de metadados
def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()


def incrementar_contador(nome_arquivo):
    if not os.path.exists(nome_arquivo):
        with open(nome_arquivo, "w") as f:
            f.write("0")
    with open(nome_arquivo, "r+") as f:
        valor = int(f.read())
        valor += 1
        f.seek(0)
        f.write(str(valor))
        f.truncate()
    return valor



# Aplica tema escuro e estilo
st.set_page_config(page_title="Suite PDF", layout="wide")

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

st.title("🧰 Suite PDF - Comprimir, Converter em Word e Remover Marca d'Água, segurança e muito mais")

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


# Função para carregar animação Lottie
def load_lottieurl(url: str):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        return None






# --- Abas ---


aba = st.tabs(["📄 PDF para Word", "💧 Remover Marca d'Água", "🗜️ Comprimir Arquivo", "🔍 Ler Metadados do PDF","🛡️ Verificar PDF Malicioso"])




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

             # Mostra contador
        total = incrementar_contador("contador.txt")
        st.info(f"📊 Total de conversões já realizadas: {total}")

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

             # Mostra contador
        total = incrementar_contador("contador.txt")
        st.info(f"📊 Total de conversões já realizadas: {total}")

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

             # Mostra contador
        total = incrementar_contador("contador.txt")
        st.info(f"📊 Total de conversões já realizadas: {total}")


# --- Aba 4: Metadados do PDF ---
# --- Aba 4: Metadados do PDF ---
with aba[3]:

    st.header("📋 Ler Metadados do PDF")
    
    uploaded_meta_pdf = st.file_uploader("Envie um PDF para extrair metadados", type="pdf", key="metadata")

    if uploaded_meta_pdf:

         # 🔄 Exibe animação enquanto processa
        lottie_url = "https://assets1.lottiefiles.com/packages/lf20_3ntisyac.json"
        lottie_animation = load_lottie_url(lottie_url)
        with st.spinner("Lendo metadados do PDF..."):
            if lottie_animation:
                st_lottie(lottie_animation, height=200)
    
    # Aqui entra sua lógica de leitura de metadados
        with st.spinner("Lendo metadados..."):
            with open("meta_temp.pdf", "wb") as f:
                f.write(uploaded_meta_pdf.read())

            doc = fitz.open("meta_temp.pdf")
            info = doc.metadata

            # Tentativa robusta de identificação do autor
            autor = info.get("author") or info.get("Author") or "Não encontrado"

            # Busca por possíveis coordenadas (latitude/longitude) no conteúdo
            lat_lon = None
            for page in doc:
                text = page.get_text()
                matches = re.findall(r"([-+]?\d{1,2}\.\d+)[, ]+([-+]?\d{1,3}\.\d+)", text)
                for lat, lon in matches:
                    try:
                        lat_f, lon_f = float(lat), float(lon)
                        if -90 <= lat_f <= 90 and -180 <= lon_f <= 180:
                            lat_lon = (lat_f, lon_f)
                            break
                    except:
                        continue
                if lat_lon:
                    break

            info_extra = {
                "Autor (detectado)": autor,
                "Número de páginas": doc.page_count,
                "Permissões": doc.permissions,
                "Protegido com senha": doc.is_encrypted,
                "Tamanho do arquivo (bytes)": os.path.getsize("meta_temp.pdf"),
                "Tem anotações": any(p.annots() for p in doc),
                "Tem formulários": any(p.widgets() for p in doc),
                "Fontes usadas": list(set(font[3] for page in doc for font in page.get_fonts(full=True))),
            }

            if lat_lon:
                coord_str = f"{lat_lon[0]}, {lat_lon[1]}"
                maps_url = f"https://www.google.com/maps?q={coord_str}"
                info_extra["Coordenadas detectadas (Lat, Lon)"] = f"[{coord_str}]({maps_url})"
            else:
                info_extra["Coordenadas detectadas (Lat, Lon)"] = "Não encontrado"

            # Combinar metadados principais e extras
            all_metadata = {**info, **info_extra}

            # Mostrar no app
            st.subheader("Metadados Detalhados")
            for chave, valor in all_metadata.items():
                st.markdown(f"**{chave}:** {valor}")

            # Exportar CSV
            df_meta = pd.DataFrame(list(all_metadata.items()), columns=["Campo", "Valor"])
            csv_bytes = df_meta.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Baixar Metadados (.csv)", data=csv_bytes, file_name="metadados.csv", mime="text/csv")

            doc.close()
            os.remove("meta_temp.pdf")



# --- Aba: Verificar PDF Malicioso ---
with aba[4]:  # Verificar PDF Malicioso
    st.header("🛡️ Verificar PDF Malicioso")
    pdf_suspeito = st.file_uploader("Faça upload de um PDF para análise", type="pdf", key="malware_pdf")

    if pdf_suspeito:
        with st.spinner("Analisando o documento..."):
            with open("pdf_check.pdf", "wb") as f:
                f.write(pdf_suspeito.read())

            total_testes = 5
            progresso_geral = st.progress(0)
            progresso_por_teste = 1 / total_testes

            resultado = {
                "scripts_encontrados": [],
                "anexos_suspeitos": [],
                "obj_suspeitos": [],
                "acoes_automaticas": [],
                "urls_detectadas": [],
            }

            doc = fitz.open("pdf_check.pdf")

            # 1. Verificar JavaScript embutido
            st.markdown("🔍 Verificando scripts embutidos (JavaScript)...")
            st.markdown("**Explicação:** O PDF pode conter scripts JavaScript embutidos que podem ser usados para executar código malicioso no computador do usuário.")
            barra1 = st.progress(0)
            for i in range(len(doc)):
                page = doc[i]
                text = page.get_text("text")  # Alterado de "raw" para "text"
                if "/JS" in text or "/JavaScript" in text:
                    resultado["scripts_encontrados"].append(f"Script JavaScript encontrado na página {i+1}")
            barra1.progress(100)
            progresso_geral.progress(progresso_por_teste)

            # 2. Verificar objetos com ações automáticas
            st.markdown("🔍 Verificando ações automáticas (OpenAction, /AA)...")
            st.markdown("**Explicação:** Alguns PDFs podem ter ações automáticas configuradas, como scripts que são executados quando o PDF é aberto.")
            barra2 = st.progress(0)
            if "OpenAction" in doc.metadata or "/AA" in str(doc.metadata):
                resultado["acoes_automaticas"].append("Ação automática detectada ao abrir o PDF")
            barra2.progress(100)
            progresso_geral.progress(progresso_por_teste * 2)

            # 3. Verificar URLs embutidas
            st.markdown("🔍 Verificando links externos (URLs)...")
            st.markdown("**Explicação:** PDFs podem conter links externos que redirecionam o usuário para sites maliciosos.")
            barra3 = st.progress(0)
            for page in doc:
                links = page.get_links()
                for link in links:
                    if "uri" in link:
                        resultado["urls_detectadas"].append(link["uri"])
            barra3.progress(100)
            progresso_geral.progress(progresso_por_teste * 3)

            # 4. Verificar anexos suspeitos
            st.markdown("🔍 Verificando anexos suspeitos...")
            st.markdown("**Explicação:** PDFs podem ter arquivos anexados, que podem ser executáveis ou disfarçados como outros tipos de arquivos maliciosos.")
            barra4 = st.progress(0)
            for i in range(len(doc)):
                anexos = doc[i].get_text("text")  # Alterado de "raw" para "text"
                if "EmbeddedFile" in anexos:
                    resultado["anexos_suspeitos"].append(f"Anexo suspeito na página {i+1}")
            barra4.progress(100)
            progresso_geral.progress(progresso_por_teste * 4)

            # 5. Verificar objetos suspeitos
            st.markdown("🔍 Verificando objetos suspeitos (Launch, EmbeddedFiles)...")
            st.markdown("**Explicação:** Objetos maliciosos podem estar embutidos no PDF, como arquivos executáveis ou links que podem ser usados para explorar vulnerabilidades.")
            barra5 = st.progress(0)
            for page in doc:
                texto = page.get_text("text")  # Alterado de "raw" para "text"
                if any(palavra in texto for palavra in ["Launch", "EmbeddedFiles", "/AA", "/JS", "JavaScript"]):
                    resultado["obj_suspeitos"].append(f"Objeto suspeito detectado na página {page.number + 1}")
            barra5.progress(100)
            progresso_geral.progress(1.0)

            doc.close()
            os.remove("pdf_check.pdf")

        # Exibição dos resultados
        st.subheader("🔍 Resultado da Análise:")

        def exibir_lista_com_icone(lista, titulo, risco="baixo"):
            if risco == "alto":
                cor = "🔴"
            elif risco == "médio":
                cor = "🟡"
            else:
                cor = "🟢"

            if lista:
                st.markdown(f"{cor} **{titulo}**")
                for item in lista:
                    st.write(f"• {item}")
            else:
                st.markdown(f"🟢 Nenhum {titulo.lower()} encontrado.")

        # Exibir resultados com ícones
        exibir_lista_com_icone(resultado["scripts_encontrados"], "Scripts encontrados", "alto")
        exibir_lista_com_icone(resultado["acoes_automaticas"], "Ações automáticas", "médio")
        exibir_lista_com_icone(resultado["urls_detectadas"], "Links externos detectados", "médio")
        exibir_lista_com_icone(resultado["anexos_suspeitos"], "Anexos suspeitos", "alto")
        exibir_lista_com_icone(resultado["obj_suspeitos"], "Objetos suspeitos", "médio")

