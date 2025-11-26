# -------------------------------------------------------------------------------
# Name:        module1
# Purpose:
#
# Author:      derojp
#
# Created:     22/02/2023
# Copyright:   (c) derojp 2023
# Licence:     <your licence>
# -------------------------------------------------------------------------------

import os
import sys
import json
from geomet import wkt
import time
import arcpy

# ------------------------------------------
url_omgeving = {
    "productie": "apps.mow.vlaanderen.be",
    "tei": "apps-tei.mow.vlaanderen.be",
    "dev": "apps-dev.mow.vlaanderen.be",
}

f_type = {
    'refpunt_wegnr': ["TEXT", 10, "rfpntWnr"],
    'refpunt_opschrift': ["DOUBLE", 0, "rfpntOpsch"],
    'refpunt_afstand': ["LONG", 0, "rfpntAfst"],
    'proj_x': ["DOUBLE", 0],
    'proj_y': ["DOUBLE", 0],
    'wsoidn': ["LONG", 0],
    'Wsoidn': ["LONG", 0],
    'wsoidn_m': ["DOUBLE", 0],
    'begin_refpunt_wegnr': ["TEXT", 10, "bRpntWnr"],
    'begin_refpunt_opschrift': ["DOUBLE", 0, "bRpntOpsch"],
    'begin_refpunt_afstand': ["LONG", 0, "bRpntAfst"],
    'begin_proj_x': ["DOUBLE", 0, "bProjX"],
    'begin_proj_y': ["DOUBLE", 0, "bProjY"],
    'begin_wsoidn': ["LONG", 0, "bWsoidn"],
    'begin_wsoidn_m': ["DOUBLE", 0, "bWsoidnM"],
    'VanM': ["DOUBLE", 0, "VanM"],
    'eind_refpunt_wegnr': ["TEXT", 10, "eRpntWnr"],
    'eind_refpunt_opschrift': ["DOUBLE", 0, "eRpntOpsch"],
    'eind_refpunt_afstand': ["LONG", 0, "eRpntAfst"],
    'eind_proj_x': ["DOUBLE", 0, "eProjX"],
    'eind_proj_y': ["DOUBLE", 0, "eProjY"],
    'eind_wsoidn': ["LONG", 0, "eWsoidn"],
    'eind_wsoidn_m': ["DOUBLE", 0, "eWsoidnM"],
    'TotM': ["DOUBLE", 0, "TotM"],
    'wegnummer': ["TEXT", 10],
}


# ---------------------------------------------
def maakJsonMultipointVanFcOrTblCoordinaten(input_table, crs, f_wegnr=None):
    # vb:[{"geometry":{"type":"Point","crs":{"properties":{"name":"EPSG:31370"},"type":"name"},"bbox":[139895.57,170047.41,139895.57,170047.41],"coordinates":[139895.57,170047.41]},"wegType":null},{"geometry":{"type":"Point","crs":{"properties":{"name":"EPSG:31370"},"type":"name"},"bbox":[140024.81,170065.2,140024.81,170065.2],"coordinates":[140024.81,170065.2]},"wegType":null}]
    import arcpy

    # ga door de data
    locaties = []
    f_sc = ["SHAPE@"]
    if f_wegnr != None:
        f_sc = ["SHAPE@", f_wegnr]

    with arcpy.da.SearchCursor(input_table, f_sc) as sc:
        for row in sc:
            # arcpy.AddMessage(f'row : {row}')
            locatie_multipoint = []
            for pnt in row[0]:
                x = pnt.X
                y = pnt.Y
                locatie_point = {
                    "geometry": {"type": "Point", "crs": {"properties": {"name": f"EPSG:{crs}"}, "type": "name"},
                                 "coordinates": [x, y]}}
            if f_wegnr != None:
                wegnr = row[1]
                locatie_point["wegnummer"] = {"nummer": f"{wegnr}"}
                locatie_multipoint.append(locatie_point)
            locaties.append(locatie_multipoint)

    return locaties


def maak_coordinatenlijst(polyline):
    multi_coords = []
    for part in polyline:
        line_coords = []
        for p in part:
            if p:
                # Opbouw coördinaten afhankelijk van Z- en M-waarden
                coord = [p.X, p.Y]
                if p.Z:
                    coord.append(p.Z)
                if p.M:
                    coord.append(p.M)
                line_coords.append(coord)

        if line_coords:  # Alleen toevoegen als er punten zijn
            multi_coords.append(line_coords)
    return multi_coords


def maak_puntenlijst(polyline):
    start_end_points = []
    for part in polyline:
        if part and len(part) > 1:  # Controleer of de part minstens 2 punten heeft
            start_end_points.append([part[0].X, part[0].Y])
            start_end_points.append([part[-1].X, part[-1].Y])

    return start_end_points


def featureline_to_ls2geometry(polyline, wsoidn, wegnummer='', van_refpunt='', van_afstand='', tot_refpunt='',
                               tot_afstand='', wegnr_van_refpunt='', wegnr_tot_refpunt=''):
    """
    outputsjabloon: rest_lijnlocatie_herbereken
    werkt enkel met projectie 31370
    """
    puntenlijst = maak_puntenlijst(polyline)
    ls2_geometry = dict()
    ls2_geometry["type"] = "Feature"
    ls2_geometry["punten"] = list()
    ls2_geometry["geometry"] = {"type": "MultiLineString",
                                "crs": {"properties": {"name": f"EPSG:31370"}, "type": "name"}}

    for i, punt in enumerate(puntenlijst):
        ls2_punt = dict()
        ls2_punt["type"] = "WegsegmentPuntLocatie"
        ls2_punt["wegsegmentId"] = {"oidn": int(wsoidn), "gidn": "", "uidn": ""}
        if wegnummer != '' and wegnummer is not None:
            ls2_punt["relatief"] = {"wegnummer": {"nummer": wegnummer}}
        if i == 0 and van_refpunt != '' and van_afstand != '':
            ls2_punt["relatief"] = {
                "wegnummer": {
                    "nummer": wegnr_van_refpunt
                },
                "afstand": van_afstand,
                "referentiepunt": {
                    "opschrift": van_refpunt,
                    "wegnummer": {
                        "nummer": wegnr_van_refpunt
                    }
                }
            }
        elif i == 1 and tot_refpunt != '' and tot_afstand != '':
            ls2_punt["relatief"] = {
                "wegnummer": {
                    "nummer": wegnr_van_refpunt
                },
                "afstand": tot_afstand,
                "referentiepunt": {
                    "opschrift": tot_refpunt,
                    "wegnummer": {
                        "nummer": wegnr_tot_refpunt
                    }
                }
            }
        ls2_punt["projectie"] = {"type": "Point", "coordinates": punt}
        ls2_punt["geometry"] = dict()
        ls2_punt["geometry"]["type"] = "Point"
        ls2_punt["geometry"]["crs"] = {"properties": {"name": "EPSG:31370"}, "type": "name"}
        ls2_punt["geometry"]["coordinates"] = punt
        ls2_geometry["punten"].append(ls2_punt)

    ls2_geometry["geometry"]["coordinates"] = maak_coordinatenlijst(polyline)
    arcpy.AddMessage(f"ls2_geometry:{(json.dumps(ls2_geometry, indent=4, ensure_ascii=False))}")

    return ls2_geometry


