
import os
import json
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from github import Github
from datetime import datetime

# Configuración
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_NAME = 'iosugomez/kotxea-backend'
DATA_PATH = 'datos/datos.json'
CSV_VIAJES_PATH = 'datos/viajes.csv'
CSV_DINERO_PATH = 'datos/dinero.csv'

app = Flask(__name__)
CORS(app)

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

    # --- Cálculo de pagos mínimos tipo Tricount ---
    deudores = []
    acreedores = []
    for p, s in saldos.items():
        if round(s, 2) < 0:
            deudores.append([p, round(-s, 2)])
        elif round(s, 2) > 0:
            acreedores.append([p, round(s, 2)])

    pagos = []
    i, j = 0, 0
    while i < len(deudores) and j < len(acreedores):
        deudor, debe = deudores[i]
        acreedor, cobra = acreedores[j]
        pago = min(debe, cobra)
        pagos.append((deudor, acreedor, pago))
        deudores[i][1] -= pago
        acreedores[j][1] -= pago
        if abs(deudores[i][1]) < 0.01:
            i += 1
        if abs(acreedores[j][1]) < 0.01:
            j += 1

    if pagos:
        csv += '\nPagos mínimos para saldar deudas:\nDeudor,Acreedor,Cantidad (€)\n'
        for deudor, acreedor, cantidad in pagos:
            csv += f'{deudor},{acreedor},{cantidad:.2f}\n'

    csv += '\nFecha,Conductor,Pasajeros,Dinero Total,Dinero por Persona\n'
    for reg in registros:
        if reg['dinero'] > 0 and len(reg['pasajeros']) > 0:
            total = len(reg['pasajeros']) + 1
            deuda = reg['dinero'] / total
            csv += f"{reg['fecha']},{reg['conductor']},\"{'|'.join(reg['pasajeros'])}\",{reg['dinero']:.2f},{deuda:.2f}\n"
    return csv

def save_multiple_files(repo, files, commit_message):
    """
    Guarda múltiples archivos en un solo commit
    files: lista de tuplas (path, content)
    """
    # Obtener el commit HEAD actual
    branch = repo.get_branch('main')
    base_commit = repo.get_commit(branch.commit.sha)
    base_tree = base_commit.tree
    
    # Crear blobs para cada archivo
    element_list = []
    for path, content in files:
        blob = repo.create_git_blob(content, "utf-8")
        element = {
            'path': path,
            'mode': '100644',  # archivo regular
            'type': 'blob',
            'sha': blob.sha
        }
        element_list.append(element)
    
    # Crear nuevo tree con los archivos
    new_tree = repo.create_git_tree(element_list, base_tree)
    
    # Crear commit
    new_commit = repo.create_git_commit(
        commit_message,
        new_tree,
        [base_commit]
    )
    
    # Actualizar la referencia del branch
    ref = repo.get_git_ref('heads/main')
    ref.edit(new_commit.sha)

@app.route('/save', methods=['POST'])
def save_data():
    data = request.json
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    repo = get_github_repo()
    try:
        # Preparar todos los archivos
        content_json = json.dumps(data, indent=2, ensure_ascii=False)
        csv_viajes = generar_csv_viajes(data)
        csv_dinero = generar_csv_dinero(data)
        
        files = [
            (DATA_PATH, content_json),
            (CSV_VIAJES_PATH, csv_viajes),
            (CSV_DINERO_PATH, csv_dinero)
        ]
        
        # Guardar todos en un solo commit
        commit_message = f"Update data files {datetime.now().isoformat()}"
        save_multiple_files(repo, files, commit_message)
        
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def calcular_pagos_minimos(saldos):
    """Calcula los pagos mínimos tipo Tricount para saldar deudas"""
    deudores = []
    acreedores = []
    for p, s in saldos.items():
        if round(s, 2) < 0:
            deudores.append([p, round(-s, 2)])
        elif round(s, 2) > 0:
            acreedores.append([p, round(s, 2)])
    
    pagos = []
    i, j = 0, 0
    while i < len(deudores) and j < len(acreedores):
        deudor, debe = deudores[i]
        acreedor, cobra = acreedores[j]
        pago = min(debe, cobra)
        pagos.append({'de': deudor, 'para': acreedor, 'cantidad': round(pago, 2)})
        deudores[i][1] -= pago
        acreedores[j][1] -= pago
        if abs(deudores[i][1]) < 0.01:
            i += 1
        if abs(acreedores[j][1]) < 0.01:
            j += 1
    return pagos

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

@app.route('/pagos-minimos', methods=['POST'])
def pagos_minimos():
    """Calcula y retorna los pagos mínimos para saldar deudas"""
    data = request.json
    if not data or not isinstance(data, list):
        return jsonify({'error': 'No data provided'}), 400
    
    participantes = ['Iosu', 'Lide', 'Asier', 'Itziar']
    saldos = {p: 0 for p in participantes}
    
    for reg in data:
        total = len(reg.get('pasajeros', [])) + 1
        if reg.get('dinero', 0) > 0 and len(reg.get('pasajeros', [])) > 0:
            deuda = reg['dinero'] / total
            saldos[reg['conductor']] -= deuda * len(reg['pasajeros'])
            for p in reg['pasajeros']:
                saldos[p] += deuda
    
    pagos = calcular_pagos_minimos(saldos)
    return jsonify({'pagos': pagos, 'saldos': saldos})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
