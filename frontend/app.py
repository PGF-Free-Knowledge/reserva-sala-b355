import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests
from datetime import datetime, timedelta

app = dash.Dash(__name__)

HORAS = [
    "08:00", "09:00", "10:00", "11:00",
    "12:00", "13:00", "14:00", "15:00",
    "16:00", "17:00"
]

app.layout = html.Div([
    html.H1("Reserva Sala Co-Working B355"),

    html.H3("Reservas actuales"),
    html.Button("Actualizar", id="btn-actualizar"),
    html.Div(id="tabla-reservas"),

    html.H3("Nueva reserva"),

    dcc.Input(id="fecha", type="text", placeholder="YYYY-MM-DD"),

    dcc.Dropdown(id="hora_inicio", placeholder="Hora inicio"),
    dcc.Dropdown(id="hora_fin", placeholder="Hora fin"),

    dcc.Input(id="responsable", type="text", placeholder="Nombre"),
    dcc.Input(id="grupo", type="text", placeholder="ELO-TECH-XX"),
    dcc.Input(id="email", type="text", placeholder="correo@usm.cl"),

    html.Button("Reservar", id="btn-reservar"),
    html.Div(id="mensaje"),
    html.Div(id="mensaje_error", style={"color": "red"}),

    html.H3("Horario del día"),
    html.H3("Calendario semanal"),
    html.Div(id="calendario"),
    html.Div(id="horario"),

    html.H3("Seleccionar horario (visual)"),
    html.Div(id="horario-visual", style={"display": "flex", "gap": "10px"}),

    dcc.Interval(id="interval-component", interval=2000, n_intervals=0),
    dcc.Store(id="rango_temp"),
])


# 🔹 Mostrar reservas
@app.callback(
    Output("tabla-reservas", "children"),
    Input("btn-actualizar", "n_clicks")
)
def listar_reservas(n):
    try:
        reservas = requests.get("http://127.0.0.1:8000/reservas").json()
        return [
            html.Div(
                f"{r['fecha']} {r['hora_inicio']} {r['hora_fin']} {r['grupo']} {r['responsable']}"
            )
            for r in reservas
        ]
    except:
        return "Error al conectar con backend"


# 🔹 Crear reserva
@app.callback(
    Output("mensaje", "children"),
    Input("btn-reservar", "n_clicks"),
    State("fecha", "value"),
    State("hora_inicio", "value"),
    State("hora_fin", "value"),
    State("responsable", "value"),
    State("grupo", "value"),
    State("email", "value"),
)
def crear_reserva(n, fecha, inicio, fin, responsable, grupo, email):
    if n is None:
        return ""

    data = {
        "fecha": fecha,
        "hora_inicio": inicio,
        "hora_fin": fin,
        "responsable": responsable,
        "grupo": grupo,
        "email": email
    }

    try:
        r = requests.post("http://127.0.0.1:8000/reservas", json=data)
        return r.json().get("mensaje", "Reserva realizada")
    except:
        return "Error al conectar con backend"


# 🔹 Dropdown dinámico
@app.callback(
    Output("hora_inicio", "options"),
    Output("hora_fin", "options"),
    Output("hora_inicio", "value", allow_duplicate=True),
    Output("hora_fin", "value", allow_duplicate=True),
    Input("interval-component", "n_intervals"),
    Input("hora_inicio", "value"),
    Input("fecha", "value"),
    State("hora_fin", "value"),
    prevent_initial_call=True
)
def actualizar_horas(_, hora_inicio_seleccionada, fecha, hora_fin_actual):
    reservas = requests.get("http://127.0.0.1:8000/reservas").json()

    reservas_del_dia = [r for r in reservas if r["fecha"] == fecha]

    ocupadas = set()
    for r in reservas_del_dia:
        inicio = int(r["hora_inicio"][:2])
        fin = int(r["hora_fin"][:2])
        for h in range(inicio, fin):
            ocupadas.add(f"{h:02d}:00")

    disponibles = [h for h in HORAS if h not in ocupadas]

    opciones_inicio = [{"label": h, "value": h} for h in disponibles]

    if hora_inicio_seleccionada and hora_inicio_seleccionada in disponibles:
        idx = disponibles.index(hora_inicio_seleccionada)
        opciones_fin_lista = disponibles[idx + 1:]
    else:
        opciones_fin_lista = disponibles

    opciones_fin = [{"label": h, "value": h} for h in opciones_fin_lista]

    valor_inicio = hora_inicio_seleccionada if hora_inicio_seleccionada in disponibles else None

    if hora_fin_actual in opciones_fin_lista:
        valor_fin = hora_fin_actual
    else:
        valor_fin = opciones_fin_lista[0] if opciones_fin_lista else None

    return opciones_inicio, opciones_fin, valor_inicio, valor_fin


