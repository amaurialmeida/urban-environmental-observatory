from __future__ import annotations

import os
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="Urban Environmental Observatory",
    page_icon="🌎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Catálogo embutido para permitir um teste simples somente com app.py.
# Não é necessário enviar data/cities.csv para o Streamlit Cloud.
DEFAULT_CITIES = [
    {"label": "Osasco, Brasil", "query": "Osasco, Brazil", "country": "Brasil", "region": "Sudeste", "latitude": -23.5329, "longitude": -46.7917},
    {"label": "São Paulo, Brasil", "query": "Sao Paulo, Brazil", "country": "Brasil", "region": "Sudeste", "latitude": -23.5505, "longitude": -46.6333},
    {"label": "Rio Gallegos, Argentina", "query": "Rio Gallegos, Argentina", "country": "Argentina", "region": "Patagônia", "latitude": -51.6230, "longitude": -69.2168},
    {"label": "Punta Arenas, Chile", "query": "Punta Arenas, Chile", "country": "Chile", "region": "Patagônia", "latitude": -53.1638, "longitude": -70.9171},
    {"label": "Bariloche, Argentina", "query": "San Carlos de Bariloche, Argentina", "country": "Argentina", "region": "Patagônia", "latitude": -41.1335, "longitude": -71.3103},
    {"label": "Ushuaia, Argentina", "query": "Ushuaia, Argentina", "country": "Argentina", "region": "Patagônia", "latitude": -54.8019, "longitude": -68.3030},
    {"label": "Puerto Williams, Chile", "query": "Puerto Williams, Chile", "country": "Chile", "region": "Patagônia", "latitude": -54.9333, "longitude": -67.6167},
]
CITIES = pd.DataFrame(DEFAULT_CITIES)
NUMBEO_BASE_URL = "https://www.numbeo.com/api"

# Os valores -2/+2 são transformados para uma escala intuitiva de 0 a 100.
# Em indicadores de problema, a escala é invertida para que maior seja melhor.
PERCEPTION_FIELDS = {
    "drinking_water_quality_accessibility": ("Água potável percebida", True),
    "water_pollution": ("Poluição da água percebida", False),
    "air_quality": ("Qualidade do ar percebida", True),
    "garbage_disposal_satisfaction": ("Descarte de resíduos percebido", True),
    "clean_and_tidy": ("Limpeza urbana percebida", True),
    "green_and_parks_quality": ("Áreas verdes percebidas", True),
    "comfortable_to_spend_time": ("Conforto ambiental percebido", True),
    "noise_and_light_pollution": ("Ruído e luz percebidos", False),
}


def value_to_score(value: Any, higher_is_better: bool) -> float | None:
    """Converte a resposta Numbeo (-2..2) para 0..100 orientado para melhor."""
    if value is None or pd.isna(value):
        return None
    try:
        score = (float(value) + 2.0) / 4.0 * 100.0
        return round(score if higher_is_better else 100.0 - score, 1)
    except (TypeError, ValueError):
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_numbeo_city(query: str, api_key: str) -> dict[str, Any]:
    """Busca índices gerais e percepção de poluição da cidade no Numbeo."""
    params = {"api_key": api_key, "query": query}
    indices_response = requests.get(
        f"{NUMBEO_BASE_URL}/indices", params=params, timeout=20
    )
    pollution_response = requests.get(
        f"{NUMBEO_BASE_URL}/city_pollution", params=params, timeout=20
    )
    indices_response.raise_for_status()
    pollution_response.raise_for_status()
    return {**indices_response.json(), **pollution_response.json()}


def normalize_city(raw: dict[str, Any], city_label: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "Cidade": city_label,
        "quality_of_life_index": raw.get("quality_of_life_index"),
        "pollution_index": raw.get("pollution_index", raw.get("index_pollution")),
        "contributors": raw.get("contributors", raw.get("contributors_pollution")),
        "last_update": "-".join(
            str(x)
            for x in [raw.get("yearLastUpdate"), raw.get("monthLastUpdate")]
            if x is not None
        )
        or "não informado",
        "numbeo_name": raw.get("name", city_label),
    }
    for field, (label, higher_is_better) in PERCEPTION_FIELDS.items():
        result[label] = value_to_score(raw.get(field), higher_is_better)
    return result


