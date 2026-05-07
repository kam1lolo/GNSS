# -*- coding: utf-8 -*-
"""
Created on Thu Apr  2 12:44:59 2026

@author: marki
"""
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pc

##########################################################
# Styl

SYS_COLORS = {
    'G': '#10b981',     # GPS
    'R': '#ef4444',     # GLONASS
    'E': '#3b82f6',     # Galileo
    'C': '#f59e0b'      # BeiDou
}

SYS_NAMES = {
    'G': 'GPS',
    'R': 'GLONASS',
    'E': 'Galileo',
    'C': 'BeiDou'
}

# Wspólny layout plotly
_LAYOUT_BASE = dict(
    paper_bgcolor = 'rgba(0,0,0,0)',
    plot_bgcolor = '#0d1526',
    font = dict(color='#b8c0cc', family='monospace', size=11),
    xaxis = dict(
        gridcolor = '#1e3a5f',
        zerolinecolor = '#1e3a5f',
        tickfont = dict(size=10),
        showspikes = True,
        spikecolor = '#334d6e',
        spikethickness = 1,
    ),
    yaxis = dict(
        gridcolor = '#1e3a5f',
        zerolinecolor = '#1e3a5f',
        tickfont = dict(size=10),
    ),
    margin = dict(l=55, r=20, t=45, b=50),
    legend = dict(
        bgcolor = 'rgba(10,14,26,0.85)',
        bordercolor = '#1e3a5f',
        borderwidth = 1,
        font = dict(size=9, color='#e2e8f0'),
        groupclick='toggleitem',
    ),
    hovermode = 'x unified',
)

def _layout(**overrides):
    """
    Zwraca słownik z opcjonalnymi nadpisaniami
    
    """
    layout = dict(_LAYOUT_BASE)
    layout.update(overrides)
    return layout

##########################################################
# Elewacja satelitów w ciągu doby

def wykres_elewacji(df_sat, maska):
    """
    Wykres elewacji satelitów w ciągu doby (powyżej maski).

    Parameters
    ----------
    df_sat  : DataFrame - dane satelitów (time_h, label, system, el)
    maska   : float     - kąt odcięcia 

    Returns
    -------
    fig : plotly Figure

    """
    fig = go.Figure()
    df_plot = df_sat.copy()
    df_plot.loc[df_plot['el'] <= maska, 'el'] = np.nan
    
    
    # Palety barw
    PALETY = {
        'G': pc.sequential.Greens[3:],
        'R': pc.sequential.Reds[3:],
        'E': pc.sequential.Blues[3:],
        'C': pc.sequential.Oranges[3:],
    }

    for sys in ['G', 'R', 'E', 'C']:
        paleta = PALETY[sys]
        saty = sorted(df_plot[df_plot['system'] == sys]['label'].unique())
        n = len(saty)
        if n == 0:
            continue
        for i, sat in enumerate(saty):
            kolor = paleta[int(i / max(n - 1, 1) * (len(paleta) - 1))]
            d = df_plot[df_plot['label'] == sat].sort_values('time_h')
            fig.add_trace(go.Scatter(
                x=d['time_h'],
                y=d['el'],
                mode='lines',
                name=sat,
                line=dict(color=kolor, width=1.5),
                legendgroup=sys,
                legendgrouptitle_text=SYS_NAMES[sys] if i == 0 else None,
                hovertemplate=f'<b>{sat}</b>  El: %{{y:.1f}}°<extra></extra>',
                connectgaps=False,
            ))
           
    # maska
    fig.add_hline(
        y=maska,
        line_dash='dash',
        line_color='#ff6b6b',
        line_width=1,
        annotation_text=f'maska {maska:.0f}°',
        annotation_font_color='#ff6b6b',
        annotation_position='right',
    )

    fig.update_layout(
        **_layout(
            title='Elewacja satelitów w ciągu doby',
            xaxis_title='Czas UTC [h]',
            yaxis_title='Elewacja [°]',
            yaxis_range=[maska - 2, 92],
            xaxis_range=[0, 24],
            height=450,
        )
    )
    return fig


##########################################################
# Liczba satelitów powyżej maski

def wykres_liczby_satelitów(df_sat, df_dop, maska):
    """
    Wykres liczby widocznych satelitów (powyżej maski) w ciągu doby,
    z podziałem na systemy GNSS.
 
    Parameters
    ----------
    df_sat : DataFrame  — dane satelitów (kolumny: time_h, system, el)
    df_dop : DataFrame  — dane DOPów (kolumny: time_h, n_visible)
    maska  : float      — kąt odcięcia [°]
 
    Returns
    -------
    fig : plotly Figure
    """
    fig = go.Figure()
 
    df_vis = df_sat[df_sat['el'] > maska].copy()
    per_system = (
        df_vis.groupby(['time_h', 'system'])
        .size()
        .reset_index(name='n')
    )
 
    for sys in ['G', 'R', 'E', 'C']:
        d = per_system[per_system['system'] == sys]
        if len(d) == 0:
            continue
        fig.add_trace(go.Scatter(
            x=d['time_h'],
            y=d['n'],
            mode='lines',
            name=SYS_NAMES[sys],
            line=dict(color=SYS_COLORS[sys], width=1.5),
            hovertemplate=f'<b>{SYS_NAMES[sys]}</b>: %{{y}}<extra></extra>',
            stackgroup='one',
        ))
 
    fig.add_trace(go.Scatter(
        x=df_dop['time_h'],
        y=df_dop['n_visible'],
        mode='lines',
        name='Łącznie',
        line=dict(color='#ffffff', width=2, dash='dot'),
        hovertemplate='<b>Łącznie</b>: %{y}<extra></extra>',
    ))
 
    fig.update_layout(
        **_layout(
            title='Liczba satelitów powyżej maski',
            xaxis_title='Czas UTC [h]',
            yaxis_title='Liczba satelitów',
            xaxis_range=[0, 24],
            height=300,
        )
    )
    return fig
            

