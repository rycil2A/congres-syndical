import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Congrès S3C CFDT BOURGOGNE 2026", page_icon="🗳️")

# Affichage du logo
try:
    st.image("LOGO CFDT SC BOURGOGNE.jpg", width=200)
except:
    st.info("Logo en attente de chargement sur GitHub.")

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
                        
                        # 2. Envoi du mail au délégué ABSENT (celui qui remplit le formulaire)
                        if email_user:
                            sujet_absent = "Confirmation de votre procuration"
                            corps_absent = f"Bonjour {user},\n\nVotre absence au congrès est enregistrée. Votre voix sera portée par {mandataire}."
                            envoyer_mail_direct(email_user, sujet_absent, corps_absent)
                        
                        # 3. Envoi du mail au MANDATAIRE (celui qui reçoit le pouvoir)
                        ligne_mandataire = df[df['Nom'] == mandataire]
                        if not ligne_mandataire.empty:
                            email_mandataire = ligne_mandataire['Email'].values[0]
                            if pd.notna(email_mandataire) and "@" in str(email_mandataire):
                                sujet_mandataire = "Vous avez reçu une procuration (Congrès 2026)"
                                corps_mandataire = f"Bonjour {mandataire},\n\n{user} ne pourra pas être présent au congrès et vous a confié sa procuration.\n\nVous porterez donc sa voix en plus de la vôtre lors des votes. Merci de votre engagement."
                                envoyer_mail_direct(email_mandataire, sujet_mandataire, corps_mandataire)
                        
                        st.balloons()
                    else:
                        st.error("Veuillez choisir un mandataire.")
            else:
                if st.button("Valider ma présence"):
                    df.loc[ligne_index, 'Statut'] = "Présent"
                    # On vide la mandataire au cas où il y avait un reste d'un test précédent
                    if 'Mandataire' in df.columns:
                        df.loc[ligne_index, 'Mandataire'] = ""
                    conn.update(data=df)
                    st.success("Présence enregistrée ! Merci.")
                    if email_user:
                        envoyer_mail_direct(email_user, "Confirmation de présence", f"Bonjour {user},\n\nVotre présence au congrès S3C CFDT BOURGOGNE 2026 est bien confirmée.")
else:
    st.error("La colonne 'Nom' est introuvable. Vérifiez votre fichier Google Sheets.")
