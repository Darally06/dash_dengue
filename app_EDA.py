# Analisis exploratorio de datos

# Importar librerías
# Librerias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from unidecode import unidecode
import folium
import plotly.graph_objects as go
import json
import dash
from dash import dash_table
from dash import dcc, html
import os
#import openpyxl

# 🔹 Lectura de la base de datos
data = pd.read_csv("Base_dengue.csv", dtype={11:str, 36:str})
#Seleccion de variables de estudio"
columnas = [ "EDAD_AJUSTADA", "SEXO", "TIP_SS", 
            "GP_MIGRANT", "GP_POBICFB", "GP_GESTAN", 
            "AREA", "PAIS_OCU", "DPTO_OCU", "MUN_OCU",
            "SEMANA", "ANO", 
            "EVENTO", "TIP_CAS", "ESTADO_FINAL", "CASO", 
            "PAC_HOS", "CON_FIN", "confirmados",
           ]
df = data[columnas]
df.loc[:,"ESTADO_FINAL"] = df["ESTADO_FINAL"].fillna(0).astype(int)


# 1. Información demográfica
# 1.1 Edad ajustada

# Ajuste de edades menores a un año (Representación de en días, semanas o meses, variable que representa años)
df.loc[df["EDAD_AJUSTADA"] > 114, "EDAD_AJUSTADA"] = np.nan
df.loc[df["EDAD_AJUSTADA"] < 1, "EDAD_AJUSTADA"] = 1 

fig_edad = px.box(df, x="EDAD_AJUSTADA", color_discrete_sequence=["dodgerblue"])
fig_edad.update_layout(
    title="Distribución de la edad",
    xaxis_title="Edad",
    yaxis_title="Frecuencia",
    title_font=dict(size=18, family='Arial', color='black')
)

# 1.1.1 Edad menor a 5 años
menores = df[df["EDAD_AJUSTADA"] <= 5]
conteo = menores["EDAD_AJUSTADA"].value_counts().sort_index()
df_conteo = conteo.reset_index()
df_conteo.columns = ["EDAD_AJUSTADA", "FRECUENCIA"]

fig_edad_5 = px.bar(df_conteo, x="EDAD_AJUSTADA", y="FRECUENCIA", 
             color_discrete_sequence=["royalblue"])

fig_edad_5.update_layout(
    title="Distribución de Edades Menores a 5 años",
    xaxis_title="Edad",
    yaxis_title="Frecuencia",
    title_font=dict(size=20, family='Arial')
)

# 1.1.2 Edad mayor a 65 años
mayores= df[df["EDAD_AJUSTADA"] >= 65]
conteo_m = mayores["EDAD_AJUSTADA"].value_counts().sort_index()
df_conteo_m = conteo_m.reset_index()
df_conteo_m.columns = ["EDAD_AJUSTADA", "FRECUENCIA"]

fig_edad_65 = px.box(df_conteo_m, x="EDAD_AJUSTADA", 
             color_discrete_sequence=["royalblue"])
fig_edad_65.update_layout(
    title="Distribución de Edades Menores a 65 años",
    xaxis_title="Edad",
    yaxis_title="Frecuencia",
    title_font=dict(size=20, family='Arial', color='blue')
)

# 1.2 General
# 1.2.1 Sexo
sexo_tabla = df["SEXO"].value_counts(normalize=True).mul(100).round(2).reset_index()
sexo_tabla.columns = ["Sexo", "Porcentaje"]

# 1.2.2 Tipo de seguro
seguro_tabla = df["TIP_SS"].value_counts(normalize=True).mul(100).round(2).reset_index()
seguro_tabla.columns = ["Tipo de Seguro", "Porcentaje"]

# 1.2.3 Grupo poblacional
grupo_cols = ["GP_MIGRANT", "GP_GESTAN", "GP_POBICFB"]
conteo_grupos = df[grupo_cols].apply(lambda x: (x == 1).sum())
grupo_tabla = pd.DataFrame({"Grupo de Pertenencia": conteo_grupos.index, "Cantidad de Personas": conteo_grupos.values})

# 1.2.4 Area de residencia
area_tabla = df["AREA"].value_counts(normalize=True).mul(100).round(2).reset_index()
area_tabla.columns = ["Área", "Porcentaje"]

# 2. Ubicación geográfica
# 2.1 Departamentos (top 10)

# Cargar datos del archivo GeoJSON
with open("Mapa_Depto.geojson", "r", encoding="utf-8") as f:
    geojson = json.load(f)

