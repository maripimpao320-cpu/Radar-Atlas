import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Radar Atlas", layout="wide")

GRUPOS = {
    "MAJORS": {
        "bitcoin": "BTC",
        "ethereum": "ETH",
        "solana": "SOL",
        "ripple": "XRP",
        "dogecoin": "DOGE",
    },
    "INFRA_L1": {
        "chainlink": "LINK",
        "avalanche-2": "AVAX",
        "cardano": "ADA",
        "sui": "SUI",
    },
    "NARRATIVAS": {
        "hyperliquid": "HYPE",
        "injective-protocol": "INJ",
        "bittensor": "TAO",
    }
}

TODAS_AS_MOEDAS = {}
for grupo in GRUPOS.values():
    TODAS_AS_MOEDAS.update(grupo)

GRUPO_POR_COIN = {}
for nome_grupo, moedas in GRUPOS.items():
    for coin_id in moedas:
        GRUPO_POR_COIN[coin_id] = nome_grupo

URL = "https://api.coingecko.com/api/v3/simple/price"
PARAMS = {
    "ids": ",".join(TODAS_AS_MOEDAS.keys()),
    "vs_currencies": "usd",
    "include_24hr_change": "true"
}

FG_URL = "https://api.alternative.me/fng/"


def classificar(change):
    if change is None:
        return "SEM DADO"
    if change >= 4:
        return "FORTE"
    elif change >= 1:
        return "POSITIVO"
    elif change >= -1:
        return "NEUTRO"
    return "FRACO"


def nota_geral(status):
    if status == "FORTE":
        return "A"
    elif status == "POSITIVO":
        return "B"
    elif status == "NEUTRO":
        return "C"
    elif status == "FRACO":
        return "D"
    return "-"


def score_day_trade(change, grupo):
    score = 0

    if change is None:
        return 0, "D"

    if change >= 6:
        score += 4
    elif change >= 4:
        score += 3
    elif change >= 2:
        score += 2
    elif change >= 0:
        score += 1
    else:
        score -= 2

    if grupo in ["NARRATIVAS", "INFRA_L1"]:
        score += 1

    if score >= 4:
        return score, "A"
    elif score >= 2:
        return score, "B"
    elif score >= 0:
        return score, "C"
    return score, "D"


def score_swing_trade(change, grupo):
    score = 0

    if change is None:
        return 0, "D"

    if change >= 4:
        score += 2
    elif change >= 1:
        score += 2
    elif change >= -1:
        score += 1
    else:
        score -= 2

    if grupo == "MAJORS":
        score += 2
    elif grupo == "INFRA_L1":
        score += 1

    if change >= 10:
        score -= 1

    if score >= 4:
        return score, "A"
    elif score >= 2:
        return score, "B"
    elif score >= 0:
        return score, "C"
    return score, "D"


@st.cache_data(ttl=300)
def buscar_dados():
    response = requests.get(URL, params=PARAMS, timeout=20)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=300)
def buscar_fear_greed():
    response = requests.get(FG_URL, timeout=15)
    response.raise_for_status()
    data = response.json()["data"][0]
    return {
        "valor": int(data["value"]),
        "texto": data["value_classification"]
    }


def montar_dataframe(data):
    linhas = []

    for coin_id, ticker in TODAS_AS_MOEDAS.items():
        if coin_id not in data:
            continue

        grupo = GRUPO_POR_COIN[coin_id]
        preco = data[coin_id]["usd"]
        variacao = data[coin_id].get("usd_24h_change", 0)

        status = classificar(variacao)
        nota = nota_geral(status)
        day_score, day_nota = score_day_trade(variacao, grupo)
        swing_score, swing_nota = score_swing_trade(variacao, grupo)

        linhas.append({
            "Ticker": ticker,
            "Grupo": grupo,
            "Preço": preco,
            "Variação 24h %": round(variacao, 2),
            "Status": status,
            "Nota Geral": nota,
            "Day Nota": day_nota,
            "Day Score": day_score,
            "Swing Nota": swing_nota,
            "Swing Score": swing_score
        })

    df = pd.DataFrame(linhas)
    df = df.sort_values("Variação 24h %", ascending=False).reset_index(drop=True)
    return df


def colorir_nota(valor):
    if valor == "A":
        return "background-color: #1f7a1f; color: white;"
    elif valor == "B":
        return "background-color: #1565c0; color: white;"
    elif valor == "C":
        return "background-color: #b28704; color: black;"
    elif valor == "D":
        return "background-color: #b71c1c; color: white;"
    return ""


def estilizar_dataframe(df):
    cols_notas = [c for c in ["Nota Geral", "Day Nota", "Swing Nota"] if c in df.columns]
    styler = df.style
    for col in cols_notas:
        styler = styler.map(colorir_nota, subset=[col])
    return styler


