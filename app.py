# ==========================================================
# DASHBOARD DU TP M1-ECAP  NOMMER: ECAP STORE
# ETUDIANT: Hamit Ahmat Hamit
# ==========================================================

import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, dash_table, Input, Output
import dash_bootstrap_components as dbc
import calendar

# ==========================================================
# 1) CHARGEMENT ET PREPARATION DES DONNEES
# ==========================================================

df = pd.read_csv("data.csv", usecols=[
    "Transaction_Date", "CustomerID", "Gender", "Location",
    "Product_Category", "Quantity", "Avg_Price",
    "Month", "Discount_pct"
])

df["CustomerID"] = df["CustomerID"].fillna(0).astype(int)
df["Transaction_Date"] = pd.to_datetime(df["Transaction_Date"])
df["Total_price"] = df["Quantity"] * df["Avg_Price"] * (1 - df["Discount_pct"] / 100)
df.sort_values("Transaction_Date", ascending=False, inplace=True)

# ==================================================================
# 2) PETITES FONCTIONS SIMPLES UTILISES POUR FORMATER LES NOMBRE
# ==================================================================

def format_k(nombre):
    if nombre >= 1000:
        return f"{int(round(nombre / 1000))}k"
    return str(int(round(nombre)))

def format_delta(nombre):
    if abs(nombre) >= 1000:
        return f"{int(round(abs(nombre) / 1000))}k"
    return str(int(round(abs(nombre))))

# ==================================================================
# 3)  FONCTIONS METIER
# ==================================================================

def calculer_chiffre_affaire(data):
    return data["Total_price"].sum()

def frequence_meilleure_vente(data, top=10, ascending=False):
    freq = (
        data.groupby(["Product_Category", "Gender"])
        .size()
        .reset_index(name="Total vente")
    )

    top_categories = (
        freq.groupby("Product_Category")["Total vente"]
        .sum()
        .sort_values(ascending=ascending)
        .head(top)
        .index
    )

    freq = freq[freq["Product_Category"].isin(top_categories)]

    ordre_categories = (
        freq.groupby("Product_Category")["Total vente"]
        .sum()
        .sort_values(ascending=ascending)
        .index
        .tolist()
    )

    return freq, ordre_categories

def indicateur_du_mois(data, current_month=12, freq=True, abbr=False):
    previous_month = current_month - 1
    if previous_month == 0:
        previous_month = 12

    nom_mois = calendar.month_abbr[current_month] if abbr else calendar.month_name[current_month]

    mask_current = data["Month"] == current_month
    mask_previous = data["Month"] == previous_month

    if freq:
        valeur_courante = mask_current.sum()
        valeur_precedente = mask_previous.sum()
    else:
        valeur_courante = data.loc[mask_current, "Total_price"].sum()
        valeur_precedente = data.loc[mask_previous, "Total_price"].sum()

    delta = valeur_courante - valeur_precedente

    return nom_mois, valeur_courante, valeur_precedente, delta

def barplot_top_10_ventes(data):
    freq, ordre_categories = frequence_meilleure_vente(data, top=10, ascending=False)

    fig = px.bar(
        freq,
        x="Total vente",
        y="Product_Category",
        color="Gender",
        orientation="h",
        barmode="group",
        category_orders={"Product_Category": ordre_categories},
        color_discrete_map={"F": "#636EFA", "M": "#EF553B"},
        title="Frequence des 10 meilleures ventes"
    )

    fig.update_layout(
        paper_bgcolor="#f5f5f5",
        plot_bgcolor="#e9eef5",
        font=dict(color="#243b67"),
        margin=dict(l=20, r=10, t=45, b=20),
        height=500,
        legend_title="Sexe",
        xaxis_title="Total vente",
        yaxis_title="Categorie du produit",
        title_x=0.02
    )

    fig.update_xaxes(showgrid=True, gridcolor="white", zeroline=False)
    fig.update_yaxes(showgrid=False)

    return fig