todos_dptos = [f["properties"]["dpto_cnmbr"] for f in geojson["features"]]
df_mapa = pd.DataFrame({"Departamento": todos_dptos})
correcciones = {
    "VALLE": "VALLE DEL CAUCA",
    "NARIÑO": "NARINO",
    "NORTE SANTANDER": "NORTE DE SANTANDER",
    "BOGOTA": "BOGOTA, D.C.",
    "GUAJIRA": "LA GUAJIRA",
    "SAN ANDRES": "ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA",
    "PROCEDENCIA DESCONOCIDA": None,
    "EXTERIOR": None
}

df.loc[:,"DPTO_OCU"] = df["DPTO_OCU"].replace(correcciones)
df = df[df["DPTO_OCU"].notna()]

# Tabla
top10 = df["DPTO_OCU"].value_counts().nlargest(10)
tabla_dptos = pd.DataFrame({
    "Departamento": top10.index,
    "Casos_top10": top10.values
})

# Mapa
df_mapa = df_mapa.merge(tabla_dptos, on="Departamento", how="left")
df_mapa["Casos_top10"] = df_mapa["Casos_top10"].fillna(0)

mapa_10 = px.choropleth(
    df_mapa,
    geojson=geojson,
    locations="Departamento",
    featureidkey="properties.dpto_cnmbr",  # este campo depende de tu archivo JSON
    color="Casos_top10",
    color_continuous_scale="Blues",
    title="Top 10 Departamentos con Mayor Ocurrencia de Dengue",
)
mapa_10.update_geos(fitbounds="locations", visible=False)
mapa_10.update_layout(margin={"r":0, "t":40, "l":0, "b":0})

# 2.2 Departamentos por densidad poblacional
# Leer base departamentos
deptos = pd.read_excel("poblacion_departamentos_colombia_2018.xlsx")
deptos.rename(columns={"Población Censada 2018": "Poblacion"}, inplace=True)
deptos["Departamento"] = deptos["Departamento"].apply(lambda x: unidecode(x.upper()))
deptos["Departamento"] = deptos["Departamento"].replace({
    "SAN ANDRES, PROVIDENCIA Y SANTA CATALINA": "ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA"
})

# Contar los casos por departamento
casos_por_dpto = df["DPTO_OCU"].value_counts().reset_index()
casos_por_dpto.columns = ["Departamento", "Casos"]

df_final = pd.merge(casos_por_dpto, deptos, on="Departamento", how="left")

# Calcular la densidad de casos por 10,000 habitantes
df_final["Densidad_Casos"] = (df_final["Casos"] / df_final["Poblacion"]) * 100000
df_final = df_final.sort_values(by="Densidad_Casos", ascending=False)

df_final["Departamento"] = df_final["Departamento"].apply(lambda x: unidecode(x.upper()))

for feature in geojson["features"]:
    dpto = unidecode(feature["properties"]["dpto_cnmbr"].upper())
    match = df_final[df_final["Departamento"] == dpto]
    if not match.empty:
        feature["properties"]["casos"] = int(match["Casos"].values[0])
        feature["properties"]["densidad"] = round(match["Densidad_Casos"].values[0], 2)
    else:
        feature["properties"]["casos"] = 0
        feature["properties"]["densidad"] = 0

# Crear mapa base centrado en Colombia
m = folium.Map(location=[4.5709, -74.2973], zoom_start=5)
# Crear choropleth
choropleth = folium.Choropleth(
    geo_data=geojson,
    name="Choropleth",
    data=df_final,
    columns=["Departamento", "Densidad_Casos"],
    key_on="feature.properties.dpto_cnmbr",  # <-- AJUSTA este campo según tu geojson
    fill_color="Blues",
    fill_opacity=0.7,
    line_opacity=0.2,
    legend_name="Densidad de Casos por 100,000 Habitantes",
    nan_fill_color="white",
).add_to(m)
# Agregar tooltip con el nombre y la densidad
folium.GeoJsonTooltip(
    fields=["dpto_cnmbr", "casos", "densidad"],  # <-- campo del GeoJSON
    aliases=["Departamento:", "Casos:", "Densidad:"],
    localize=True,
    sticky=False,
    labels=True,
    style="background-color: white; color: black; font-size: 12px; padding: 5px;",
).add_to(choropleth.geojson)
m.save("mapa_dengue.html")

# 2.3 Municipios (top 10)
municipios_casos = df["MUN_OCU"].value_counts()
tops = {
    "Top 5": municipios_casos.nlargest(5),
    "Top 10": municipios_casos.nlargest(10),
    "Top 15": municipios_casos.nlargest(15),
    "Top 20": municipios_casos.nlargest(20),
}

