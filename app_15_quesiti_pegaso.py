import streamlit as st
import pandas as pd
import numpy as np
import io

# Meta tag per evitare la traduzione automatica di Chrome (previene errori di rendering React)
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# ==========================================
# CONFIGURAZIONE PAGINA E STILE
# ==========================================
st.set_page_config(
    page_title="Pegaso Co-Tutoring Matching Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# GESTIONE STATO INIZIALE (DEMO DATASET REGIONALE)
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
# SIDEBAR NAVIGATION
# ==========================================
st.sidebar.title("Co-Tutoring Pegaso")
st.sidebar.caption("Sistema di Abbinamento Regionale (Parte Quinta)")

menu_choice = st.sidebar.radio(
    "Navigazione Moduli:",
    [
        "📝 Profilazione Tutor (Questionario QP-CoT - 15 Quesiti)",
        "⚡ Engine di Matching Regionale",
        "📊 Gestione Dati e File Excel/CSV",
        "📜 Patto di Corresponsabilità",
        "📖 Quadro Scientifico (Parte Quinta)"
    ]
)

# ==========================================
# ALGORITMO DI MATCHING (ENGINE)
# ==========================================
def compute_diad_score(t1, t2, w1=0.35, w2=0.30, w3=0.35):
    if t1['sede'] != t2['sede'] or not t1['disponibile'] or not t2['disponibile']:
        return -1e6
    
    s1 = set([s.strip() for s in str(t1['skills']).split(',')])
    s2 = set([s.strip() for s in str(t2['skills']).split(',')])
    all_skills = s1.union(s2)
    skills_coverage = min(len(all_skills) / 4.0, 1.0)
    
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
# MODULO 1: QUESTIONARIO PSICOMETRICO COMPLETO (15 QUESITI)
# ==========================================
if menu_choice == "📝 Profilazione Tutor (Questionario QP-CoT - 15 Quesiti)":
    st.header("Questionario di Profilazione e Stili di Co-Tutoraggio (QP-CoT)")
    st.markdown("""
    *Compili il questionario a 15 quesiti su scala Likert (1 = Completamente in disaccordo, 5 = Completamente in accordo).*
    *Le Sue risposte alimenteranno l'algoritmo di abbinamento in diadi e triadi.*
    """)

    with st.form("qp_cot_form"):
        st.subheader("📋 Dati Anagrafici e Professionali")
        c1, c2 = st.columns(2)
        with c1:
            nome_tutor = st.text_input("Nome e Cognome:", "Dr. Mario Rossi")
            sede_tutor = st.selectbox("Sede d'Afferimento:", ["Napoli", "Roma", "Milano", "Palermo"])
        with c2:
            disponibile_tutor = st.checkbox("Disponibile per il ciclo laboratoriale attuale", value=True)
            skills_tutor = st.multiselect(
                "Competenze Metodologiche d'Aula:",
                ["Bilancio", "Diario", "E-Portfolio", "Inclusione", "Metodologie", "Regia"],
                default=["Bilancio", "Diario"]
            )

        st.markdown("---")
        st.subheader("🔹 AREA A: AGENCY & REGIA D'AULA (Assertività, Guida e Alternanza)")
        item1 = st.slider("1. Nelle situazioni d'aula mi trovo naturale ed efficace nel prendere la parola in plenaria, guidare la discussione generale e orientare i ritmi del gruppo classe.", 1, 5, 4)
        item2 = st.slider("2. Non ho alcuna difficoltà a fare un passo indietro per lasciare la conduzione principale al collega, affiancandolo in modo discreto e senza sovrappormi.", 1, 5, 4)
        item3 = st.slider("3. Quando in aula si verificano momenti di esitazione o di empasse, intervengo in modo deciso e assertivo per ripristinare la direzione del lavoro.", 1, 5, 4)

        st.markdown("---")
        st.subheader("🔹 AREA B: COMMUNION & RELAZIONE DI TEAM (Affiliazione, Cooperazione e Fiducia)")
        item4 = st.slider("4. Ritengo fondamentale definire in anticipo e nei minimi dettagli ogni scelta didattica insieme al collega, cercando sempre un consenso condiviso prima di entrare in classe.", 1, 5, 5)
        item5 = st.slider("5. Durante la lezione in presenza cerco costantemente il contatto visivo con il co-tutor per rimandargli segnali di incoraggiamento, intesa e supporto empatico.", 1, 5, 5)
        item6 = st.slider("6. Nel confronto post-aula mi sento completamente a mio agio nel condividere con il collega i miei dubbi, le mie incertezze o gli errori commessi durante la lezione.", 1, 5, 5)

        st.markdown("---")
        st.subheader("🔹 AREA C: COSCIENZIOSITÀ & TEMPI PROTETTI (Metodo, Rigore e Tempi)")
        item7 = st.slider("7. Considero i 60 minuti di co-progettazione preparatoria un vincolo non negoziabile da svolgere con scrupolo prima di qualsiasi laboratorio.", 1, 5, 5)
        item8 = st.slider("8. In aula monitoro costantemente l'orologio e mantengo un controllo rigoroso sul rispetto delle tempistiche assegnate alle diverse attività.", 1, 5, 4)
        item9 = st.slider("9. Completo sempre con precisione e puntualità la documentazione di sintesi e le schede di debriefing entro le 48 ore successive all'incontro.", 1, 5, 5)

        st.markdown("---")
        st.subheader("🔹 AREA D: APERTURA MENTALE & ADATTABILITÀ IN ITINERE (Flessibilità Didattica)")
        item10 = st.slider("10. Se durante il laboratorio percepisco un bisogno emergente dei corsisti, non ho problemi a deviare dalla scaletta prevista e riadattare la Co-Roadmap al volo.", 1, 5, 4)
        item11 = st.slider("11. Amo sperimentare strategie didattiche dinamiche e articolate, come il lavoro a stazioni rotanti (Station Teaching) o la gestione di gruppi alternativi.", 1, 5, 4)

        st.markdown("---")
        st.subheader("🔹 AREA E: RUOLI DI TEAM DI BELBIN & MODELLING RELAZIONALE")
        item12 = st.slider("12. Nel lavoro d'aula mi attivo al meglio quando posso coordinare l'architettura generale dell'incontro, fare le sintesi conclusive e assicurarmi che gli obiettivi siano raggiunti.", 1, 5, 4)
        item13 = st.slider("13. La mia massima efficacia si esprime quando circolo tra i banchi, affianco direttamente i piccoli gruppi di corsisti e facilito le dinamiche relazionali nei tavoli di lavoro.", 1, 5, 4)
        item14 = st.slider("14. Trovo stimolante osservare in modo discreto i processi d'aula, raccogliere dati oggettivi sulle interazioni dei corsisti e analizzare con metodo cosa ha funzionato e cosa no.", 1, 5, 4)
        item15 = st.slider("15. Considero la presenza del collega in aula non come un elemento di controllo, ma come una straordinaria risorsa speculare per migliorare la mia professionalità.", 1, 5, 5)

        st.markdown("---")
        submitted = st.form_submit_button("💾 Calcola e Salva Profilo Co-Tutor")

        if submitted:
            # Algoritmo di conversione psicometrica in punteggi centesimali
            agency_score = int((((item1 + item3) / 2.0) * 0.6 + ((6 - item2) * 0.4)) * 20)
            communion_score = int(((item4 + item5 + item6 + item15) / 4.0) * 20)
            cosc_score = int(((item7 + item8 + item9) / 3.0) * 20)
            apertura_score = int(((item10 + item11) / 2.0) * 20)

            # Determinazione del Ruolo Dominante di Belbin
            belbin_scores = {
                'Azione': item12,
                'Sociale': item13,
                'Valutazione': item14
            }
            belbin_role = max(belbin_scores, key=belbin_scores.get)

            new_tutor = {
                'nome': nome_tutor,
                'sede': sede_tutor,
                'agency': agency_score,
                'communion': communion_score,
                'coscienziosita': cosc_score,
                'apertura': apertura_score,
                'skills': ", ".join(skills_tutor),
                'belbin_role': belbin_role,
                'disponibile': disponibile_tutor
            }

            st.session_state['tutors_df'] = pd.concat([st.session_state['tutors_df'], pd.DataFrame([new_tutor])], ignore_index=True)

            st.success(f"🎉 **Profilo registrato con successo per {nome_tutor}!**")
            st.info(f"📊 **Risultati della Profilazione Psicometrica**:")
            res_col1, res_col2, res_col3, res_col4, res_col5 = st.columns(5)
            res_col1.metric("Agency (Guida)", f"{agency_score}/100")
            res_col2.metric("Communion (Calore)", f"{communion_score}/100")
            res_col3.metric("Coscienziosità", f"{cosc_score}/100")
            res_col4.metric("Apertura Mentale", f"{apertura_score}/100")
            res_col5.metric("Ruolo Belbin", belbin_role)

# ==========================================
# MODULO 2: ENGINE DI MATCHING REGIONALE
# ==========================================
elif menu_choice == "⚡ Engine di Matching Regionale":
    st.header("Engine di Matching e Ottimizzazione Regionale")
    st.write("Abbinamento automatico in **Diadi** e **Triadi** basato sulle risposte psicometriche dei Co-Tutor.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sedi_disponibili = ["Tutte"] + list(st.session_state['tutors_df']['sede'].unique())
        selected_sede = st.selectbox("Filtra per Sede Regionale:", sedi_disponibili)
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

        # Triadi per aule complesse (>70 corsisti)
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

        # Diadi per aule ordinarie
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
        st.success(f"✅ Matching completato con successo per {len(results)} aule!")
        st.dataframe(res_df, use_container_width=True)

        csv_bytes = res_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Scarica Report Abbinamenti (CSV)",
            data=csv_bytes,
            file_name="Abbinamenti_Co_Tutor_Pegaso.csv",
            mime="text/csv"
        )

# ==========================================
# MODULO 3: GESTIONE DATI E FILE EXCEL/CSV
# ==========================================
elif menu_choice == "📊 Gestione Dati e File Excel/CSV":
    st.header("Gestione Tabella Tutor e Aule Regionali")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Elenco Co-Tutor Registrati")
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
# MODULO 5: QUADRO SCIENTIFICO (PARTE QUINTA)
# ==========================================
elif menu_choice == "📖 Quadro Scientifico (Parte Quinta)":
    st.header("Quadro Scientifico e Fondamenti Metodologici (Parte Quinta)")
    st.markdown("""
    ### Parte Quinta — La complementarità relazionale nel co-tutoraggio
    
    1. **Big Five / OCEAN**:
       - *Coscienziosità*: garanzia del rispetto dei 60 min di co-planning e 45 min di co-debriefing.
       - *Stabilità Emotiva*: disattivazione dell'ansia da prestazione e del *judgementoring*.
    
    2. **Circomplesso Interpersonale**:
       - *Omofilia sulla Communion*: alto calore relazionale condiviso per un ambiente sicuro.
       - *Complementarità sull'Agency*: alternanza tra un profilo guida e un profilo ad ascolto attivo.
    
    3. **Ruoli di Team di Belbin**:
       - Copertura tripartita (*Azione, Sociale, Valutazione*) per le aule complesse (>70 corsisti).
    """)
