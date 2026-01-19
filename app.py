import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import smtplib
from email.mime.text import MIMEText

# --- 1. CONFIGURATION DE LA PAGE (Optimisée Mobile) ---
st.set_page_config(
    page_title="Congrès S3C Bourgogne 2026", 
    page_icon="🗳️",
    initial_sidebar_state="collapsed"
)

# Style CSS pour les boutons larges (Spécial Smartphone)
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
st.title("🗳️ Congrès S3C 2026")
st.markdown("### **Élection du Bureau Syndical**")
st.info("💡 *Confirmez votre présence ou transmettez votre mandat pour ce vote.*")
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
                            ["Présent", "Absent (Donner procuration)"])

            st.write("") 

            # --- CAS : ABSENCE / PROCURATION ---
            if "Absent" in choix:
                mandataires_pris = df['Mandataire'].dropna().unique().tolist()
                disponibles = [n for n in noms_liste if n != user and n not in mandataires_pris]
                
                mandataire = st.selectbox("🤝 À qui confiez-vous votre mandat ?", [""] + disponibles)
                
                if st.button("🚀 VALIDER MA PROCURATION"):
                    if mandataire:
                        df.loc[ligne_index, 'Statut'] = "Absent"
                        df.loc[ligne_index, 'Mandataire'] = mandataire
                        conn.update(data=df)
                        
                        st.success(f"Enregistré ! {mandataire} votera pour vous.")
                        st.balloons() # <--- BALLONS ICI
                        
                        if email_user:
                            envoyer_mail_direct(email_user, "Confirmation de votre procuration", 
                                f"Bonjour {user},\n\nMerci pour ton retour, ton absence au congrès du S3C Bourgogne est bien enregistrée. \nTa voix sera portée par {mandataire}. \n\nLe S3C Bourgogne te remercie")
                        
                        ligne_mandataire = df[df['Nom'] == mandataire]
                        if not ligne_mandataire.empty:
                            email_mandataire = ligne_mandataire['Email'].values[0]
                            if pd.notna(email_mandataire):
                                envoyer_mail_direct(email_mandataire, "Vous avez reçu un mandat", 
                                    f"Bonjour {mandataire},\n\n{user} ne pourra pas être présent au congrés du S3C Bourgogne et te donne procuration.\n\nTu portera sa voix en plus de la tienne lors des votes pour l'élection du Bureau du S3C Bourgogne. \n\nLe S3C Bourgogne te remercie")
                    else:
                        st.error("⚠️ Veuillez choisir un mandataire.")
            
            # --- CAS : PRÉSENCE ---
            else:
                if st.button("✅ VALIDER MA PRÉSENCE"):
                    df.loc[ligne_index, 'Statut'] = "Présent"
                    if 'Mandataire' in df.columns:
                        df.loc[ligne_index, 'Mandataire'] = ""
                    conn.update(data=df)
                    
                    st.success("Présence enregistrée ! Merci.")
                    st.balloons() # <--- BALLONS ICI AUSSI
                    
                    if email_user:
                        envoyer_mail_direct(email_user, "Confirmation de présence", 
                            f"Bonjour {user},\n\nTa présence au congrès S3C BOURGOGNE 2026 est bien confirmée. \n\nLe S3C Bourgogne te remercie")
else:
    st.error("Impossible de charger la liste des délégués.")