fig_mun = go.Figure()
for i, (label, data) in enumerate(tops.items()):
    data = data.sort_values(ascending=True)  # Ordenar de menor a mayor para el gráfico horizontal
    fig_mun.add_trace(go.Bar(
        x=data.values,
        y=data.index,
        orientation='h',
        name=label,
        visible=(i == 1),  # Mostrar Top 10 por defecto
        marker=dict(color='dodgerblue')
    ))
buttons = []
for i, label in enumerate(tops.keys()):
    visible = [False] * len(tops)
    visible[i] = True
    buttons.append(
        dict(
            label=label,
            method="update",
            args=[{"visible": visible},
                  {"title": f"{label} Municipios con más casos"}]
        )
    )
fig_mun.update_layout(
    title='Municipios con más casos reportados de dengue',
    xaxis_title='Frecuencia',
    yaxis_title='Municipios',
    updatemenus=[dict(
        buttons=buttons,
        direction="down",
        x=1.05,
        xanchor="left",
        y=1.1,
        yanchor="top"
    )],
    height=700,
    margin=dict(l=100, r=40, t=80, b=40)
)

# 3. Variables temporales
conteo_semanal_anual = df.groupby(["ANO", "SEMANA"]).size().unstack(level=0, fill_value=0)
fig_semana = go.Figure()
for año in conteo_semanal_anual.columns:
    fig_semana.add_trace(go.Scatter(
        x=conteo_semanal_anual.index,
        y=conteo_semanal_anual[año],
        mode="lines",
        name=str(año),
        line=dict(width=2)
    ))
fig_semana.update_layout(
    title="Casos de Dengue por Semana y Año",
    xaxis_title="Semana",
    yaxis_title="Número de Casos",
    template="plotly_white",
    hovermode="x unified",
    legend_title="Año"
)

# 4. Datos clínicos
# 4.1 Evento

# Casos por año y tipo de evento
df_eventos = df.groupby(["ANO", "EVENTO"]).size().reset_index(name="Pacientes")
fig_eve_y = px.bar(
    df_eventos,
    x="ANO",
    y="Pacientes",
    color="EVENTO",
    title="Pacientes por Evento y Año",
    labels={"ANO": "Año", "Pacientes": "Número de Pacientes"},
    barmode="group",  # Agrupa las barras por año
    color_discrete_map={"DENGUE": "dodgerblue", "DENGUE GRAVE": "mediumblue"}
)
fig_eve_y.update_layout(
    xaxis=dict(tickmode="linear"),
    legend_title="Evento",
    hovermode="x",
    template="plotly_white"
)

# 4.2 Estado final del caso
df_estado = df[df["ESTADO_FINAL"].isin([2, 3, 5])].copy()
estado_map = {
    2: "Probable",
    3: "C. por laboratorio",
    5: "C. por nexo"
}
df_estado["ESTADO_FINAL"] = df_estado["ESTADO_FINAL"].map(estado_map)
df_estado = df_estado.groupby(["ANO", "ESTADO_FINAL"]).size().reset_index(name="Frecuencia")

fig_est = px.bar(
    df_estado,
    x="ANO",
    y="Frecuencia",
    color="ESTADO_FINAL",
    title="Estado Final del Caso por Año",
    labels={"ANO": "Año", "Frecuencia": "Número de Casos", "ESTADO_FINAL": "Estado Final"},
    barmode="group",  # Agrupa las barras por año
    color_discrete_map={
        "Probable": "mediumblue",
        "C. por laboratorio": "deepskyblue",
        "C. por nexo": "royalblue"
    }
)
fig_est.update_layout(
    xaxis=dict(tickmode="linear"),
    legend_title="Estado Final",
    hovermode="x",
    template="plotly_white"
)

# 4.3 Confirmados
df["confirmados_str"] = df["confirmados"].map({0: "No", 1: "Sí"})
df_conf = df.groupby(["ANO", "confirmados_str"]).size().reset_index(name="Frecuencia")
fig_cf = px.bar(
    df_conf,
    x="ANO",
    y="Frecuencia",
    color="confirmados_str",
    title="Distribución de Casos confirmados por año",
    labels={"ANO": "Año", "Frecuencia": "Número de Casos", "confirmados_str": "Confirmados"},
    barmode="group",
    color_discrete_map={"No": "deepskyblue", "Sí": "blue"}
)
fig_cf.update_layout(
    template="plotly_white",
    hovermode="x",
    legend_title="Confirmados"
)

# 4.4 Hospitalizados
# Agrupar por año y hospitalización
df_hosp = df[df["PAC_HOS"] == 1]
df_hosp = df_hosp.groupby("ANO").size().reset_index(name="Frecuencia")
fig_hosp = px.bar(
    df_hosp,
    x="ANO",
    y="Frecuencia",
    color_discrete_sequence=["dodgerblue"],
    title="Pacientes Hospitalizados por Año",
    labels={"ANO": "Año", "Frecuencia": "Número de Casos"},
)
fig_hosp.update_layout(
    template="plotly_white",
    hovermode="x unified"
)

