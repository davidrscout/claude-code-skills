"""Servidor MCP «centro-ia» (stdio, JSON-RPC por líneas). Sin dependencias.

Da al agente herramientas para delegar en otras IAs por su CLI (Claude Code, Codex, Kimi,
OpenCode) o por API (Experiential Labs). EXPERIMENTAL: ver README.md. Registro:
  Claude Code: claude mcp add centro-ia -s user -- python /ruta/a/mcp/centro-ia/mcp_ias.py
  OpenCode:    sección "mcp" de opencode.json (ver README.md)
"""
import json
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nucleo  # noqa: E402

PROFUNDIDAD = int(os.environ.get('CENTRO_IA_PROFUNDIDAD', '0'))
PADRE = os.environ.get('CENTRO_IA_PADRE', '')
_lock_salida = threading.Lock()
_trabajos: dict[str, nucleo.Trabajo] = {}

MOTORES_DOC = ('Ids de motor: auto:<tipo> (recomendado, con respaldo) · claude:<cuenta> (las de config.json; '
               'por defecto claude:principal) · codex · kimi · opencode:<proveedor/modelo> (p. ej. '
               'opencode:opencode/<modelo>-free) · exp:<modelo> (Experiential Labs por API, solo texto, rápido).')

HERRAMIENTAS = [
    {
        'name': 'ias_estado',
        'description': 'Cupos de las cuentas de IA configuradas (Claude Code, Codex, Kimi), qué modelos son GRATIS ahora '
                       '(Experiential y OpenCode, sondeados) y trabajos en curso. Llamar antes de delegar. '
                       'sondear=true vuelve a comprobar los gratis (tarda ~1 min).',
        'inputSchema': {'type': 'object', 'properties': {
            'sondear': {'type': 'boolean', 'description': 'Re-sondear ahora los modelos gratis'}}},
    },
    {
        'name': 'ia_delegar',
        'description': 'Encarga una tarea a otra IA y devuelve su respuesta. Los motores agénticos (claude, codex, kimi, '
                       'opencode) pueden leer/editar ficheros y ejecutar comandos en cwd; exp:* solo devuelve texto. '
                       'El prompt debe ser autocontenido. esperar=false devuelve un id para recoger con ia_resultado '
                       '(sirve para lanzar varias a la vez). ' + MOTORES_DOC,
        'inputSchema': {'type': 'object', 'required': ['motor', 'prompt'], 'properties': {
            'motor': {'type': 'string', 'description': 'Lo normal: auto:<tipo> (texto, sencillo, front, codigo, investigacion, lote, largo, '
                                                       'revision, pensar) = cadena con respaldo automático según cupos y gratis. '
                                                       'O un motor concreto.'},
            'respaldo': {'type': 'array', 'items': {'type': 'string'},
                         'description': 'Motores de respaldo en orden si el principal falla o se queda sin cupo; '
                                        'formato motor o motor|modelo (p. ej. claude:principal|claude-sonnet-5-5)'},
            'prompt': {'type': 'string'},
            'tipo': {'type': 'string', 'description': 'Tipo de tarea si usas un motor concreto (para aprender qué IA va mejor en qué)'},
            'modelo': {'type': 'string', 'description': 'Opcional. Claude: claude-opus-5-5 / claude-sonnet-5-5 / '
                                                        'claude-haiku-5-5 u otro id de tu plan. Kimi y Codex: los '
                                                        'modelos de su CLI.'},
            'cwd': {'type': 'string', 'description': 'Carpeta de trabajo (ruta absoluta) para motores agénticos'},
            'esperar': {'type': 'boolean', 'description': 'true (por defecto) espera y devuelve la respuesta'},
            'timeout_min': {'type': 'number', 'description': 'Límite en minutos (por defecto 30 agéntico, 5 texto)'},
        }},
    },
    {
        'name': 'ia_resultado',
        'description': 'Recoge el resultado de un trabajo lanzado con esperar=false. esperar=true bloquea hasta que termine.',
        'inputSchema': {'type': 'object', 'required': ['id'], 'properties': {
            'id': {'type': 'string'}, 'esperar': {'type': 'boolean'}}},
    },
    {
        'name': 'ia_comparar',
        'description': 'Manda el MISMO prompt a varios motores en paralelo y devuelve todas las respuestas con tiempo y '
                       'coste. Solo para tareas cortas de texto. ' + MOTORES_DOC,
        'inputSchema': {'type': 'object', 'required': ['motores', 'prompt'], 'properties': {
            'motores': {'type': 'array', 'items': {'type': 'string'}},
            'prompt': {'type': 'string'},
            'cwd': {'type': 'string'},
        }},
    },
    {
        'name': 'ia_valorar',
        'description': 'Pon nota (1-5) a un trabajo delegado tras revisarlo: calidad del resultado teniendo en cuenta '
                       'tiempo y si hubo que rehacerlo. Con estas notas las cadenas auto:<tipo> se reordenan solas '
                       '(la IA que rinde mejor en cada tipo sube). Hazlo SIEMPRE tras revisar una delegación.',
        'inputSchema': {'type': 'object', 'required': ['id', 'nota'], 'properties': {
            'id': {'type': 'string', 'description': 'id del trabajo (el que hizo el trabajo, no la cadena)'},
            'nota': {'type': 'number', 'description': '1 = inútil, 3 = aceptable con retoques, 5 = perfecto'},
            'comentario': {'type': 'string'},
            'tipo': {'type': 'string', 'description': 'Tipo de tarea si no iba por auto:<tipo>'}}},
    },
    {
        'name': 'ia_cancelar',
        'description': 'Cancela un trabajo en curso por id.',
        'inputSchema': {'type': 'object', 'required': ['id'], 'properties': {'id': {'type': 'string'}}},
    },
]


