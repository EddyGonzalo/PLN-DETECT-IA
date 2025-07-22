import sys
import os
import re
from transformers import pipeline

def extract_text_from_docx(path):
    import docx
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])

def extract_text_from_pdf(path):
    import pdfplumber
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

def split_sentences(text):
    # Simple sentence splitter
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

def main():
    if len(sys.argv) != 2:
        print("Uso: python paraphrase_doc.py archivo.docx|archivo.pdf")
        sys.exit(1)
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print("Archivo no encontrado:", file_path)
        sys.exit(1)
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        text = extract_text_from_docx(file_path)
    elif ext == ".pdf":
        text = extract_text_from_pdf(file_path)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        print("Solo se aceptan archivos .docx, .pdf o .txt")
        sys.exit(1)
    print("Cargando pipeline de parafraseo de Hugging Face...")
    pipe = pipeline("text-generation", model="kalpeshk2011/dipper-paraphraser-xxl", max_new_tokens=128)
    print("Parafraseando oraciones...\n")
    sentences = split_sentences(text)
    paraphrased_sentences = []
    for sent in sentences:
        result = pipe(sent)
        para = result[0]['generated_text']
        print(f"Original: {sent}")
        print(f"Parafraseado: {para}\n")
        paraphrased_sentences.append(para)
    # Guardar resultado en archivo
    out_file = "paraphrased_output.txt"
    with open(out_file, "w", encoding="utf-8") as f:
        for para in paraphrased_sentences:
            f.write(para + "\n")
    print(f"\nTexto parafraseado guardado en: {out_file}")

if __name__ == "__main__":
    main()
