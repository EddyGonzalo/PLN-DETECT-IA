import sys
import os
import re
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

def contiene_cita_apa(oracion):
    # Patrón para el nombre de autor/organización (permite múltiples palabras, guiones, puntos, acentos)
    single_author_name_pattern = r'[A-ZÀ-Ÿ][a-zA-Zà-ÿ\s\.-]*'

    # Patrón para el año (4 dígitos, opcionalmente con letra como 2020a, o 'n.d.')
    year_pattern = r'\d{4}[a-z]?|n\.d\.'

    # Patrones para citas parentéticas (e.g., (Autor, Año), (Autor & Autor, Año), (Autor et al., Año))
    parenthetical_authors_years_pattern = rf"""
        \(                                             # Paréntesis de apertura
        (?:                                             # Inicio de grupo no capturador para lista de autores
            {single_author_name_pattern}                # Primer autor
            (?:,\s*{single_author_name_pattern})*       # Autores subsiguientes separados por coma y espacio
            (?:                                         # Opcional " and " o " & " antes del último autor
                \s*(?:&|and)\s*{single_author_name_pattern}
            )?
            |                                           # O, para casos de "et al." (APA 7ma para 3+ autores)
            {single_author_name_pattern}\s+et al\.      # Autor et al.
        )
        ,\s*                                            # Coma y espacio antes del año/n.d.
        (?:                                             # Inicio de grupo no capturador para año/n.d.
            {year_pattern}
        )
        \)                                             # Paréntesis de cierre
    """

    # Patrones para citas narrativas (e.g., Autor (Año), Autor et al. (Año))
    narrative_authors_years_pattern = rf"""
        {single_author_name_pattern}                    # Nombre del autor
        (?:                                             # Opcional "et al."
            \s+et al\.
        )?
        \s*                                            # Espacio opcional antes del año
        \(                                             # Paréntesis de apertura para el año
        {year_pattern}                                  # Año
        \)                                             # Paréntesis de cierre
    """

    # Combina ambos patrones principales con OR, usando re.VERBOSE para legibilidad y re.IGNORECASE para insensibilidad a mayúsculas/minúsculas
    apa_regex = re.compile(
        rf'{parenthetical_authors_years_pattern}|{narrative_authors_years_pattern}',
        re.VERBOSE | re.IGNORECASE
    )

    return bool(apa_regex.search(oracion))

def parece_cita_sin_apa(oracion):
    marcadores = [
        "según", "de acuerdo con", "como señala", "como afirma", "en palabras de",
        "tal como indica", "como sostiene"
    ]
    return any(m in oracion.lower() for m in marcadores) and not contiene_cita_apa(oracion)

def main():
    if len(sys.argv) != 2:
        print("Uso: python detect_apa_citations.py archivo.docx|archivo.pdf|archivo.txt")
        sys.exit(1)
    file_path = sys.argv[1]
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".docx":
        import docx
        doc = docx.Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    elif ext == ".pdf":
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        print("Solo se aceptan archivos .docx, .pdf o .txt")
        sys.exit(1)
    sentences = split_sentences(text)
    bien_citadas = []
    sospechosas = []
    for idx, sent in enumerate(sentences):
        if contiene_cita_apa(sent):
            bien_citadas.append(idx)
        elif parece_cita_sin_apa(sent):
            sospechosas.append(idx)
    print(f"TOTAL:{len(sentences)}")
    print(f"BIEN:{','.join(map(str, bien_citadas))}")
    print(f"SOSPECHOSAS:{','.join(map(str, sospechosas))}")

if __name__ == "__main__":
    main()