def top3_texto(df):
    top = df.head(3)
    return " | ".join([f"{r['Ticker']} ({r['Variação 24h %']}%)" for _, r in top.iterrows()])


def bottom3_texto(df):
    bot = df.sort_values("Variação 24h %", ascending=True).head(3)
    return " | ".join([f"{r['Ticker']} ({r['Variação 24h %']}%)" for _, r in bot.iterrows()])


def filtrar_dataframe(df, grupo_escolhido, notas_escolhidas):
    df_filtrado = df.copy()

    if grupo_escolhido != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["Grupo"] == grupo_escolhido]

    if notas_escolhidas:
        df_filtrado = df_filtrado[df_filtrado["Nota Geral"].isin(notas_escolhidas)]

    return df_filtrado


def texto_fg(valor):
    if valor >= 75:
        return "Ganância extrema"
    elif valor >= 55:
        return "Ganância"
    elif valor >= 45:
        return "Neutro"
    elif valor >= 25:
        return "Medo"
    return "Medo extremo"


st.title("Radar Atlas")
st.caption("Watchlist cripto com leitura geral, day trade, swing trade e sentimento")

col_a, col_b, col_c = st.columns([1, 1, 1])
with col_a:
    grupo_escolhido = st.selectbox(
        "Filtrar grupo",
        ["TODOS", "MAJORS", "INFRA_L1", "NARRATIVAS"]
    )

with col_b:
    notas_escolhidas = st.multiselect(
        "Filtrar nota geral",
        ["A", "B", "C", "D"],
        default=[]
    )

with col_c:
    if st.button("Atualizar radar"):
        st.cache_data.clear()
        st.rerun()

try:
    dados = buscar_dados()
    fg = buscar_fear_greed()
    df = montar_dataframe(dados)
    df_filtrado = filtrar_dataframe(df, grupo_escolhido, notas_escolhidas)

    if df_filtrado.empty:
        st.warning("Nenhum ativo encontrado com esse filtro.")
        st.stop()

    mais_forte = df_filtrado.sort_values("Variação 24h %", ascending=False).iloc[0]
    mais_fraca = df_filtrado.sort_values("Variação 24h %", ascending=True).iloc[0]

    day_top = df_filtrado.sort_values(["Day Score", "Variação 24h %"], ascending=[False, False])
    swing_top = df_filtrado.sort_values(["Swing Score", "Variação 24h %"], ascending=[False, False])

    melhor_day = day_top.iloc[0]
    melhor_swing = swing_top.iloc[0]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Mais forte", mais_forte["Ticker"], f"{mais_forte['Variação 24h %']}%")
    c2.metric("Mais fraca", mais_fraca["Ticker"], f"{mais_fraca['Variação 24h %']}%")
    c3.metric("Melhor day trade", melhor_day["Ticker"], f"Score {melhor_day['Day Score']}")
    c4.metric("Melhor swing trade", melhor_swing["Ticker"], f"Score {melhor_swing['Swing Score']}")
    c5.metric("Fear & Greed", fg["valor"], texto_fg(fg["valor"]))

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Geral",
        "Majors",
        "Infra/L1",
        "Narrativas",
        "Day Trade",
        "Swing Trade"
    ])

    with tab1:
        st.subheader("Tabela geral")
        st.dataframe(estilizar_dataframe(df_filtrado), use_container_width=True)

    with tab2:
        st.subheader("MAJORS")
        df_majors = df_filtrado[df_filtrado["Grupo"] == "MAJORS"].sort_values("Variação 24h %", ascending=False)
        st.dataframe(estilizar_dataframe(df_majors), use_container_width=True)

    with tab3:
        st.subheader("INFRA_L1")
        df_infra = df_filtrado[df_filtrado["Grupo"] == "INFRA_L1"].sort_values("Variação 24h %", ascending=False)
        st.dataframe(estilizar_dataframe(df_infra), use_container_width=True)

    with tab4:
        st.subheader("NARRATIVAS")
        df_narr = df_filtrado[df_filtrado["Grupo"] == "NARRATIVAS"].sort_values("Variação 24h %", ascending=False)
        st.dataframe(estilizar_dataframe(df_narr), use_container_width=True)

    with tab5:
        st.subheader("Foco operacional | Day Trade")
        st.dataframe(
            estilizar_dataframe(day_top[[
                "Ticker", "Grupo", "Preço", "Variação 24h %", "Status",
                "Nota Geral", "Day Nota", "Day Score"
            ]]),
            use_container_width=True
        )

    with tab6:
        st.subheader("Foco operacional | Swing Trade")
        st.dataframe(
            estilizar_dataframe(swing_top[[
                "Ticker", "Grupo", "Preço", "Variação 24h %", "Status",
                "Nota Geral", "Swing Nota", "Swing Score"
            ]]),
            use_container_width=True
        )

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
