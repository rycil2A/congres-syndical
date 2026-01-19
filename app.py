# --- LECTURE ET NETTOYAGE ---
df = conn.read(ttl=0)

# Cette ligne supprime les espaces invisibles avant ou après les noms de colonnes
df.columns = df.columns.str.strip()

# Sélection de l'utilisateur
noms_liste = df['Nom'].tolist()
user = st.selectbox("Sélectionnez votre nom :", [""] + noms_liste)

if user:
    ligne_index = df[df['Nom'] == user].index[0]
    
    # Sécurité : on vérifie si la colonne Statut existe, sinon on la considère vide
    statut_actuel = df.loc[ligne_index, 'Statut'] if 'Statut' in df.columns else None

    if pd.notna(statut_actuel) and statut_actuel != "":
        st.info(f"Votre choix est déjà enregistré : **{statut_actuel}**")
    else:
        choix = st.radio("Serez-vous présent au congrès ?", ["Présent", "Absent (Donner procuration)"])

        if "Absent" in choix:
            # Sécurité : on vérifie si la colonne Mandataire existe
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
                # Si la colonne Mandataire existe, on la vide pour ce présent
                if 'Mandataire' in df.columns:
                    df.loc[ligne_index, 'Mandataire'] = ""
                conn.update(data=df)
                st.success("Présence enregistrée ! Merci.")
