import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# CONFIGURAZIONE PAGINA
# ==========================================
st.set_page_config(
    page_title="Pegaso Co-Tutoring Matching Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Blocco prevenzione errori traduzione automatica Chrome
st.markdown('<meta name="google" content="notranslate">', unsafe_allow_html=True)

# ==========================================
# GESTIONE STATO INIZIALE (DATASET DEMO)
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
# NAVIGAZIONE SIDEBAR
# ==========================================
st.sidebar.title("Co-Tutoring Pegaso")
st.sidebar.caption("Modello di Abbinamento Regionale (Parte Quinta)")

menu_choice = st.sidebar.radio(
    "Navigazione Moduli:",
    [
        "⚡ Engine di Matching Regionale",
        "📝 Profilazione Tutor (Questionario QP-CoT - 15 Item)",
        "📊 Gestione Dati e Tabella Tutor",
        "📜 Patto di Corresponsabilità",
        "📖 Quadro Scientifico (Parte Quinta)"
    ]
)

# ==========================================
# ALGORITMO DI MATCHING (FUNZIONI DI CALCOLO)
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
# MODULO 1: ENGINE DI MATCHING
# ==========================================
if menu_choice == "⚡ Engine di Matching Regionale":
    st.header("Engine di Matching e Ottimizzazione Regionale")
    st.write("Abbinamento automatico in **Diadi** e **Triadi** basato sui profili dei Co-Tutor registrati.")

    selected_sede = st.selectbox("Filtra per Sede d'Ateneo:", ["Tutte le sedi"] + list(st.session_state['tutors_df']['sede'].unique()))

    if st.button("🚀 Calcola Abbinamenti Ottimali"):
        tutors = st.session_state['tutors_df'].copy()
        rooms = st.session_state['classrooms_df'].copy()

        if selected_sede != "Tutte le sedi":
            tutors = tutors[tutors['sede'] == selected_sede]
            rooms = rooms[rooms['sede'] == selected_sede]

        results = []
        avail_tutors = tutors.copy()

        # 1. Assegnazione Triadi (>70 corsisti)
        triad_rooms = rooms[rooms['tipo'] == 'Triade']
        for _, room in triad_rooms.iterrows():
            best_team, best_score = None, -1
            t_idx = avail_tutors.index.tolist()
            for i in range(len(t_idx)):
                for j in range(i + 1, len(t_idx)):
                    for k in range(j + 1, len(t_idx)):
                        t1, t2, t3 = avail_tutors.loc[t_idx[i]], avail_tutors.loc[t_idx[j]], avail_tutors.loc[t_idx[k]]
                        sc = compute_triad_score(t1, t2, t3)
                        if sc > best_score:
                            best_score, best_team = sc, (t1, t2, t3, t_idx[i], t_idx[j], t_idx[k])
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

        # 2. Assegnazione Diadi
        diad_rooms = rooms[rooms['tipo'] == 'Diade']
        for _, room in diad_rooms.iterrows():
            best_team, best_score = None, -1
            t_idx = avail_tutors.index.tolist()
            for i in range(len(t_idx)):
                for j in range(i + 1, len(t_idx)):
                    t1, t2 = avail_tutors.loc[t_idx[i]], avail_tutors.loc[t_idx[j]]
                    sc = compute_diad_score(t1, t2)
                    if sc > best_score:
                        best_score, best_team = sc, (t1, t2, t_idx[i], t_idx[j])
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
# MODULO 2: PROFILAZIONE TUTOR (15 QUESITI PSICOMETRICI QP-CoT)
# ==========================================
elif menu_choice == "📝 Profilazione Tutor (Questionario QP-CoT - 15 Item)":
    st.header("Questionario di Profilazione e Stili di Co-Tutoraggio (QP-CoT)")
    st.markdown("Compila i **15 quesiti psicometrici** per registrare il tuo profilo professionale nel sistema d'abbinamento. *(Scala 1 = Completamente in disaccordo, 5 = Completamente in accordo)*")

    with st.form("qp_cot_form"):
        st.subheader("📌 Dati Anagrafici e Logistici")
        c1, c2 = st.columns(2)
        with c1:
            nome_tutor = st.text_input("Nome e Cognome:", "Dr. Mario Rossi")
            sede_tutor = st.selectbox("Sede d'Afferimento:", ["Napoli", "Roma", "Milano", "Palermo", "Bari"])
        with c2:
            disponibile_tutor = st.checkbox("Disponibile per il ciclo attuale", value=True)
            skills_tutor = st.multiselect("Competenze Chiave Mappate:", ["Bilancio", "Diario", "E-Portfolio", "Inclusione", "Metodologie", "Regia"], default=["Bilancio", "Diario"])

        st.divider()
        st.subheader("🔹 AREA A: Agency & Regia d'Aula (Assertività e Guida)")
        i1 = st.slider("Item 1. Nelle situazioni d'aula mi trovo naturale ed efficace nel prendere la parola in plenaria, guidare la discussione generale e orientare i ritmi del gruppo classe.", 1, 5, 4)
        i2 = st.slider("Item 2. Non ho alcuna difficoltà a fare un passo indietro per lasciare la conduzione principale al collega, affiancandolo in modo discreto e senza sovrappormi.", 1, 5, 4)
        i3 = st.slider("Item 3. Quando in aula si verificano momenti di esitazione o di impasse, intervengo in modo deciso e assertivo per ripristinare la direzione del lavoro.", 1, 5, 4)

        st.divider()
        st.subheader("🔹 AREA B: Communion & Relazione di Team (Affiliazione e Cooperazione)")
        i4 = st.slider("Item 4. Ritengo fondamentale definire in anticipo e nei minimi dettagli ogni scelta didattica insieme al collega, cercando sempre un consenso condiviso prima di entrare in classe.", 1, 5, 5)
        i5 = st.slider("Item 5. Durante la lezione in presenza cerco costantemente il contatto visivo con il co-tutor per rimandargli segnali di incoraggiamento, intesa e supporto empatico.", 1, 5, 4)
        i6 = st.slider("Item 6. Nel confronto post-aula mi sento completamente a mio agio nel condividere con il collega i miei dubbi, le mie incertezze o gli errori commessi durante la lezione.", 1, 5, 5)

        st.divider()
        st.subheader("🔹 AREA C: Coscienziosità & Tempi Protetti (Metodo e Rigore)")
        i7 = st.slider("Item 7. Considero i 60 minuti di co-progettazione preparatoria un vincolo non negoziabile da svolgere con scrupolo prima di qualsiasi laboratorio.", 1, 5, 5)
        i8 = st.slider("Item 8. In aula monitoro costantemente l'orologio e mantengo un controllo rigoroso sul rispetto delle tempistiche assegnate alle diverse attività.", 1, 5, 4)
        i9 = st.slider("Item 9. Completo sempre con precisione e puntualità la documentazione di sintesi e le schede di debriefing entro le 48 ore successive all'incontro.", 1, 5, 5)

        st.divider()
        st.subheader("🔹 AREA D: Apertura Mentale & Flessibilità Didattica")
        i10 = st.slider("Item 10. Se durante il laboratorio percepisco un bisogno emergente dei corsisti, non ho problemi a deviare dalla scaletta prevista e riadattare la Co-Roadmap al volo.", 1, 5, 4)
        i11 = st.slider("Item 11. Amo sperimentare strategie didattiche dinamiche e articolate, come il lavoro a stazioni rotanti (Station Teaching) o la gestione di gruppi alternativi.", 1, 5, 4)

        st.divider()
        st.subheader("🔹 AREA E: Ruoli d'Aula di Belbin & Modeling")
        i12 = st.slider("Item 12. Nel lavoro d'aula mi attivo al meglio quando posso coordinare l'architettura generale dell'incontro, fare le sintesi conclusive e assicurarmi che gli obiettivi siano raggiunti.", 1, 5, 4)
        i13 = st.slider("Item 13. La mia massima efficacia si esprime quando circolo tra i banchi, affianco direttamente i piccoli gruppi di corsisti e facilito le dinamiche relazionali nei tavoli di lavoro.", 1, 5, 5)
        i14 = st.slider("Item 14. Trovo stimolante osservare in modo discreto i processi d'aula, raccogliere dati oggettivi sulle interazioni dei corsisti e analizzare con metodo cosa ha funzionato e cosa no.", 1, 5, 4)
        i15 = st.slider("Item 15. Considero la presenza del collega in aula non come un elemento di controllo, ma come una straordinaria risorsa speculare per migliorare la mia professionalità.", 1, 5, 5)

        submitted = st.form_submit_button("💾 Calcola e Salva Profilo Co-Tutor")

        if submitted:
            # Calcolo indici psicometrici su scala 0-100
            agency_val = int(((i1 + i3 + (6 - i2)) / 15.0) * 100)
            communion_val = int(((i4 + i5 + i6 + i15) / 20.0) * 100)
            cosc_val = int(((i7 + i8 + i9) / 15.0) * 100)
            apertura_val = int(((i10 + i11) / 10.0) * 100)

            # Determinazione del Ruolo Belbin prevalente
            if i12 >= i13 and i12 >= i14:
                belbin_role = "Azione"
            elif i13 >= i14:
                belbin_role = "Sociale"
            else:
                belbin_role = "Valutazione"

            new_tutor = {
                'nome': nome_tutor,
                'sede': sede_tutor,
                'agency': agency_val,
                'communion': communion_val,
                'coscienziosita': cosc_val,
                'apertura': apertura_val,
                'skills': ", ".join(skills_tutor),
                'belbin_role': belbin_role,
                'disponibile': disponibile_tutor
            }

            st.session_state['tutors_df'] = pd.concat([st.session_state['tutors_df'], pd.DataFrame([new_tutor])], ignore_index=True)
            
            st.success(f"🎉 Profilo registrato con successo per **{nome_tutor}**!")
            st.info(f"📊 **Parametri Psicometrici Calcolati**: Agency: **{agency_val}/100** | Communion: **{communion_val}/100** | Coscienziosità: **{cosc_val}/100** | Apertura: **{apertura_val}/100** | Ruolo Belbin: **{belbin_role}**")

# ==========================================
# MODULO 3: GESTIONE DATI
# ==========================================
elif menu_choice == "📊 Gestione Dati e Tabella Tutor":
    st.header("Gestione Tabella Tutor e Aule Regionali")
    st.write("Visualizza tutti i Co-Tutor registrati con i relativi parametri e le aule da abbinare.")

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
    st.write("Seleziona la coppia di Co-Tutor abbinata per generare il Patto formale etico-operativo.")

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
elif menu_choice == "📖 Quadro Scientifico (Parte Quinta)":
    st.header("Quadro Scientifico e Fondamenti Metodologici (Parte Quinta)")
    st.markdown("""
    ### Principi dell'Abbinamento Relazionale e Psicometrico
    - **Big Five / OCEAN**: Coscienziosità (rispetto tempi protetti) e Stabilità Emotiva (de-strutturazione del judgementoring).
    - **Circomplesso Interpersonale**: Omofilia della Communion (calore) e Complementarità dell'Agency (scambio guida/ascolto).
    - **Ruoli di Belbin**: Copertura tripartita (Azione, Sociale, Valutazione) per le aule complesse.
    """)