# 🔹 Horario texto
@app.callback(
    Output("horario", "children"),
    Input("interval-component", "n_intervals"),
    State("fecha", "value"),
)
def mostrar_horario(_, fecha):
    try:
        reservas = requests.get("http://127.0.0.1:8000/reservas").json()

        reservas_del_dia = [r for r in reservas if r["fecha"] == fecha]

        ocupadas = set()
        for r in reservas_del_dia:
            inicio = int(r["hora_inicio"][:2])
            fin = int(r["hora_fin"][:2])
            for h in range(inicio, fin):
                ocupadas.add(f"{h:02d}:00")

        return [
            html.Div(
                f"{h} - {'OCUPADO' if h in ocupadas else 'DISPONIBLE'}",
                style={"color": "red" if h in ocupadas else "green"}
            )
            for h in HORAS
        ]

    except:
        return "Error cargando horario"


# 🔹 Bloques visuales
@app.callback(
    Output("horario-visual", "children"),
    Input("interval-component", "n_intervals"),
    State("fecha", "value"),
    State("hora_inicio", "value"),
    State("hora_fin", "value"),
)
def mostrar_horario_visual(_, fecha, inicio_sel, fin_sel):
    try:
        reservas = requests.get("http://127.0.0.1:8000/reservas").json()

        reservas_del_dia = [r for r in reservas if r["fecha"] == fecha]

        ocupadas = set()
        for r in reservas_del_dia:
            inicio = int(r["hora_inicio"][:2])
            fin = int(r["hora_fin"][:2])
            for h in range(inicio, fin):
                ocupadas.add(f"{h:02d}:00")

        seleccionadas = set()
        if inicio_sel and fin_sel:
            i = int(inicio_sel[:2])
            f = int(fin_sel[:2])
            for h in range(i, f + 1):
                seleccionadas.add(f"{h:02d}:00")

        bloques = []

        for h in HORAS:
            if h in ocupadas:
                color = "red"
            elif h in seleccionadas:
                color = "dodgerblue"
            else:
                color = "lightgreen"

            bloques.append(
                html.Button(
                    h,
                    id={"type": "bloque-hora", "index": h},
                    n_clicks=0,
                    disabled=True if h in ocupadas else False,
                    style={
                        "padding": "10px",
                        "border": "1px solid black",
                        "backgroundColor": color,
                        "cursor": "pointer",
                        "width": "60px"
                    }
                )
            )

        return bloques

    except:
        return "Error"


