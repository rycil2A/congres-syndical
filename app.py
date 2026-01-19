import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Congrès 2026", page_icon="🗳️")

st.title("🗳️ Élection du Bureau Syndical")
st.markdown("Confirmez votre présence ou désignez un mandataire.")

# Connexion sécurisée au Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# Lecture des données (ttl=0 pour rafraîchir à chaque action)
df = conn.read(ttl=0)

# Sélection de l'utilisateur
noms_liste = df['Nom'].tolist()
user = st.selectbox("Sélectionnez votre nom :", [""] + noms_liste)

if user:
    # On regarde si l'utilisateur a déjà voté dans le tableau
    ligne_index = df[df['Nom'] == user].index[0]
    statut_actuel = df.loc[ligne_index, 'Statut']

    if pd.notna(statut_actuel) and statut_actuel != "":
        st.info(f"Votre choix est déjà enregistré : **{statut_actuel}**")
    else:
        choix = st.radio("Serez-vous présent au congrès ?", ["Présent", "Absent (Donner procuration)"])

        if "Absent" in choix:
            # RÈGLE : Un mandataire ne peut avoir qu'une seule procuration
            mandataires_deja_pris = df['Mandataire'].dropna().unique().tolist()
            disponibles = [n for n in noms_liste if n != user and n not in mandataires_deja_pris]
            
            mandataire = st.selectbox("À qui donnez-vous votre procuration ?", [""] + disponibles)
            
            if st.button("Valider ma procuration"):
                if mandataire:
                    # Mise à jour du DataFrame
                    df.loc[ligne_index, 'Statut'] = "Absent"
                    df.loc[ligne_index, 'Mandataire'] = mandataire
                    # Sauvegarde dans Google Sheets
                    conn.update(data=df)
                    st.success(f"C'est enregistré. {mandataire} votera pour vous.")
                    st.balloons()
                else:
                    st.error("Veuillez choisir un mandataire.")
        else:
            if st.button("Valider ma présence"):
                df.loc[ligne_index, 'Statut'] = "Présent"
                conn.update(data=df)
                st.success("Présence enregistrée ! Merci.")
