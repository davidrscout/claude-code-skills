"""Convierte resultados de calibración en notas 1-5 y en el orden inicial de cada cadena.
Nota = calidad objetiva (0-1) × 4 + 1; −1 si su tiempo mediano > 2× la mediana del tipo; −0,5 × tasa de fallos técnicos.
Empate (±0,3) → gana el más rápido.  Uso: python analizar_calibracion.py <carpeta> [--aplicar]
"""
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo  # noqa: E402


def main():
    carpeta = Path(sys.argv[1])
    aplicar = '--aplicar' in sys.argv
    res = json.loads((carpeta / 'resultados.json').read_text(encoding='utf-8'))
    por = {}
    for r in res:
        por.setdefault(r['tipo'], {}).setdefault((r['motor'], r['modelo']), []).append(r)
    orden = {}
    informe = []
    for tipo, cands in por.items():
        med_tipo = st.median([r['segundos'] for rs in cands.values() for r in rs])
        filas = []
        for (m, mod), rs in cands.items():
            calidad = st.mean(r['objetivo'] for r in rs)
            seg = st.median(r['segundos'] for r in rs)
            fallos = sum(1 for r in rs if r['estado'] != 'ok') / len(rs)
            nota = calidad * 4 + 1 - (1 if seg > 2 * med_tipo else 0) - 0.5 * fallos
            filas.append({'motor': m, 'modelo': mod, 'nota': round(max(1, nota), 2), 'calidad': round(calidad, 3),
                          'seg': round(seg, 1), 'fallos': round(fallos, 2), 'n': len(rs),
                          'detalles': sorted({r['detalle'][:60] for r in rs})})
        filas.sort(key=lambda f: (-round(f['nota'] / 0.3), f['seg']))
        orden[tipo] = [[f['motor'], f['modelo'], f['nota']] for f in filas]
        informe.append({'tipo': tipo, 'mediana_tipo_s': round(med_tipo, 1), 'filas': filas})
    print(json.dumps(informe, ensure_ascii=False, indent=1))
    if aplicar:
        f = nucleo.DATOS / 'orden_inicial.json'
        previo = nucleo.leer_json(f, {}) or {}
        previo.update({'origen': str(carpeta), **orden})
        nucleo.escribir_json(f, previo)
        print('ORDEN INICIAL GUARDADO en', f)


if __name__ == '__main__':
    main()
