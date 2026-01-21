import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="Congrès S3C Bourgogne 9 juin 2026", 
    page_icon="🗳️",
    initial_sidebar_state="collapsed"
)

# Style CSS : On optimise l'affichage pour mobile (très compact)
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 2rem;
    }
    [data-testid="stImage"] {
        margin-top: 0px !important;
        margin-bottom: 5px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 6px;
        height: 3.5em;
        font-weight: bold;
        background-color: #ff4b4b;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGO ET TITRE ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        st.image("LOGO CFDT SC BOURGOGNE.jpg", use_container_width=True)
    except:
        st.write("LOGO CFDT S3C")

st.title("🗳️ Congrès S3C")

# --- 3. CONNEXION ET PROGRESSION ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)
df.columns = df.columns.str.strip()

reponses = df[df['Statut'].fillna('') != ''].shape[0]
st.progress(reponses / len(df))
st.write(f"📈 **Réponses : {reponses}/{len(df)}**")

# --- 4. FONCTION MAIL ---
def envoyer_mail_direct(destinataire, sujet, message):
    try:
        gmail_user = st.secrets["emails"]["user"]
        gmail_password = st.secrets["emails"]["password"]
        msg = MIMEText(message)
        msg['Subject'] = sujet
        msg['From'] = f"S3C Bourgogne CFDT <{gmail_user}>"
        msg['To'] = destinataire
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()
    except:
        pass

# --- 5. INTERFACE ---
if 'Nom' in df.columns:
    noms_liste = df['Nom'].dropna().sort_values().tolist()
    user = st.selectbox("👤 Sélectionnez votre nom :", [""] + noms_liste)

    if user:
        ligne_index = df[df['Nom'] == user].index[0]
        email_user = df.loc[ligne_index, 'Email'] if 'Email' in df.columns else None
        df['Statut'] = df['Statut'].fillna('').astype(str)
        statut_actuel = df.loc[ligne_index, 'Statut']

        if statut_actuel != "":
            st.success(f"✅ Enregistré : **{statut_actuel}**")
        else:
            # CORRECTION : Utilisation d'un selectbox simple pour le choix de statut
            # C'est plus stable que le radio avec index=None et prend moins de place
            choix = st.selectbox("Serez-vous présent ?", 
                                ["Cliquer pour choisir...", "Présent", "Absent (Procuration)", "Absent (Remplacement)"])

            if choix != "Cliquer pour choisir...":
                st.divider()
                
                # CAS PRÉSENCE
                if choix == "Présent":
                    st.write("📍 Dijon | 📅 9 juin 2026")
                    confirm = st.checkbox("Je confirme ma présence.")
                    if st.button("✅ VALIDER MA PRÉSENCE", disabled=not confirm):
                        df.loc[ligne_index, 'Statut'] = "Présent"
                        conn.update(data=df)
                        st.balloons()
                        if email_user: envoyer_mail_direct(email_user, "Confirmation", f"Bonjour {user}, ta présence est confirmée.")
                        st.rerun()

                # CAS PROCURATION
                elif "Procuration" in choix:
                    mask_absents = df['Statut'].str.contains("Absent|Remplacé", na=False, case=False)
                    absents = df[mask_absents]['Nom'].tolist()
                    deja_mandataires = df['Mandataire'].dropna().unique().tolist()
                    # On retire soi-même et ceux déjà pris
                    disponibles = [n for n in noms_liste if n != user and n not in absents and n not in deja_mandataires]
                    
                    mandataire = st.selectbox("🤝 À qui confiez-vous votre mandat ?", [""] + disponibles)
                    if mandataire:
                        confirm = st.checkbox(f"Je confirme le mandat à {mandataire}.")
                        if st.button("🚀 VALIDER LA PROCURATION", disabled=not confirm):
                            df.loc[ligne_index, 'Statut'] = "Absent (Procuration)"
                            df.loc[ligne_index, 'Mandataire'] = mandataire
                            conn.update(data=df)
                            st.balloons()
                            if email_user: envoyer_mail_direct(email_user, "Procuration", f"Bonjour {user}, ton mandat est confié à {mandataire}.")
                            st.rerun()

                # CAS REMPLACEMENT
                elif "Remplacement" in choix:
                    nom_remp = st.text_input("Nom du remplaçant")
                    mail_remp = st.text_input("Email du remplaçant")
                    if nom_remp and mail_remp:
                        confirm = st.checkbox(f"Je confirme le remplacement par {nom_remp}.")
                        if st.button("🚀 VALIDER LE REMPLACEMENT", disabled=not confirm):
                            df.loc[ligne_index, 'Statut'] = "Remplacé"
                            df.loc[ligne_index, 'Invite_Nom'] = nom_remp
                            df.loc[ligne_index, 'Invite_Email'] = mail_remp
                            conn.update(data=df)
                            st.balloons()
                            st.rerun()
else:
    st.error("Erreur de base de données.")
