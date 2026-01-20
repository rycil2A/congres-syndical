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

# Style CSS : Couleur orange pour la barre de progression et boutons larges
st.markdown("""
    <style>
    /* Barre de progression en orange CFDT */
    .stProgress > div > div > div > div {
        background-color: #EF8F04;
    }
    /* Boutons larges et gras */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3.5em;
        font-weight: bold;
        background-color: #ff4b4b;
        color: white;
    }
    /* Style des textes informatifs */
    .stAlert {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. AFFICHAGE DU LOGO ---
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    try:
        st.image("LOGO CFDT SC BOURGOGNE.jpg", use_container_width=True)
    except:
        st.info("Logo CFDT S3C Bourgogne")

# --- 3. TITRE ET CONSIGNE ---
st.title("🗳️ Congrès S3C Bourgogne \n9 juin 2026")
st.markdown("### **Élection du Bureau Syndical**")
st.info("💡 *Confirmez votre présence ou désignez un remplaçant/mandataire.*")

# --- 4. FONCTION D'ENVOI DE MAIL ---
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
    except Exception as e:
        st.error(f"Erreur d'envoi de mail : {e}")

# --- 5. CONNEXION ET LECTURE ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(ttl=0)
df.columns = df.columns.str.strip()

# Barre de progression personnalisée
total_delegues = len(df)
reponses = df[df['Statut'].fillna('') != ''].shape[0]
pourcentage = reponses / total_delegues
st.write(f"📈 **Avancement du recensement : {reponses}/{total_delegues} délégués ont répondu**")
st.progress(pourcentage)
st.divider()

# --- 6. INTERFACE UTILISATEUR ---
if 'Nom' in df.columns:
    noms_liste = df['Nom'].dropna().sort_values().tolist()
    user = st.selectbox("👤 Sélectionnez votre nom :", [""] + noms_liste)

    if user:
        ligne_index = df[df['Nom'] == user].index[0]
        email_user = df.loc[ligne_index, 'Email'] if 'Email' in df.columns else None
        
        df['Statut'] = df['Statut'].fillna('').astype(str)
        statut_actuel = df.loc[ligne_index, 'Statut']

        if pd.notna(statut_actuel) and statut_actuel != "":
            st.success(f"✅ Ton choix est déjà enregistré : **{statut_actuel}**")
            if "Procuration" in statut_actuel:
                st.info(f"Mandataire désigné : **{df.loc[ligne_index, 'Mandataire']}**")
            elif "Remplacé" in statut_actuel:
                st.info(f"Remplaçant : **{df.loc[ligne_index, 'Invite_Nom']}**")
            st.write("---")
            st.write("🙏 *Merci de ton implication. Si tu as besoin de modifier cette information, contacte le Gestionnaire de l'application, Cyril ANTOLINI.*")
        else:
            choix = st.radio("Serez-vous présent au congrès ?", 
                            ["Présent", 
                             "Absent (Donner ma procuration à un autre responsable de section)", 
                             "Absent (Me faire remplacer par un autre membre de ma section)"])

            st.write("") 

            # --- CAS 1 : PRÉSENCE ---
            if choix == "Présent":
                st.write("📍 **Lieu :** Dijon\n📅 **Date :** 9 juin 2026")
                confirm = st.checkbox("Je confirme ma présence effective au Congrès.")
                if st.button("✅ VALIDER MA PRÉSENCE", disabled=not confirm):
                    df.loc[ligne_index, 'Statut'] = "Présent"
                    conn.update(data=df)
                    st.balloons()
                    st.success("C'est noté ! Ta présence est bien enregistrée.")
                    if email_user:
                        envoyer_mail_direct(email_user, "Confirmation de présence", 
                            f"Bonjour {user},\n\nTa présence au congrès du S3C Bourgogne le 9 juin 2026 à Dijon est confirmée.\nNous sommes ravis de te compter parmi nous.\n\nLe S3C Bourgogne")
                    st.rerun()

            # --- CAS 2 : PROCURATION ---
            elif "procuration" in choix:
                mask_absents = df['Statut'].str.contains("Absent|Remplacé", na=False, case=False)
                absents = df[mask_absents]['Nom'].tolist()
                deja_mandataires = df['Mandataire'].dropna().unique().tolist()
                ceux_qui_m_ont_choisi = df[df['Mandataire'] == user]['Nom'].tolist()

                disponibles = [n for n in noms_liste if n != user and n not in absents and n not in deja_mandataires and n not in ceux_qui_m_ont_choisi]
                mandataire = st.selectbox("🤝 À qui confiez-vous votre mandat ?", [""] + disponibles)
                
                if mandataire:
                    confirm = st.checkbox(f"Je confirme confier mon mandat de vote à {mandataire}.")
                    if st.button("🚀 VALIDER MA PROCURATION", disabled=not confirm):
                        df.loc[ligne_index, 'Statut'] = "Absent (Procuration)"
                        df.loc[ligne_index, 'Mandataire'] = mandataire
                        conn.update(data=df)
                        st.balloons()
                        st.success("Mandat enregistré avec succès.")
                        if email_user:
                            envoyer_mail_direct(email_user, "Confirmation de procuration", 
                                f"Bonjour {user},\n\nTon absence est bien enregistrée. Ta voix sera portée par {mandataire}.\nNous te remercions.\n\nLe S3C Bourgogne")
                        
                        email_mandataire = df[df['Nom'] == mandataire]['Email'].values[0]
                        if pd.notna(email_mandataire):
                            envoyer_mail_direct(email_mandataire, "Nouveau mandat reçu", 
                                f"Bonjour {mandataire},\n\n{user} te donne procuration pour le Congrès du 9 juin 2026 à Dijon.\n\nLe S3C Bourgogne")
                        st.rerun()

            # --- CAS 3 : REMPLACEMENT ---
            elif "remplacer" in choix:
                nom_remplacant = st.text_input("Nom et Prénom du remplaçant")
                email_remplacant = st.text_input("Adresse Email du remplaçant")

                if nom_remplacant and email_remplacant:
                    confirm = st.checkbox(f"Je confirme que {nom_remplacant} me remplacera.")
                    if st.button("🚀 VALIDER LE REMPLACEMENT", disabled=not confirm):
                        df.loc[ligne_index, 'Statut'] = "Remplacé"
                        df.loc[ligne_index, 'Invite_Nom'] = nom_remplacant
                        df.loc[ligne_index, 'Invite_Email'] = email_remplacant
                        conn.update(data=df)
                        st.balloons()
                        if email_user:
                            envoyer_mail_direct(email_user, "Confirmation de remplacement", 
                                f"Bonjour {user},\n\nTu seras remplacé(e) par {nom_remplacant} au Congrès.\n\nLe S3C Bourgogne")
                        envoyer_mail_direct(email_remplacant, "Invitation au Congrès", 
                            f"Bonjour {nom_remplacant},\n\n{user} t'a désigné(e) pour le remplacer au Congrès du S3C CFDT Bourgogne.\nÀ bientôt.\n\nLe S3C Bourgogne")
                        st.rerun()
else:
    st.error("Impossible de charger la base de données délégués.")