def feature_class_to_ls2_geometries(fc, where_clause, f_wsoidn, f_relatieve_weglocatie: dict = None):
    ls2_geometries = list()
    f_sc = ["SHAPE@", f_wsoidn]
    if f_relatieve_weglocatie is not None:
        f_sc.append(f_relatieve_weglocatie["f_wegnummer"])
        f_sc.append(f_relatieve_weglocatie["f_van_refpunt"])
        f_sc.append(f_relatieve_weglocatie["f_van_afstand"])
        f_sc.append(f_relatieve_weglocatie["f_tot_refpunt"])
        f_sc.append(f_relatieve_weglocatie["f_tot_afstand"])
        f_sc.append(f_relatieve_weglocatie["f_wegnr_van_refpunt"])
        f_sc.append(f_relatieve_weglocatie["f_wegnr_tot_refpunt"])
    with arcpy.da.SearchCursor(
            in_table=fc,
            field_names=f_sc,
            where_clause=where_clause
    ) as sc:
        for row in sc:
            ls2_geometry = featureline_to_ls2geometry(
                polyline=row[0],
                wsoidn=row[1],
                wegnummer=row[2],
                van_refpunt=row[3],
                van_afstand=row[4],
                tot_refpunt=row[5],
                tot_afstand=row[6],
                wegnr_van_refpunt=row[7],
                wegnr_tot_refpunt=row[8],
            )
            ls2_geometries.append(ls2_geometry)

    return ls2_geometries


def maakJsonLineVanLineFc(input_table, crs, f_wegnr=None):
    import arcpy
    arcpy.AddMessage("maakJsonLineVanLineFc")
    # vb: [[{"geometry":{"type":"Point","crs":{"properties":{"name":"EPSG:31370"},"type":"name"},"coordinates":[134229.15,169108.23]},"wegType":"Ongenummerd"},{"geometry":{"type":"Point","crs":{"properties":{"name":"EPSG:31370"},"type":"name"},"coordinates":[134154.92,169239.68]},"wegType":"Ongenummerd"}]]

    # ga door de data
    locaties = []
    f_sc = ["SHAPE@"]
    if f_wegnr != None:
        f_sc = ["SHAPE@", f_wegnr]

    arcpy.AddMessage('lees geometrie uit de tabel en laadt deze in memory')
    with arcpy.da.SearchCursor(input_table, f_sc) as sc:
        i = 0
        for row in sc:
            i += 1
            if round(row[0].length, 3) < 0.001:
                arcpy.AddWarning('i={i},mogelijk probleem met de geometrie')
            # arcpy.AddMessage(f'i={i},row : {row}')
            if i in range(0, 1000, 200) or i % 10000 == 0:
                arcpy.AddMessage(f'{i} geometrieën geladen in memory')
            multiline = row[0]
            # arcpy.AddMessage(f'multiline : {multiline.JSON}')
            locatie_multipoint = []
            for line in multiline:
                # arcpy.AddMessage(f'line : {line}')
                for pnt in line:
                    # arcpy.AddMessage(f'pnt : {pnt}')
                    x = pnt.X
                    y = pnt.Y
                    locatie_point = {
                        "geometry": {"type": "Point", "crs": {"properties": {"name": f"EPSG:{crs}"}, "type": "name"},
                                     "coordinates": [x, y]}}
                    if f_wegnr != None and row[1] != None:
                        wegnr = row[1]
                        locatie_point["wegnummer"] = {"nummer": f"{wegnr}"}
                    if locatie_point not in locatie_multipoint:
                        locatie_multipoint.append(locatie_point)
                    else:
                        arcpy.AddWarning("identieke coördinaat geweigerd")
            locaties.append(locatie_multipoint)
            # arcpy.AddMessage(f'locaties (eerste): {locaties[0]}')

    return locaties


def maakJsonVanFcOrTblCoordinaten(in_table: str, crs, f_wegnr, f_begin_x, f_begin_y, f_eind_x, f_eind_y,
                                  objectids_selectie):
    """ gebruik gegevens uit feature class of table om een json te creëren"""
    # gebruik gegevens uit feature class of table om een json te creëren
    # vb. return
    # [{'wegnummer': {'nummer': 'N2850001'}, 'geometry': {'crs': {'type': 'name', 'properties': {'name': 'EPSG:31370'}}, 'type': 'Point', 'coordinates': [134266.54850000143, 169565.59329999983]}}, {'wegnummer': {'nummer': 'N0080001'}, 'geometry': {'crs': {'type': 'name', 'properties': {'name': 'EPSG:31370'}}, 'type': 'Point', 'coordinates': [134629.81139999628, 169441.55909999833]}}]

    f_oid = [f.name for f in arcpy.ListFields(in_table) if f.type == "OID"][0]
    # invoer Shape aanpassen
    if f_begin_x == 'SHAPE': f_begin_x += '@'
    if f_begin_y == 'SHAPE': f_begin_y += '@'
    if f_eind_x == 'SHAPE': f_eind_x += '@'
    if f_eind_y == 'SHAPE': f_eind_y += '@'

    # ga door de data en bereken de posities voor het gevraagde veld
    locaties = []
    f_sc = [f_wegnr, f_begin_x, f_begin_y]
    if f_eind_x != '':
        f_sc += [f_eind_x, f_eind_y]
    where_clause = f"{f_oid} IN {str(objectids_selectie).replace(',)', ')')}"
    # arcpy.AddMessage(f"where_clause: {where_clause}")
    with arcpy.da.SearchCursor(in_table, f_sc, where_clause) as sc:
        i = 0
        for row in sc:
            i += 1
            if i % 5000 == 0 or i in range(0, 2, 1) or i in range(0, 1000, 100):
                arcpy.AddMessage(f'{i} geometrieën geladen in memory')
            # arcpy.AddMessage(f'row : {row}')
            wegnummer = row[0]
            if f_begin_x == 'SHAPE@':
                x = row[1].firstPoint.X
            else:
                if type(row[1]) == str:
                    x = float(row[1].replace(',', '.'))
                else:
                    x = row[1]
            if f_begin_y == 'SHAPE@':
                y = row[2].firstPoint.Y
            else:
                if type(row[2]) == str:
                    y = float(row[2].replace(',', '.'))
                else:
                    y = row[2]

            locatie = {"wegnummer": {"nummer": wegnummer},
                       "geometry": {"crs": {"type": "name", "properties": {"name": f"EPSG:{crs}"}}, "type": "Point",
                                    "coordinates": [x, y]}}
            locaties.append(locatie)

            if f_eind_x in f_sc:
                type_locatie = 'lijn'
                wegnummer = row[0]
                if f_begin_x == 'SHAPE@':
                    x = row[3].lastPoint.X
                else:
                    if type(row[3]) == str:
                        x = float(row[3].replace(',', '.'))
                    else:
                        x = row[3]
                if f_begin_y == 'SHAPE@':
                    y = row[4].lastPoint.Y
                else:
                    if type(row[4]) == str:
                        y = float(row[4].replace(',', '.'))
                    else:
                        y = row[4]

                locatie = {"wegnummer": {"nummer": wegnummer},
                           "geometry": {"crs": {"type": "name", "properties": {"name": "EPSG:31370"}}, "type": "Point",
                                        "coordinates": [x, y]}}
                locaties.append(locatie)

            else:
                type_locatie = 'punt'

    arcpy.AddMessage(f'{i} geometrieën geladen in memory')
    return locaties, type_locatie