def enviar(msg: dict) -> None:
    with _lock_salida:
        sys.stdout.write(json.dumps(msg, ensure_ascii=False) + '\n')
        sys.stdout.flush()


def formatear(r: dict) -> str:
    cab = f"[{r['motor']}{' · ' + r['modelo'] if r.get('modelo') else ''}] id={r.get('id', '')} estado={r['estado']} · {r['segundos']} s"
    if r.get('coste') is not None:
        cab += f" · coste {r['coste']} $" + (' (equivalente API, no se cobra)' if r['motor'].startswith('claude:') else '')
    if r.get('error'):
        cab += f"\nERROR: {r['error']}"
    if r.get('intentos') and len(r['intentos']) > 1 or (r.get('intentos') and r['estado'] != 'ok'):
        cab += '\nIntentos: ' + ' → '.join(f"{i['motor']} {i['estado']} {i['segundos']}s" + (f" ({i['error'][:80]})" if i['error'] else '')
                                          for i in r['intentos'])
    return cab + '\n\n' + (r.get('respuesta') or '(sin texto)')


def _normalizar(motor: str) -> str:
    motor = motor.strip()
    if motor.startswith('claude:'):
        cu = nucleo.cuenta_claude(motor.split(':', 1)[1])
        if not cu:
            raise RuntimeError(f'Cuenta de Claude desconocida: {motor}')
        return f"claude:{cu['id']}"
    return motor


def lanzar(a: dict):
    if PROFUNDIDAD >= 2:
        raise RuntimeError('Profundidad máxima de delegación alcanzada (una IA delegada no puede volver a delegar dos veces).')
    motor = a['motor'].strip()
    respaldo = a.get('respaldo') or []
    if motor.startswith('auto:') or respaldo:
        if motor.startswith('auto:'):
            tipo = motor.split(':', 1)[1]
            if tipo not in nucleo.TIPOS:
                raise RuntimeError(f'Tipo desconocido: {tipo}. Tipos: {", ".join(nucleo.TIPOS)}')
            lista = nucleo.cadena(tipo)
        else:
            lista = [(_normalizar(motor), a.get('modelo', ''))]
        for r in respaldo:
            m, _, mod = r.partition('|')
            lista.append((_normalizar(m), mod))
        if not lista:
            raise RuntimeError(f'No hay ningún motor disponible para {motor}: hazlo tú.')
        c = nucleo.Cadena(lista, a['prompt'], cwd=a.get('cwd', ''), origen='mcp', padre=PADRE,
                          timeout_min=a.get('timeout_min'), etiqueta=motor,
                          tipo=motor.split(':', 1)[1] if motor.startswith('auto:') else a.get('tipo', ''))
        _trabajos[c.id] = c
        return c.lanzar()
    motor = _normalizar(motor)
    if motor.startswith('claude:'):
        cu = nucleo.cuenta_claude(motor.split(':', 1)[1])
        if not cu:
            raise RuntimeError(f'Cuenta de Claude desconocida: {motor}')
        motor = f"claude:{cu['id']}"
    t = nucleo.Trabajo(motor, a['prompt'], modelo=a.get('modelo', ''), cwd=a.get('cwd', ''),
                       origen='mcp', padre=PADRE, timeout_min=a.get('timeout_min'), tipo=a.get('tipo', ''))
    _trabajos[t.id] = t
    nucleo._trabajos_vivos[t.id] = t
    return t.lanzar()


def esperar_trabajo(t: nucleo.Trabajo) -> dict:
    t.hecho.wait()
    return t.resultado()


