# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 20:08:22 2026

@author: marki
"""

import streamlit as st
from datetime import date
import os

from GNSS import oblicz_widocznosc, pobranieBRDC
from wizualizacje import (
    wykres_elewacji,
    wykres_liczby_satelitów,
    wykres_skyplot,
    wykres_dop,
    wykres_groundtrack,
)


##########################################################
# Konfiguracja

st.set_page_config(
    page_title = 'GNSS Planning Tool',
    layout = 'wide',
    initial_sidebar_state = 'expanded',
)


##########################################################
# Sidebar

with st.sidebar:
    st.header('Parametry')
    
    st.subheader('Data')
    sel_date = st.date_input('', value=date(2026, 4, 20), label_visibility='collapsed')
    
    st.subheader('Obserwator')
    col1, col2 = st.columns(2)
    with col1:
        phi = st.number_input('φ [°N]', value = 52.0, min_value=-90.0, max_value=90.0, step=0.1, format='%.4f')
        h = st.number_input('h [m]', value=100.0, step=1.0, format='%.1f')
        
    with col2:
        lam = st.number_input('λ [°E]', value = 21.0, min_value=-180.0, max_value=180.0, step=0.1, format='%.4f')
        maska = st.number_input('Maska [°]', value=0.0, min_value=0.0, max_value=45.0, step=1.0, format='%.0f')
    
    st.subheader('Systemy GNSS')
    cG, cR = st.columns(2)
    cE, cC = st.columns(2)
    with cG: use_gps = st.checkbox('GPS (G)',       value=True)
    with cR: use_glo = st.checkbox('GLONASS (R)',   value=True)
    with cE: use_gal = st.checkbox('Galileo (E)',   value=True)
    with cC: use_bei = st.checkbox('BeiDou (C)',    value=True)
    
    st.subheader('Plik nawigacyjny')
    auto_download = st.checkbox('Pobierz automatycznie', value=False)
    if auto_download:
        brdc_folder = st.text_input('Folder docelowy', value='brdc', label_visibility='collapsed')
        nav_path_input = None
    else:
        nav_path_input = st.text_input(
            'Ścieżka do pliku .rnx',
            value='brdc/BRDC00IGS_R_20260600000_01D_MN.rnx',
            label_visibility = 'collapsed',
        )
    
    st.divider()
    compute_btn = st.button('OBLICZ', use_container_width=True)

    st.markdown("""
    **Kodowanie satelitów:**  
    GPS (G01–G32)  
    GLONASS (R01–R24)  
    Galileo (E01–E36)  
    BeiDou (C01–C63)  
    """)


##########################################################
# Nagłówek

st.title('GNSS Planning Tool')
st.caption('Satellite Visibility & DOP Analysis')
st.divider()


##########################################################
# Stan sesji

if "df_sat" not in st.session_state:
    st.session_state.df_sat = None
    st.session_state.df_dop = None
    st.session_state.computed = False


##########################################################
# Obliczenia

if compute_btn:
    systems = []
    if use_gps: systems.append('G')
    if use_glo: systems.append('R')
    if use_gal: systems.append('E')
    if use_bei: systems.append('C')
    
    if not systems:
        st.error('Wybierz co najmniej jeden system GNSS.')
        st.stop()
    
    
    if sel_date >= date.today():
        st.error("Niepoprawna data — wybierz datę z przeszłości.")
        st.stop()
    
    nav_path = None
    if auto_download:
        try:
            with st.spinner('Pobieranie pliku BRDC...'):
                nav_path = pobranieBRDC(
                    sel_date.year, sel_date.month, sel_date.day, folder=brdc_folder)
        except Exception as e:
            st.error(f'Błąd pobierania pliku: {e}')
            st.stop()
    else:
        nav_path = nav_path_input
        if not os.path.exists(nav_path):
            st.error(f'Plik nie istnieje: `{nav_path}`')
            st.stop()
    
    with st.spinner('Obliczanie pozycji satelitów...'):
        df_sat, df_dop = oblicz_widocznosc(
            y=sel_date.year, m=sel_date.month, d=sel_date.day,
            phi_deg=phi, lam_deg=lam, h_obs=h, maska=maska,
            systems=tuple(systems), nav_path=nav_path, step_min=10)
    
    st.session_state.df_sat = df_sat
    st.session_state.df_dop = df_dop
    st.session_state.computed = True


##########################################################
# Wyniki

if st.session_state.computed:
    df_sat = st.session_state.df_sat
    df_dop = st.session_state.df_dop
    
    # METRYKI
    n_total     = df_sat['label'].nunique()
    n_vis_avg   = df_dop['n_visible'].mean()
    gdop_avg    = df_dop['GDOP'].mean()
    gdop_min    = df_dop['GDOP'].min()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Łączna liczba satelitów", n_total)
    m2.metric("Śr. widocznych / epoka",  f"{n_vis_avg:.1f}")
    m3.metric("Średnie GDOP",            f"{gdop_avg:.2f}")
    m4.metric("Najlepsze GDOP",          f"{gdop_min:.2f}")
    
    st.divider()
    
    # ZAKŁADKI
    tab1, tab2, tab3, tab4 = st.tabs([
        'ELEWACJA & SATELITY',
        'SKYPLOT',
        'DOP',
        'GROUNDTRACK',
    ])
    
    with tab1:
        wszystkie_saty_el = sorted(df_sat['label'].unique())
        wybrane_saty_el = st.multiselect(
            'Wybierz satelity (puste = wszystkie)',
            wszystkie_saty_el, default=[], key='multiselect_el')
        df_el = df_sat[df_sat['label'].isin(wybrane_saty_el)] if wybrane_saty_el else df_sat
        
        st.plotly_chart(wykres_elewacji(df_el, maska), use_container_width=True)
        st.plotly_chart(wykres_liczby_satelitów(df_sat, df_dop, maska), use_container_width=True)
    
    with tab2:
        max_h = float(df_sat['time_h'].max())
        epoch_h = st.slider(
            'Epoka [h UTC]', 0.0, 23.0, 0.0, step=1.0)
        st.plotly_chart(wykres_skyplot(df_sat, epoch_h, maska), use_container_width=True)
    
    with tab3:
        st.plotly_chart(wykres_dop(df_dop), use_container_width=True)
        with st.expander('Statystyki DOP'):
            st.dataframe(
                df_dop[['GDOP', 'PDOP', 'HDOP', 'VDOP', 'TDOP']].agg({'min', 'max', 'mean'}).round(3))
    
    with tab4:
        col_gt1, col_gt2 = st.columns([3, 1])
        with col_gt1:
            wszystkie_saty_gt = sorted(df_sat['label'].unique())
            wybrane_saty_gt = st.multiselect(
                'Wybierz satelity (puste = wszystkie)',
                wszystkie_saty_gt, default=[], key='multiselelect_gt')
        with col_gt2:
            tylko_maska = st.toggle('Powyżej maski', value=False)
        saty_do_mapy = wybrane_saty_gt if wybrane_saty_gt else None
        st.plotly_chart(
            wykres_groundtrack(df_sat, phi_obs=phi, lam_obs=lam, systemy=None, wybrane=saty_do_mapy, tylko_powyzej_maski=tylko_maska, maska=maska), use_container_width=True)


##########################################################
# Ekran startowy                

else:
    st.markdown("""
    <div style="text-align:center; padding:5rem 2rem; color:#1e3a5f;">
        <h2 style="color:#1e3a5f !important; font-family:'Space Mono',monospace;">
            Ustaw parametry i naciśnij OBLICZ
        </h2>
        <p style="color:#334155; font-size:0.9rem;">
            Wybierz datę, współrzędne obserwatora, systemy GNSS<br>
            i wskaż plik BRDC w panelu po lewej.
        </p>
    </div>
    """, unsafe_allow_html=True)
