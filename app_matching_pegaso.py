import streamlit as st
import pandas as pd
import numpy as np
import io

# ==========================================
# CONFIGURAZIONE PAGINA E PREVENZIONE TRANSLATE
# ==========================================
st.set_page_config(
    page_title="Pegaso Co-Tutoring Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Blocco traduzione automatica per evitare bug 'removeChild' in Chrome
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# ==========================================
# DATASET INIZIALE DI PROVA
# ==========================================
if 'tutors_df' not in st.session_state:
    st.session_state['tutors_df'] = pd.DataFrame([
        {'nome': 'Dr. Iadicicco', 'sede': 'Napoli', 'agency': 82, 'communion': 88, 'coscienziosita': 90, 'apertura': 85, 'skills': 'Bilancio, E-Portfolio', 'belbin_role': 'Azione', 'disponibile': True},
        {'nome': 'Dr. Macera', 'sede': 'Napoli', 'agency': 55, 'communion': 85, 'coscienziosita': 88, 'apertura': 80, 'skills': 'Diario, Inclusione', 'belbin_role': 'Sociale', 'disponibile': True},
        {'nome': 'Dr. Messina', 'sede': 'Napoli', 'agency': 60, 'communion': 92, 'coscienziosita': 85, 'apertura': 90, 'skills': 'E-Portfolio, Metodologie', 'belbin_role': 'Valutazione', 'disponibile': True},
        {'nome': 'Dr. Salis', 'sede': 'Napoli', 'agency': 78, 'communion': 80, 'coscienziosita': 92, 'apertura': 75, 'skills': 'Regia, Diario', 'belbin_role': 'Azione', 'disponibile': True},
        {'nome': 'Dr. Scialpi', 'sede': 'Napoli', 'agency': 50, 'communion': 90, 'coscienziosita': 86, 'apertura': 88, 'skills': 'Bilancio, Metodologie', 'belbin_role': 'Sociale', 'disponibile': True},
        {'nome': 'Dr. Scipilliti', 'sede': 'Roma', 'agency': 80, 'communion': 84, 'coscienziosita': 89, 'apertura': 82, 'skills': 'Inclusione, E-Portfolio', 'belbin_role': 'Azione', 'disponibile': True},
        {'nome': 'Dr. Rossi', 'sede': 'Roma', 'agency': 52, 'communion': 86, 'coscienziosita': 87, 'apertura': 85, 'skills': 'Bilancio, Diario', 'belbin_role': 'Sociale', 'disponibile': True},
    ])

if 'classrooms_df' not in st.session_state:
    st.session_state['classrooms_df'] = pd.DataFrame([
        {'nome_aula': 'Aula Magna A1', 'sede': 'Napoli', 'n_corsisti': 85, 'tipo': 'Triade'},
        {'nome_aula': 'Aula Laboratorio B2', 'sede': 'Napoli', 'n_corsisti': 48, 'tipo': 'Diade'},
        {'nome_aula': 'Aula Seminariale R1', 'sede': 'Roma', 'n_corsisti': 52, 'tipo': 'Diade'},
    ])

# ==========================================
# NAVIGAZIONE LATERALE
# ==========================================
st.sidebar.title("Co-Tutoring Pegaso")
st.sidebar.caption("Modello di Abbinamento Regionale (Parte Quinta)")

menu_choice = st.sidebar.radio(
    "Seleziona Modulo:",
    [
        "⚡ Engine di Matching Regionale",
        "📝 Profilazione Tutor (QP-CoT)",
        "📊 Gestione Dati e File",
        "📜 Patto di Corresponsabilità",
        "📖 Quadro Scientifico"
    ]
)

# ==========================================
# FUNZIONI CALCOLO MATCHING
# ==========================================
def compute_diad_score(t1, t2, w1=0.35, w2=0.30, w3=0.35):
    if t1['sede'] != t2['sede'] or not t1['disponibile'] or not t2['disponibile']:
        return -1e6
    s1 = set([s.strip() for s in str(t1['skills']).split(',')])
    s2 = set([s.strip() for s in str(t2['skills']).split(',')])
    skills_coverage = min(len(s1.union(s2)) / 4.0, 1.0)
    comm_fit = 1.0 - (abs(t1['communion'] - t2['communion']) / 100.0)
    cosc_fit = 1.0 - (abs(t1['coscienziosita'] - t2['coscienziosita']) / 100.0)
    comm_cosc_score = (comm_fit + cosc_fit) / 2.0
    a1, a2 = t1['agency'], t2['agency']
    if a1 > 75 and a2 > 75:
        agency_score = 0.2
    elif (a1 >= 60 and a2 < 60) or (a2 >= 60 and a1 < 60):
        agency_score = 1.0
    else:
        agency_score = 0.7
    total_score = (w1 * skills_coverage) + (w2 * comm_cosc_score) + (w3 * agency_score)
    return round(total_score * 100, 2)

def compute_triad_score(t1, t2, t3, w1=0.35, w2=0.30, w3=0.35):
    d12 = compute_diad_score(t1, t2, w1, w2, w3)
    d23 = compute_diad_score(t2, t3, w1, w2, w3)
    d13 = compute_diad_score(t1, t3, w1, w2, w3)
    if min(d12, d23, d13) < 0:
        return -1e6
    avg_diad = (d12 + d23 + d13) / 3.0
    roles = {t1['belbin_role'], t2['belbin_role'], t3['belbin_role']}
    belbin_bonus = 15.0 if len(roles) == 3 else (5.0 if len(roles) == 2 else 0.0)
    return round(avg_diad + belbin_bonus, 2)

# ==========================================
# MODULO 1: ENGINE DI MATCHING
# ==========================================
if menu_choice == "⚡ Engine di Matching Regionale":
    st.header("Engine di Matching e Ottimizzazione Regionale")
    st.write("Abbinamento automatico in **Diadi** e **Triadi** per le sedi regionali.")
    
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        selected_sede = st.selectbox("Filtra per Sede Regionale:", ["Tutte"] + list(st.session_state['tutors_df']['sede'].unique()))
    with col_f2:
        st.write("Pesi Algoritmo:")
        w_skills = st.slider("Peso Competenze", 0.0, 1.0, 0.35, 0.05)
        w_comm = st.slider("Peso Communion/Coscienziosità", 0.0, 1.0, 0.30, 0.05)
        w_agency = st.slider("Peso Complementarità Agency", 0.0, 1.0, 0.35, 0.05)

    if st.button("🚀 Calcola Abbinamenti Ottimali", type="primary"):
        tutors = st.session_state['tutors_df'].copy()
        classrooms = st.session_state['classrooms_df'].copy()
        if selected_sede != "Tutte":
            tutors = tutors[tutors['sede'] == selected_sede]
            classrooms = classrooms[classrooms['sede'] == selected_sede]

        results = []
        avail_tutors = tutors.copy()

        # Triadi
        for _, room in classrooms[classrooms['tipo'] == 'Triade'].iterrows():
            best_score, best_team = -1, None
            t_idx = avail_tutors.index.tolist()
            for i in range(len(t_idx)):
                for j in range(i + 1, len(t_idx)):
                    for k in range(j + 1, len(t_idx)):
                        t1, t2, t3 = avail_tutors.loc[t_idx[i]], avail_tutors.loc[t_idx[j]], avail_tutors.loc[t_idx[k]]
                        if t1['sede'] == room['sede']:
                            s = compute_triad_score(t1, t2, t3, w_skills, w_comm, w_agency)
                            if s > best_score:
                                best_score, best_team = s, (t1, t2, t3, t_idx[i], t_idx[j], t_idx[k])
            if best_team:
                t1, t2, t3, i1, i2, i3 = best_team
                results.append({
                    'Aula': room['nome_aula'], 'Sede': room['sede'], 'Tipo': 'Triade', 'Corsisti': room['n_corsisti'],
                    'Co-Tutor 1 (Azione)': f"{t1['nome']} ({t1['agency']})",
                    'Co-Tutor 2 (Sociale)': f"{t2['nome']} ({t2['agency']})",
                    'Co-Tutor 3 (Valutazione)': f"{t3['nome']} ({t3['agency']})",
                    'Matching Score': best_score
                })
                avail_tutors = avail_tutors.drop([i1, i2, i3])

        # Diadi
        for _, room in classrooms[classrooms['tipo'] == 'Diade'].iterrows():
            best_score, best_team = -1, None
            t_idx = avail_tutors.index.tolist()
            for i in range(len(t_idx)):
                for j in range(i + 1, len(t_idx)):
                    t1, t2 = avail_tutors.loc[t_idx[i]], avail_tutors.loc[t_idx[j]]
                    if t1['sede'] == room['sede']:
                        s = compute_diad_score(t1, t2, w_skills, w_comm, w_agency)
                        if s > best_score:
                            best_score, best_team = s, (t1, t2, t_idx[i], t_idx[j])
            if best_team:
                t1, t2, i1, i2 = best_team
                results.append({
                    'Aula': room['nome_aula'], 'Sede': room['sede'], 'Tipo': 'Diade', 'Corsisti': room['n_corsisti'],
                    'Co-Tutor 1 (Azione)': f"{t1['nome']} ({t1['agency']})",
                    'Co-Tutor 2 (Sociale)': f"{t2['nome']} ({t2['agency']})",
                    'Co-Tutor 3 (Valutazione)': "— (Non previsto)",
                    'Matching Score': best_score
                })
                avail_tutors = avail_tutors.drop([i1, i2])

        res_df = pd.DataFrame(results)
        st.session_state['matching_results'] = res_df
        st.success(f"✅ Matching completato per {len(results)} aule!")
        st.dataframe(res_df, use_container_width=True)

        # Download CSV semplice per compatibilità garantita al 100%
        csv_bytes = res_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Scarica Report Abbinamenti (CSV)",
            data=csv_bytes,
            file_name="Abbinamenti_Co_Tutor_Pegaso.csv",
            mime="text/csv"
        )

