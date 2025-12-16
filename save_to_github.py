
import os
import json
from flask import Flask, request, jsonify, Response
from github import Github
from datetime import datetime

# Configuración
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = 'iosugomez/kotxea-backend'
DATA_PATH = 'datos/datos.json'
CSV_VIAJES_PATH = 'datos/viajes.csv'
CSV_DINERO_PATH = 'datos/dinero.csv'

app = Flask(__name__)

def get_github_repo():
    g = Github(GITHUB_TOKEN)
    repo = g.get_repo(REPO_NAME)
    return repo

def generar_csv_viajes(registros):
    # Calcula saldos y genera CSV de viajes
    participantes = ['Iosu', 'Lide', 'Asier', 'Itziar']
    saldos = {p: 0 for p in participantes}
    for reg in registros:
        total = len(reg['pasajeros']) + 1
        c = 1 / total
        saldos[reg['conductor']] += (1 - c)
        for p in reg['pasajeros']:
            saldos[p] -= c
    csv = 'Persona,Balance\n'
    for p, s in sorted(saldos.items(), key=lambda x: x[1]):
        csv += f'{p},{s:.3f}\n'
    csv += '\nFecha,Conductor,Pasajeros,Número de Pasajeros\n'
    for reg in registros:
        csv += f"{reg['fecha']},{reg['conductor']},\"{'|'.join(reg['pasajeros'])}\",{len(reg['pasajeros'])}\n"
    return csv

def generar_csv_dinero(registros):
    participantes = ['Iosu', 'Lide', 'Asier', 'Itziar']
    saldos = {p: 0 for p in participantes}
    for reg in registros:
        total = len(reg['pasajeros']) + 1
        if reg['dinero'] > 0 and len(reg['pasajeros']) > 0:
            deuda = reg['dinero'] / total
            saldos[reg['conductor']] -= deuda * len(reg['pasajeros'])
            for p in reg['pasajeros']:
                saldos[p] += deuda
    csv = 'Persona,Saldo (€)\n'
    for p, s in saldos.items():
        csv += f'{p},{s:.2f}\n'
    csv += '\nFecha,Conductor,Pasajeros,Dinero Total,Dinero por Persona\n'
    for reg in registros:
        if reg['dinero'] > 0 and len(reg['pasajeros']) > 0:
            total = len(reg['pasajeros']) + 1
            deuda = reg['dinero'] / total
            csv += f"{reg['fecha']},{reg['conductor']},\"{'|'.join(reg['pasajeros'])}\",{reg['dinero']:.2f},{deuda:.2f}\n"
    return csv

def save_file(repo, path, content, message):
    try:
        contents = repo.get_contents(path)
        sha = contents.sha
    except Exception:
        sha = None
    if sha:
        repo.update_file(path, message, content, sha)
    else:
        repo.create_file(path, message, content)

@app.route('/save', methods=['POST'])
def save_data():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    repo = get_github_repo()
    try:
        # Guardar datos.json
        content_str = json.dumps(data, indent=2, ensure_ascii=False)
        save_file(repo, DATA_PATH, content_str, f"Update datos.json {datetime.now().isoformat()}")
        # Guardar CSVs
        csv_viajes = generar_csv_viajes(data)
        save_file(repo, CSV_VIAJES_PATH, csv_viajes, f"Update viajes.csv {datetime.now().isoformat()}")
        csv_dinero = generar_csv_dinero(data)
        save_file(repo, CSV_DINERO_PATH, csv_dinero, f"Update dinero.csv {datetime.now().isoformat()}")
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_file_content(repo, path):
    try:
        contents = repo.get_contents(path)
        return contents.decoded_content.decode()
    except Exception:
        return None

@app.route('/datos', methods=['GET'])
def get_datos():
    repo = get_github_repo()
    content = get_file_content(repo, DATA_PATH)
    if content:
        return Response(content, mimetype='application/json')
    return jsonify([])

@app.route('/csv/viajes', methods=['GET'])
def get_csv_viajes():
    repo = get_github_repo()
    content = get_file_content(repo, CSV_VIAJES_PATH)
    if content:
        return Response(content, mimetype='text/csv')
    return '', 404

@app.route('/csv/dinero', methods=['GET'])
def get_csv_dinero():
    repo = get_github_repo()
    content = get_file_content(repo, CSV_DINERO_PATH)
    if content:
        return Response(content, mimetype='text/csv')
    return '', 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
