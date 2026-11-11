"""Calibración: mide qué IA rinde mejor en cada tipo de tarea.
Uso: python calibrar.py [tipo ...]      (tareas en calib_tareas.py)
Cada ejecución trabaja en su propia carpeta; el corrector puntúa de forma objetiva cuando se puede.
Resultados: datos/calibracion/<fecha>/resultados.json (+ cada trabajo en el historial del Centro).
"""
import json
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nucleo  # noqa: E402
import calib_tareas as CT  # noqa: E402

LIMITE_MOTOR = {'kimi': 1, 'codex': 2}   # a la vez por motor (el resto sin límite propio)
LIMITE_TOTAL = 8

_sem_total = threading.Semaphore(LIMITE_TOTAL)
_sems: dict[str, threading.Semaphore] = {}
_lock = threading.Lock()


def sem_motor(m: str) -> threading.Semaphore:
    clave = m.split(':')[0] if m.split(':')[0] in LIMITE_MOTOR else m
    with _lock:
        if clave not in _sems:
            _sems[clave] = threading.Semaphore(LIMITE_MOTOR.get(clave, 3))
        return _sems[clave]


def ejecutar(tarea: dict, motor: str, modelo: str, rep: int, base: Path, resultados: list):
    d = base / f"{tarea['id']}__{motor.replace(':', '_').replace('/', '_')}{('__' + modelo) if modelo else ''}__{rep}"
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    if tarea.get('preparar'):
        tarea['preparar'](d)
    prompt = tarea['prompt'].replace('{DIR}', str(d).replace('\\', '/'))
    with _sem_total, sem_motor(motor):
        t = nucleo.Trabajo(motor, prompt, modelo=modelo, cwd=str(d), origen='calibracion', tipo=tarea['tipo'],
                           timeout_min=tarea.get('timeout_min', 12),
                           extra_args=['--strict-mcp-config'] if motor.startswith('claude:') else None)
        nucleo._trabajos_vivos[t.id] = t
        t.lanzar()
        t.hecho.wait()
    r = t.resultado()
    try:
        obj, detalle = tarea['comprobar'](d, r['respuesta'])
    except Exception as e:
        obj, detalle = 0.0, f'error del corrector: {e}'
    reg = {'tarea': tarea['id'], 'tipo': tarea['tipo'], 'motor': motor, 'modelo': modelo, 'rep': rep,
           'trabajo': t.id, 'estado': r['estado'], 'segundos': r['segundos'], 'coste': r['coste'],
           'objetivo': round(obj, 3), 'detalle': detalle, 'respuesta': r['respuesta'][:1500], 'dir': str(d)}
    with _lock:
        resultados.append(reg)
    print(f"{tarea['tipo']:13} {tarea['id']:14} {motor:46} {modelo:18} {r['estado']:8} {r['segundos']:6}s obj={obj:.2f} {detalle[:70]}", flush=True)


def main():
    tipos = sys.argv[1:] or None
    base = nucleo.DATOS / 'calibracion' / datetime.now().strftime('%Y%m%d_%H%M')
    base.mkdir(parents=True, exist_ok=True)
    resultados: list = []
    hilos = []
    for tarea in CT.TAREAS:
        if tipos and tarea['tipo'] not in tipos:
            continue
        for motor, modelo in CT.CANDIDATOS[tarea['tipo']]:
            for rep in range(tarea.get('reps', 1)):
                h = threading.Thread(target=ejecutar, args=(tarea, motor, modelo, rep, base, resultados))
                h.start()
                hilos.append(h)
                time.sleep(0.3)
    for h in hilos:
        h.join()
    (base / 'resultados.json').write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding='utf-8')
    print('GUARDADO', base / 'resultados.json')


if __name__ == '__main__':
    main()