# ==========================================
# MODULO 2: PROFILAZIONE TUTOR (QP-CoT)
# ==========================================
elif menu_choice == "📝 Profilazione Tutor (QP-CoT)":
    st.header("Questionario di Profilazione e Stili di Co-Tutoraggio (QP-CoT)")
    st.write("Compila la scheda per registrarti come Co-Tutor nel sistema regionale.")

    with st.form("tutor_form"):
        c1, c2 = st.columns(2)
        with c1:
            nome_tutor = st.text_input("Nome e Cognome:", "Dr. Nuovo Tutor")
            sede_tutor = st.selectbox("Sede d'Afferimento:", ["Napoli", "Roma", "Milano", "Palermo"])
        with c2:
            disponibile_tutor = st.checkbox("Disponibile per il ciclo attuale", value=True)
            skills_tutor = st.multiselect("Competenze Chiave:", ["Bilancio", "Diario", "E-Portfolio", "Inclusione", "Metodologie", "Regia"], default=["Bilancio", "Diario"])

        st.subheader("Valutazione Stili Relazionali (Scala 1-5)")
        q1 = st.slider("1. Guida attiva in plenaria e conduzione flussi", 1, 5, 4)
        q2 = st.slider("2. Capacità di cedere il controllo al collega", 1, 5, 4)
        q3 = st.slider("3. Attitudine alla co-progettazione scrupolosa (60 min)", 1, 5, 5)
        q4 = st.slider("4. Apertura all'intervisione e debriefing non giudicante", 1, 5, 5)
        q5 = st.slider("5. Rispetto rigoroso dei tempi e della documentazione", 1, 5, 4)
        q6 = st.slider("6. Flessibilità e adattamento della Co-Roadmap d'aula", 1, 5, 4)
        
        belbin_choice = st.radio("Ruolo d'Aula Preferito:", ["Azione (Guida Plenaria)", "Sociale (Facilitazione Sottogruppi)", "Valutazione (Osservazione OMF)"])

        submitted = st.form_submit_button("💾 Salva Profilo Co-Tutor")
        if submitted:
            agency_val = int(((q1 * 20) + ((6 - q2) * 20)) / 2)
            communion_val = int(q4 * 20)
            cosc_val = int(((q3 + q5) / 2) * 20)
            apertura_val = int(q6 * 20)
            role_clean = belbin_choice.split(" ")[0]

            new_row = {
                'nome': nome_tutor, 'sede': sede_tutor, 'agency': agency_val,
                'communion': communion_val, 'coscienziosita': cosc_val, 'apertura': apertura_val,
                'skills': ", ".join(skills_tutor), 'belbin_role': role_clean, 'disponibile': disponibile_tutor
            }
            st.session_state['tutors_df'] = pd.concat([st.session_state['tutors_df'], pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"🎉 Profilo registrato con successo per **{nome_tutor}**!")

# ==========================================
# MODULO 3: GESTIONE DATI E FILE
# ==========================================
elif menu_choice == "📊 Gestione Dati e File":
    st.header("Gestione Tabella Tutor e Aule")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Elenco Co-Tutor")
        st.dataframe(st.session_state['tutors_df'], use_container_width=True)
    with col2:
        st.subheader("Elenco Aule Regionali")
        st.dataframe(st.session_state['classrooms_df'], use_container_width=True)

# ==========================================
# MODULO 4: PATTO DI CORRESPONSABILITÀ
# ==========================================
elif menu_choice == "📜 Patto di Corresponsabilità":
    st.header("Generatore del Patto di Corresponsabilità Professionale")
    t1 = st.selectbox("Seleziona Primo Co-Tutor:", st.session_state['tutors_df']['nome'].unique(), index=0)
    t2 = st.selectbox("Seleziona Secondo Co-Tutor:", st.session_state['tutors_df']['nome'].unique(), index=1)
    
    patto = f"""
=================================================================================
         UNIVERSITÀ TELEMATICA PEGASO — PERCORSI ABILITANTI (D.P.C.M. 4 AGOSTO 2023)
               PATTO DI CORRESPONSABILITÀ PROFESSIONALE TRA CO-TUTOR
=================================================================================

I sottoscritti Co-Tutor:
1. {t1}
2. {t2}

SOTTOSCRIVONO IL SEGUENTE IMPEGNO ETICO-OPERATIVO:
- Parità di status professionale (Parity of Professional Status) in aula.
- Rispetto dei 60 minuti protetti di Co-Planning pre-aula.
- Co-conduzione fluida e integrata in presenza.
- 45 minuti entro 48 ore dedicati al Co-Debriefing riflessivo.

Data: ____________________   Firme: _______________________ / _______________________
"""
    st.code(patto, language="text")
    st.download_button("📥 Scarica Patto (.txt)", patto, file_name=f"Patto_{t1}_{t2}.txt")

# ==========================================
# MODULO 5: QUADRO SCIENTIFICO
# ==========================================
elif menu_choice == "📖 Quadro Scientifico":
    st.header("Quadro Scientifico (Parte Quinta)")
    st.markdown("""
    ### Principi dell'Abbinamento Relazionale e Psicometrico
    - **Big Five / OCEAN**: Coscienziosità (rispetto tempi protetti) e Stabilità Emotiva (de-strutturazione del judgementoring).
    - **Circomplesso Interpersonale**: Omofilia della Communion (calore) e Complementarità dell'Agency (scambio guida/ascolto).
    - **Ruoli di Belbin**: Copertura tripartita (Azione, Sociale, Valutazione) per le aule complesse.
    """)