def _sondeo_si_toca() -> None:
    """Si los datos de modelos gratis tienen más de sondeo_horas, re-sondea EN SEGUNDO PLANO.
    Candado en la carpeta temporal para que solo lo haga uno de los MCP abiertos a la vez."""
    try:
        g = nucleo.leer_json(nucleo.GRATIS, {}) or {}
        horas = float(nucleo.config().get('sondeo_horas', 3))
        if nucleo.ahora() - min(g.get('exp_ts', 0), g.get('opencode_ts', 0)) <= horas * 3600:
            return
        cand = os.path.join(tempfile.gettempdir(), 'centro-ia-sondeo.lock')
        try:
            if time.time() - os.path.getmtime(cand) < 1800:
                return  # otro MCP está sondeando (o lo hizo hace nada)
        except OSError:
            pass
        with open(cand, 'w') as f:
            f.write(str(os.getpid()))

        def correr():
            try:
                nucleo.sondear('todo')
            except Exception:
                pass

        threading.Thread(target=correr, daemon=True).start()
    except Exception:
        pass


def llamar(nombre: str, a: dict) -> str:
    if nombre == 'ias_estado':
        if a.get('sondear'):
            nucleo.sondear('todo')
        else:
            _sondeo_si_toca()
        return nucleo.estado_texto()
    if nombre == 'ia_delegar':
        t = lanzar(a)
        if a.get('esperar') is False:
            return f'Lanzado: id={t.id} ({t.motor}). Recógelo con ia_resultado.'
        return formatear(esperar_trabajo(t))
    if nombre == 'ia_resultado':
        t = _trabajos.get(a['id'])
        if not t:
            for h in nucleo.historial(500):
                if h['id'] == a['id']:
                    return formatear({**h, 'respuesta': h.get('respuesta', '')})
            return f"No encuentro el trabajo {a['id']}"
        if a.get('esperar', True):
            return formatear(esperar_trabajo(t))
        r = t.resultado()
        return formatear(r) if t.hecho.is_set() else f"{t.id} sigue en curso ({r['segundos']} s)."
    if nombre == 'ia_comparar':
        ts = [lanzar({'motor': m, 'prompt': a['prompt'], 'cwd': a.get('cwd', '')}) for m in a['motores']]
        return '\n\n────────\n\n'.join(formatear(esperar_trabajo(t)) for t in ts)
    if nombre == 'ia_valorar':
        r = nucleo.valorar(a['id'], a['nota'], a.get('comentario', ''), a.get('tipo', ''))
        return f"Anotado: {r['motor']} · {r['tipo'] or 'sin tipo'} · nota {r['nota']}"
    if nombre == 'ia_cancelar':
        c = _trabajos.get(a['id'])
        if isinstance(c, nucleo.Cadena):
            c.cancelada = True
            if c.actual:
                c.actual.estado = 'cancelado'
                nucleo.cancelar(c.actual.id)
            return 'Cancelada la cadena.'
        return 'Cancelado.' if nucleo.cancelar(a['id']) else 'No se pudo cancelar (¿ya terminó?).'
    raise RuntimeError(f'Herramienta desconocida: {nombre}')


def atender(msg: dict) -> None:
    mid = msg.get('id')
    metodo = msg.get('method')
    try:
        if metodo == 'initialize':
            ver = (msg.get('params') or {}).get('protocolVersion', '2025-06-18')
            enviar({'jsonrpc': '2.0', 'id': mid, 'result': {
                'protocolVersion': ver,
                'capabilities': {'tools': {}},
                'serverInfo': {'name': 'centro-ia', 'version': '1.0'},
                'instructions': nucleo.politica(),
            }})
        elif metodo == 'tools/list':
            enviar({'jsonrpc': '2.0', 'id': mid, 'result': {'tools': HERRAMIENTAS}})
        elif metodo == 'tools/call':
            p = msg.get('params') or {}

            def trabajar():
                try:
                    texto = llamar(p.get('name'), p.get('arguments') or {})
                    enviar({'jsonrpc': '2.0', 'id': mid, 'result': {'content': [{'type': 'text', 'text': texto}]}})
                except Exception as e:
                    enviar({'jsonrpc': '2.0', 'id': mid, 'result': {
                        'content': [{'type': 'text', 'text': f'Error: {e}'}], 'isError': True}})
            threading.Thread(target=trabajar, daemon=True).start()
        elif metodo == 'ping':
            enviar({'jsonrpc': '2.0', 'id': mid, 'result': {}})
        elif mid is not None and metodo:
            enviar({'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32601, 'message': f'Método no soportado: {metodo}'}})
    except Exception as e:
        if mid is not None:
            enviar({'jsonrpc': '2.0', 'id': mid, 'error': {'code': -32603, 'message': str(e)}})


def main() -> None:
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    for linea in sys.stdin:
        linea = linea.strip()
        if not linea:
            continue
        try:
            atender(json.loads(linea))
        except Exception:
            continue
    # al cerrarse Claude, corta lo que siga corriendo
    for t in list(_trabajos.values()):
        if not t.hecho.is_set():
            nucleo.cancelar(t.id)
    time.sleep(0.5)


if __name__ == '__main__':
    main()