def show_metric_card(title: str, value_a: Any, value_b: Any, city_a: str, city_b: str):
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric(city_a, "—" if value_a is None else value_a)
    with col2:
        st.metric(title, "comparação")
    with col3:
        st.metric(city_b, "—" if value_b is None else value_b)


def radar_chart(a: dict[str, Any], b: dict[str, Any]) -> go.Figure:
    labels = [label for label, _ in PERCEPTION_FIELDS.values()]
    values_a = [a.get(label) or 0 for label in labels]
    values_b = [b.get(label) or 0 for label in labels]
    labels_closed = labels + [labels[0]]
    fig = go.Figure()
    for city, values, color in [
        (a["Cidade"], values_a, "#58d68d"),
        (b["Cidade"], values_b, "#67b7dc"),
    ]:
        fig.add_trace(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=labels_closed,
                fill="toself",
                name=city,
                line={"color": color, "width": 2},
                opacity=0.72,
            )
        )
    fig.update_layout(
        polar={
            "radialaxis": {"visible": True, "range": [0, 100], "ticksuffix": "%"},
            "angularaxis": {"tickfont": {"size": 11}},
        },
        height=560,
        margin={"l": 40, "r": 40, "t": 40, "b": 40},
        legend={"orientation": "h", "y": -0.12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def comparison_bar(a: dict[str, Any], b: dict[str, Any]) -> go.Figure:
    rows = [
        ("Qualidade de vida", a.get("quality_of_life_index"), b.get("quality_of_life_index")),
        ("Poluição percebida", a.get("pollution_index"), b.get("pollution_index")),
    ]
    labels = [r[0] for r in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(name=a["Cidade"], x=labels, y=[r[1] for r in rows], marker_color="#58d68d"))
    fig.add_trace(go.Bar(name=b["Cidade"], x=labels, y=[r[2] for r in rows], marker_color="#67b7dc"))
    fig.update_layout(
        barmode="group",
        yaxis_title="Índice Numbeo",
        height=380,
        margin={"l": 30, "r": 30, "t": 20, "b": 70},
        legend={"orientation": "h", "y": 1.08},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


st.markdown(
    """
    <style>
    .hero {padding: 1.2rem 1.5rem; border-radius: 18px; background: linear-gradient(120deg,#092b28,#115447); color:white; margin-bottom:1.2rem;}
    .hero h1 {font-size:2.45rem; margin:0; letter-spacing:-.04em;}
    .hero p {font-size:1.05rem; color:#c8efe0; max-width:850px; margin:.6rem 0 0;}
    .tag {display:inline-block; color:#8df0bd; font-weight:700; letter-spacing:.12em; font-size:.72rem; text-transform:uppercase; margin-bottom:.4rem;}
    .note {padding: .9rem 1rem; border-left: 4px solid #58d68d; background: rgba(88,214,141,.10); border-radius: 8px;}
    </style>
    <div class="hero">
      <div class="tag">Sistema exploratório de comparação socioambiental urbana</div>
      <h1>Urban Environmental Observatory</h1>
      <p>Veja a distância socioambiental entre grandes centros e cidades da Patagônia — combinando percepção dos usuários, infraestrutura e indicadores ambientais.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Escolha as cidades")
    city_labels = CITIES["label"].tolist()
    city_a_label = st.selectbox("Cidade A", city_labels, index=0)
    city_b_label = st.selectbox("Cidade B", city_labels, index=2)
    st.divider()
    st.caption("MVP · Camada ativa: percepção urbana via Numbeo")
    st.caption("Próximas camadas: ar medido, saneamento, resíduos e cobertura vegetal.")

api_key = st.secrets.get("NUMBEO_API_KEY", os.getenv("NUMBEO_API_KEY", ""))
if not api_key:
    st.warning(
        "Configure `NUMBEO_API_KEY` nos Secrets do Streamlit para carregar a comparação real. "
        "A chave nunca deve ser publicada no GitHub."
    )
    st.markdown(
        """
        <div class="note"><b>O MVP já está pronto para a API oficial.</b><br>
        No Streamlit Cloud, crie o secret <code>NUMBEO_API_KEY</code>. Depois, selecione duas cidades para ver os dados.</div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

row_a = CITIES.loc[CITIES["label"] == city_a_label].iloc[0]
row_b = CITIES.loc[CITIES["label"] == city_b_label].iloc[0]

try:
    with st.spinner("Consultando os indicadores urbanos..."):
        city_a = normalize_city(fetch_numbeo_city(row_a["query"], api_key), city_a_label)
        city_b = normalize_city(fetch_numbeo_city(row_b["query"], api_key), city_b_label)
except requests.RequestException as exc:
    st.error(f"Não foi possível consultar a API do Numbeo agora: {exc}")
    st.info("Verifique a chave, o plano contratado e os nomes das cidades aceitos pela API.")
    st.stop()

st.subheader(f"{city_a_label}  ×  {city_b_label}")
st.caption("Escala dos indicadores ambientais: 0–100, em que maior significa melhor percepção ambiental.")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Qualidade de vida · A", f"{city_a['quality_of_life_index']:.1f}" if city_a["quality_of_life_index"] is not None else "N/D")
col2.metric("Qualidade de vida · B", f"{city_b['quality_of_life_index']:.1f}" if city_b["quality_of_life_index"] is not None else "N/D")
col3.metric("Poluição · A", f"{city_a['pollution_index']:.1f}" if city_a["pollution_index"] is not None else "N/D", help="No índice original do Numbeo, menor é melhor.")
col4.metric("Poluição · B", f"{city_b['pollution_index']:.1f}" if city_b["pollution_index"] is not None else "N/D", help="No índice original do Numbeo, menor é melhor.")

st.plotly_chart(comparison_bar(city_a, city_b), use_container_width=True)

st.markdown("### A distância ambiental percebida")
left, right = st.columns([1.15, 1])
with left:
    st.plotly_chart(radar_chart(city_a, city_b), use_container_width=True)
with right:
    st.markdown(
        """
        <div class="note"><b>Como ler este painel</b><br><br>
        O gráfico não declara qual cidade é “melhor” em termos absolutos. Ele mostra como os usuários percebem diferentes dimensões ambientais e urbanas.
        <br><br><b>Próximo passo:</b> confrontar percepção com medições de qualidade do ar, cobertura de água e esgoto, resíduos e áreas verdes.</div>
        """,
        unsafe_allow_html=True,
    )
    st.metric("Contribuintes ambientais · A", city_a.get("contributors") or "N/D")
    st.metric("Contribuintes ambientais · B", city_b.get("contributors") or "N/D")

st.markdown("### Indicadores de percepção")
comparison = pd.DataFrame(
    {
        "Indicador": list(PERCEPTION_FIELDS.values()),
        city_a_label: [city_a.get(label) for label, _ in PERCEPTION_FIELDS.values()],
        city_b_label: [city_b.get(label) for label, _ in PERCEPTION_FIELDS.values()],
    }
)
comparison["Indicador"] = [x[0] for x in comparison["Indicador"]]
st.dataframe(comparison, hide_index=True, use_container_width=True)

with st.expander("Metodologia e limites"):
    st.markdown(
        f"""
        - **Fonte desta versão:** Numbeo API, dados de percepção urbana.
        - **Cidade A reconhecida pela API:** {city_a['numbeo_name']}.
        - **Cidade B reconhecida pela API:** {city_b['numbeo_name']}.
        - **Atualização informada pela API — A:** {city_a['last_update']}.
        - **Atualização informada pela API — B:** {city_b['last_update']}.
        - Os dados não representam análise laboratorial da água, medição oficial de saneamento ou monitoramento ambiental completo.
        - A ausência de contribuintes ou baixa cobertura pode aumentar a incerteza da comparação.
        - Consulte a [metodologia do Numbeo](https://www.numbeo.com/pollution/indices_explained.jsp) e seus [termos de uso](https://www.numbeo.com/common/terms_of_use.jsp).
        """
    )

st.download_button(
    "Baixar comparação em CSV",
    comparison.to_csv(index=False).encode("utf-8"),
    file_name="urban_environmental_observatory_comparacao.csv",
    mime="text/csv",
)

st.caption("Urban Environmental Observatory · MVP · Percepção não é medição: é o primeiro sinal para investigar.")
