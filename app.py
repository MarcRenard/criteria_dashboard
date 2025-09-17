import streamlit as st
import pandas as pd
import requests
from io import StringIO, BytesIO
import os
from dotenv import load_dotenv
import plotly.graph_objects as go

# Charger les variables d'environnement
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Critères",
    page_icon="🌳",
    layout="wide"
)

# Fonction pour récupérer les données depuis Nextcloud
@st.cache_data(ttl=300)  # Cache pendant 5 minutes
def fetch_data_from_nextcloud():
    """Récupère les données depuis le serveur Nextcloud (Excel ou CSV)"""

    # Récupération des identifiants - d'abord les variables d'environnement, puis les secrets Streamlit
    username = os.getenv('NEXTCLOUD_USER')
    password = os.getenv('NEXTCLOUD_PASSWORD')

    # Si pas trouvé dans les variables d'environnement, essayer les secrets Streamlit
    if not username or not password:
        try:
            username = st.secrets.get('NEXTCLOUD_USER', username)
            password = st.secrets.get('NEXTCLOUD_PASSWORD', password)
        except:
            # Si les secrets Streamlit ne sont pas disponibles, continuer avec les variables d'env

    if not username or not password:
        st.error("⚠️ Identifiants Nextcloud manquants. Vérifiez vos variables d'environnement ou secrets Streamlit.")
        return None

    # URL du fichier partagé Nextcloud
    url = "https://nuage.relief-aura.fr/f/142356"

    try:
        # Tentative de récupération avec authentification
        response = requests.get(url, auth=(username, password), timeout=10)

        if response.status_code == 200:
            # Détecter le type de fichier et le traiter accordingly
            try:
                # Essayer de lire comme Excel d'abord (fichier binaire)
                df = pd.read_excel(BytesIO(response.content), engine='openpyxl')
                # Normaliser les noms de colonnes pour correspondre aux attendus
                if len(df.columns) >= 4:
                    df.columns = ['impact', 'type', 'critère', 'description'] + list(df.columns[4:])
                return df
            except:
                # Si Excel échoue, essayer CSV
                try:
                    df = pd.read_csv(StringIO(response.text), sep=',')
                    if len(df.columns) < 4:
                        # Essayer avec un autre séparateur
                        df = pd.read_csv(StringIO(response.text), sep=';')
                    # Normaliser les noms de colonnes
                    if len(df.columns) >= 4:
                        df.columns = ['impact', 'type', 'critère', 'description'] + list(df.columns[4:])
                    return df
                except Exception as e:
                    st.error(f"Erreur lors de la lecture du fichier : {str(e)}")
                    return None
        else:
            st.error(f"Erreur lors de la récupération des données : HTTP {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion : {str(e)}")
        return None

def create_tree_visualization(df):
    """Crée une structure de données hiérarchique pour la visualisation"""

    tree_data = []

    # Nettoyer les données - supprimer les lignes avec des valeurs manquantes critiques
    df_clean = df.dropna(subset=['impact', 'type', 'critère'])

    # Regrouper les données par hiérarchie
    for _, row in df_clean.iterrows():
        tree_data.append({
            'impact': str(row['impact']).strip(),
            'type': str(row['type']).strip(),
            'critere': str(row['critère']).strip(),
            'description': str(row['description']).strip() if pd.notna(row['description']) else "Pas de description disponible"
        })

    return tree_data

def display_interactive_tree(tree_data):
    """Affiche l'arbre interactif avec Streamlit - Version améliorée"""

    st.subheader("🌳 Arbre des Critères Interactif")

    # Vue d'ensemble des impacts
    impacts = sorted(list(set([item['impact'] for item in tree_data])))

    # Créer des onglets pour chaque impact (limité à 5 pour éviter les problèmes d'affichage)
    if len(impacts) <= 5:
        # Raccourcir les noms d'onglets pour l'affichage
        tab_names = []
        for impact in impacts:
            if len(impact) > 25:
                tab_name = impact[:22] + "..."
            else:
                tab_name = impact
            tab_names.append(f"📊 {tab_name}")

        tabs = st.tabs(tab_names)

        for i, impact in enumerate(impacts):
            with tabs[i]:
                display_impact_tree(tree_data, impact)
    else:
        # Si trop d'impacts, utiliser une sélection
        selected_impact = st.selectbox("🎯 Sélectionnez un impact :", impacts)
        if selected_impact:
            display_impact_tree(tree_data, selected_impact)