def plot_evolution_chiffre_affaire(data):
    ca_semaine = (
        data.groupby(pd.Grouper(key="Transaction_Date", freq="W"))["Total_price"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        ca_semaine,
        x="Transaction_Date",
        y="Total_price",
        title="Evolution du chiffre d'affaire par semaine",
        labels={
            "Transaction_Date": "Semaine",
            "Total_price": "Chiffre d'affaire"
        }
    )

    fig.update_traces(line=dict(color="#5b66ff", width=2))

    fig.update_layout(
        paper_bgcolor="#f5f5f5",
        plot_bgcolor="#e9eef5",
        font=dict(color="#243b67"),
        margin=dict(l=20, r=10, t=45, b=20),
        height=340,
        title_x=0.02
    )

    fig.update_xaxes(showgrid=True, gridcolor="white", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="white", zeroline=False)

    return fig

def plot_chiffre_affaire_mois(data):
    ca_mois = (
        data.groupby("Month", as_index=False)["Total_price"]
        .sum()
        .sort_values("Month")
    )

    fig = px.bar(
        ca_mois,
        x="Month",
        y="Total_price",
        title="Chiffre d'affaire par mois",
        labels={"Month": "Mois", "Total_price": "Chiffre d'affaire"}
    )

    return fig

def plot_vente_mois(data, abbr=False):
    ventes_mois = (
        data.groupby("Month", as_index=False)
        .size()
        .rename(columns={"size": "Nombre de ventes"})
        .sort_values("Month")
    )

    if abbr:
        ventes_mois["Nom_Mois"] = ventes_mois["Month"].apply(lambda x: calendar.month_abbr[x])
    else:
        ventes_mois["Nom_Mois"] = ventes_mois["Month"].apply(lambda x: calendar.month_name[x])

    fig = px.bar(
        ventes_mois,
        x="Nom_Mois",
        y="Nombre de ventes",
        title="Nombre de ventes par mois",
        labels={"Nom_Mois": "Mois", "Nombre de ventes": "Nombre de ventes"}
    )

    return fig


# ==========================================================
# 4) LISTE DU DROPDOWN
# ==========================================================

options_zones = [
    {"label": zone, "value": zone}
    for zone in sorted(df["Location"].dropna().unique())
]

# ==========================================================
# 5) CREATION DE L'APP
# ==========================================================

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "ECAP Store"

server = app.server 

# ==========================================================
# 6) STYLES CSS UTILISEE 
# ==========================================================

style_page = {
    "backgroundColor": "#f5f5f5",
    "minHeight": "100vh",
    "fontFamily": "Arial"
}

style_header = {
    "backgroundColor": "#c8e7f1",
    "padding": "16px 12px",
    "display": "flex",
    "justifyContent": "space-between",
    "alignItems": "center"
}

style_kpi_box = {
    "backgroundColor": "#f5f5f5",
    "borderRadius": "6px",
    "padding": "10px 6px 0px 6px",
    "height": "210px"
}

style_kpi_title = {
    "textAlign": "center",
    "fontSize": "18px",
    "color": "#243b67",
    "marginTop": "6px",
    "marginBottom": "10px"
}

style_kpi_value = {
    "textAlign": "center",
    "fontSize": "74px",
    "color": "#243b67",
    "lineHeight": "1",
    "fontWeight": "500"
}

# ==========================================================
# 7) LAYOUT DU DASHBOARD
# ==========================================================

app.layout = html.Div(
    style=style_page,
    children=[

        # HEADER
        html.Div(
            style=style_header,
            children=[
                html.H1(
                    "ECAP Store",
                    style={
                        "margin": "0",
                        "fontSize": "32px",
                        "fontWeight": "600",
                        "color": "#1f2d3d"
                    }
                ),
                html.Div(
                    style={"width": "395px"},
                    children=[
                        dcc.Dropdown(
                            id="zone-dropdown",
                            options=options_zones,
                            value=[],
                            multi=True,
                            placeholder="Choisissez des zones"
                        )
                    ]
                )
            ]
        ),

        # CONTENU
        dbc.Container(
            fluid=True,
            style={"padding": "24px 26px 18px 26px"},
            children=[
                dbc.Row([

                    # COLONNE GAUCHE
                    dbc.Col(
                        md=5,
                        children=[
                            dbc.Row(
                                className="mb-3",
                                children=[
                                    dbc.Col(
                                        html.Div([
                                            html.Div("December", id="ca-title", style=style_kpi_title),
                                            html.Div(id="ca-value", style=style_kpi_value),
                                            html.Div(id="ca-delta")
                                        ], style=style_kpi_box),
                                        md=6
                                    ),
                                    dbc.Col(
                                        html.Div([
                                            html.Div("December", id="sales-title", style=style_kpi_title),
                                            html.Div(id="sales-value", style=style_kpi_value),
                                            html.Div(id="sales-delta")
                                        ], style=style_kpi_box),
                                        md=6
                                    )
                                ]
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id="bar-chart", config={"displayModeBar": False}),
                                    width=12
                                )
                            ])
                        ]
                    ),

                    # COLONNE DROITE
                    dbc.Col(
                        md=7,
                        children=[
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id="line-chart", config={"displayModeBar": False}),
                                    width=12
                                )
                            ]),
                            dbc.Row([
                                dbc.Col([
                                    html.H3(
                                        "Table des 100 dernières ventes",
                                        style={
                                            "fontSize": "18px",
                                            "color": "#222",
                                            "marginTop": "8px",
                                            "marginBottom": "10px"
                                        }
                                    ),
                                    dash_table.DataTable(
                                        id="sales-table",
                                        page_size=10,
                                        filter_action="native",
                                        sort_action="native",
                                        style_table={
                                            "overflowX": "auto",
                                            "backgroundColor": "#f5f5f5"
                                        },
                                        style_header={
                                            "backgroundColor": "#f0f0f0",
                                            "fontWeight": "bold",
                                            "fontSize": "13px",
                                            "border": "1px solid #d0d0d0",
                                            "textAlign": "center"
                                        },
                                        style_cell={
                                            "backgroundColor": "#f9f9f9",
                                            "color": "#222",
                                            "textAlign": "center",
                                            "padding": "8px",
                                            "fontSize": "13px",
                                            "fontFamily": "Arial",
                                            "border": "1px solid #dcdcdc",
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                            "minWidth": "90px",
                                            "width": "90px",
                                            "maxWidth": "160px"
                                        }
                                    )
                                ], width=12)
                            ])
                        ]
                    )
                ])
            ]
        )
    ]
)