##########################################################
# Skyplot

def wykres_skyplot(df_sat, epoch_h, maska):
    """
    Skyplort biegunowy dla wybranej epoki

    Parameters
    ----------
    df_sat  : DataFrame - dane satelitów (time_h, label, system, el, az)
    epoch_h : float     - wybrana epoka [h]
    maska   : float     - kąt odcięcia 

    Returns
    -------
    fig : plotly Figure

    """
    #najbliższa dostępna epoka
    czasy = df_sat['time_h'].unique()
    t = czasy[np.argmin(np.abs(czasy - epoch_h))]
    df_ep = df_sat[(df_sat['time_h'] == t) & (df_sat['el'] > maska)].copy()
    
    fig = go.Figure()
    
    # okręgi elewacji
    for el_ring in [0, 15, 30, 45, 60, 75]:
        r_ring = 90 - el_ring
        theta_ring = np.linspace(0, 360, 361)
        fig.add_trace(go.Scatterpolar(
            r = [r_ring] * 361,
            theta = theta_ring,
            mode = 'lines',
            line = dict(color='#14263d', width=0.7),
            showlegend = False,
            hoverinfo = 'skip',
        ))
        
        #etykieta elewacji
        fig.add_trace(go.Scatterpolar(
            r = [r_ring],
            theta = [0],
            mode = 'text',
            text = [f'{el_ring}°'],
            textfont = dict(color='#334d6e', size=8),
            showlegend = False,
            hoverinfo = 'skip',
        ))
    
    # satelity per system
    for sys in ['G', 'R', 'E', 'C']:
        d = df_ep[df_ep['system'] == sys]
        if len(d) == 0:
            continue
        fig.add_trace(go.Scatterpolar(
            r = 90 - d['el'],
            theta = d['az'],
            mode = 'markers+text',
            marker = dict(
                color = SYS_COLORS[sys],
                size = 10,
                symbol = 'circle',
                line= dict(color='white', width=0.5),
            ),
            text = d['label'],
            textposition = 'top center',
            textfont = dict(size=7, color=SYS_COLORS[sys]),
            name = SYS_NAMES[sys],
            legendgroup=sys,
            customdata = np.stack([d['el'], d['az']], axis=1),
            hovertemplate = '<b>%{text}</b><br>EL: %{customdata[0]:.1f}°<br>Az: %{customdata[1]:.1f}°<extra></extra>',
        ))
        
    fig.update_layout(
        polar = dict(
            bgcolor = '#0d1526',
            radialaxis = dict(
                range = [0, 90],
                showticklabels = False,
                gridcolor = '#1e3a5f',
                linecolor = '#1e3a5f',
            ),
            angularaxis = dict(
                direction = 'clockwise',
                rotation = 90,
                tickvals = [0, 45, 90, 135, 180, 225, 270, 315],
                ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'],
                gridcolor = '#1e3a5f',
                linecolor = '#1e3a5f',
                tickfont = dict(color='#94a3b8', size=10),
            ),
        ),
        paper_bgcolor = 'rgba(0,0,0,0)',
        font = dict(color='#94a3b8', family='monospace', size=10),
        title = f'Skyplot - epoka {t:.2f}h UTC',
        height = 460,
        legend = dict(
            bgcolor = 'rgba(0,0,0,0)',
            bordercolor = '#1e3a5f',
            borderwidth = 1,
            font = dict(size=9),
        ),
        margin = dict(l=30, r=30, t=50, b=30),
    )
    return fig


##########################################################
# DOP 