def display_impact_tree(tree_data, selected_impact):
    """Affiche l'arbre pour un impact spécifique"""

    # Filtrer les données pour l'impact sélectionné
    filtered_data = [item for item in tree_data if item['impact'] == selected_impact]
    types = sorted(list(set([item['type'] for item in filtered_data])))

    st.markdown(f"### 🎯 {selected_impact}")
    st.markdown(f"*{len(types)} types de critères • {len(filtered_data)} critères au total*")

    # Affichage en colonnes adaptatives
    if len(types) <= 2:
        cols = st.columns(len(types))
    elif len(types) <= 4:
        cols = st.columns(2)
    else:
        cols = st.columns(3)

    for i, type_name in enumerate(types):
        with cols[i % len(cols)]:
            # Titre du type avec compteur
            type_data = [item for item in filtered_data if item['type'] == type_name]
            st.markdown(f"#### 📂 {type_name}")
            st.markdown(f"*{len(type_data)} critères*")

            # Afficher les critères dans ce type
            for item in type_data:
                # Utiliser un expander avec icône
                with st.expander(f"🔍 {item['critere']}", expanded=False):
                    # Description avec formatage amélioré
                    if item['description'] and item['description'] != "Pas de description disponible":
                        st.markdown("**Description :**")
                        st.write(item['description'])

                        # Ajouter des métadonnées
                        st.caption(f"📍 {item['impact']} → {item['type']}")
                    else:
                        st.info("Aucune description disponible")

            # Espacement entre les colonnes
            if i < len(types) - 1:
                st.markdown("---")

def display_search_results(filtered_data):
    """Affiche les résultats de recherche"""

    for item in filtered_data:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**🔍 {item['critere']}**")
                if item['description'] and item['description'] != "Pas de description disponible":
                    st.write(item['description'])
                else:
                    st.caption("Pas de description disponible")
            with col2:
                st.caption(f"📊 {item['impact']}")
                st.caption(f"📂 {item['type']}")
            st.markdown("---")