def maakJsonVanFcOrTblCoordinatenZonderWegnr(in_table, crs, f_begin_x, f_begin_y, f_eind_x, f_eind_y,
                                             objectids_selectie, wegtype="alle wegen"):
    # gebruik gegevens uit feature class of table om een json te creëren
    # vb. return
    # [{"wegnummer": {"nummer": "N2850001"}, "geometry": {"crs": {"type": "name", "properties": {"name": "EPSG:31370"}}, "type": "Point", "coordinates": [134266.54850000143, 169565.59329999983]}}, {"wegnummer": {"nummer": "N0080001"}, "geometry": {"crs": {"type": "name", "properties": {"name": "EPSG:31370"}}, "type": "Point", "coordinates": [134629.81139999628, 169441.55909999833]}}]
    f_oid = [f.name for f in arcpy.ListFields(in_table) if f.type == "OID"][0]
    # invoer Shape aanpassen
    if f_begin_x == 'SHAPE': f_begin_x += '@'
    if f_begin_y == 'SHAPE': f_begin_y += '@'
    if f_eind_x == 'SHAPE': f_eind_x += '@'
    if f_eind_y == 'SHAPE': f_eind_y += '@'

    # ga door de data en bereken de posities voor het gevraagde veld
    locaties = []
    f_sc = [f_begin_x, f_begin_y]
    if f_eind_x != '':
        f_sc += [f_eind_x, f_eind_y]
    where_clause = f"{f_oid} IN {str(objectids_selectie).replace(',)', ')')}"
    # arcpy.AddMessage(f"where_clause: {where_clause}")
    with arcpy.da.SearchCursor(in_table, f_sc, where_clause) as sc:
        for row in sc:
            # arcpy.AddMessage(f'row : {row}')
            if f_begin_x == 'SHAPE@':
                x = row[0].firstPoint.X
            else:
                if type(row[0]) == str:
                    x = float(row[0].replace(',', '.'))
                else:
                    x = row[0]
            if f_begin_y == 'SHAPE@':
                y = row[1].firstPoint.Y
            else:
                if type(row[1]) == str:
                    y = float(row[1].replace(',', '.'))
                else:
                    y = row[1]

            locatie = {"geometry": {"crs": {"type": "name", "properties": {"name": f"EPSG:{crs}"}}, "type": "Point",
                                    "coordinates": [x, y]}}
            if wegtype == "Genummerd":
                locatie["wegType"] = "Genummerd"
            locaties.append(locatie)

            if f_eind_x in f_sc:
                type_locatie = 'lijn'
                if f_begin_x == 'SHAPE@':
                    x = row[2].firstPoint.X
                else:
                    if type(row[2]) == str:
                        x = float(row[1].replace(',', '.'))
                    else:
                        x = row[2]
                if f_begin_y == 'SHAPE@':
                    y = row[3].firstPoint.Y
                else:
                    if type(row[3]) == str:
                        y = float(row[3].replace(',', '.'))
                    else:
                        y = row[3]

                locatie = {"geometry": {"crs": {"type": "name", "properties": {"name": "EPSG:31370"}}, "type": "Point",
                                        "coordinates": [x, y]}}
                if wegtype == "Genummerd":
                    locatie["wegType"] = "Genummerd"
                locaties.append(locatie)

            else:
                type_locatie = 'punt'

    return locaties, type_locatie


def maakJsonVanFcOrTblCRelatieveLocatie(input_table, f_wegnr, f_refpunt_opschrift, f_refpunt_afstand):  # WERKT NOG NIET
    # gebruik gegevens uit feature class of table om een json te creëren, enkel puntlocaties mogelijk
    # vb. return
    # locaties = [
    # {"wegnummer": {"nummer": "N0080001"},"geometry": {"crs": {"type": "name","properties": {"name": "EPSG:31370"}},"type": "Point", "coordinates": [136561.67, 169622.14 ] } },
    # {"referentiepunt": { "opschrift": "5.1",   "wegnummer": {"nummer": "N2820001" }  },"afstand":0,"wegType": "Genummerd", "wegnummer": {"nummer": "N2820001"}}
    # ]
    # ga door de data en bereken de posities voor het gevraagde veld
    locaties = []
    f_sc = [f_wegnr, f_refpunt_opschrift, f_refpunt_afstand]
    with arcpy.da.SearchCursor(input_table, f_sc) as sc:
        for row in sc:
            # arcpy.AddMessage(f'row : {row}')
            wegnummer = row[0]
            refpunt_opschrift = row[1].replace(',', '.')
            refpunt_afstand = int(row[2])

            locatie = {"wegnummer": {"nummer": wegnummer},
                       "referentiepunt": {"opschrift": str(refpunt_opschrift), "wegnummer": {"nummer": wegnummer}},
                       "afstand": refpunt_afstand}

            locaties.append(locatie)

    return locaties


def request_ls2_puntlocatie(locatie, session, crs="EPSG:31370", zoekafstand=20, gebruik_kant_van_de_weg='false'):
    """
    deze code is niet klaar, doel is klikken op de kaar in qgis en de relatieve weglocatie opvragen
    vb locatie: {
    "geometry": {
    "type": "Point",
    "coordinates": [126374.95, 178685.89]
    }
    }
    """
    url = f'https://apps.mow.vlaanderen.be/locatieservices2/rest/puntlocatie/?crs={crs}&zoekafstand={zoekafstand}&gebruikKantVanDeWeg={gebruik_kant_van_de_weg}'
    jsonArgs = json.dumps(locatie).encode('utf8')
    session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})
    response = session.post(url, jsonArgs)
    print(response)

    return response.json