# Agrupar por sexo
df_hosp_grouped = df.groupby(["ANO", "SEXO"]).size().reset_index(name="Frecuencia")
fig_hosp_sex = px.bar(
    df_hosp_grouped,
    x="ANO",
    y="Frecuencia",
    color="SEXO",
    title="Pacientes Hospitalizados por Año y Sexo",
    labels={"ANO": "Año", "Frecuencia": "Pacientes Hospitalizados", "sexo_label": "Sexo"},
    barmode="group",
    color_discrete_map={"M": "blue", "F": "indianred"}
)
fig_hosp_sex.update_layout(
    template="plotly_white",
    hovermode="x unified",
    legend_title="Sexo"
)

# 4.5 Decesos
df_decesos = df[df["CON_FIN"] == 2]
tabla_decesos = df_decesos["EVENTO"].value_counts().reset_index()
tabla_decesos.columns = ["Evento", "Decesos"]
fig_des = px.pie(
    tabla_decesos,
    names="Evento",
    values="Decesos",
    title="Distribución de Decesos por Evento",
    color_discrete_sequence=px.colors.sequential.Blues,
    hole=0.4  # Si quieres estilo "donut"
)
fig_des.update_traces(
    textposition="inside",
    textinfo="percent+label",
    hovertemplate="%{label}: %{value} casos (%{percent})"
)

def tabla_dash(dataframe):
    return dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in dataframe.columns],
        data=dataframe.to_dict("records"),
        style_header={'backgroundColor': '#f0f0f0', 'fontWeight': 'bold'},
        style_cell={"textAlign": "center", "padding": "8px"},
        style_table={'height': '300px', 'overflowY': 'auto'},  # Definir el tamaño de la tabla
        style_data={"textAlign": "center"},
    )

#______________________________________
# Crear la aplicación Dash
app_EDA = dash.Dash(__name__)
server = app_EDA.server

app_EDA.title = "Visualización de Dengue"

# Layout de la aplicación
app_EDA.layout = html.Div([
    html.H1("Análisis Exploratorio de Casos de Dengue en Colombia", style={'textAlign': 'center'}),

    dcc.Tabs([
        dcc.Tab(label='Información Demográfica', children=[

            html.H3("Distribución de Edades", style={'marginTop': '30px'}),
            dcc.Graph(figure=fig_edad),

            html.H3("Edades menores a 5 años"),
            dcc.Graph(figure=fig_edad_5),

            html.H3("Edades mayores o iguales a 65 años"),
            dcc.Graph(figure=fig_edad_65),

            html.H3("Sexo"),
            tabla_dash(sexo_tabla),

            html.H3("Tipo de seguro"),
            tabla_dash(seguro_tabla),

            html.H3("Grupo Poblacional"),
            tabla_dash(grupo_tabla),

            html.H3("Área de residencia"),
            tabla_dash(area_tabla),
        ]),

        dcc.Tab(label='Ubicación Geográfica', children=[

            html.H3("Top 10 Departamentos con más casos", style={'marginTop': '30px'}),
            dcc.Graph(figure=mapa_10),

            html.H3("Mapa de Densidad de Casos por Departamento"),
            html.Iframe(srcDoc=open("mapa_dengue.html", "r", encoding="utf-8").read(), width="100%", height="600px"),

            html.H3("Top 10 Municipios con más casos"),
            dcc.Graph(figure=fig_mun),

        ]),
        dcc.Tab(label='Variables Temporales', children=[

            html.H3("Casos de Dengue por Semana y Año", style={'marginTop': '30px'}),
            dcc.Graph(figure=fig_semana),

        ]),
        dcc.Tab(label='Datos Clínicos', children=[
            html.H3("Pacientes por Evento", style={'marginTop': '30px'}),
            dcc.Graph(figure=fig_eve_y),

            html.H3("Estado Final del Caso"),
            dcc.Graph(figure=fig_est),

            html.H3("Casos Confirmados"),
            dcc.Graph(figure=fig_cf),

            html.H3("Pacientes Hospitalizados"),
            dcc.Graph(figure=fig_hosp),
            dcc.Graph(figure=fig_hosp_sex),

            html.H3("Decesos por Evento"),
            dcc.Graph(figure=fig_des),
        ])

    ]),
])


# Ejecutar la aplicación
if __name__ == "__main__":
            port = int(os.environ.get("PORT", 8050))
    app_EDA.run_server(host='0.0.0.0', port=port)