def display_summary_stats(df):
    """Affiche des statistiques résumées avec visualisations"""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("📊 Impacts", len(df['impact'].unique()))

    with col2:
        st.metric("📂 Types", len(df['type'].unique()))

    with col3:
        st.metric("🔍 Critères", len(df['critère'].unique()))

    with col4:
        st.metric("📝 Total lignes", len(df))

    # Graphique de répartition
    st.markdown("### 📈 Répartition des critères par impact")

    # Compter les critères par impact
    impact_counts = df.groupby('impact').size().reset_index(name='count')
    impact_counts = impact_counts.sort_values('count', ascending=True)

    # Créer un graphique horizontal
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=impact_counts['impact'],
        x=impact_counts['count'],
        orientation='h',
        marker_color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FECA57'][:len(impact_counts)],
        text=impact_counts['count'],
        textposition='auto'
    ))

    fig.update_layout(
        title="Nombre de critères par impact",
        xaxis_title="Nombre de critères",
        yaxis_title="Impacts",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    st.plotly_chart(fig, use_container_width=True)

def main():
    # Titre principal
    st.title("🌳 Dashboard des Critères d'Évaluation")
    st.markdown("---")

    # Sidebar pour les options
    with st.sidebar:
        st.header("🎛️ Options")
        refresh_data = st.button("🔄 Actualiser les données")
        show_raw_data = st.checkbox("📋 Afficher les données brutes")
        show_search = st.checkbox("🔍 Recherche avancée")

        # Section d'aide
        with st.expander("ℹ️ À propos"):
            st.markdown("""
            **Dashboard des Critères d'Évaluation**

            Ce tableau de bord affiche une hiérarchie de critères organisée en :
            - **Impacts** principaux
            - **Types** de critères
            - **Critères** détaillés avec descriptions

            Naviguez par onglets ou utilisez la recherche pour explorer les données.
            """)

    # Fonctionnalité de recherche
    search_query = ""
    if show_search:
        st.markdown("### 🔍 Recherche dans les critères")
        search_query = st.text_input("Rechercher un critère ou une description:", "")

    # Récupération des données
    with st.spinner("Récupération des données depuis Nextcloud..."):
        df = fetch_data_from_nextcloud()

    if df is not None:
        st.success("✅ Données récupérées avec succès !")

        # Vérification des colonnes requises
        required_columns = ['impact', 'type', 'critère', 'description']
        if not all(col in df.columns for col in required_columns):
            st.error(f"⚠️ Colonnes manquantes. Colonnes trouvées : {list(df.columns)}")
            st.info("Colonnes requises : impact, type, critère, description")
            return

        # Statistiques résumées
        display_summary_stats(df)
        st.markdown("---")

        # Création et affichage de l'arbre
        tree_data = create_tree_visualization(df)

        # Filtrage par recherche si activé
        if search_query:
            filtered_tree_data = [
                item for item in tree_data
                if search_query.lower() in item['critere'].lower()
                or search_query.lower() in item['description'].lower()
                or search_query.lower() in item['type'].lower()
                or search_query.lower() in item['impact'].lower()
            ]
            if filtered_tree_data:
                st.info(f"🔍 {len(filtered_tree_data)} critères trouvés pour '{search_query}'")
                display_search_results(filtered_tree_data)
            else:
                st.warning(f"Aucun résultat trouvé pour '{search_query}'")
        else:
            display_interactive_tree(tree_data)

        # Affichage des données brutes si demandé
        if show_raw_data:
            st.markdown("---")
            st.subheader("📊 Données brutes")
            st.dataframe(df, use_container_width=True)

            # Option de téléchargement
            csv = df.to_csv(index=False)
            st.download_button(
                label="💾 Télécharger les données (CSV)",
                data=csv,
                file_name="criteria_data.csv",
                mime="text/csv"
            )

    else:
        st.error("❌ Impossible de récupérer les données.")

        # Données de démonstration basées sur votre fichier réel
        st.info("💡 Utilisation des données de démonstration basées sur votre structure")
        demo_data = {
            'impact': [
                'Impacts environnementaux directs', 'Impacts environnementaux directs',
                'Impacts environnementaux directs', 'Impacts environnementaux directs',
                'Impacts environnementaux indirects', 'Impacts environnementaux indirects',
                'Impacts éco-sociaux', 'Impacts éco-sociaux',
                'Impacts temporels et contextuels', 'Critères d\'évaluation transversaux'
            ],
            'type': [
                'Matériaux et ressources', 'Matériaux et ressources',
                'Énergie et climat', 'Transport et logistique',
                'Cycle de vie', 'Effets systémiques',
                'Justice sociale et équité', 'Économie locale et territoriale',
                'Durée et intensité', 'Innovation et exemplarité'
            ],
            'critère': [
                'Empreinte carbone des matériaux', 'Consommation d\'eau',
                'Consommation énergétique éclairage', 'Distance parcourue matériaux',
                'Fin de vie des matériaux', 'Îlot de chaleur urbain',
                'Équité d\'accès au projet', 'Impact sur économie locale',
                'Durée de vie du projet', 'Caractère innovant'
            ],
            'description': [
                'Gaz à effet de serre liés à l\'extraction, transformation et transport.',
                'Volume d\'eau utilisé pour fabriquer les matériaux.',
                'Énergie utilisée pour l\'éclairage.',
                'Kilomètres parcourus par les matériaux depuis leur origine.',
                'Mode de traitement : incinération, enfouissement, recyclage.',
                'Contribution au réchauffement local.',
                'Le projet bénéficie-t-il équitablement à tous les groupes sociaux ?',
                'Effet positif sur l\'économie et l\'emploi local.',
                'Estimation de la durée de vie technique et fonctionnelle.',
                'Degré d\'innovation technique, sociale ou environnementale.'
            ]
        }
        df_demo = pd.DataFrame(demo_data)

        display_summary_stats(df_demo)
        st.markdown("---")

        tree_data_demo = create_tree_visualization(df_demo)
        display_interactive_tree(tree_data_demo)

if __name__ == "__main__":
    main()
