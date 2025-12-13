# -*- coding: utf-8 -*-
"""
Dashboard Streamlit pour visualiser les alertes du Bot Market
Accès web aux données de la base de données SQLite
"""

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configuration de la page
st.set_page_config(
    page_title="Bot Market Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# AUTHENTIFICATION (Optionnelle)
# ============================================

def check_password():
    """Vérifie le mot de passe si configuré."""
    # Si pas de mot de passe configuré, accès libre
    password_env = os.getenv("DASHBOARD_PASSWORD", "")
    if not password_env:
        return True

    def password_entered():
        """Vérifie le mot de passe entré."""
        if st.session_state["password"] == password_env:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "🔒 Mot de passe",
            type="password",
            on_change=password_entered,
            key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "🔒 Mot de passe",
            type="password",
            on_change=password_entered,
            key="password"
        )
        st.error("❌ Mot de passe incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ============================================
# CONNEXION BASE DE DONNÉES
# ============================================

@st.cache_resource
def get_connection():
    """Connexion à la base de données SQLite."""
    db_path = os.getenv('DB_PATH', '/data/alerts_history.db')

    # Fallback pour test local
    if not os.path.exists(db_path):
        db_path = 'alerts_history.db'

    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        return conn
    except Exception as e:
        st.error(f"❌ Erreur connexion DB: {e}")
        st.info(f"Chemin DB: {db_path}")
        return None

conn = get_connection()

if conn is None:
    st.stop()

# ============================================
# FONCTIONS DE LECTURE DB
# ============================================

@st.cache_data(ttl=60)  # Cache 1 minute
def get_stats_globales():
    """Récupère les statistiques globales."""
    try:
        # Total alertes
        total_alerts = pd.read_sql("SELECT COUNT(*) as total FROM alerts", conn).iloc[0]['total']

        # Alertes analysées
        analyzed = pd.read_sql("SELECT COUNT(*) as total FROM alert_analysis", conn).iloc[0]['total']

        # ROI moyen 24h
        avg_roi = pd.read_sql("""
            SELECT AVG(roi_at_24h) as avg
            FROM alert_analysis
            WHERE roi_at_24h IS NOT NULL
        """, conn).iloc[0]['avg']
        avg_roi = avg_roi if avg_roi is not None else 0

        # Taux TP1
        tp_rates = pd.read_sql("""
            SELECT
                COUNT(CASE WHEN tp1_was_hit = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as tp1,
                COUNT(CASE WHEN tp2_was_hit = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as tp2,
                COUNT(CASE WHEN tp3_was_hit = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as tp3,
                COUNT(CASE WHEN sl_was_hit = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as sl,
                COUNT(CASE WHEN was_profitable = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as profitable
            FROM alert_analysis
        """, conn).iloc[0]

        return {
            'total_alerts': int(total_alerts),
            'analyzed': int(analyzed),
            'avg_roi': float(avg_roi),
            'tp1_rate': float(tp_rates['tp1'] or 0),
            'tp2_rate': float(tp_rates['tp2'] or 0),
            'tp3_rate': float(tp_rates['tp3'] or 0),
            'sl_rate': float(tp_rates['sl'] or 0),
            'profitable_rate': float(tp_rates['profitable'] or 0)
        }
    except Exception as e:
        st.error(f"Erreur stats: {e}")
        return None

@st.cache_data(ttl=60)
def get_recent_alerts(limit=50):
    """Récupère les alertes récentes."""
    try:
        return pd.read_sql(f"""
            SELECT
                id,
                timestamp,
                token_name,
                network,
                score,
                confidence_score,
                price_at_alert,
                volume_24h,
                liquidity,
                buy_ratio
            FROM alerts
            ORDER BY timestamp DESC
            LIMIT {limit}
        """, conn)
    except Exception as e:
        st.error(f"Erreur alertes récentes: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_alert_detail(alert_id):
    """Récupère le détail d'une alerte."""
    try:
        alert = pd.read_sql(f"SELECT * FROM alerts WHERE id = {alert_id}", conn)
        tracking = pd.read_sql(f"""
            SELECT * FROM price_tracking
            WHERE alert_id = {alert_id}
            ORDER BY minutes_after_alert
        """, conn)
        analysis = pd.read_sql(f"SELECT * FROM alert_analysis WHERE alert_id = {alert_id}", conn)

        return alert, tracking, analysis
    except Exception as e:
        st.error(f"Erreur détail alerte: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=300)
def get_performance_data():
    """Récupère les données de performance pour graphiques."""
    try:
        # Distribution des scores
        scores = pd.read_sql("SELECT score, confidence_score FROM alerts", conn)

        # ROI par score
        roi_by_score = pd.read_sql("""
            SELECT
                CASE
                    WHEN a.score >= 80 THEN '80-100'
                    WHEN a.score >= 60 THEN '60-79'
                    WHEN a.score >= 40 THEN '40-59'
                    ELSE '0-39'
                END as score_range,
                AVG(an.roi_at_24h) as avg_roi,
                COUNT(*) as count,
                AVG(a.score) as avg_score
            FROM alerts a
            LEFT JOIN alert_analysis an ON a.id = an.alert_id
            WHERE an.roi_at_24h IS NOT NULL
            GROUP BY score_range
            ORDER BY avg_score DESC
        """, conn)

        # Evolution dans le temps
        timeline = pd.read_sql("""
            SELECT
                DATE(timestamp) as date,
                COUNT(*) as alert_count,
                AVG(score) as avg_score
            FROM alerts
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        """, conn)

        # Performance par réseau
        by_network = pd.read_sql("""
            SELECT
                a.network,
                COUNT(*) as total,
                AVG(an.roi_at_24h) as avg_roi,
                COUNT(CASE WHEN an.tp1_was_hit = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0) as tp1_rate
            FROM alerts a
            LEFT JOIN alert_analysis an ON a.id = an.alert_id
            WHERE an.roi_at_24h IS NOT NULL
            GROUP BY a.network
            ORDER BY total DESC
        """, conn)

        return scores, roi_by_score, timeline, by_network
    except Exception as e:
        st.error(f"Erreur données performance: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# ============================================
# INTERFACE PRINCIPALE
# ============================================

# Titre
st.title("🚀 Bot Market - Dashboard")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("⚙️ Options")

    page = st.radio(
        "Navigation",
        ["📊 Vue d'ensemble", "📋 Alertes récentes", "🔍 Détail alerte", "📈 Performance", "🪙 Tokens"]
    )

    st.markdown("---")
    st.markdown("### 🔄 Rafraîchir")
    if st.button("Actualiser les données"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ Info")
    st.caption("Dashboard Bot Market v1.0")
    st.caption(f"DB: {os.getenv('DB_PATH', 'alerts_history.db')}")

# ============================================
# PAGE 1: VUE D'ENSEMBLE
# ============================================

if page == "📊 Vue d'ensemble":
    st.header("📊 Vue d'Ensemble")

    stats = get_stats_globales()

    if stats:
        # Métriques principales
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("Total Alertes", f"{stats['total_alerts']:,}")

        with col2:
            st.metric("Analysées (24h+)", f"{stats['analyzed']:,}")

        with col3:
            st.metric("ROI Moyen 24h", f"{stats['avg_roi']:+.2f}%")

        with col4:
            st.metric("Taux TP1", f"{stats['tp1_rate']:.1f}%")

        with col5:
            st.metric("Taux Profitable", f"{stats['profitable_rate']:.1f}%")

        st.markdown("---")

        # Graphiques
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🎯 Taux d'Atteinte des Objectifs")
            fig = go.Figure(data=[
                go.Bar(
                    x=['TP1 (+5%)', 'TP2 (+10%)', 'TP3 (+15%)', 'Stop Loss'],
                    y=[stats['tp1_rate'], stats['tp2_rate'], stats['tp3_rate'], stats['sl_rate']],
                    marker_color=['green', 'lightgreen', 'darkgreen', 'red']
                )
            ])
            fig.update_layout(
                yaxis_title="Taux (%)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📊 Distribution Performance")
            scores, roi_by_score, timeline, by_network = get_performance_data()

            if not roi_by_score.empty:
                fig = px.bar(
                    roi_by_score,
                    x='score_range',
                    y='avg_roi',
                    text='count',
                    labels={'score_range': 'Tranche de Score', 'avg_roi': 'ROI Moyen 24h (%)', 'count': 'Nombre'},
                    color='avg_roi',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_traces(texttemplate='%{text} alertes', textposition='outside')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

        # Timeline
        st.markdown("---")
        st.subheader("📈 Évolution dans le Temps")

        if not timeline.empty:
            timeline['date'] = pd.to_datetime(timeline['date'])

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=timeline['date'],
                y=timeline['alert_count'],
                mode='lines+markers',
                name='Nombre d\'alertes',
                yaxis='y',
                line=dict(color='blue')
            ))
            fig.add_trace(go.Scatter(
                x=timeline['date'],
                y=timeline['avg_score'],
                mode='lines+markers',
                name='Score moyen',
                yaxis='y2',
                line=dict(color='green')
            ))
            fig.update_layout(
                yaxis=dict(title='Nombre d\'alertes'),
                yaxis2=dict(title='Score moyen', overlaying='y', side='right'),
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

        # Performance par réseau
        st.markdown("---")
        st.subheader("🌐 Performance par Réseau")

        if not by_network.empty:
            col1, col2 = st.columns(2)

            with col1:
                fig = px.bar(
                    by_network,
                    x='network',
                    y='total',
                    labels={'network': 'Réseau', 'total': 'Nombre d\'alertes'},
                    color='total',
                    color_continuous_scale='Blues'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = px.bar(
                    by_network,
                    x='network',
                    y='avg_roi',
                    labels={'network': 'Réseau', 'avg_roi': 'ROI Moyen 24h (%)'},
                    color='avg_roi',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

# ============================================
# PAGE 2: ALERTES RÉCENTES
# ============================================

elif page == "📋 Alertes récentes":
    st.header("📋 Alertes Récentes")

    # Filtres
    col1, col2, col3 = st.columns(3)

    with col1:
        limit = st.number_input("Nombre d'alertes", min_value=10, max_value=200, value=50, step=10)

    with col2:
        network_filter = st.selectbox("Réseau", ["Tous", "eth", "bsc", "arbitrum", "base", "solana"])

    with col3:
        min_score = st.slider("Score minimum", 0, 100, 0)

    # Récupérer les alertes
    df = get_recent_alerts(limit)

    if not df.empty:
        # Appliquer filtres
        if network_filter != "Tous":
            df = df[df['network'] == network_filter]

        df = df[df['score'] >= min_score]

        st.info(f"📊 {len(df)} alertes affichées")

        # Formater le DataFrame
        df_display = df.copy()
        df_display['timestamp'] = pd.to_datetime(df_display['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        df_display['price_at_alert'] = df_display['price_at_alert'].apply(lambda x: f"${x:.10f}" if x < 0.01 else f"${x:.6f}")
        df_display['volume_24h'] = df_display['volume_24h'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
        df_display['liquidity'] = df_display['liquidity'].apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
        df_display['buy_ratio'] = df_display['buy_ratio'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")

        # Afficher le tableau
        st.dataframe(
            df_display,
            use_container_width=True,
            height=600,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "timestamp": st.column_config.TextColumn("Date", width="medium"),
                "token_name": st.column_config.TextColumn("Token", width="medium"),
                "network": st.column_config.TextColumn("Réseau", width="small"),
                "score": st.column_config.ProgressColumn("Score", format="%d/100", min_value=0, max_value=100, width="small"),
                "confidence_score": st.column_config.ProgressColumn("Sécurité", format="%d/100", min_value=0, max_value=100, width="small"),
            }
        )

# ============================================
# PAGE 3: DÉTAIL ALERTE
# ============================================

elif page == "🔍 Détail alerte":
    st.header("🔍 Détail d'une Alerte")

    alert_id = st.number_input("ID de l'alerte", min_value=1, value=1, step=1)

    if st.button("Charger l'alerte"):
        alert, tracking, analysis = get_alert_detail(alert_id)

        if not alert.empty:
            alert_data = alert.iloc[0]

            # Informations principales
            st.subheader(f"🪙 {alert_data['token_name']}")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Score Opportunité", f"{alert_data['score']}/100")

            with col2:
                st.metric("Score Sécurité", f"{alert_data['confidence_score']}/100")

            with col3:
                st.metric("Réseau", alert_data['network'].upper())

            with col4:
                st.metric("Date", pd.to_datetime(alert_data['timestamp']).strftime('%Y-%m-%d %H:%M'))

            st.markdown("---")

            # Niveaux de prix
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("💰 Niveaux de Prix")
                st.write(f"**Prix à l'alerte:** ${alert_data['price_at_alert']:.10f}")
                st.write(f"**Entry:** ${alert_data['entry_price']:.10f}")
                st.write(f"**Stop Loss:** ${alert_data['stop_loss_price']:.10f} ({alert_data['stop_loss_percent']:+.1f}%)")
                st.write(f"**TP1:** ${alert_data['tp1_price']:.10f} ({alert_data['tp1_percent']:+.1f}%)")
                st.write(f"**TP2:** ${alert_data['tp2_price']:.10f} ({alert_data['tp2_percent']:+.1f}%)")
                st.write(f"**TP3:** ${alert_data['tp3_price']:.10f} ({alert_data['tp3_percent']:+.1f}%)")

            with col2:
                st.subheader("📊 Métriques")
                st.write(f"**Volume 24h:** ${alert_data['volume_24h']:,.0f}" if pd.notna(alert_data['volume_24h']) else "N/A")
                st.write(f"**Liquidité:** ${alert_data['liquidity']:,.0f}" if pd.notna(alert_data['liquidity']) else "N/A")
                st.write(f"**Transactions 24h:** {alert_data['total_txns']}" if pd.notna(alert_data['total_txns']) else "N/A")
                st.write(f"**Buy Ratio:** {alert_data['buy_ratio']:.2f}" if pd.notna(alert_data['buy_ratio']) else "N/A")
                st.write(f"**Age:** {alert_data['age_hours']:.1f}h" if pd.notna(alert_data['age_hours']) else "N/A")

            # Tracking des prix
            if not tracking.empty:
                st.markdown("---")
                st.subheader("📈 Tracking des Prix")

                # Graphique ROI
                fig = go.Figure()

                fig.add_trace(go.Scatter(
                    x=tracking['minutes_after_alert'],
                    y=tracking['roi_percent'],
                    mode='lines+markers',
                    name='ROI',
                    line=dict(color='blue', width=2),
                    marker=dict(size=8)
                ))

                # Lignes TP/SL
                fig.add_hline(y=alert_data['tp1_percent'], line_dash="dash", line_color="green", annotation_text="TP1")
                fig.add_hline(y=alert_data['tp2_percent'], line_dash="dash", line_color="lightgreen", annotation_text="TP2")
                fig.add_hline(y=alert_data['tp3_percent'], line_dash="dash", line_color="darkgreen", annotation_text="TP3")
                fig.add_hline(y=alert_data['stop_loss_percent'], line_dash="dash", line_color="red", annotation_text="SL")

                fig.update_layout(
                    xaxis_title="Minutes après alerte",
                    yaxis_title="ROI (%)",
                    height=400,
                    hovermode='x unified'
                )

                st.plotly_chart(fig, use_container_width=True)

                # Tableau tracking
                st.dataframe(tracking, use_container_width=True)

            # Analyse de performance
            if not analysis.empty:
                st.markdown("---")
                st.subheader("🎯 Analyse de Performance (24h)")

                analysis_data = analysis.iloc[0]

                col1, col2, col3 = st.columns(3)

                with col1:
                    profitable = "✅ OUI" if analysis_data['was_profitable'] else "❌ NON"
                    st.metric("Profitable", profitable)

                with col2:
                    st.metric("ROI à 24h", f"{analysis_data['roi_at_24h']:+.2f}%" if pd.notna(analysis_data['roi_at_24h']) else "N/A")

                with col3:
                    st.metric("Qualité", analysis_data['prediction_quality'] if pd.notna(analysis_data['prediction_quality']) else "N/A")

                col1, col2 = st.columns(2)

                with col1:
                    st.write("**Objectifs atteints:**")
                    st.write(f"- TP1: {'✅' if analysis_data['tp1_was_hit'] else '❌'} {f'(en {analysis_data["time_to_tp1"]}min)' if pd.notna(analysis_data['time_to_tp1']) else ''}")
                    st.write(f"- TP2: {'✅' if analysis_data['tp2_was_hit'] else '❌'} {f'(en {analysis_data["time_to_tp2"]}min)' if pd.notna(analysis_data['time_to_tp2']) else ''}")
                    st.write(f"- TP3: {'✅' if analysis_data['tp3_was_hit'] else '❌'} {f'(en {analysis_data["time_to_tp3"]}min)' if pd.notna(analysis_data['time_to_tp3']) else ''}")
                    st.write(f"- Stop Loss: {'⛔' if analysis_data['sl_was_hit'] else '✅'} {f'(touché en {analysis_data["time_to_sl"]}min)' if pd.notna(analysis_data['time_to_sl']) else ''}")

                with col2:
                    st.write("**Performance:**")
                    st.write(f"- Meilleur ROI (4h): {analysis_data['best_roi_4h']:+.2f}%" if pd.notna(analysis_data['best_roi_4h']) else "N/A")
                    st.write(f"- Pire ROI (4h): {analysis_data['worst_roi_4h']:+.2f}%" if pd.notna(analysis_data['worst_roi_4h']) else "N/A")
                    st.write(f"- Cohérent: {'✅ OUI' if analysis_data['was_coherent'] else '❌ NON'}")
                    if pd.notna(analysis_data['coherence_notes']):
                        st.caption(f"Notes: {analysis_data['coherence_notes']}")

        else:
            st.warning(f"❌ Alerte #{alert_id} introuvable")

# ============================================
# PAGE 4: PERFORMANCE
# ============================================

elif page == "📈 Performance":
    st.header("📈 Analyse de Performance")

    scores, roi_by_score, timeline, by_network = get_performance_data()

    # Distribution des scores
    if not scores.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Distribution Score Opportunité")
            fig = px.histogram(
                scores,
                x='score',
                nbins=20,
                labels={'score': 'Score', 'count': 'Nombre'},
                color_discrete_sequence=['blue']
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Distribution Score Sécurité")
            fig = px.histogram(
                scores,
                x='confidence_score',
                nbins=20,
                labels={'confidence_score': 'Score Sécurité', 'count': 'Nombre'},
                color_discrete_sequence=['green']
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    # ROI par score
    if not roi_by_score.empty:
        st.markdown("---")
        st.subheader("ROI Moyen par Tranche de Score")

        fig = px.bar(
            roi_by_score,
            x='score_range',
            y='avg_roi',
            text='count',
            labels={'score_range': 'Tranche de Score', 'avg_roi': 'ROI Moyen 24h (%)', 'count': 'Nombre'},
            color='avg_roi',
            color_continuous_scale='RdYlGn'
        )
        fig.update_traces(texttemplate='%{text} alertes', textposition='outside')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(roi_by_score, use_container_width=True)

# ============================================
# PAGE 5: TOKENS
# ============================================

elif page == "🪙 Tokens":
    st.header("🪙 Tokens Suivis")

    tokens = pd.read_sql("""
        SELECT
            token_name,
            token_address,
            network,
            COUNT(*) as alert_count,
            MAX(timestamp) as last_alert,
            AVG(score) as avg_score,
            AVG(confidence_score) as avg_security
        FROM alerts
        GROUP BY token_address
        ORDER BY last_alert DESC
    """, conn)

    if not tokens.empty:
        st.info(f"📊 {len(tokens)} tokens uniques suivis")

        # Formater
        tokens['last_alert'] = pd.to_datetime(tokens['last_alert']).dt.strftime('%Y-%m-%d %H:%M')
        tokens['avg_score'] = tokens['avg_score'].round(1)
        tokens['avg_security'] = tokens['avg_security'].round(1)

        st.dataframe(
            tokens,
            use_container_width=True,
            height=600,
            column_config={
                "token_name": st.column_config.TextColumn("Token", width="medium"),
                "token_address": st.column_config.TextColumn("Adresse", width="large"),
                "network": st.column_config.TextColumn("Réseau", width="small"),
                "alert_count": st.column_config.NumberColumn("Nb Alertes", width="small"),
                "last_alert": st.column_config.TextColumn("Dernière Alerte", width="medium"),
                "avg_score": st.column_config.ProgressColumn("Score Moyen", format="%.1f/100", min_value=0, max_value=100, width="small"),
                "avg_security": st.column_config.ProgressColumn("Sécurité Moy", format="%.1f/100", min_value=0, max_value=100, width="small"),
            }
        )

# Footer
st.markdown("---")
st.caption("🚀 Bot Market Dashboard - v1.0 - Créé avec Streamlit")