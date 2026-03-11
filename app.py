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

    if grupo == "NARRATIVAS":
        score += 1
    elif grupo == "INFRA_L1":
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


def top3_texto(df):
    top = df.head(3)
    return " | ".join([f"{r['Ticker']} ({r['Variação 24h %']}%)" for _, r in top.iterrows()])


def bottom3_texto(df):
    bot = df.sort_values("Variação 24h %", ascending=True).head(3)
    return " | ".join([f"{r['Ticker']} ({r['Variação 24h %']}%)" for _, r in bot.iterrows()])


st.title("Radar Atlas")
st.caption("Watchlist cripto com leitura geral, day trade e swing trade")

try:
    dados = buscar_dados()
    df = montar_dataframe(dados)

    mais_forte = df.iloc[0]
    mais_fraca = df.sort_values("Variação 24h %", ascending=True).iloc[0]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mais forte", mais_forte["Ticker"], f"{mais_forte['Variação 24h %']}%")
    c2.metric("Mais fraca", mais_fraca["Ticker"], f"{mais_fraca['Variação 24h %']}%")
    c3.metric("Top 3 geral", top3_texto(df))
    c4.metric("Bottom 3 geral", bottom3_texto(df))

    st.subheader("Tabela geral")
    st.dataframe(df, use_container_width=True)

    st.subheader("Por grupo")
    for grupo in ["MAJORS", "INFRA_L1", "NARRATIVAS"]:
        st.markdown(f"### {grupo}")
        df_grupo = df[df["Grupo"] == grupo].sort_values("Variação 24h %", ascending=False)
        st.dataframe(df_grupo, use_container_width=True)

    st.subheader("Foco operacional")

    day_top = df.sort_values(["Day Score", "Variação 24h %"], ascending=[False, False]).head(3)
    swing_top = df.sort_values(["Swing Score", "Variação 24h %"], ascending=[False, False]).head(3)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Day Trade")
        st.dataframe(
            day_top[["Ticker", "Grupo", "Variação 24h %", "Day Nota", "Day Score"]],
            use_container_width=True
        )

    with col2:
        st.markdown("### Swing Trade")
        st.dataframe(
            swing_top[["Ticker", "Grupo", "Variação 24h %", "Swing Nota", "Swing Score"]],
            use_container_width=True
        )

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
