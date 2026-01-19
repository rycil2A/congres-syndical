import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Congrès 2026", page_icon="🗳️")

st.title("🗳️ Élection du Bureau Syndical")
st.markdown("Confirmez votre présence ou désignez un mandataire.")

# --- 1. CONNEXION (Indispensable) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. LECTURE ET NETTOYAGE ---
# On lit le lien directement depuis les secrets
df = conn.read(spreadsheet=st.secrets["connections"]["gsheets"]["spreadsheet"], ttl=0)

# Nettoyage des colonnes pour éviter les erreurs de frappe (espaces, etc.)
df.columns = df.columns.str.strip()

# --- 3. INTERFACE ---
# On s'assure que la colonne 'Nom' existe
if 'Nom' in df.columns:
    noms_liste = df['Nom'].dropna().tolist()
    user = st.selectbox("Sélectionnez votre nom :", [""] + noms_liste)

    if user:
        ligne_index = df[df['Nom'] == user].index[0]
        
        # Sécurité pour la colonne Statut
        statut_actuel = df.loc[ligne_index, 'Statut'] if 'Statut' in df.columns else None

        if pd.notna(statut_actuel) and statut_actuel != "":
            st.info(f"Votre choix est déjà enregistré : **{statut_actuel}**")
        else:
            choix = st.radio("Serez-vous présent au congrès ?", ["Présent", "Absent (Donner procuration)"])

            if "Absent" in choix:
                # Logique des mandataires (1 seule procuration autorisée)
                if 'Mandataire' in df.columns:
                    mandataires_deja_pris = df['Mandataire'].dropna().unique().tolist()
                else:
                    mandataires_deja_pris = []
                    
                disponibles = [n for n in noms_liste if n != user and n not in mandataires_deja_pris]
                
                mandataire = st.selectbox("À qui donnez-vous votre procuration ?", [""] + disponibles)
                
                if st.button("Valider ma procuration"):
                    if mandataire:
                        df.loc[ligne_index, 'Statut'] = "Absent"
                        df.loc[ligne_index, 'Mandataire'] = mandataire
                        conn.update(data=df)
                        st.success(f"C'est enregistré. {mandataire} votera pour vous.")
                        st.balloons()
                    else:
                        st.error("Veuillez choisir un mandataire.")
            else:
                if st.button("Valider ma présence"):
                    df.loc[ligne_index, 'Statut'] = "Présent"
                    if 'Mandataire' in df.columns:
                        df.loc[ligne_index, 'Mandataire'] = ""
                    conn.update(data=df)
                    st.success("Présence enregistrée ! Merci.")
else:
    st.error("La colonne 'Nom' est introuvable dans votre Google Sheet. Vérifiez la première ligne (A1).")
