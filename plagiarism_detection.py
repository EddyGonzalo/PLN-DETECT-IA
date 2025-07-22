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
        print("Uso: python plagiarism_detection.py archivo.docx|archivo.pdf")
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
    print("Cargando pipeline de Hugging Face para detección de plagio parafraseado...")
    pipe = pipeline("text-classification", model="jpwahle/longformer-base-plagiarism-detection")
    print("Analizando oraciones...\n")
    sentences = split_sentences(text)
    plagio_count = 0
    for sent in sentences:
        result = pipe(sent)[0]
        label = result['label']
        score = result['score']
        print(f"Oración: {sent}")
        print(f"  Predicción: {label} (score={score:.2f})")
        if label.lower() == 'plagiarised':
            plagio_count += 1
    porcentaje = round(plagio_count / len(sentences) * 100, 2) if sentences else 0
    print(f"\nTotal de oraciones: {len(sentences)}")
    print(f"Oraciones detectadas como plagio parafraseado: {plagio_count}")
    print(f"Porcentaje de oraciones con plagio parafraseado: {porcentaje}%")

if __name__ == "__main__":
    main()