def requestLs2Puntlocatie(locaties, omgeving, zoekafstand=2, crs=31370, session=None, gebruik_kant_van_de_weg='false'):
    response_json = None
    url = f'https://apps.mow.vlaanderen.be/locatieservices2/rest/puntlocatie/batch?crs={crs}&zoekafstand={zoekafstand}&gebruikKantVanDeWeg={gebruik_kant_van_de_weg}'

    jsonArgs = json.dumps(locaties).encode('utf8')
    session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})
    response = session.post(url, jsonArgs)

    i = 0
    while i < 4:
        i += 1
        if response.status_code == 401:
            arcpy.AddError("authorisatie mislukt: is cookie nog geldig?")
            sys.exit()
            i = 4
        elif response.status_code == 200:
            arcpy.AddMessage("authorisatie gelukt")
            response_json = response.json()
            i = 4
        else:
            arcpy.AddError(f"probleem bij opvragen: status {response.status_code}")
            arcpy.AddError(f'response:{response[:2]}')
            arcpy.AddError(f'jsonArgs:{jsonArgs[:2]}')

        return response_json


def requestLs2Locatie(locaties, omgeving, zoekafstand, crs, session):
    url = f'https://apps.mow.vlaanderen.be/locatieservices2/rest/lijnlocatie/batch?crs={crs}&zoekafstand={zoekafstand}&enkelViaAwvWegen=true'
    arcpy.AddMessage(f"url: {url}")
    i = 0
    jsonArgs = json.dumps(locaties).encode('utf8')
    session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})

    aantal_pogingen = 5
    while i <= aantal_pogingen:
        response = session.post(url, jsonArgs)

        if response.status_code == 401:
            arcpy.AddWarning("authorisatie mislukt: is cookie nog geldig?")
            i = 10
        elif response.status_code == 200:
            arcpy.AddMessage("authorisatie gelukt")
            response_json = response.json()
            return response_json
        else:
            time.sleep(2)
            arcpy.AddWarning(f"probleem bij opvragen: status {response.status_code}, poging {i + 1}")
            if i == aantal_pogingen:
                arcpy.AddError(f'response (2000):{str(response)[:2000]}')
                arcpy.AddError(f'locaties (2000):{str(locaties)[:2000]}')
            i += 1

    # arcpy.AddWarning(f'jsonArgs:{jsonArgs}')
    # arcpy.AddMessage(f'response_json (eerste 200 karakters):{str(response_json)[:200]}')



def schrijfGegevens(in_table, response, type_locatie='punt', objectids_selectie=None):
    f_oid = [f.name for f in arcpy.ListFields(in_table) if f.type == "OID"][0]
    if type_locatie == 'punt':
        f_uc = ['refpunt_wegnr', 'refpunt_opschrift', 'refpunt_afstand', 'proj_x', 'proj_y', 'wsoidn', 'wsoidn_m']
    elif type_locatie == 'lijn':
        f_uc = ['begin_refpunt_wegnr', 'begin_refpunt_opschrift', 'begin_refpunt_afstand', 'begin_proj_x',
                'begin_proj_y', 'begin_wsoidn', 'begin_wsoidn_m',
                'eind_refpunt_wegnr', 'eind_refpunt_opschrift', 'eind_refpunt_afstand', 'eind_proj_x', 'eind_proj_y',
                'eind_wsoidn', 'eind_wsoidn_m']

    for i in range(len(f_uc)):
        f_name = f_uc[i]
        if arcpy.Describe(in_table).dataElementType == 'DEShapeFile' and len(f_name) > 10:
            add_f_name = f_type[f_name][2]
            f_uc[i] = add_f_name
            arcpy.AddMessage(f"shapefile: {add_f_name}")
        else:
            add_f_name = f_name

        if add_f_name not in [f.name for f in arcpy.ListFields(in_table)]:
            # arcpy.AddMessage(f"listfield: {[f.name for f in arcpy.ListFields(in_table)]}")
            field_alias = f_name
            field_type = f_type[f_name][0]
            field_length = f_type[f_name][1]
            arcpy.AddMessage(f"voeg veld '{f_name}' toe")
            arcpy.AddField_management(
                in_table=in_table,
                field_name=add_f_name,
                field_type=field_type,
                field_length=field_length,
                field_alias=field_alias,
                field_is_nullable="NULLABLE"
            )

    i = 0
    # arcpy.AddMessage(f'f_uc: {f_uc}, lengte: {len(f_uc)}')
    where_clause = f"{f_oid} IN {str(objectids_selectie).replace(',)', ')')}"
    with arcpy.da.UpdateCursor(in_table, f_uc, where_clause) as uc:
        for row in uc:
            try:
                response_row = response[i]
                if 'success' in response_row.keys():
                    response_row = response[i]['success']
                    try:
                        refpunt_wegnr = response_row['relatief']['referentiepunt']['wegnummer']['nummer']
                        refpunt_opschrift = float((response_row['relatief']['referentiepunt']['opschrift']))
                        refpunt_afstand = response_row['relatief']['afstand']
                    except:
                        if arcpy.Describe(in_table).dataElementType == 'DEShapeFile':
                            refpunt_wegnr = "-"
                            refpunt_opschrift = "-9"
                            refpunt_afstand = "0"
                        else:
                            refpunt_wegnr = None
                            refpunt_opschrift = None
                            refpunt_afstand = None
                    proj_x = response_row['projectie']['coordinates'][0]
                    proj_y = response_row['projectie']['coordinates'][1]
                    wsoidn = response_row['wegsegmentId']['oidn']
                    wsoidn_m = response_row['projectie']['coordinates'][3]

                else:
                    arcpy.AddWarning(f'alle waarden worden op None gezet voor response_row:{response_row}')
                    refpunt_wegnr = None
                    refpunt_opschrift = None
                    refpunt_afstand = None
                    proj_x = None
                    proj_y = None
                    wsoidn = None
                    wsoidn_m = None

                row = [refpunt_wegnr, refpunt_opschrift, refpunt_afstand, proj_x, proj_y, wsoidn, wsoidn_m]
                i += 1

                if type_locatie == 'lijn':
                    # arcpy.AddMessage('type_locatie : lijn')
                    response_row_eind = response[i]
                    if 'success' in response_row_eind.keys():
                        response_row_eind = response_row_eind['success']
                        try:
                            refpunt_wegnr_eind = response_row_eind['relatief']['referentiepunt']['wegnummer']['nummer']
                            refpunt_opschrift_eind = float(
                                (response_row_eind['relatief']['referentiepunt']['opschrift']))
                            refpunt_afstand_eind = response_row_eind['relatief']['afstand']
                        except:
                            refpunt_wegnr_eind = None
                            refpunt_opschrift_eind = None
                            refpunt_afstand_eind = None
                        proj_x_eind = response_row_eind['projectie']['coordinates'][0]
                        proj_y_eind = response_row_eind['projectie']['coordinates'][1]
                        wsoidn_eind = response_row_eind['wegsegmentId']['oidn']
                        wsoidn_m_eind = response_row_eind['projectie']['coordinates'][3]
                    else:
                        arcpy.AddWarning(
                            f'alle waarden worden op None gezet voor response_row_eind:{response_row_eind}')
                        refpunt_wegnr_eind = None
                        refpunt_opschrift_eind = None
                        refpunt_afstand_eind = None
                        proj_x_eind = None
                        proj_y_eind = None
                        wsoidn_eind = None
                        wsoidn_m_eind = None

                    row += [refpunt_wegnr_eind, refpunt_opschrift_eind, refpunt_afstand_eind, proj_x_eind, proj_y_eind,
                            wsoidn_eind, wsoidn_m_eind]
                    i += 1
                uc.updateRow(row)
            except:
                arcpy.AddError(f'row kan niet weggeschreven worden: {row}')
                arcpy.AddError(f'type locatie: {type_locatie}')
                arcpy.AddError(f'response_row:{response_row}')
                arcpy.AddError(f'response_row_eind:{response_row_eind}')
                response_row


