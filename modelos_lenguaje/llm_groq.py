"""Adaptador de Groq: traduce entre el formato neutro de llm.py y la librería groq.

Groq usa el formato de mensajes estilo OpenAI (system / user / assistant / tool).
Documentación consultada (20/11/2026):
  - Modelos:            https://console.groq.com/docs/models
  - Salidas en JSON:    https://console.groq.com/docs/structured-outputs
  - Herramientas:       https://console.groq.com/docs/tool-use/overview
"""
import os
import json
import logging

from groq import Groq, BadRequestError

NOMBRE = "groq"
log = logging.getLogger("modelos")

# Modelos que aceptan "json_schema" estricto: la salida queda forzada al esquema, token por token.
# Con los demás se usa "json_object" (JSON válido, pero sin garantía del esquema).
MODELOS_JSON_ESTRICTO = {"openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "meta-models/muse-spark-open"}

_cliente = None


def disponible() -> bool:
    return bool(os.getenv("GROQ_API_KEY"))


def _cli():
    global _cliente
    if _cliente is None:
        # max_retries=0: los reintentos los maneja la cadena de respaldo de llm.py, no la librería.
        _cliente = Groq(api_key=os.getenv("GROQ_API_KEY"), max_retries=0)
    return _cliente


def _extra(modelo: str) -> dict:
    # Los gpt-oss y qwen son modelos de razonamiento: pensar poco = responder rápido,
    # y el razonamiento nunca debe mezclarse con la respuesta para el estudiante.
    if modelo.startswith("openai/gpt-oss"):
        return {"reasoning_effort": "low"}
    if modelo.startswith("qwen/"):
        return {"reasoning_format": "hidden"}
    return {}


# En las pruebas (20/11/2026) gpt-oss en Groq a veces escribe mal la llamada a la herramienta
# (nombre cortado como "corr...", o texto en vez de la llamada) y Groq responde 400.
# Es al azar: repetir la misma petición una vez casi siempre funciona.
ERRORES_DE_GENERACION = {"tool_use_failed", "output_parse_failed"}


def _codigo_groq(e: Exception) -> str | None:
    cuerpo = getattr(e, "body", None)
    if isinstance(cuerpo, dict):
        detalle = cuerpo.get("error", cuerpo)
        if isinstance(detalle, dict):
            return detalle.get("code")
    return None


def generar_json(modelo, instruccion, texto, esquema, temperatura, timeout) -> str:
    """Pide una respuesta que cumpla el esquema JSON. Devuelve el texto JSON."""
    if modelo in MODELOS_JSON_ESTRICTO:
        formato = {"type": "json_schema", "json_schema": {"name": "respuesta", "strict": True, "schema": esquema}}
    else:
        formato = {"type": "json_object"}
        instruccion += "\nResponde solo con un objeto JSON que siga este esquema: " + json.dumps(esquema, ensure_ascii=False)
    r = _cli().chat.completions.create(
        model=modelo,
        messages=[{"role": "system", "content": instruccion}, {"role": "user", "content": texto}],
        response_format=formato,
        temperature=temperatura,
        timeout=timeout,
        **_extra(modelo),
    )
    if r.choices[0].finish_reason == "length":
        raise ValueError("respuesta cortada a la mitad (límite de longitud)")
    return r.choices[0].message.content or ""


def paso(modelo, sistema, mensajes, herramientas, timeout) -> dict:
    """Una sola llamada al modelo. Devuelve un mensaje neutro del asistente."""
    opciones = {}
    if herramientas:
        opciones["tools"] = [
            {"type": "function", "function": {
                "name": h["nombre"], "description": h["descripcion"], "parameters": h["parametros"]}}
            for h in herramientas
        ]
        opciones["tool_choice"] = "auto"
    peticion = dict(
        model=modelo,
        messages=[{"role": "system", "content": sistema}] + _a_groq(mensajes),
        timeout=timeout,
        **opciones,
        **_extra(modelo),
    )
    try:
        r = _cli().chat.completions.create(**peticion)
    except BadRequestError as e:
        if _codigo_groq(e) not in ERRORES_DE_GENERACION:
            raise
        log.warning("MODELO | groq/%s escribió mal la llamada a la herramienta (%s); se repite una vez",
                    modelo, _codigo_groq(e))
        r = _cli().chat.completions.create(**peticion)
    if r.choices[0].finish_reason == "length":
        # El proveedor cortó la respuesta a la mitad: mejor que responda el siguiente modelo
        # que mandarle al estudiante media frase.
        raise ValueError("respuesta cortada a la mitad (límite de longitud)")
    msg = r.choices[0].message
    llamadas = [
        {"id": tc.id, "nombre": tc.function.name, "args": json.loads(tc.function.arguments or "{}")}
        for tc in (msg.tool_calls or [])
    ]
    return {"rol": "asistente", "texto": (msg.content or "").strip(), "llamadas": llamadas}


def _a_groq(mensajes: list) -> list:
    """Convierte la conversación neutra al formato de Groq."""
    salida = []
    for m in mensajes:
        if m["rol"] == "usuario":
            salida.append({"role": "user", "content": m["texto"]})
        elif m["rol"] == "asistente":
            if m.get("llamadas"):
                salida.append({
                    "role": "assistant",
                    "content": m["texto"] or None,
                    "tool_calls": [
                        {"id": l["id"], "type": "function",
                         "function": {"name": l["nombre"], "arguments": json.dumps(l["args"], ensure_ascii=False)}}
                        for l in m["llamadas"]
                    ],
                })
            else:
                salida.append({"role": "assistant", "content": m["texto"] or "..."})
        elif m["rol"] == "herramienta":
            salida.append({
                "role": "tool",
                "tool_call_id": m["id"],
                "name": m["nombre"],
                "content": json.dumps(m["resultado"], ensure_ascii=False, default=str),
            })
    return salida
