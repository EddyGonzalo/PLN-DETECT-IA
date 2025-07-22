from flask import Flask, render_template, request
import subprocess
import tempfile
import os
import re

app = Flask(__name__)

# Nombres de tus scripts
SCRIPTS = {
    'ia': 'detect_ia_percentage.py',
    'paraphrase': 'paraphrase_doc.py',
    'plagiarism': 'plagiarism_detection.py',
    'apa': 'detect_apa_citations.py'
}

def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = ""
    texto = ""
    opcion = ""
    oraciones_resaltadas = []
    ia_predictions_html = ""
    ia_summary_html = ""
    ia_percentage = 0.0

    if request.method == 'POST':
        texto = request.form['texto']
        opcion = request.form['opcion']
        # Guardar el texto en un archivo temporal .txt
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tmp:
            tmp.write(texto)
            tmp_path = tmp.name
        # Llamar al script correspondiente
        script = SCRIPTS.get(opcion)
        if script:
            try:
                result = subprocess.run(
                    ["python", script, tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=1800  # 10 minutos máximo, por si el modelo es grande
                )
                salida = result.stdout if result.returncode == 0 else result.stderr

                if opcion == 'ia':
                    # Procesar la salida para Detección de IA
                    predictions = []
                    summary_lines = []
                    current_ia_percentage = 0.0
                    for line in salida.splitlines():
                        if line.startswith("Oración:") or line.startswith("  Predicción:"):
                            if line.startswith("Oración:"):
                                predictions.append(f"<p><strong>{line}</strong></p>")
                            else:
                                predictions.append(f"<p style=\"margin-left: 20px;\">{line}</p>")
                        elif line.startswith("Total de oraciones:") or \
                             line.startswith("Oraciones detectadas como IA:"):
                            summary_lines.append(f"<p>{line}</p>")
                        elif line.startswith("Porcentaje de texto generado por IA:"):
                            summary_lines.append(f"<p>{line}</p>")
                            match = re.search(r'Porcentaje de texto generado por IA: (\d+(\.\d+)?)%', line)
                            if match: 
                                current_ia_percentage = float(match.group(1))

                    ia_predictions_html = "".join(predictions)
                    ia_summary_html = "".join(summary_lines)
                    ia_percentage = current_ia_percentage
                    resultado = "" # Limpiar resultado para que no se duplique

                elif opcion == 'paraphrase':
                    # Procesar la salida para Parafraseo
                    formatted_output = []
                    for line in salida.splitlines():
                        if line.startswith("Original:"):
                            formatted_output.append(f"<p><strong>{line}</strong></p>")
                        elif line.startswith("Parafraseado:"):
                            formatted_output.append(f"<p style=\"margin-left: 20px;\">{line}</p>")
                        elif line.startswith("Texto parafraseado guardado en:"):
                            formatted_output.append(f"<p style=\"margin-top: 1em; font-style: italic;\">{line}</p>")
                    resultado = "".join(formatted_output)

                elif opcion == 'plagiarism':
                    # Procesar la salida para Detección de Plagio
                    formatted_output = []
                    summary_line = ""
                    for line in salida.splitlines():
                        if line.startswith("Oración:"):
                            formatted_output.append(f"<p><strong>{line}</strong></p>")
                        elif line.startswith("  Predicción:"):
                            formatted_output.append(f"<p style=\"margin-left: 20px;\">{line}</p>")
                        elif line.startswith("Total de oraciones:") or \
                             line.startswith("Oraciones detectadas como plagio parafraseado:") or \
                             line.startswith("Porcentaje de oraciones con plagio parafraseado:"):
                            summary_line += f"<p>{line}</p>"
                    resultado = "".join(formatted_output) + summary_line

                elif opcion == 'apa':
                    # El procesamiento de APA ya es especial, pero asegurar el formato de resultado
                    total = 0
                    bien = []
                    sospechosas = []
                    for line in salida.splitlines():
                        if line.startswith("TOTAL:"):
                            total = int(line.split(":")[1])
                        elif line.startswith("BIEN:"):
                            bien = [int(i) for i in line.split(":")[1].split(",") if i]
                        elif line.startswith("SOSPECHOSAS:"):
                            sospechosas = [int(i) for i in line.split(":")[1].split(",") if i]
                    sentences = split_sentences(texto)
                    oraciones_resaltadas = []
                    for idx, sent in enumerate(sentences):
                        if idx in bien:
                            oraciones_resaltadas.append({'texto': sent, 'clase': 'resaltado-apa-bien'})
                        elif idx in sospechosas:
                            oraciones_resaltadas.append({'texto': sent, 'clase': 'resaltado-apa-sospechosa'})
                        else:
                            oraciones_resaltadas.append({'texto': sent, 'clase': ''})
                    resultado = f"<p><strong>Total de oraciones:</strong> {total}</p>" \
                                f"<p><strong>Oraciones bien citadas (APA):</strong> {len(bien)}</p>" \
                                f"<p><strong>Oraciones sospechosas sin referencia APA:</strong> {len(sospechosas)}</p>"
                else:
                    resultado = salida # Fallback para cualquier otra opción inesperada

            except Exception as e:
                resultado = f"<p style=\"color: red;\">Error al ejecutar el script: {e}</p>"
        else:
            resultado = "<p style=\"color: red;\">Opción no válida.</p>"
        # Eliminar el archivo temporal
        try:
            os.remove(tmp_path)
        except Exception:
            pass
    return render_template('index.html', resultado=resultado, texto=texto, opcion=opcion, oraciones_resaltadas=oraciones_resaltadas, request_method=request.method, ia_predictions_html=ia_predictions_html, ia_summary_html=ia_summary_html, ia_percentage=ia_percentage)

if __name__ == '__main__':
    app.run(debug=True)