def schrijfLijnEventTable(input_table, output_event_table, response):
    # maak route event table
    arcpy.AddMessage(f'maak route event table {output_event_table} aan')
    arcpy.CreateTable_management(os.path.dirname(output_event_table), os.path.basename(output_event_table), input_table)
    # vul tabel aan met ls2-gegevens
    f_event = ['Wsoidn', 'VanM', 'TotM']
    for f in f_event:
        field_type = f_type[f][0]
        field_length = f_type[f][1]
        arcpy.management.AddField(output_event_table, f, field_type, field_length)
    # arcpy.AddMessage(f'f_ic: {f_ic}, lengte: {len(f_ic)}')

    f_input_table = [f.name for f in arcpy.ListFields(input_table) if f.type not in ('Geometry',)]
    ic = arcpy.da.InsertCursor(output_event_table, f_event + f_input_table)

    with arcpy.da.SearchCursor(input_table, f_input_table) as sc:
        i = 0
        for row in sc:
            # arcpy.AddMessage(f'row:{row}')
            response_row = response[i]
            if 'success' in response_row.keys():
                # arcpy.AddMessage(f"response[i]:{response[i]['success']['geometry']}")
                response_row = response[i]['success']
                geometry = response_row['geometry']
                geometry = verwijder_0mlineparts(geometry)['coordinates']

                wsoidn_list = []
                punten = response_row['punten']
                punten = verwijder_identieke_punten(punten)
                for punt in punten:
                    wsoidn_list.append(punt['wegsegmentId']['oidn'])
                wsoidn_list = wsoidn_list[:-1]
                # arcpy.AddMessage(f'wsoidn_list: {wsoidn_list}')

                wsoidn_m_list = []
                for line in geometry:
                    m1 = line[0][-1]
                    m2 = line[-1][-1]
                    wsoidn_m_list.append([m1, m2])
                # arcpy.AddMessage(f'wsoidn_m_list:{wsoidn_m_list}')

            for wsoidn, m_list in zip(wsoidn_list, wsoidn_m_list):
                row_insert = [wsoidn] + m_list + list(row)
                # arcpy.AddMessage(f'row_insert: {row_insert}')
                ic.insertRow(row_insert)

            i += 1


def verwijder_0mlineparts(geometry):
    # vb:{'type': 'MultiLineString', 'coordinates': [[[142023.094, 167453.313, 0, 39.546], [142023.094, 167453.313, 0, 39.546]], [[142023.094, 167453.313, 0, 0], [142017.83, 167452.618, 0, 5.31], [142016.938, 167452.5, 0, 6.209], [142006.985, 167450.938, 0, 16.284], [142002.578, 167450.157, 0, 20.76], [142001.016, 167449.86, 0, 22.35], [141991.016, 167447.828, 0, 32.554], [141988.094, 167447.188, 0, 35.546], [141986.297, 167446.813, 0, 37.381], [141981.563, 167445.782, 0, 42.226], [141977.063, 167444.782, 0, 46.836], [141972.157, 167443.578, 0, 51.888], [141969.844, 167442.969, 0, 54.279], [141967.532, 167442.328, 0, 56.679], [141962.907, 167441.047, 0, 61.478], [141953.813, 167438.875, 0, 70.828], [141949.25, 167437.844, 0, 75.506], [141944.688, 167436.844, 0, 80.176], [141941.735, 167436.235, 0, 83.191], [141938.766, 167435.688, 0, 86.21], [141934.063, 167434.907, 0, 90.977], [141928.704, 167434.141, 0, 96.391], [141923.344, 167433.422, 0, 101.799], [141919.391, 167432.953, 0, 105.78], [141913.157, 167432.344, 0, 112.043], [141902.953, 167431.578, 0, 122.276], [141900.016, 167431.407, 0, 125.218], [141886.594, 167430.61, 0, 138.664], [141882.329, 167430.453, 0, 142.932], [141870.219, 167430.422, 0, 155.042], [141859.375, 167430.782, 0, 165.892], [141852.75, 167430.985, 0, 172.52], [141844.016, 167431.344, 0, 181.261], [141836.141, 167431.672, 0, 189.143], [141835.282, 167431.703, 0, 190.002], [141822.203, 167432.282, 0, 203.094], [141815.672, 167432.594, 0, 209.633], [141809.125, 167432.875, 0, 216.186], [141801.5, 167433.063, 0, 223.813], [141794.157, 167433.25, 0, 231.158], [141779.188, 167433.141, 0, 246.128], [141774.985, 167433, 0, 250.333], [141770.766, 167432.782, 0, 254.558], [141766.563, 167432.5, 0, 258.77], [141760.141, 167431.907, 0, 265.22], [141751.485, 167430.922, 0, 273.931], [141741.188, 167429.563, 0, 284.318], [141730.266, 167428, 0, 295.351], [141620.61, 167412.532, 0, 406.093]]], 'bbox': [141620.61, 167412.532, 142023.094, 167453.313], 'crs': {'properties': {'name': 'EPSG:31370'}, 'type': 'name'}}
    # arcpy.AddMessage(f"geometry:{geometry}")
    # arcpy.AddMessage(f"geometry['coordinates']:{geometry['coordinates']}")
    new_coordinates = []
    for part in geometry['coordinates']:
        if len(part) > 2:
            new_coordinates.append(part)
        elif len(part) == 2:
            # arcpy.AddMessage(f'len part:{len(part)}')
            if part[0][0:1] == part[1][0:1]:
                arcpy.AddMessage(f'eerste en tweede coordinaat zijn gelijk')
            else:
                new_coordinates.append(part)
        else:
            arcpy.AddError('fout')
    geometry['coordinates'] = new_coordinates
    # arcpy.AddMessage(f"geometry['coordinates'] verbeterd:{geometry['coordinates']}")
    # arcpy.AddMessage(f'geometry:{geometry}')
    return geometry


