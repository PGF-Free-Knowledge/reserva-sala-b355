import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State
import requests
from datetime import datetime, timedelta

# Instancia principal de Dash
app = dash.Dash(__name__)

# URL del backend
BACKEND_URL = "https://reserva-sala-b355-elo.onrender.com/reservas"

HORAS = [
    "08:00","09:00","10:00","11:00",
    "12:00","13:00","14:00","15:00",
    "16:00","17:00"
]

# Layout principal
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
    html.Div(id="horario"),

    html.H3("Calendario semanal"),
    html.Div(id="calendario"),

    html.H3("Seleccionar horario (visual)"),
    html.Div(id="horario-visual", style={"display": "flex", "gap": "10px"}),

    dcc.Interval(id="interval-component", interval=2000, n_intervals=0),
    dcc.Store(id="rango_temp"),
])

# Mostrar reservas
@app.callback(Output("tabla-reservas","children"), Input("btn-actualizar","n_clicks"))
def listar_reservas(n):
    try:
        reservas = requests.get(BACKEND_URL).json()
        return [html.Div(f"{r['fecha']} {r['hora_inicio']} {r['hora_fin']} {r['grupo']} {r['responsable']}") for r in reservas]
    except Exception as e:
        return f"Error al conectar con backend: {str(e)}"

# Crear reserva
@app.callback(Output("mensaje","children"),
              Input("btn-reservar","n_clicks"),
              State("fecha","value"), State("hora_inicio","value"), State("hora_fin","value"),
              State("responsable","value"), State("grupo","value"), State("email","value"))
def crear_reserva(n, fecha, inicio, fin, responsable, grupo, email):
    if n is None:
        return ""
    data = {"fecha":fecha,"hora_inicio":inicio,"hora_fin":fin,"responsable":responsable,"grupo":grupo,"email":email}
    try:
        r = requests.post(BACKEND_URL, json=data)
        if r.status_code == 200:
            return r.json().get("mensaje","Reserva realizada")
        else:
            return f"Error: {r.json().get('detail','No se pudo crear la reserva')}"
    except Exception as e:
        return f"Error al conectar con backend: {str(e)}"

# Horario texto
@app.callback(Output("horario","children"), Input("interval-component","n_intervals"), State("fecha","value"))
def mostrar_horario(_, fecha):
    try:
        reservas = requests.get(BACKEND_URL).json()
        reservas_del_dia = [r for r in reservas if r["fecha"] == fecha]
        ocupadas = set()
        for r in reservas_del_dia:
            inicio = int(r["hora_inicio"][:2]); fin = int(r["hora_fin"][:2])
            for h in range(inicio, fin): ocupadas.add(f"{h:02d}:00")
        return [html.Div(f"{h} - {'OCUPADO' if h in ocupadas else 'DISPONIBLE'}",
                         style={"color":"red" if h in ocupadas else "green"}) for h in HORAS]
    except Exception as e:
        return f"Error cargando horario: {str(e)}"

# Calendario semanal
@app.callback(Output("calendario","children"),
              Input("interval-component","n_intervals"),
              State("fecha","value"))
def mostrar_calendario(_, fecha_seleccionada):
    try:
        reservas = requests.get(BACKEND_URL).json()
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
                html.Td(fecha,
                        id={"type":"fecha-click","index":fecha},
                        style={"cursor":"pointer","fontWeight":"bold",
                               "backgroundColor":"dodgerblue" if fecha==fecha_seleccionada else "white",
                               "color":"white" if fecha==fecha_seleccionada else "black"})
            ]
            for h in HORAS:
                ocupado = h in calendario[fecha]
                fila.append(html.Td("X" if ocupado else "-",
                                    style={"backgroundColor":"red" if ocupado else "lightgreen",
                                           "textAlign":"center"}))
            filas.append(html.Tr(fila))

        return html.Table([html.Tr(header)] + filas,
                          style={"border":"1px solid black","borderCollapse":"collapse"})
    except Exception as e:
        return f"Error cargando calendario: {str(e)}"

# Selección de fecha desde calendario
@app.callback(Output("fecha","value"),
              Input({"type":"fecha-click","index":dash.ALL},"n_clicks"),
              State({"type":"fecha-click","index":dash.ALL},"id"))
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

# Run local (no se usa en Render, porque se monta desde main.py)
if __name__ == "__main__":
    app.run(debug=True)
