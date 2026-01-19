import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Congrès S3C CFDT BOURGOGNE 2026", page_icon="🗳️")

# Ligne à ajouter pour le logo
st.image("LOGO CFDT SC BOURGOGNE.jpg", width=200)

st.title("🗳️ Élection du Bureau Syndical")
st.markdown("Confirmez votre présence ou désignez un mandataire.")

# --- FONCTION D'ENVOI DE MAIL ---
def envoyer_mail_direct(destinataire, sujet, message):
    try:
        gmail_user = st.secrets["emails"]["user"]
        gmail_password = st.secrets["emails"]["password"]

        msg = MIMEText(message)
        msg['Subject'] = sujet
        msg['From'] = gmail_user
        msg['To'] = destinataire

        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        st.error(f"Erreur d'envoi de mail à {destinataire}: {e}")

# --- CONNEXION ET LECTURE ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)
df.columns = df.columns.str.strip()

# --- INTERFACE UTILISATEUR ---
if 'Nom' in df.columns:
    noms_liste = df['Nom'].dropna().tolist()
    user = st.selectbox("Sélectionnez votre nom :", [""] + noms_liste)

    if user:
        ligne_index = df[df['Nom'] == user].index[0]
        email_user = df.loc[ligne_index, 'Email'] if 'Email' in df.columns else None
        
        statut_actuel = df.loc[ligne_index, 'Statut'] if 'Statut' in df.columns else None

        if pd.notna(statut_actuel) and statut_actuel != "":
            st.warning(f"Votre choix est déjà enregistré : **{statut_actuel}**")
        else:
            choix = st.radio("Serez-vous présent au congrès ?", ["Présent", "Absent (Donner procuration)"])

            if "Absent" in choix:
                mandataires_pris = df['Mandataire'].dropna().unique().tolist()
                disponibles = [n for n in noms_liste if n != user and n not in mandataires_pris]
                
                mandataire = st.selectbox("À qui donnez-vous votre procuration ?", [""] + disponibles)
                
                if st.button("Valider ma procuration"):
                    if mandataire:
                        # 1. Mise à jour Google Sheets
                        df.loc[ligne_index, 'Statut'] = "Absent"
                        df.loc[ligne_index, 'Mandataire'] = mandataire
                        conn.update(data=df)
                        
                        st.success(f"Enregistré ! {mandataire} votera pour vous.")
                        
                        # 2. Envoi des emails
                        if email_user:
                            envoyer_mail_direct(email_user, "Confirmation de Procuration", 
                                               f"Bonjour {user},\n\nVotre absence est enregistrée. Votre voix sera portée par {mandataire}.")
                        
                        # Trouver l'email du mandataire
                        email_mandataire = df[df['Nom'] == mandataire]['Email'].values[0]
                        if pd.notna(email_mandataire):
                            envoyer_mail_direct(email_mandataire, "Vous avez une procuration", 
                                               f"Bonjour {mandataire},\n\n{user} vous a confié sa procuration pour le congrès de juin.")
                        
                        st.balloons()
                    else:
                        st.error("Veuillez choisir un mandataire.")
            else:
                if st.button("Valider ma présence"):
                    df.loc[ligne_index, 'Statut'] = "Présent"
                    conn.update(data=df)
                    st.success("Présence enregistrée ! Merci.")
                    if email_user:
                        envoyer_mail_direct(email_user, "Confirmation de présence", f"Bonjour {user}, votre présence est confirmée.")
else:
    st.error("Colonne 'Nom' introuvable dans le fichier.")