def verwijder_identieke_punten(punten):
    # arcpy.AddMessage(f'verwijder_identieke_punten 1:{punten}')
    if len(punten) > 2:
        if punten[0]['geometry']['coordinates'][0:1] == punten[1]['geometry']['coordinates'][0:1]:
            arcpy.AddMessage(f'2 eerste punten hebben identieke xy-coordinaten')
            punten = punten[1:]

        if punten[-1]['geometry']['coordinates'][0:1] == punten[-2]['geometry']['coordinates'][0:1]:
            arcpy.AddMessage(f'2 laatste punten hebben identieke xy-coordinaten')
            punten = punten[:-1]

    # arcpy.AddMessage(f'verwijder_identieke_punten 2:{punten}')
    return punten


def ls2_line_geometries_to_fl(ls2_geometries, line_fl, where_clause):
    """
    vervangt geometrie van bestaande features, de volgorde en aantal features moeten gelijk lopen met de volgorde van ls2_geometries
    """
    arcpy.AddMessage("ls2_line_geometries_to_fl")
    with arcpy.da.UpdateCursor(
            in_table=line_fl,
            field_names=["SHAPE@"],
            where_clause=where_clause
    ) as uc:
        for row, ls2_geometry in zip(uc, ls2_geometries):
            arcpy.AddMessage(f"row:{row}")
            arcpy.AddMessage(f"ls2_geometry:{ls2_geometry}")
            if 'success' in ls2_geometry.keys():
                geometry = json_ls2_to_geom(ls2_geometry["success"])
                row[0] = geometry
                uc.updateRow(row)
            else:
                arcpy.AddError(f"geen nieuwe geometrie voor oid {row[0]}")
                arcpy.AddError(f"{ls2_geometry}")


def schrijfLijnGeometry(input_table, output_line_fc, response):
    # schrijf attributen naar output fc
    spatial_reference = arcpy.Describe(input_table).spatialReference
    f_input_table = [f.name for f in arcpy.ListFields(input_table)]
    f_ls2 = ['wegnummer', 'begin_refpunt_wegnr', 'begin_refpunt_opschrift', 'begin_refpunt_afstand',
             'eind_refpunt_wegnr',
             'eind_refpunt_opschrift', 'eind_refpunt_afstand']

    arcpy.management.CreateFeatureclass(os.path.dirname(output_line_fc), os.path.basename(output_line_fc), "POLYLINE",
                                        input_table, has_m='ENABLED', has_z='ENABLED',
                                        spatial_reference=spatial_reference)
    f_output_line_fc = [f.name for f in arcpy.ListFields(output_line_fc)]
    for f in f_ls2:
        if f not in f_output_line_fc:
            arcpy.AddMessage(f'addfield:{f}')
            arcpy.management.AddField(
                in_table=output_line_fc,
                field_name=f,
                field_type=f_type[f][0],
                field_length=f_type[f][1],
                field_is_nullable="NULLABLE"
            )

    ic = arcpy.da.InsertCursor(output_line_fc, f_input_table)
    with arcpy.da.SearchCursor(input_table, f_input_table) as sc:
        i = 0
        for row in sc:
            i += 1
            if i in range(0, 10000000, 1000):
                arcpy.AddMessage(f'{i} features geschreven in nieuwe fc')
            ic.insertRow(row)
    del ic

    i = 0
    with arcpy.da.UpdateCursor(output_line_fc, ['SHAPE@WKT'] + f_ls2) as uc:
        for row in uc:
            if i in range(0, 10000000, 1000):
                arcpy.AddMessage(f'{i + 1} locaties geschreven in nieuwe fc')
            response_row = response[i]
            if 'success' in response_row.keys():
                response_row = response[i]['success']
                # arcpy.AddMessage(response_row['geometry'])
                # verwijder lineparts die bestaan uit identieke punten
                geometry = verwijder_0mlineparts(response_row['geometry'])
                punten = verwijder_identieke_punten(response_row['punten'])
                polyline_wkt = wkt.dumps(geometry).strip('SRID=:31370;').replace('MULTILINESTRING',
                                                                                 'MULTILINESTRING ZM')
                # polyline_wkt = wkt.dumps(response_row['geometry']).strip('SRID=:31370;').replace('MULTILINESTRING',
                #                                                                                  'MULTILINESTRING ZM')
                # arcpy.AddMessage(f'polyline_wkt:{polyline_wkt}')
                # lees eerste punt om relatieve locatie af te leiden
                max_wegnr = bereken_meest_voorkomende_wegnr(response_row)
                # if 'relatief' in response_row['punten'][0]:
                if 'relatief' in punten[0]:
                    # arcpy.AddMessage(f"punten[0]keys:{punten[0].keys()}")
                    punten[0]['relatief']
                    begin_refpunt_wegnr = punten[0]['relatief']['wegnummer']['nummer']
                    begin_refpunt_opschrift = float(
                        punten[0]['relatief']['referentiepunt']['opschrift'])
                    begin_refpunt_afstand = punten[0]['relatief']['afstand']
                else:
                    begin_refpunt_wegnr, begin_refpunt_opschrift, begin_refpunt_afstand = None, None, None

                # arcpy.AddMessage(f"punten*****: {punten}")
                if 'relatief' in punten[-1]:
                    eind_refpunt_wegnr = punten[-1]['relatief']['wegnummer']['nummer']
                    eind_refpunt_opschrift = float(
                        punten[-1]['relatief']['referentiepunt']['opschrift'])
                    eind_refpunt_afstand = punten[-1]['relatief']['afstand']
                else:
                    eind_refpunt_wegnr, eind_refpunt_opschrift, eind_refpunt_afstand = None, None, None

                row = [polyline_wkt, max_wegnr, begin_refpunt_wegnr, begin_refpunt_opschrift, begin_refpunt_afstand,
                       eind_refpunt_wegnr, eind_refpunt_opschrift, eind_refpunt_afstand]
                # arcpy.AddMessage(f'row:{row}')
                uc.updateRow(row)
            else:
                arcpy.AddWarning(f"fout voor lijn {i}{response[i]}")
            i += 1


def bereken_meest_voorkomende_wegnr(response_row):
    wegnrs = {}
    for punt in response_row['punten']:
        if 'relatief' in punt:
            wegnr = punt['relatief']['wegnummer']['nummer']
            # arcpy.AddMessage(f'wegnr: {wegnr}')
            if wegnr not in wegnrs:
                wegnrs[wegnr] = 1
            else:
                wegnrs[wegnr] += 1
    if wegnrs != {}:
        max_wegnr = max(wegnrs, key=wegnrs.get)
    else:
        max_wegnr = '-'
    # arcpy.AddMessage(f'maxwegnr: {wegnrs}/{max_wegnr}')
    return max_wegnr


