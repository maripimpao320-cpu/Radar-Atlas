import streamlit as st
import pandas as pd

st.set_page_config(page_title="ATLAS 2.0", layout="wide")

# =========================
# CONFIG / HELPERS
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 1.2rem;
    padding-bottom: 1.2rem;
}
.card {
    border: 1px solid rgba(250,250,250,0.12);
    border-radius: 14px;
    padding: 16px 18px;
    background: rgba(255,255,255,0.03);
    margin-bottom: 12px;
}
.card-title {
    font-size: 0.90rem;
    font-weight: 700;
    letter-spacing: 0.4px;
    opacity: 0.90;
    margin-bottom: 8px;
}
.big-value {
    font-size: 1.35rem;
    font-weight: 800;
    margin-bottom: 4px;
}
.small-muted {
    font-size: 0.84rem;
    opacity: 0.75;
}
.tag {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    margin-right: 6px;
    margin-bottom: 6px;
}
.green {
    background: rgba(0, 200, 100, 0.18);
    color: #7CFFB2;
}
.yellow {
    background: rgba(255, 193, 7, 0.18);
    color: #FFD95A;
}
.red {
    background: rgba(255, 82, 82, 0.18);
    color: #FF8E8E;
}
.blue {
    background: rgba(50, 150, 255, 0.18);
    color: #8EC5FF;
}
.gray {
    background: rgba(180, 180, 180, 0.15);
    color: #D6D6D6;
}
hr {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.08);
    margin: 0.7rem 0 1rem 0;
}
.metric-line {
    margin-bottom: 6px;
    font-size: 0.92rem;
}
.score-a {color: #7CFFB2; font-weight: 800;}
.score-b {color: #A8E66A; font-weight: 800;}
.score-c {color: #FFD95A; font-weight: 800;}
.score-d {color: #FF8E8E; font-weight: 800;}
</style>
""", unsafe_allow_html=True)


def grade_from_score(score: int) -> str:
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    return "D"


def grade_class(grade: str) -> str:
    return {
        "A": "score-a",
        "B": "score-b",
        "C": "score-c",
        "D": "score-d",
    }.get(grade, "score-d")


def status_color(status: str) -> str:
    s = status.lower()
    if "liberado" in s or "verde" in s:
        return "green"
    if "observ" in s or "esperar" in s or "amarelo" in s:
        return "yellow"
    if "bloqueado" in s or "vermelho" in s:
        return "red"
    return "gray"


def bias_color(bias: str) -> str:
    b = bias.lower()
    if "long" in b:
        return "green"
    if "short" in b:
        return "red"
    return "gray"


def render_tag(text: str, color: str = "gray"):
    st.markdown(f'<span class="tag {color}">{text}</span>', unsafe_allow_html=True)


def card_start(title: str):
    st.markdown(f'<div class="card"><div class="card-title">{title}</div>', unsafe_allow_html=True)


def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# MOCK DATA
# =========================
atlas_permission = "LONG LIBERADO"
macro_bias = "Risk-On Moderado"
confidence = 78
risk_regime = "Agressivo Controlado"

macro_check = {
    "DXY": "Leve fraqueza",
    "Global Liquidity / M2": "Neutro-positivo",
    "BTC HTF": "Alta acima de suporte",
    "ETH HTF": "Recuperação",
    "S&P 500": "Positivo",
    "Nasdaq": "Positivo",
    "BTC Dominance": "Estável",
    "Aggregated Funding": "Controlado",
    "Aggregated OI": "Saudável",
    "Institutional / ETF Flow": "Levemente positivo",
}

candidates = [
    {
        "Ticker": "AKTUSDT",
        "Score": 82,
        "Bias": "LONG",
        "Status": "LIBERADO",
        "Entry Zone": "15.10 - 15.22",
        "Invalidation": "14.88",
        "TP1": "15.48",
        "TP2": "15.86",
        "Risk": "Moderado",
        "Reason": "VWAP + momentum + OI estável + liquidez acima",
        "Confluences": "VWAP, volume, funding controlado, heatmap favorável",
    },
    {
        "Ticker": "LINKUSDT",
        "Score": 76,
        "Bias": "LONG",
        "Status": "LIBERADO",
        "Entry Zone": "18.20 - 18.34",
        "Invalidation": "17.95",
        "TP1": "18.70",
        "TP2": "19.10",
        "Risk": "Moderado",
        "Reason": "Estrutura limpa e fluxo setorial",
        "Confluences": "HTF, volume, narrativa",
    },
    {
        "Ticker": "ARBUSDT",
        "Score": 63,
        "Bias": "LONG",
        "Status": "OBSERVAÇÃO",
        "Entry Zone": "1.22 - 1.24",
        "Invalidation": "1.18",
        "TP1": "1.28",
        "TP2": "1.33",
        "Risk": "Médio/Alto",
        "Reason": "Boa leitura, mas ainda sem confirmação plena",
        "Confluences": "Momentum parcial",
    },
    {
        "Ticker": "FETUSDT",
        "Score": 49,
        "Bias": "NEUTRO",
        "Status": "BLOQUEADO",
        "Entry Zone": "-",
        "Invalidation": "-",
        "TP1": "-",
        "TP2": "-",
        "Risk": "Alto",
        "Reason": "Heatmap ruim e estrutura fraca",
        "Confluences": "Nenhuma",
    },
]

df = pd.DataFrame(candidates)
df["Grade"] = df["Score"].apply(grade_from_score)
df = df[[
    "Ticker", "Score", "Grade", "Bias", "Status",
    "Entry Zone", "Invalidation", "TP1", "TP2", "Risk", "Reason"
]]

top_row = df.sort_values("Score", ascending=False).iloc[0]
selected_ticker = st.sidebar.selectbox("Selecionar ativo", df["Ticker"].tolist(), index=0)

selected_data = next(item for item in candidates if item["Ticker"] == selected_ticker)
selected_grade = grade_from_score(selected_data["Score"])

# =========================
# HEADER
# =========================
st.title("ATLAS 2.0")
st.caption("Macro Filter + Tactical Score + Liquidity Layer")
st.markdown(
    "Motor de decisão operacional para filtrar contexto, ranquear setups e bloquear entradas ruins."
)

# =========================
# TOP STATUS ROW
# =========================
c1, c2, c3 = st.columns([1.2, 1.2, 1.6])

with c1:
    card_start("ATLAS STATUS")
    st.markdown(f'<div class="big-value">{macro_bias}</div>', unsafe_allow_html=True)
    render_tag(atlas_permission, status_color(atlas_permission))
    render_tag(f"Confidence {confidence}", "blue")
    render_tag(risk_regime, "gray")
    st.markdown('<div class="small-muted">Sem liberação macro, não há trade.</div>', unsafe_allow_html=True)
    card_end()

with c2:
    card_start("TRADE STATUS")
    trade_status = (
        "VERDE | Pode procurar entrada"
        if selected_grade in ["A", "B"] and "LIBERADO" in selected_data["Status"]
        else "AMARELO | Observação"
        if selected_grade == "C"
        else "VERMELHO | Bloqueado"
    )
    st.markdown(f'<div class="big-value">{trade_status}</div>', unsafe_allow_html=True)
    render_tag(f"Bias {selected_data['Bias']}", bias_color(selected_data["Bias"]))
    render_tag(f"Grade {selected_grade}", status_color(selected_data["Status"]))
    render_tag(selected_data["Status"], status_color(selected_data["Status"]))
    st.markdown('<div class="small-muted">Status operacional do ativo selecionado.</div>', unsafe_allow_html=True)
    card_end()

with c3:
    card_start("SYSTEM ANCHOR")
    st.markdown("""
**Sem Atlas, não há trade.**  
**Sem score, não há convicção.**  
**Sem liquidez favorável, não há pressa.**  
**Sem risco definido, não há entrada.**
""")
    card_end()

# =========================
# SECOND ROW
# =========================
col_a, col_b, col_c = st.columns([1.35, 1, 1])

with col_a:
    card_start("MACRO CHECK")
    for k, v in macro_check.items():
        st.markdown(f'<div class="metric-line"><b>{k}:</b> {v}</div>', unsafe_allow_html=True)
    card_end()

with col_b:
    card_start("SCORE ENGINE")
    st.markdown("""
- **A | 85–100** | Setup Forte  
- **B | 70–84** | Setup Bom  
- **C | 55–69** | Observação  
- **D | <55** | Descartar
""")
    st.markdown("**Regra:** somente ativos **A** ou **B** podem virar operação.")
    st.markdown("---")
    st.markdown("""
**Pesos**
- Macro Alignment | 25  
- Technical Structure | 20  
- Volume / Momentum | 15  
- Healthy Open Interest | 10  
- Funding Quality | 10  
- Liquidity / Heatmap | 10  
- Narrative / Sector Flow | 10
""")
    card_end()

with col_c:
    card_start("LIQUIDITY LAYER")
    st.markdown("""
- **Heatmap:** favorável  
- **Liquidity Pools:** acima do preço  
- **Open Interest:** controlado  
- **Funding:** neutro  
- **Squeeze Risk:** moderado  
- **Trap Risk:** baixo
""")
    st.markdown("---")
    st.markdown("""
**Regras**
- Heatmap contrário = esperar  
- OI sobe sem preço = risco  
- Funding extremo = reduzir convicção  
- Preço esticado em pool = evitar agressão
""")
    card_end()

# =========================
# RADAR / SOURCES
# =========================
card_start("RADAR SCAN")
rad1, rad2, rad3, rad4 = st.columns(4)
with rad1:
    render_tag("TradingView", "blue")
with rad2:
    render_tag("CoinGlass", "blue")
with rad3:
    render_tag("SoSoValue", "blue")
with rad4:
    render_tag("CryptoBubbles", "blue")
st.markdown('<div class="small-muted">O Radar entra apenas quando o Atlas libera o mercado.</div>', unsafe_allow_html=True)
card_end()

# =========================
# TABLE OF CANDIDATES
# =========================
st.subheader("TOP CANDIDATES")

def highlight_grade(val):
    colors = {
        "A": "background-color: rgba(0,200,100,0.18); color: #7CFFB2; font-weight: 700;",
        "B": "background-color: rgba(150,200,50,0.18); color: #B6F36B; font-weight: 700;",
        "C": "background-color: rgba(255,193,7,0.18); color: #FFD95A; font-weight: 700;",
        "D": "background-color: rgba(255,82,82,0.18); color: #FF8E8E; font-weight: 700;",
    }
    return colors.get(val, "")

def highlight_status(val):
    if "LIBERADO" in str(val):
        return "background-color: rgba(0,200,100,0.18); color: #7CFFB2; font-weight: 700;"
    if "OBSERV" in str(val):
        return "background-color: rgba(255,193,7,0.18); color: #FFD95A; font-weight: 700;"
    if "BLOQUEADO" in str(val):
        return "background-color: rgba(255,82,82,0.18); color: #FF8E8E; font-weight: 700;"
    return ""

styled_df = df.style.map(highlight_grade, subset=["Grade"]).map(highlight_status, subset=["Status"])
st.dataframe(styled_df, use_container_width=True, hide_index=True)

# =========================
# EXECUTION CARD
# =========================
st.subheader("EXECUTION CARD")

left, right = st.columns([1.1, 1])

with left:
    card_start(selected_data["Ticker"])
    st.markdown(
        f'<div class="big-value">{selected_data["Ticker"]} '
        f'<span class="{grade_class(selected_grade)}">| Grade {selected_grade}</span></div>',
        unsafe_allow_html=True
    )
    render_tag(f"Score {selected_data['Score']}", "blue")
    render_tag(selected_data["Bias"], bias_color(selected_data["Bias"]))
    render_tag(selected_data["Status"], status_color(selected_data["Status"]))

    st.markdown("---")
    st.markdown(f"**Reason:** {selected_data['Reason']}")
    st.markdown(f"**Confluences:** {selected_data['Confluences']}")
    st.markdown(f"**Risk:** {selected_data['Risk']}")
    card_end()

with right:
    card_start("TRADE PLAN")
    st.markdown(f"**Entry:** {selected_data['Entry Zone']}")
    st.markdown(f"**Stop:** {selected_data['Invalidation']}")
    st.markdown(f"**TP1:** {selected_data['TP1']}")
    st.markdown(f"**TP2:** {selected_data['TP2']}")

    st.markdown("---")
    rr_hint = "Aceitável" if selected_grade in ["A", "B"] else "Fraco"
    st.markdown(f"**R/R Quality:** {rr_hint}")

    final_note = (
        "Entrada válida somente com confirmação de fluxo."
        if selected_grade in ["A", "B"] and "LIBERADO" in selected_data["Status"]
        else "Ativo em observação. Evitar antecipação."
        if selected_grade == "C"
        else "Trade bloqueado. Preservar capital."
    )
    st.markdown(f"**Final Note:** {final_note}")
    card_end()

# =========================
# FOOTER RULES / FLOW
# =========================
r1, r2 = st.columns(2)

with r1:
    card_start("SYSTEM RULES")
    st.markdown("""
- Radar não opera sem Atlas  
- Atlas x Radar divergentes = sem trade  
- Score C = observar  
- Score D = descartar  
- Sem estrutura = sem trade  
- Sem stop = sem entrada  
- RR ruim = cancelar  
- Liquidez contrária = esperar
""")
    card_end()

with r2:
    card_start("DECISION FLOW")
    st.markdown("""
1. Atlas define permissão  
2. Radar seleciona ativos  
3. Score ranqueia qualidade  
4. Liquidez valida entrada  
5. Card operacional executa
""")
    card_end()
