import dash
from dash import html, dcc, Input, Output, State
import requests

app = dash.Dash(__name__)

BACKEND_URL = "http://127.0.0.1:8000"

def obtener_reservas():
    try:
        r = requests.get(f"{BACKEND_URL}/reservas")
        return r.json()
    except:
        return []

def generar_tabla(reservas):
    filas = []
    for r in reservas:
        filas.append(html.Tr([
            html.Td(r["fecha"]),
            html.Td(r["hora_inicio"]),
            html.Td(r["hora_fin"]),
            html.Td(r["grupo"]),
            html.Td(r["responsable"])
        ]))
    return filas

app.layout = html.Div([
    
    html.H1("Reserva Sala Co-Working B355"),

    html.H3("Reservas actuales"),

    html.Button("Actualizar", id="btn-refresh"),

    html.Table([
        html.Thead(html.Tr([
            html.Th("Fecha"),
            html.Th("Inicio"),
            html.Th("Fin"),
            html.Th("Grupo"),
            html.Th("Responsable")
        ])),
        html.Tbody(id="tabla")
    ]),

    html.Hr(),

    html.H3("Nueva reserva"),

    dcc.Input(id="fecha", placeholder="YYYY-MM-DD"),
    dcc.Input(id="hora_inicio", placeholder="HH:MM"),
    dcc.Input(id="hora_fin", placeholder="HH:MM"),
    dcc.Input(id="responsable", placeholder="Nombre"),
    dcc.Input(id="grupo", placeholder="ELO-TECH-XX"),
    dcc.Input(id="email", placeholder="correo@usm.cl"),

    html.Button("Reservar", id="btn-reservar"),

    html.Div(id="resultado")
])

@app.callback(
    Output("tabla", "children"),
    Input("btn-refresh", "n_clicks")
)
def actualizar(n):
    reservas = obtener_reservas()
    return generar_tabla(reservas)

@app.callback(
    Output("resultado", "children"),
    Input("btn-reservar", "n_clicks"),
    State("fecha", "value"),
    State("hora_inicio", "value"),
    State("hora_fin", "value"),
    State("responsable", "value"),
    State("grupo", "value"),
    State("email", "value"),
)
def reservar(n, fecha, inicio, fin, responsable, grupo, email):
    if not n:
        return ""

    data = {
        "fecha": fecha,
        "hora_inicio": inicio,
        "hora_fin": fin,
        "responsable": responsable,
        "grupo": grupo,
        "email": email
    }

    r = requests.post(f"{BACKEND_URL}/reservas", json=data)

    return str(r.json())

if __name__ == "__main__":
    app.run(debug=True)