def requestLs2WegMeasure(geometry, wegnummer, omgeving, crs, session):
    # vb.https://apps.mow.vlaanderen.be/locatieservices2/rest/weg/N2820001/measure?crs=31370&x=134589.88&y=166209.18
    x = geometry.firstPoint.X
    y = geometry.firstPoint.Y
    if omgeving == 'productie':
        url = f'https://apps.mow.vlaanderen.be/locatieservices2/rest/weg/{wegnummer}/measure?crs={crs}&x={x}&y={y}'
        # arcpy.AddMessage(f"url:{url}")
    i = 0
    while i < 4:
        response = session.get(url)
        if response.status_code == 401:
            arcpy.AddWarning("authorisatie mislukt: is cookie nog geldig?")
            i = 10
        elif response.status_code == 200:
            # arcpy.AddMessage("authorisatie gelukt")
            i = 10
        else:
            time.sleep(2)
            i += 1
            arcpy.AddError(f"probleem bij opvragen: status {response.status_code}, poging {i}")

    m = response.text
    return m


def request_ls2_wegnummers(session, omgeving="productie"):
    arcpy.AddMessage(f"vraag wegnummers op, omgeving: {omgeving}")
    url = f"https://{url_omgeving[omgeving]}/locatieservices2/rest/weg"
    session.headers.update({'accept': 'application/json'})
    response = session.get(url)

    if response.status_code == 200:
        pass
    elif response.status_code == 401:
        arcpy.AddError("authorisatie mislukt: is cookie nog geldig?")
    else:
        arcpy.AddError(f"probleem bij opvragen: status {response.status_code}, response: {response}")

    return response.json()


def request_weg_gekalibreerd_batch(wegnummers, session):
    url = 'https://apps.mow.vlaanderen.be/locatieservices2/rest/weg/gekalibreerd/batch'
    jsonArgs = json.dumps(wegnummers).encode('utf8')
    session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})
    response = session.post(url, jsonArgs)

    aantal_pogingen = 2
    i = 0
    if response.status_code == 401:
        arcpy.AddWarning("authorisatie mislukt: is cookie nog geldig?")
        i = 10
    elif response.status_code == 200:
        arcpy.AddMessage("authorisatie gelukt")
        response_json = response.json()
        return response_json
    else:
        time.sleep(2)
        arcpy.AddWarning(f"probleem bij opvragen: status {response.status_code}, poging {i + 1}")
        if i == aantal_pogingen:
            arcpy.AddError(f'response (2000):{str(wegnummers)[:2000]}')
            arcpy.AddError(f'locaties (2000):{str(wegnummers)[:2000]}')
        i += 1


def request_ls2__attgenumweg(wsoidn_bulk, session):
    url = 'https://apps.mow.vlaanderen.be/locatieservices2/rest/attgenumweg'
    jsonArgs = json.dumps(wsoidn_bulk).encode('utf8')
    session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})
    response = session.post(url, jsonArgs)

    aantal_pogingen = 2
    i = 0
    if response.status_code == 401:
        arcpy.AddWarning("authorisatie mislukt: is cookie nog geldig?")
        i = 10
    elif response.status_code == 200:
        # arcpy.AddMessage("authorisatie gelukt")
        response_json = response.json()
        return response_json
    else:
        time.sleep(2)
        arcpy.AddWarning(f"probleem bij opvragen: status {response.status_code}, poging {i + 1}")
        if i >= aantal_pogingen:
            arcpy.AddError(f'response (2000):{str(wegnummers)[:2000]}')
            arcpy.AddError(f'locaties (2000):{str(wegnummers)[:2000]}')
        i += 1


def request_ls2_weg__wegnummer__lijnlocaties(wegnummer, session):
    url = f'https://apps.mow.vlaanderen.be/locatieservices2/rest/weg/{wegnummer}/lijnlocaties'
    response = session.get(url)

    aantal_pogingen = 2
    i = 0
    if response.status_code == 401:
        arcpy.AddWarning("authorisatie mislukt: is cookie nog geldig?")
        i = 10
    elif response.status_code == 200:
        # arcpy.AddMessage("authorisatie gelukt")
        response_json = response.json()
        return response_json
    else:
        time.sleep(2)
        arcpy.AddWarning(f"probleem bij opvragen: status {response.status_code}, poging {i + 1}")
        arcpy.AddWarning(f"probleem bij opvragen: status {response.text}")
        arcpy.AddWarning(f"url: {url}")
        print(f"probleem bij opvragen: status {response.status_code}, poging {i + 1}")
        print(f"probleem bij opvragen: status {response.text}")
        print(f"url: {url}")
        if i == aantal_pogingen:
            arcpy.AddError(f"response: {response}")
        i += 1


def request_lijnlocatie_herbereken(ls2_geometries, session):
    """ input moet lijst zijn"""
    url = 'https://apps.mow.vlaanderen.be/locatieservices2/rest/lijnlocatie/herbereken'
    jsonArgs = json.dumps(ls2_geometries, ensure_ascii=False).encode('utf8')
    session.headers.update({'Content-Type': 'application/json', 'accept': 'application/json'})
    response = session.post(url, jsonArgs)

    aantal_pogingen = 2
    i = 0
    if response.status_code == 401:
        arcpy.AddWarning("authorisatie mislukt: is cookie nog geldig?")
        i = 10
    elif response.status_code == 200:
        arcpy.AddMessage("authorisatie gelukt")
        response_json = response.json()
        return response_json
    else:
        time.sleep(2)
        arcpy.AddWarning(f"probleem bij opvragen: status {response.status_code}, poging {i + 1}")
        if i == aantal_pogingen:
            arcpy.AddError(f'response (2000):{str(wegnummers)[:2000]}')
            arcpy.AddError(f'locaties (2000):{str(wegnummers)[:2000]}')
        i += 1

    return response


def json_ls2_to_geom(geometry_dict):
    multi_line_coords = geometry_dict["geometry"]["coordinates"]
    multipart_array = arcpy.Array()

    # Loop door elke sub-lijn (deel van de MultiLineString)
    for line_coords in multi_line_coords:
        part_array = arcpy.Array()  # Array voor één deel
        for x, y, z, m in line_coords:  # Coördinaten ophalen
            part_array.add(arcpy.Point(x, y, z, m))  # Voeg punt toe
        multipart_array.add(part_array)  # Voeg het deel toe aan de hoofd-array

    # Maak een Polyline met meerdere delen
    multipart_polyline = arcpy.Polyline(multipart_array, has_z=True, has_m=True)

    return multipart_polyline


def bereken_unieke_measures(polyline):
    if polyline.partCount <= 1:
        return polyline

    new_parts = []  # Hier slaan we de gewijzigde delen op
    prev_end_m = 0  # Startwaarde voor eerste part

    for i, part in enumerate(polyline):
        new_part = []
        for j, point in enumerate(part):
            if point:
                new_m = point.M
                if i > 0:  # Eerste punt van nieuw part aanpassen
                    new_m = prev_end_m + 1 + point.M
                new_part.append(arcpy.Point(point.X, point.Y, point.Z, new_m))

        prev_end_m = new_part[-1].M  # Update eindmeasure van vorige part
        new_parts.append(new_part)  # Opslaan in lijst

    # Maak een nieuwe polyline met de aangepaste M-waarden
    new_polyline = arcpy.Polyline(arcpy.Array([arcpy.Array(p) for p in new_parts]), has_z=True, has_m=True, )

    return new_polyline


