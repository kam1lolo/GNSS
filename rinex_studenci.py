# -*- coding: utf-8 -*-
"""
Created on Thu Mar  5 11:12:18 2026

@author: mgrzy
"""
import numpy as np
import math

def date2tow(y,m,d,hour=0,minute=0,s=0):
    days = date2mjd(y,m,d,0,0,0) - date2mjd(1980,1,6,0,0,0)
    weeks = int(days//7)
    dow = days % 7
    tow = hour*3600 + minute*60 + s + dow*86400
    return weeks, tow

def date2doy(y,m,d):
    mjd = date2mjd(y,m,d)
    doy = mjd - date2mjd(y,1,1) + 1
    return doy
    

def date2mjd(y,m,d,hour=0,minute=0,s=0):
    '''
    Simplified Modified Julian Date generator, valid only between
    1 March 1900 to 28 February 2100
    '''
    h = hour + minute/60 + s/3600
    if m <= 2:
        y = y - 1
        m = m + 12
    # A = np.trunc(y/100)
    # B = 2-A+np.trunc(A/4)
    # C = np.trunc(365.25*y)
    # D = np.trunc(30.6001 * (m+1))
    # jd = B + C + D + d + 1720994.5
    jd = np.floor(365.25*(y+4716))+np.floor(30.6001*(m+1))+d+h/24-1537.5-2400000.5;
    return jd

def mjd2date(mjd):
    """
    >>> jd_to_date(2446113.75)
    (1985, 2, 17.25)
    
    """
    jd = mjd + 2400001
    
    F, I = math.modf(jd)
    I = int(I)
    
    A = math.trunc((I - 1867216.25)/36524.25)
    
    if I > 2299160:
        B = I + 1 + A - math.trunc(A / 4.)
    else:
        B = I
        
    C = B + 1524
    
    D = math.trunc((C - 122.1) / 365.25)
    
    E = math.trunc(365.25 * D)
    
    G = math.trunc((C - E) / 30.6001)
    
    day = C - E + F - math.trunc(30.6001 * G)
    
    if G < 13.5:
        month = G - 1
    else:
        month = G - 13
        
    if month > 2.5:
        year = D - 4716
    else:
        year = D - 4715
        
    return int(year), int(month), day

def s2e(s,p,n):
    epoch = [int(s[p:p+4]), int(s[p+5:p+5+2]), int(s[p+8:p+8+2]), int(s[p+11:p+11+2]), int(s[p+14:p+14+2]), float(s[p+17:n])]
    return epoch 

def s2n(s,p,n):
    a = s[p:p+n]
    if (not (a and not a.isspace())):
        a = np.nan
    else:
        a = float(a)        
    return a
    
def findConstell(cc):
    """
    determine constellation integer value 

    Parameters
    -----------
    cc : string  is one character (from rinex satellite line)
        constellation definition:
            G : GPS
            R : Glonass
            E : Galileo
            C : Beidou

    Returns
    -------
    out : integer
        value added to satellite number for our system,
        0 for GPS, 100 for Glonass, 200 for Galileo, 300 for everything else
    """
    if (cc == 'G' or cc == ' '):
        out = 0
    elif (cc == 'R'): # glonass
        out = 100
    elif (cc == 'E'): # galileo
        out = 200
    elif (cc == 'C'): # galileo
        out = 300
    elif (cc == 'I'):
        out = 400
    elif (cc == 'Q'):
        out = 500
    elif (cc == 'S'):
        out = 600 
    else:
        out = 700
    return out

def readrnxnav3(file, gnss=['G','R','E','C']):
    n = 0
    nav = []
    inav = []
    a = None
    prn = None
    alfa = np.zeros((4))*np.nan; beta = np.zeros((4))*np.nan
    with open(file, "r") as f:  
        # szablon do wczytywania informacji z nagłówka pliku
        for s in f:
            label = s[60:]
            if label.find('IONOSPHERIC CORR') != -1:
                if s[0:4] == 'GPSA':
                    s = s.replace('D', 'E')
                    alfa = np.array(([float(s[6:6+11]), float(s[18:18+11]), float(s[30:30+11]), float(s[42:42+11])]))
                elif s[0:4] == 'GPSB':
                    s = s.replace('D', 'E')
                    beta = np.array(([float(s[6:6+11]), float(s[18:18+11]), float(s[30:30+11]), float(s[42:42+11])]))
            answer = s.find('END OF HEADER') # skip header
            if answer != -1:
                break
        # koniec czytania nagłówka - można usunąć, ale może się przydać w projekcie nr 2
        
        bsize = 37
        for s in f:
            s = s.replace('D', 'E')
            if (s[0].strip() != ""):
                if n!=0:
                    # koniec poprzedniej ramki   
                    b = np.zeros((bsize))*np.nan
                    b[:len(a)] = a
                    nav.append(b)
                    inav.append(prn)
                n+=1
                a = []
                system = s[0]
                add = findConstell(system)
                prn=int(s[1:1+2])+add
                p=4
                epoch = [int(s[p:p+4]), int(s[p+5:p+5+2]), int(s[p+8:p+8+2]), int(s[p+11:p+11+2]), int(s[p+14:p+14+2]), float(s[p+17:23])]
                a.extend(epoch)
            else:
                a.append(s2n(s,4,19))
            for x in range (3):
                p=23+x*19
                a.append(s2n(s,p,19))
        
            
        # ostatnia ramka        
        b = np.zeros((bsize))*np.nan
        b[:len(a)] = a
        nav.append(b)
        inav.append(prn)
    f.close()
    # zamiana na numpy        
    inav = np.array(inav).astype(int)
    nav = np.array(nav)
    nav = np.column_stack((inav, nav))
    return nav

def satposR(week, tow, nav_sat):
    tutc = tow - 18
    # zamiana week i tow na mjd
    days = week*7
    dayplus = int(tutc//86400)
    sod = tutc%86400
    mjd = date2mjd(1980,1,6,0) + days + dayplus + sod/86400   
    # dodanie kolumny z mjd do tablicy nav GLONASS
    for i, nav1 in enumerate(nav_sat):
        mjd_ = date2mjd(nav1[1], nav1[2], nav1[3],nav1[4],nav1[5],nav1[6])
        nav_sat[i, 22] = mjd_

    mjd_nav = nav_sat[:, 22]

    tk = mjd - mjd_nav
    i = np.argmin(np.abs(tk))
    mjd_nav = mjd_nav[i]

    nav_sat1 = nav_sat[i, :]


    OMEGAe = 7.2921151467e-5  # rad/s
    a = 6378136.0
    mu = 398600440000000.0
    C20 = -1.08263e-3

    # pozycje/pochodne z nav
    X0 = nav_sat1[10] * 1000.0
    Y0 = nav_sat1[14] * 1000.0
    Z0 = nav_sat1[18] * 1000.0

    X1 = nav_sat1[11] * 1000.0
    Y1 = nav_sat1[15] * 1000.0
    Z1 = nav_sat1[19] * 1000.0

    X2 = nav_sat1[12] * 1000.0
    Y2 = nav_sat1[16] * 1000.0
    Z2 = nav_sat1[20] * 1000.0

    # thetaGe = 0 (tak jak w oryginale)
    thetaGe = 0.0

    # pozycja ECI (tu thetaGe = 0 więc uproszczenie to X0,Y0)
    xa = X0 * math.cos(thetaGe) - Y0 * math.sin(thetaGe)
    ya = X0 * math.sin(thetaGe) + Y0 * math.cos(thetaGe)
    za = Z0

    # PRZYWRÓCONO korekcję rotacji (Coriolis) tak jak w oryginale
    Vxa = X1 * math.cos(thetaGe) - Y1 * math.sin(thetaGe) - OMEGAe * ya
    Vya = X1 * math.sin(thetaGe) + Y1 * math.cos(thetaGe) + OMEGAe * xa
    Vza = Z1

    # perturbacje (J2-like) - thetaGe=0 -> prosto X2,Y2
    Jxa = X2 * math.cos(thetaGe) - Y2 * math.sin(thetaGe)
    Jya = X2 * math.sin(thetaGe) + Y2 * math.cos(thetaGe)
    Jza = Z2

    # krok integ.
    h = 300.0
    T = (mjd - mjd_nav) * 86400.0  # integration duration (s)
    if T < 0:
        h = -h

    # zachowujemy zachowanie oryginału (MATLAB: fix -> Python int)
    Nstep = int(T / h) + 1
    last_step_duration = T - int(T / h) * h

    # jeśli ostatni krok jest w praktyce 0 -> ustaw na 0
    if abs(last_step_duration) < 1e-12:
        last_step_duration = 0.0

    # stan początkowy (skalary)
    x, y, z = xa, ya, za
    vx, vy, vz = Vxa, Vya, Vza

    # funkcja akceleracji (została taka sama jak w Twojej wersji)
    def accel(x, y, z):
        r = math.sqrt(x * x + y * y + z * z)
        inv_r = 1.0 / r
        mu_r2 = mu * inv_r * inv_r

        xb = x * inv_r
        yb = y * inv_r
        zb = z * inv_r
        rho2 = (a * inv_r) ** 2

        c = 1.5 * C20 * mu_r2 * rho2

        ax = -mu_r2 * xb + c * xb * (1.0 - 5.0 * zb * zb) + Jxa
        ay = -mu_r2 * yb + c * yb * (1.0 - 5.0 * zb * zb) + Jya
        az = -mu_r2 * zb + c * zb * (3.0 - 5.0 * zb * zb) + Jza
        return ax, ay, az

    # pętla RK4 — zachowujemy oryginalną liczbę kroków i ostatni krok
    for step in range(Nstep):
        if (step == Nstep - 1) and (last_step_duration != 0.0):
            h_step = last_step_duration
        else:
            h_step = h

        # K1
        ax1, ay1, az1 = accel(x, y, z)
        k1x, k1y, k1z = vx, vy, vz
        k1vx, k1vy, k1vz = ax1, ay1, az1

        # K2
        x2 = x + 0.5 * h_step * k1x
        y2 = y + 0.5 * h_step * k1y
        z2 = z + 0.5 * h_step * k1z
        vx2 = vx + 0.5 * h_step * k1vx
        vy2 = vy + 0.5 * h_step * k1vy
        vz2 = vz + 0.5 * h_step * k1vz
        ax2, ay2, az2 = accel(x2, y2, z2)
        k2x, k2y, k2z = vx2, vy2, vz2
        k2vx, k2vy, k2vz = ax2, ay2, az2

        # K3
        x3 = x + 0.5 * h_step * k2x
        y3 = y + 0.5 * h_step * k2y
        z3 = z + 0.5 * h_step * k2z
        vx3 = vx + 0.5 * h_step * k2vx
        vy3 = vy + 0.5 * h_step * k2vy
        vz3 = vz + 0.5 * h_step * k2vz
        ax3, ay3, az3 = accel(x3, y3, z3)
        k3x, k3y, k3z = vx3, vy3, vz3
        k3vx, k3vy, k3vz = ax3, ay3, az3

        # K4
        x4 = x + h_step * k3x
        y4 = y + h_step * k3y
        z4 = z + h_step * k3z
        vx4 = vx + h_step * k3vx
        vy4 = vy + h_step * k3vy
        vz4 = vz + h_step * k3vz
        ax4, ay4, az4 = accel(x4, y4, z4)
        k4x, k4y, k4z = vx4, vy4, vz4
        k4vx, k4vy, k4vz = ax4, ay4, az4

        # update
        x += h_step / 6.0 * (k1x + 2.0 * k2x + 2.0 * k3x + k4x)
        y += h_step / 6.0 * (k1y + 2.0 * k2y + 2.0 * k3y + k4y)
        z += h_step / 6.0 * (k1z + 2.0 * k2z + 2.0 * k3z + k4z)

        vx += h_step / 6.0 * (k1vx + 2.0 * k2vx + 2.0 * k3vx + k4vx)
        vy += h_step / 6.0 * (k1vy + 2.0 * k2vy + 2.0 * k3vy + k4vy)
        vz += h_step / 6.0 * (k1vz + 2.0 * k2vz + 2.0 * k3vz + k4vz)

    # rotacja do ECEF (jak w oryginale)
    theta = OMEGAe * T
    X_ECEF_PZ90 = x * math.cos(theta) + y * math.sin(theta)
    Y_ECEF_PZ90 = -x * math.sin(theta) + y * math.cos(theta)
    Z_ECEF_PZ90 = z

    # translacja (nie nadpisuj T)
    T_trans = np.array([-0.36, 0.08, 0.18])
    xyz = np.array([X_ECEF_PZ90, Y_ECEF_PZ90, Z_ECEF_PZ90]) + T_trans

    dte = nav_sat1[7] + nav_sat1[8] * T

    return xyz, dte