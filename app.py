import streamlit as st
import pandas as pd
import requests
from io import BytesIO
import plotly.express as px

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Critères",
    page_icon="🌳",
    layout="wide"
)

@st.cache_data(ttl=300)
def load_criteria_data():
    """Charge les données depuis Nextcloud"""

    try:
        username = st.secrets['NEXTCLOUD_USER']
        password = st.secrets['NEXTCLOUD_PASSWORD']
    except:
        st.error("⚠️ Identifiants Nextcloud manquants")
        return None

    file_url = f"https://nuage.relief-aura.fr/remote.php/dav/files/{username}/Déjà-Vu/03%20-%20Activités/32%20-%20Le%20Conseil/322%20-%20Exposcore/criteres_eco_eval_db.xlsx"

    try:
        response = requests.get(file_url, auth=(username, password), timeout=10)
        if response.status_code == 200:
            file_content = BytesIO(response.content)
            df = pd.read_excel(file_content, engine='openpyxl')
            df.columns = df.columns.str.strip()
            return df
    except Exception as e:
        st.error(f"Erreur : {e}")
        return None

def prepare_tree_data(df):
    """Prépare les données pour le treemap"""

    # Nettoyer les données
    df_clean = df.dropna(subset=[df.columns[0], df.columns[1], df.columns[2]])

    # Créer le dataframe pour le treemap
    tree_data = []

    for _, row in df_clean.iterrows():
        impact = str(row.iloc[0]).strip()
        type_name = str(row.iloc[1]).strip()
        critere = str(row.iloc[2]).strip()
        description = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""

        tree_data.append({
            'impact': impact,
            'type': type_name,
            'critere': critere,
            'description': description,
            'path': f"Exposcore / {impact} / {type_name} / {critere}",
            'hover_info': f"<b>{critere}</b><br>{description}"
        })

    return pd.DataFrame(tree_data)

def create_treemap_by_impact(df_tree):
    """Crée un treemap séparé pour chaque impact"""

    # Variables de configuration - modifiables manuellement
    EXPOSCORE_SIZE = 40     # Taille du texte pour Exposcore (titre principal)
    IMPACT_SIZE =  26       # Taille du texte pour les sous-titres d'impacts
    TYPE_SIZE = 22          # Taille du texte pour les types
    CRITERE_SIZE = 18       # Taille du texte pour les critères
    DESCRIPTION_SIZE = 26   # Taille du texte des descriptions au survol
    CHART_HEIGHT = 600      # Hauteur de chaque graphique
    MAX_CHARS_PER_LINE = 20 # Caractères max par ligne pour les critères

    impacts = df_tree['impact'].unique()

    # Titre principal Exposcore
    st.markdown(f"<h1 style='font-size:{EXPOSCORE_SIZE}px; text-align:center'>🌳 Exposcore</h1>", unsafe_allow_html=True)

    for impact in impacts:
        # Titre de l'impact avec taille personnalisée
        st.markdown(f"<h2 style='font-size:{IMPACT_SIZE}px'> {impact}</h2>", unsafe_allow_html=True)

        # Filtrer les données pour cet impact
        impact_data = df_tree[df_tree['impact'] == impact].copy()

        # Formatter le texte des critères sur plusieurs lignes
        def format_text_multiline(text, max_chars=MAX_CHARS_PER_LINE):
            words = text.split()
            lines = []
            current_line = ""

            for word in words:
                if len(current_line + " " + word) <= max_chars:
                    current_line = current_line + " " + word if current_line else word
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            return "<br>".join(lines)

        # Appliquer le formatage multiligne aux critères
        impact_data['critere_formatted'] = impact_data['critere'].apply(format_text_multiline)

        fig = px.treemap(
            impact_data,
            path=['type', 'critere_formatted'],
            hover_data={'description': True},
            title=None
        )

        fig.update_traces(
            textinfo="label",
            hovertemplate=f'<span style="font-size:{DESCRIPTION_SIZE}px">%{{customdata[0]}}</span><extra></extra>',
            textfont_size=CRITERE_SIZE,
            textfont_color="black",
            textposition="middle center"
        )

        # Mise en forme avec tailles différenciées
        fig.update_layout(
            height=CHART_HEIGHT,
            margin=dict(t=10, b=10, l=10, r=10),
            font=dict(size=TYPE_SIZE)
        )

        st.plotly_chart(fig, use_container_width=True)
        st.markdown("---")

def main():
    df = load_criteria_data()

    if df is not None:
        df_tree = prepare_tree_data(df)
        create_treemap_by_impact(df_tree)
    else:
        st.error("❌ Impossible de charger les données")

if __name__ == "__main__":
    main()