def schrijf_weg_gekalibreerd_batch(output_line_fc, response, unieke_measures=False):
    # schrijf attributen naar output fc
    spatial_reference = 31370
    f_geometry = "SHAPE@"
    f_wegnummer = "wegnummer"

    arcpy.management.CreateFeatureclass(
        out_path=os.path.dirname(output_line_fc),
        out_name=os.path.basename(output_line_fc),
        geometry_type="POLYLINE",
        has_m='ENABLED',
        has_z='ENABLED',
        spatial_reference=spatial_reference)
    arcpy.management.AddField(
        in_table=output_line_fc,
        field_name=f_wegnummer,
        field_type="TEXT",
        field_length=10
    )

    with arcpy.da.InsertCursor(output_line_fc, [f_geometry, f_wegnummer]) as ic:
        for i, row in enumerate(response):
            row = row["success"]
            print(row.keys())
            geometry = json_ls2_to_geom(row)
            if unieke_measures:
                geometry = bereken_unieke_measures(geometry)
            wegnummer = row["wegnummer"]["nummer"]
            arcpy.AddMessage(wegnummer)
            ic.insertRow([geometry, wegnummer])
            if i + 1 % 1000 == 0:
                arcpy.AddMessage(f'{i} locaties geschreven in nieuwe fc')


def attgenumweg(session, output_table):
    # vraag wegnummers op
    wegnummers = request_ls2_wegnummers(session, omgeving="productie")
    arcpy.AddMessage(f"{len(wegnummers)}wegnummers (eerste 10): {(wegnummers[:10])}......")

    arcpy.AddMessage(f"maak table '{output_table}' aan")
    arcpy.CreateTable_management(
        out_path=os.path.dirname(output_table),
        out_name=os.path.basename(output_table)
    )
    f_ic = {
        "wegnummer": {"type": "TEXT", "length": 10},
        "ws_oidn": {"type": "LONG", "length": None},
        "gw_oidn": {"type": "LONG", "length": None},
        "richting": {"type": "SHORT", "length": None},
        "volgnummer": {"type": "SHORT", "length": None}
    }
    for f, properties in f_ic.items():
        arcpy.AddField_management(
            in_table=output_table,
            field_name=f,
            field_type=properties["type"],
            field_length=properties["length"])

    with arcpy.da.InsertCursor(output_table, tuple(f_ic.keys())) as ic:
        # vraag ws_oidn op waar er één of meerdere wegnummers aan verbonden zijn
        wsoidn_lijnlocaties = []
        for wegnummer in wegnummers:
            lijnlocaties = request_ls2_weg__wegnummer__lijnlocaties(wegnummer, session)
            for lijnlocatie in lijnlocaties:
                for punt in lijnlocatie["punten"]:
                    wsoidn = punt["wegsegmentId"]["oidn"]
                    wsoidn_lijnlocaties.append(wsoidn)

        wsoidn_lijnlocaties = tuple(set(wsoidn_lijnlocaties))

        aantal_wsoidn = len(wsoidn_lijnlocaties)
        arcpy.AddMessage(f"{aantal_wsoidn}wsoidn'en (eerste 10): {wsoidn_lijnlocaties[:10]}......")

        start = 0
        limit = 10000
        # Itereer door de data in blokken
        while start < aantal_wsoidn:
            tot = min(start + limit, aantal_wsoidn)
            arcpy.AddMessage(f'maak lijst met wsoidn van {start} tot {tot}, totaal: {aantal_wsoidn}')
            wsoidn_bulk = wsoidn_lijnlocaties[start:tot]
            attgenumwegs = request_ls2__attgenumweg(wsoidn_bulk, session)
            for attgenumweg in attgenumwegs:
                wegnummer = attgenumweg["wegnummer"]
                wsoidn = attgenumweg["wegsegmentId"]
                gw_oidn = attgenumweg["gw_oidn"]
                richting = attgenumweg["richting"]
                volgnummer = attgenumweg["volgnummer"]

                row = [wegnummer, wsoidn, gw_oidn, richting, volgnummer]
                ic.insertRow(row)

            start += limit

    return output_table


from math import sqrt


def punten_afstand(x1, y1, x2, y2, max_afstand=10):
    d = sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return d < max_afstand, d


def controleer_referentiepunten_wegnummers(session, wegnummers, omgeving="productie"):
    arcpy.AddMessage(f"controleer referentiepunten voor wegnummers, omgeving: {omgeving}")
    fouten_count = 0
    referentiepunten_fouten = []
    for wegnummer in (wegnummers):
        referentiepunten = get_rest_weg_wegnummer_globalemeasures_refpunten(session, wegnummer, omgeving="productie")
        tmp_opschrift = -1
        tmp_x = 0
        tmp_y = 0
        for referentiepunt in referentiepunten:
            for (m, opschrift, x, y) in referentiepunt:
                fout = False
                if tmp_opschrift >= float(opschrift):
                    fout = True
                    arcpy.AddWarning(
                        f"wegnummer: {wegnummer}\nopschrift {opschrift} niet groter dan vorig opschrift {tmp_opschrift} voor wegnummer {wegnummer}\nXY:{x} {y}, M:{m}")
                elif punten_afstand(tmp_x, tmp_y, x, y, max_afstand=5)[0]:
                    fout = True
                    arcpy.AddMessage(f"wegnummer: {wegnummer}\nreferentiepunten te dicht bij elkaar: vorige XY:{tmp_x} {tmp_y}, huidige XY:{x} {y}, afstand:{punten_afstand(tmp_x,tmp_y,x,y)[1]:.2f}m\nopschrift vorig:{tmp_opschrift}, huidig:{opschrift}")
                if fout:
                    fouten_count += 1
                    referentiepunten_fouten.append((wegnummer, m, opschrift, x, y))
                tmp_opschrift = float(opschrift)
                tmp_x = x
                tmp_y = y
    arcpy.AddMessage(f"totaal aantal fouten: {fouten_count}")


def get_rest_weg_wegnummer_globalemeasures_refpunten(session, wegnummer, omgeving="productie"):
    """
    response is een lijst van lijsten met waarde m,opschrift,x,y
    """
    # arcpy.AddMessage(f"Vraag de refpunten gesorteerd op hun globale measure. Gegroepeerd per geconnecteerd wegdeel, omgeving: {omgeving}")
    url = f"https://{url_omgeving[omgeving]}/locatieservices2/rest/weg/{wegnummer}/globalemeasures"
    session.headers.update({'accept': 'application/json'})
    response = session.get(url)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        arcpy.AddError("authorisatie mislukt: is cookie nog geldig?")
    else:
        arcpy.AddError(f"probleem bij opvragen: status {response.status_code}, response: {response}")