def wykres_dop(df_dop):
    """
    Wykres wartosci DOP w ciągu doby.

    Parameters
    ----------
    df_dop : Data Frame - dane DOP-ów (time_h, GDOP, PDOP, HDOP, VDOP, TDOP)

    Returns
    -------
    fig : plotly figure

    """
    dopy = [
        ('GDOP', '#7cb5ec', 2.5),
        ('PDOP', '#90ed7d', 2.0),
        ('HDOP', '#f7a35c', 1.5),
        ('VDOP', '#8085e9', 1.5),
        ('TDOP', '#434348', 1.5)
    ]
    fig = go.Figure()
    
    for nazwa, kolor, szerokosc in dopy:
        fig.add_trace(go.Scatter(
            x = df_dop['time_h'],
            y = df_dop[nazwa],
            mode = 'lines',
            name = nazwa,
            line = dict(color=kolor, width=szerokosc),
            hovertemplate = f'<b>{nazwa}</b>: %{{y:.2f}}<extra></extra>',
        ))
    
    y_max = min(10, df_dop['GDOP'].dropna().max() * 1.15 + 0.3)
    
    fig.update_layout(
        **_layout(
            title = 'Wartosci DOP w ciągu doby',
            xaxis_title = 'Czas UTC [h]',
            yaxis_title = 'DOP',
            yaxis_range = [0, y_max],
            xaxis_range =[0, 24],
            height = 360,
        )
    )
    return fig
       
       
##########################################################
# Mapa

def xyz2latlon(X, Y, Z):
    """
    Przelicza współrzędne ECEF (X,Y,Z) na szerokoć i długosć geograficzną.

    Returns
    -------
    lat, lon : float

    """
    lon = np.rad2deg(np.arctan2(Y, X))
    lat = np.rad2deg(np.arctan2(Z, np.sqrt(X**2 + Y**2)))
    return lat, lon
       
def wykres_groundtrack(df_sat, phi_obs=None, lam_obs=None, systemy=None, wybrane=None, tylko_powyzej_maski=False, maska=0.0):
    fig = go.Figure()
    
    df_plot = df_sat.copy()
    if systemy:
        df_plot = df_plot[df_plot['system'].isin(systemy)]
    if wybrane:
        df_plot = df_plot[df_plot['label'].isin(wybrane)]
    if tylko_powyzej_maski:
        df_plot = df_plot[df_plot['el'] > maska]
        
    # lat/lon z XYZ
    df_plot['lat'] = np.rad2deg(np.arctan2(df_plot['Z'], np.sqrt(df_plot['X']**2 + df_plot['Y']**2)))
    df_plot['lon'] = np.rad2deg(np.arctan2(df_plot['Y'], df_plot['X']))
    
    for sys in ['G', 'R', 'E', 'C']:
        if systemy and sys not in systemy:
            continue
        color = SYS_COLORS[sys]
        saty = sorted(df_plot[df_plot['system'] == sys]['label'].unique())
        
        for i, sat in enumerate(saty):
            d = df_sat[df_sat['label'] == sat].sort_values('time_h').copy()
            if len(d) < 2:
                continue
            
            d['lat'] = np.rad2deg(np.arctan2(d['Z'], np.sqrt(d['X']**2 + d['Y']**2)))
            d['lon'] = np.rad2deg(np.arctan2(d['Y'], d['X']))

            # Maska
            if tylko_powyzej_maski:
                d.loc[d['el'] <= maska, ['lat', 'lon']] = np.nan

            lat_vals = d['lat'].values.astype(float)
            lon_vals = d['lon'].values.astype(float)

            # Nieciągłosci
            lon_diff = np.abs(np.diff(np.where(np.isnan(lon_vals), 0, lon_vals)))
            breaks = np.where(lon_diff > 180)[0] + 1
            for b in breaks:
                lat_vals = np.insert(lat_vals, b, np.nan)
                lon_vals = np.insert(lon_vals, b, np.nan)

            fig.add_trace(go.Scattergeo(
                lat = lat_vals,
                lon = lon_vals,
                mode = 'lines',
                line = dict(color=color, width=1.2),
                name = SYS_NAMES[sys],
                legendgroup = sys,
                showlegend = (i == 0),
                hovertemplate = f'<b>{sat}</b><br><extra></extra>',
            ))
    
    # Pozycja obserwatora
    if phi_obs is not None and lam_obs is not None:
        fig.add_trace(go.Scattergeo(
            lat = [phi_obs],
            lon = [lam_obs],
            mode = 'markers+text',
            marker = dict(color='#00d4ff', size=10, symbol='star'),
            text = [f' {phi_obs:.2f}°N {lam_obs:.2f}°E'],
            textfont = dict(color='#00d4ff', size=9),
            name = 'Obserwator',
            hovertemplate = f'Obserwator<br>{phi_obs:.3f}°N {lam_obs:.3f}°E<extra></extra>',
        ))
    
    fig.update_layout(
        geo = dict(
            bgcolor = '#0d1526',
            showland = True,
            landcolor = '#1a2235',
            showocean = True,
            oceancolor = '#0d1526',
            showcoastlines = True,
            coastlinecolor = '#2d4a6b',
            showcountries = True,
            countrycolor = '#1e3a5f',
            showframe = False,
            projection_type = 'natural earth',
        ),
        paper_bgcolor = 'rgba(0,0,0,0)',
        font = dict(color='#94a3b8', family='monospace', size=10),
        title = 'Groundtrack satelitów',
        height = 420,
        legend = dict(
            bgcolor = 'rgba(10,14,25,0.85)',
            bordercolor = '#1e3a5f',
            borderwidth = 1,
            font = dict(size=9, color='#e2e8f0'),
        ),
        margin = dict(l=0, r=0, t=45, b=0),
    )
    return fig
