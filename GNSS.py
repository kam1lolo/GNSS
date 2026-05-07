# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 12:21:17 2026
@author: marki

"""
import rinex_studenci as rnx
from ftplib import FTP_TLS
import gzip
import shutil
import os
import numpy as np

##########################################################
# STAŁE

MU = 3.986005e14            # stała grawitacyjna Ziemi
OME_E = 7.2921151467e-5     # prędkosć kątowa Ziemi
C = 299792458.0             # prędkosć swiatła
A_ELL = 6378137.0           # wielka półos
E2 = 0.00669438002290       # kwadrat pierwszego mimosrodu


##########################################################
# BRDC

def pobranieBRDC(y,m,d,folder=''):
    """
    Pobiera plik nawigacyjny BRDC z serwera CDDIS dla podanej daty

    Parameters
    ----------
    y, m, d : int - rok, miesiąc, dzień
    folder : str - folder docelowy

    Returns
    -------
    str - scieżka do rozpakowanego pliku .rnx

    """
    os.makedirs(folder, exist_ok=True)
    doy = rnx.date2doy(y,m,d)
    filename = 'BRDC00IGS_R_' + str(y) + str(int(doy)).zfill(3) + '0000_01D_MN.rnx.gz'
    directory = (
        '/gps/data/daily/'
        + str(y) + '/'
        + str(int(doy)).zfill(3) + '/'
        + str(y)[2:] + 'p/'
    )
    new_filename = folder + '/' + filename
    rnx_filename = new_filename[:-3]
    
    if os.path.exists(rnx_filename):
        print("Plik już istnieje")
        return rnx_filename
        
    if not os.path.exists(new_filename):
        ftps = FTP_TLS(host = 'gdc.cddis.eosdis.nasa.gov')
        email = os.environ.get('CDDIS_EMAIL', 'your@email.com')
        ftps.login(user='anonymous', passwd=email)
        ftps.prot_p()
        ftps.cwd(directory)
        ftps.retrbinary("RETR " + filename, open(new_filename, 'wb').write)
        ftps.close()
        siz = os.path.getsize(new_filename)
        if siz == 0:
            print('No file found')
            os.remove(new_filename)
        with gzip.open(new_filename, 'rb') as f_in:
            with open(new_filename[0:-3], 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
    
    print(f"Zapisano do: {rnx_filename}")
    return rnx_filename


##########################################################
# Transformacja

def zamiana_na_xyz(phi, lam, h):
    """
    Zamiana współrzędnych geodezyjnych (phi, lam, h) na kartezjańskie XYZ.
    Phi, lam w radianach, h w metrach.
    """
    N = A_ELL / np.sqrt(1 - E2 * np.sin(phi)**2)
    X = (N + h) * np.cos(phi) * np.cos(lam)
    Y = (N + h) * np.cos(phi) * np.sin(lam)
    Z = (N * (1 - E2) + h) * np.sin(phi)
    return np.array([X,Y,Z])

def macierz_obrotu(phi, lam):
    """
    Macierz obrotu z układu XYZ do NEU dla punktu (phi, lam).
    """
    macierz = np.array([
        [-np.sin(phi) * np.cos(lam),    -np.sin(lam),   np.cos(phi) * np.cos(lam)],
        [-np.sin(phi) * np.sin(lam),    np.cos(lam),    np.cos(phi) * np.sin(lam)],
        [np.cos(phi),                   0,              np.sin(phi)]])
    return macierz


##########################################################
# Pozycja satelity - GPS / Galileo / BeiDou

def oblicz_xyz_satelity(tow, week, nav_sat):
    """
    Oblicza pozycję ECEF satelity GPS/Galileo/BeiDou z efemeryd Keplera.

    Parameters
    ----------
    tow : float         - czas w sekundach tygodnia
    week : int          - numer tygodnia GPS
    nav_sat : ndarray   - wiersze tablicy nav dla danego satelity

    Returns
    -------
    XYZ : ndarray [3]   - współrzędne ECEF [m]
    dett_rel_s : float  - poprawka zegara satelity [s]
    """    
    dt = tow + (week*7*86400) - (nav_sat[:,18] + nav_sat[:,28]*7*86400)
    idx_dt = np.argmin(np.abs(dt))
    nav = nav_sat[idx_dt,:]
    
    # Parametry zegara
    a_f0 = nav[7]
    a_f1 = nav[8]
    a_f2 = nav[9]
    
    # Elementy orbity Keplerowskiej
    sqrt_a  = nav[17]
    e       = nav[15]
    i_0     = nav[22]
    ome_0   = nav[20]
    l_0     = nav[24]
    m_0     = nav[13]
    
    # Parametry perturbacyjne
    dlt_n   = nav[12]
    ome_dot = nav[25]
    idot    = nav[26]
    c_uc    = nav[14]
    c_us    = nav[16]
    c_ic    = nav[19]
    c_is    = nav[21]
    c_rc    = nav[23]
    c_rs    = nav[11]
    t_oe    = nav[18]
    
    # 1
    tk = dt[idx_dt]

    if tk > 302400:
        tk -= 604800
    elif tk < -302400:
        tk += 604800
    
    # 2
    a = sqrt_a**2
    # 3
    n_0 = np.sqrt(MU/a**3)
    # 4 poprawiony ruch sredni
    n = n_0 + dlt_n
    # 5 anomalia srednia
    M_k = m_0 + n * tk

    # 6 anomalia mimosrodowa
    E = M_k
    while True:
        E_nowe = M_k + e*np.sin(E)
        if np.abs(E_nowe - E) < 1e-12:
            break
        E = E_nowe
        
    # 7 anomalia prawdziwa
    v_k = np.arctan2(np.sqrt(1 - e**2) * np.sin(E), np.cos(E) - e)
    
    # 8
    lat_k = v_k + l_0
    
    # 9 
    det_u = c_us * np.sin(2*lat_k) + c_uc * np.cos(2*lat_k)
    det_r = c_rs * np.sin(2*lat_k) + c_rc * np.cos(2*lat_k)
    det_i = c_is * np.sin(2*lat_k) + c_ic * np.cos(2*lat_k)
    
    # 10 
    u_k = lat_k + det_u
    r_k = a * (1 - e*np.cos(E)) + det_r
    i_k = i_0 + idot*tk + det_i
    
    # 11
    x_k = r_k * np.cos(u_k)
    y_k = r_k * np.sin(u_k)
    
    r_kontrola = np.sqrt(x_k**2 + y_k**2)
    if np.abs(r_k - r_kontrola) > 0.01:
        raise ValueError("Błąd kontroli wyznaczenia długości promienia w układzie orbitalnym")    
    
    # 12 
    ome_k = ome_0 + (ome_dot - OME_E)*tk - OME_E*t_oe
    
    # 13 
    Xk = x_k * np.cos(ome_k) - y_k * np.cos(i_k) * np.sin(ome_k)
    Yk = x_k * np.sin(ome_k) + y_k * np.cos(i_k) * np.cos(ome_k)
    Zk = y_k * np.sin(i_k)
    XYZ = np.array([Xk, Yk, Zk])
    
    r_kontrola = np.sqrt(Xk**2 + Yk**2 + Zk**2)
    if np.abs(r_k - r_kontrola) > 0.01:
        raise ValueError("Błąd kontroli wyznaczenia długości promienia w układzie geocentrycznym ECEF")   
    
    # 14
    det_ts = a_f0 + a_f1*tk + a_f2*(tk**2)
    
    # 15
    dett_rel = ((-2) * np.sqrt(MU) / C**2) * e * np.sqrt(a) * np.sin(E)
    dett_rel_s = det_ts + dett_rel

    return XYZ, dett_rel_s


##########################################################
# Pozycja satelity - GLONASS

def oblicz_xyz_satelity_GLONASS(week, tow, nav_sat):
    """
    Oblicza pozycję ECEF satelity GLONASS na podstawie funkcji z rinex_studenci

    Returns
    -------
    XYZ : ndarray [3] — współrzędne ECEF [m]
    dte : float        — poprawka zegara [s]

    """
    
    return rnx.satposR(week, tow, nav_sat)


##########################################################
# Identyfikacja systemu

def get_system(sat_id):
    """
    Zwraca literę systemu GNSS na podstawie ID satelity.
    """
    sat_id = int(sat_id)
    if sat_id < 100:   return 'G'
    elif sat_id < 200: return 'R'
    elif sat_id < 300: return 'E'
    elif sat_id < 400: return 'C'
    return 'X'
    
def sat_label(sat_id):
    """
    Zwraca etykietę satelity.
    """
    sat_id = int(sat_id)
    sys_letter = get_system(sat_id)
    offset = (sat_id // 100) * 100
    return f"{sys_letter}{sat_id - offset:02d}"


##########################################################
# Funkcja obliczeniowa

def oblicz_widocznosc(y, m, d, phi_deg, lam_deg, h_obs, maska, 
                      systems=('G', 'R', 'E', 'C'), nav_path=None, step_min=10):
    """
    Oblicza elewację, azymut i DOP-y dla wszystkich satelitów przez całą dobę.

    Parameters
    ----------
    y, m, d     : int - data
    phi_deg     : float - szerokosć geograficzna obserwatora
    lam_deg     : float - długosć geograficzna obserwatora
    h_obs       : float - wysokosć obserwatora
    maska       : float - kąt odcięcia obserwacji
    systems     : tuple - system GNSS do uwzględnienia
    nav_path    : str - scieżka do pliku RINEX nav; None = pobierz
    step_min    : krok czasowy [min]

    Returns
    -------
    df_sat  : DataFrame - kolumny: time_h, sat_id, label, system, el, az, X, Y, Z
    df_dop  : DataFrame - kolumny: time_h, n_visible, GDOP, PDOP, HDOP, VDOP, TDOP

    """
    import pandas as pd
    
    if nav_path is None:
        nav_path = pobranieBRDC(y, m, d)

    nav = rnx.readrnxnav3(nav_path)
    
    # Filtrowanie systemów
    OFFSETS = {'G': 0, 'R': 100, 'E': 200, 'C':300}
    mask_arr = np.zeros(len(nav), dtype=bool)
    for sys in systems:
        off = OFFSETS[sys]
        mask_arr |= (nav[:,0] >= off) & (nav[:,0] < off + 100)
    nav = nav[mask_arr & (nav[:,0] < 400)]
    
    week_start, tow_start= rnx.date2tow(y,m,d, 0,0,0)
    satelity = np.unique(nav[:,0])

    phi = np.deg2rad(phi_deg)
    lam = np.deg2rad(lam_deg)
    xyz_obs = zamiana_na_xyz(phi, lam, h_obs)
    R_neu = macierz_obrotu(phi, lam)
    
    step_s = step_min * 60
    records = []
    dop_recs = []

    SYSTEMS_ORDER = ['G', 'R', 'E', 'C']

    for tow in range(int(tow_start), int(tow_start) + 86400, step_s):
        t_hours = (tow - tow_start) / 3600.0
        A_rows = []
        
        for sat in satelity:
            ind_sat = nav[:,0] == sat
            nav_sat = nav[ind_sat,:].copy()
            sys = get_system(sat)
            
            try:
                if sys in ('G', 'E'):
                    xyz,_ = oblicz_xyz_satelity(tow, week_start, nav_sat)
                elif sys == 'R':
                    xyz, _ = oblicz_xyz_satelity_GLONASS(week_start, tow, nav_sat)
                elif sys == 'C':
                    week_BD = week_start - 1356
                    tow_BD = tow - 14
                    xyz, _ = oblicz_xyz_satelity(tow_BD, week_BD, nav_sat)
                else:
                    continue
            except Exception:
                continue
            
            vec = xyz - xyz_obs
            ro = np.linalg.norm(vec)
            neu = R_neu.T@vec
            el = np.rad2deg(np.arcsin(neu[2] / ro))              
            az = np.rad2deg(np.arctan2(neu[1], neu[0]))
            if az < 0:
                az += 360.0
                
            records.append({
                'time_h':   t_hours,
                'tow':      tow,
                'sat_id':   int(sat),
                'label':    sat_label(sat),
                'system':   sys,
                'el':       el,
                'az':       az,
                'X':        xyz[0],
                'Y':        xyz[1],
                'Z':        xyz[2]
            })

            if el > maska:
                time_cols = [1 if s == sys else 0 for s in SYSTEMS_ORDER if s in systems]
                A_rows.append([-vec[0]/ro, -vec[1]/ro, -vec[2]/ro] + time_cols)

        #DOP
        n_vis = len(A_rows)
        base = {'time_h': t_hours, 'tow': tow, 'n_visible':n_vis}
        if n_vis >= 4:
            A = np.array(A_rows)
            Q = np.linalg.inv(A.T @ A)
            diag = np.diag(Q)
            q_x, q_y, q_z = diag[0], diag[1], diag[2]
            q_t = np.sum(diag[3:])
            Q_neu = R_neu.T @ Q[:3,:3] @ R_neu
            q_n, q_e, q_u = np.diag(Q_neu)
            base.update({
                'GDOP': np.sqrt(q_x + q_y + q_z + q_t),
                'PDOP': np.sqrt(q_x + q_y + q_z),
                'TDOP': np.sqrt(q_t),
                'HDOP': np.sqrt(q_n + q_e),
                'VDOP': np.sqrt(q_u),
                })
        else:
            base.update({
                'GDOP': np.nan,
                'PDOP': np.nan,
                'TDOP': np.nan,
                'HDOP': np.nan,
                'VDOP': np.nan
                })
        dop_recs.append(base)
    df_sat = pd.DataFrame(records)
    df_dop = pd.DataFrame(dop_recs)
    return df_sat, df_dop