# 🔥 SELECCIÓN DE RANGO (FINAL COMPLETO)
@app.callback(
    Output("hora_inicio", "value", allow_duplicate=True),
    Output("hora_fin", "value", allow_duplicate=True),
    Output("rango_temp", "data"),
    Output("mensaje_error", "children"),
    Input({"type": "bloque-hora", "index": dash.ALL}, "n_clicks_timestamp"),
    State({"type": "bloque-hora", "index": dash.ALL}, "id"),
    State("rango_temp", "data"),
    State("fecha", "value"),
    prevent_initial_call=True
)
def seleccionar_rango(timestamps, ids, rango_temp, fecha):

    if not timestamps:
        return dash.no_update, dash.no_update, rango_temp, ""

    reservas = requests.get("http://127.0.0.1:8000/reservas").json()
    reservas_del_dia = [r for r in reservas if r["fecha"] == fecha]

    ocupadas = set()
    for r in reservas_del_dia:
        inicio = int(r["hora_inicio"][:2])
        fin = int(r["hora_fin"][:2])
        for h in range(inicio, fin):
            ocupadas.add(f"{h:02d}:00")

    max_ts = max([t for t in timestamps if t is not None], default=None)

    if max_ts is None:
        return dash.no_update, dash.no_update, rango_temp, ""

    for i, t in enumerate(timestamps):
        if t == max_ts:
            hora = ids[i]["index"]

            if not rango_temp:
                return hora, dash.no_update, {"inicio": hora}, ""

            else:
                inicio = rango_temp["inicio"]

                h_inicio = int(inicio[:2])
                h_fin = int(hora[:2])

                duracion = abs(h_fin - h_inicio)

                # 🔒 Validar duración
                if duracion < 2 or duracion > 4:
                    return dash.no_update, dash.no_update, None, "Rango inválido: solo entre 2 y 4 horas"

                # 🔒 Validar cruce con ocupadas
                for h in range(min(h_inicio, h_fin), max(h_inicio, h_fin)):
                    if f"{h:02d}:00" in ocupadas:
                        return dash.no_update, dash.no_update, None, "No puedes seleccionar un rango con horas ocupadas"

                if h_fin > h_inicio:
                    return inicio, hora, None, ""
                else:
                    return hora, inicio, None, ""

    return dash.no_update, dash.no_update, rango_temp, ""

@app.callback(
    Output("calendario", "children"),
    Input("interval-component", "n_intervals"),
    State("fecha", "value")
)
def mostrar_calendario(_, fecha_seleccionada):
    try:
        reservas = requests.get("http://127.0.0.1:8000/reservas").json()

        calendario = {}

        for r in reservas:
            fecha = r["fecha"]

            if fecha not in calendario:
                calendario[fecha] = set()

            inicio = int(r["hora_inicio"][:2])
            fin = int(r["hora_fin"][:2])

            for h in range(inicio, fin):
                calendario[fecha].add(f"{h:02d}:00")

        hoy = datetime.today()

        fechas_ordenadas = sorted(calendario.keys())

        fechas_filtradas = [
            f for f in fechas_ordenadas
            if datetime.fromisoformat(f) >= hoy - timedelta(days=3)
            and datetime.fromisoformat(f) <= hoy + timedelta(days=3)
        ]

        header = [html.Th("Fecha")] + [html.Th(h[:2]) for h in HORAS]

        filas = []

        for fecha in fechas_filtradas:

            fila = [
                html.Td(
                    fecha,
                    id={"type": "fecha-click", "index": fecha},
                    style={
                        "cursor": "pointer",
                        "fontWeight": "bold",
                        "backgroundColor": "dodgerblue" if fecha == fecha_seleccionada else "white",
                        "color": "white" if fecha == fecha_seleccionada else "black"
                    }
                )
            ]

            for h in HORAS:
                ocupado = h in calendario[fecha]

                fila.append(
                    html.Td(
                        "X" if ocupado else "-",
                        style={
                            "backgroundColor": "red" if ocupado else "lightgreen",
                            "textAlign": "center"
                        }
                    )
                )

            filas.append(html.Tr(fila))

        return html.Table(
            [html.Tr(header)] + filas,
            style={"border": "1px solid black", "borderCollapse": "collapse"}
        )

    except:
        return "Error cargando calendario"

@app.callback(
    Output("fecha", "value"),
    Input({"type": "fecha-click", "index": dash.ALL}, "n_clicks"),
    State({"type": "fecha-click", "index": dash.ALL}, "id"),
)
def seleccionar_fecha(n_clicks, ids):

    if not n_clicks:
        return dash.no_update

    max_click = max([c for c in n_clicks if c is not None], default=None)

    if max_click is None:
        return dash.no_update

    for i, c in enumerate(n_clicks):
        if c == max_click:
            return ids[i]["index"]

    return dash.no_update

if __name__ == "__main__":
    app.run(debug=True)