# ==========================================================
# 8) CALLBACK PRINCIPAL POUR FAIRE LES ELEMENTS INTERACTIVE
# ==========================================================

@app.callback(
    Output("ca-title", "children"),
    Output("ca-value", "children"),
    Output("ca-delta", "children"),
    Output("sales-title", "children"),
    Output("sales-value", "children"),
    Output("sales-delta", "children"),
    Output("ca-delta", "style"),
    Output("sales-delta", "style"),
    Output("bar-chart", "figure"),
    Output("line-chart", "figure"),
    Output("sales-table", "data"),
    Output("sales-table", "columns"),
    Input("zone-dropdown", "value")
)
def update_dashboard(zone):

    # ------------------------------------------------------
    # FILTRER LES DONNEES
    # ------------------------------------------------------
    #dff = df if not zone else df[df["Location"].isin(zone)] c'est une autre alternative qu'on pourra utiliser

    if zone:
        dff = df[df["Location"].isin(zone)]
    else:
        dff = df

    # ------------------------------------------------------
    # KPI 1 : CHIFFRE D'AFFAIRE DE DECEMBRE
    # ------------------------------------------------------
    mois_ca, ca_decembre, ca_novembre, delta_ca = indicateur_du_mois(
        dff, current_month=12, freq=False, abbr=False
    )

    # ------------------------------------------------------
    # KPI 2 : NOMBRE DE VENTES DE DECEMBRE
    # ------------------------------------------------------
    mois_ventes, ventes_decembre, ventes_novembre, delta_ventes = indicateur_du_mois(
        dff, current_month=12, freq=True, abbr=False
    )

    # Texte des KPI
    texte_ca = format_k(ca_decembre)
    texte_ventes = str(ventes_decembre)

    if delta_ca < 0:
        texte_delta_ca = "▼ -" + format_delta(delta_ca)
        couleur_ca = "#ff4136"
    else:
        texte_delta_ca = "▲ " + format_delta(delta_ca)
        couleur_ca = "#2ca25f"

    if delta_ventes < 0:
        texte_delta_ventes = "▼ -" + format_delta(delta_ventes)
        couleur_ventes = "#ff4136"
    else:
        texte_delta_ventes = "▲ " + format_delta(delta_ventes)
        couleur_ventes = "#2ca25f"

    style_delta_ca = {
        "textAlign": "center",
        "fontSize": "38px",
        "fontWeight": "500",
        "marginTop": "2px",
        "color": couleur_ca
    }

    style_delta_ventes = {
        "textAlign": "center",
        "fontSize": "38px",
        "fontWeight": "500",
        "marginTop": "2px",
        "color": couleur_ventes
    }

    # ------------------------------------------------------
    # GRAPHIQUE 1 : TOP 10 DES MEILLEURES VENTES
    # ------------------------------------------------------
    fig_bar = barplot_top_10_ventes(dff)

    # ------------------------------------------------------
    # GRAPHIQUE 2 : EVOLUTION DU CHIFFRE D'AFFAIRE
    # ------------------------------------------------------
    fig_line = plot_evolution_chiffre_affaire(dff)

    # ------------------------------------------------------
    # TABLE DES 100 DERNIERES VENTES
    # ------------------------------------------------------
    cols_table = [
        "Transaction_Date", "Gender", "Location",
        "Product_Category", "Quantity", "Avg_Price", "Discount_pct"
    ]

    table_df = (
        dff[cols_table]
        .head(100)
        .assign(
            Transaction_Date=lambda x: x["Transaction_Date"].dt.strftime("%Y-%m-%d"),
            Avg_Price=lambda x: x["Avg_Price"].round(2),
            Discount_pct=lambda x: x["Discount_pct"].round(0)
        )
    )

    data_table = table_df.to_dict("records")
    colonnes_table = [{"name": col, "id": col} for col in cols_table]

    return (
        mois_ca,
        texte_ca,
        texte_delta_ca,
        mois_ventes,
        texte_ventes,
        texte_delta_ventes,
        style_delta_ca,
        style_delta_ventes,
        fig_bar,
        fig_line,
        data_table,
        colonnes_table
    )

# ==========================================================
# 8) EXECUTION
# ==========================================================

if __name__ == "__main__":
    app.run_server(debug=True)