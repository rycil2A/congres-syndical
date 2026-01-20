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



st.markdown("""

    <style>

    .stButton>button {

        width: 100%;

        border-radius: 5px;

        height: 3.5em;

        font-weight: bold;

    }

    </style>

    """, unsafe_allow_html=True)



# --- 2. AFFICHAGE DU LOGO ---

try:

    st.image("LOGO CFDT SC BOURGOGNE.jpg", width=180)

except:

    st.info("Logo CFDT S3C Bourgogne")



# --- 3. TITRE ET CONSIGNE ---

st.title("🗳️ Congrès S3C Bourgogne \n9 juin 2026")

st.markdown("### **Élection du Bureau Syndical**")

st.info("💡 *Confirmez votre présence ou désignez un remplaçant/mandataire.*")

st.divider()



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



# --- 6. INTERFACE UTILISATEUR ---

if 'Nom' in df.columns:

    noms_liste = df['Nom'].dropna().sort_values().tolist()

    user = st.selectbox("👤 Sélectionnez votre nom :", [""] + noms_liste)



    if user:

        ligne_index = df[df['Nom'] == user].index[0]

        email_user = df.loc[ligne_index, 'Email'] if 'Email' in df.columns else None

        statut_actuel = df.loc[ligne_index, 'Statut'] if 'Statut' in df.columns else None



        if pd.notna(statut_actuel) and statut_actuel != "":

            st.warning(f"✅ Votre choix est déjà enregistré : **{statut_actuel}**")

        else:

            choix = st.radio("Serez-vous présent au congrès ?", 

                            ["Présent", 

                             "Absent (Donner procuration à un délégué sur liste)", 

                             "Absent (Me faire remplacer par un membre de section)"])



            st.write("") 



           # --- CAS 1 : PROCURATION CLASSIQUE (AVEC FILTRES STRICTS) ---

            if "procuration" in choix:

                # On s'assure que la colonne Statut est traitée comme du texte pour éviter l'erreur

                df['Statut'] = df['Statut'].fillna('').astype(str)

                

                # FILTRE 1 : Les absents (ceux qui ont "Absent" ou "Remplacé" dans leur statut)

                mask_absents = df['Statut'].str.contains("Absent|Remplacé", na=False, case=False)

                absents = df[mask_absents]['Nom'].tolist()

                

                # FILTRE 2 : Personnes ayant déjà reçu une procuration (Limite de 1 mandat)

                deja_mandataires = df['Mandataire'].dropna().unique().tolist()

                

                # FILTRE 3 : Réciprocité (Qui m'a déjà donné son mandat ?)

                ceux_qui_m_ont_choisi = df[df['Mandataire'] == user]['Nom'].tolist()



                # CONSTRUCTION DE LA LISTE FINALE

                disponibles = [

                    n for n in noms_liste 

                    if n != user                      # Pas soi-même

                    and n not in absents              # Pas un absent déclaré

                    and n not in deja_mandataires      # Pas quelqu'un qui a déjà un mandat

                    and n not in ceux_qui_m_ont_choisi # Pas mon propre "donneur"

                ]

                

                mandataire = st.selectbox("🤝 À qui confiez-vous votre mandat ?", [""] + disponibles)

                

                if not disponibles:

                    st.error("⚠️ Aucun mandataire disponible pour le moment (tous les délégués présents ont déjà reçu un mandat ou sont absents).")



                if st.button("🚀 VALIDER MA PROCURATION"):

                    if mandataire:

                        df.loc[ligne_index, 'Statut'] = "Absent (Procuration)"

                        df.loc[ligne_index, 'Mandataire'] = mandataire

                        conn.update(data=df)

                        st.success(f"Enregistré ! {mandataire} votera pour vous.")

                        st.balloons()

                        

                        if email_user:

                            envoyer_mail_direct(email_user, "Confirmation de procuration", f"Bonjour {user},\n\nTon absence est enregistrée. Ta voix sera portée par {mandataire}.\n\nLe S3C Bourgogne te remercie.")

                        

                        email_mandataire = df[df['Nom'] == mandataire]['Email'].values[0]

                        if pd.notna(email_mandataire):

                            envoyer_mail_direct(email_mandataire, "Nouveau mandat reçu", f"Bonjour {mandataire},\n\n{user} te donne procuration pour le congrès du 9 juin 2026 à Dijon.\n\nMerci de ton engagement.")

                    else:

                        st.error("⚠️ Choisissez un mandataire.")
