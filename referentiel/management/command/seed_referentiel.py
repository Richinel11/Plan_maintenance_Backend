# referentiel/management/commands/seed_referentiel.py

from django.core.management.base import BaseCommand
from referentiel.models import Troncon, Poste, Ouvrage, Depart, Centrale, ReferenceReseau
from user.models import EntiteMetier
from planning.models import TypeActivite


class Command(BaseCommand):
    help = 'Seed referentiel data'

    def handle(self, *args, **kwargs):

        #   TRONCONS 
        troncons_data = [
            "DISTRIBUTION-MAINTENANCE POSTES", "DISTRIBUTION-DRY", "DISTRIBUTION-DRD",
            "DISTRIBUTION-DRNEA", "DISTRIBUTION-DRSM", "DISTRIBUTION-DRONO",
            "DISTRIBUTION-DRE", "DISTRIBUTION-DRSOM", "DISTRIBUTION-DRSANO",
            "DISTRIBUTION-DRC", "TRANSPORT-CSE", "TRANSPORT-LSO", "TRANSPORT-NEA",
            "TRANSPORT-ONO", "TRANSPORT", "PRODUCTION - EDEA", "PRODUCTION - LAGDO",
            "PRODUCTION - SLL", "PRODUCTION - NHPC", "PRODUCTION - KPDC", "PRODUCTION - DPDC",
        ]
        for nom in troncons_data:
            Troncon.objects.get_or_create(nom=nom, defaults={"actif": True})
        self.stdout.write(" Troncons créés")

        #   POSTES 
        postes_data = [
            "BRGM", "NGOUSSO", "KONDENGUI", "AHALA", "NSIMALEN", "NOMAYOS",
            "OYOMABANG", "NYOM II", "KOUMASSI", "BEKOKO", "BONABERI", "DEIDO",
            "MAKEPE", "NGODI BAKOKO", "LOGBABA", "BASSA", "MAROUA", "DJAMBOUTOU",
            "GUIDER", "LAGDO", "NGAOUNDERE", "DJOB", "EKOMBITIE", "NDJOCK NKONG",
            "NJOMBE", "NKONGSAMBA", "MILE 2 LIMBE", "BAFOUSSAM", "BAMENDA",
            "BERTOUA", "MPOLONGWE", "MANGOMBE", "DIBAMBA", "NYOM",
        ]
        for nom in postes_data:
            Poste.objects.get_or_create(nom=nom, defaults={"actif": True})
        self.stdout.write(" Postes créés")

        #   OUVRAGES 
        ouvrages_data = [
            {"nom": "POSTE SOURCE_HTA", "type": "Poste"},
            {"nom": "POSTE SOURCE_HTB", "type": "Poste"},
            {"nom": "LIGNE_HTB", "type": "Ligne"},
            {"nom": "POSTE DE MANGOMBE", "type": "Poste"},
            {"nom": "DCP", "type": "Centrale"},
            {"nom": "IPP", "type": "Centrale"},
        ]
        for o in ouvrages_data:
            Ouvrage.objects.get_or_create(nom=o['nom'], defaults={"type": o['type']})
        self.stdout.write(" Ouvrages créés")

        #   DEPARTS 
        departs_data = [
            # BRGM
            "BRG.PMR A12 ETOUG-EBE", "BRG.PMR D13 CITE VERTE", "BRG.PMR D14 SNEC MESSA",
            "BRG.PMR D15 CUSS", "BRG.PMR D16 HOPITAL CENTRAL", "BRG.PMR D115 BRGM",
            "BRG.PMR D112 ASSEMBLEE NATIONALE", "BRG.PMR D113 ELOUMDEN",
            "BRG.D11 P4", "BRG.D12 MESSA", "BRG.D17 PALAIS DES CONGRES",
            "BRG.D18 P61", "BRG.D19 PREFECTURE", "BRG.D117 BRGM",
            "BRG.D110 BIYEMASSI", "BRG.D111 MELEN", "BRG.D31 BRGM",
            # AHALA
            "AHA.D11 OBAM ONGOLA", "AHA.D12 BRASSERIES", "AHA.D13 NSIMEYONG",
            "AHA.D14 MENDONG", "AHA.D15 EP AUTOROUTE", "AHA.D16 ODZA",
            "AHA.D17 DAMASE", "AHA.D18 JOUVENCE", "AHA.D31 MESSAMENDONGO", "AHA.D32 MAKAK",
            # NGOUSSO
            "NGOU.D11 P265", "NGOU.D12 PRESIDENCE", "NGOU.D13 ESSOS",
            "NGOU.D14 P135", "NGOU.D15 SAFCA / D115 STADE OLEMBE",
            "NGOU.D110 P2 SNI", "NGOU.D116 NGOULMEKONG",
            "NGOU.D16 HOTEL DU PLATEAU", "NGOU.D17 HOPITAL GENERAL",
            "NGOU.D18 SOA", "NGOU.D19 MANSEL HOTEL / D114 EMANA",
            "NGOU.D111 BEAC", "NGOU.D112 SNEC NGOUSSO / D113 MVOG EBANDA",
            "NGOU.D117 NGOULMEKONG", "NGOU.D118 HOPITAUX",
            "NGO.D31 MONATELE", "NGO.D32 OBALA", "NGO.D34 AKONOLINGA",
            # KONDENGUI
            "KON.D11 KONDENGUI", "KON.D12 ETAM BAFIA", "KON.D13 P112 CORON",
            "KON.D14 P9 MVOG MBI", "KON.D15 P15 EKOUNOU",
            "KON.D16 SNEC NKOAYOS", "KON.D17 NKOABANG", "KON.D112 BRASSERIES",
            # NSIMALEN
            "NSI.D11 AEROGARE", "NSI.D31 MBALMAYO", "NSI.D32 YAOUNDE",
            # NOMAYOS
            "NOM.D31 CIMENCAM", "NOM.D32 - AHALA II", "NOM.AHALA I",
            # NYOM
            "NYO.D31 NYOM", "NYO.D32 AKAK", "NYO.D33 PAEPYS",
            # OYOMABANG
            "OYO.D11 OYOMABANG", "OYO.D12 OYOMABANG",
            "OYO.D13 OYOMABANG", "OYO.D14 OYOMABANG",
            # KOUMASSI
            "KOU.D 122 VALLEE BONANJO", "KOU.D123 KOUMASSI RAIL",
            "KOU.D12 AKWA", "KOU.D11 SONEL BUREAU", "KOU.D13 BK3",
            "KOU.D17 DEIDO", "KOU.D18 LOWE", "KOU.D19 LYCEE SAVIO",
            "KOU.D110 LYCEE TECHNIQUE", "KOU.D111 NDOUMBE EPEE",
            "KOU.D113 SERPENTS", "KOU.D117 ST MICHEL",
            "KOU.D14 BK4", "KOU.D15 BRASSERIES", "KOU.D16 CNPS",
            "KOU.D112 NGOLLE", "KOU.D114 SNCDV", "KOU.D115 SNEC ASTREINTE",
            "KOU.D116 AVIATION", "KOU.D18 KITCHNER", "KOU.D119 MEDCEM",
            "KOU.D120 CIMENTERIE MIRA", "KOU.D121 YABASSI",
            # BASSA
            "BAS.D118JAPOMA", "BAS.D11BASSA NORD", "BAS.D16SNEC",
            "BAS.D17POLANO", "BAS.D121 ACIERIES", "BAS.D14STADE BEPANDA",
            "BAS.D126GRAND MALL", "BAS.D127 OYACK MEDUSE", "BAS.D12BK3",
            "BAS.D13BK4", "BAS.D18PROFOR", "BAS.D111SCIMPOS",
            "BAS.D116DUMEZ", "BAS.D124VIETEL", "BAS.D15ST MICHEL",
            "BAS.D110GUINNESS", "BAS.D115TP", "BAS.D117MASSOUMBOU",
            "BAS.D122COMAGRI", "BAS.D123MALANGUE",
            # BEKOKO
            "BKK.D38BRASAF", "BKK.D39 ELIM", "BKK.D310 WFI",
            "BKK.D31DIBOMBARI", "BKK.D32BOMONO", "BKK.D33ROUTETIKO",
            "BKK.D34MINKWELLE", "BKK.D35BOADIBO", "BKK.D36CAMWATER", "BKK.D37OLAMCAM",
            # BONABERI
            "BON.D113 ACERO METAL", "BON.D114 MAYA", "BON.D13SOCAME",
            "BON.D112 NOVIA", "BON.D11BONABERI VILLE", "BON.D12P1ZI",
            "BON.D14INSTITUT TONJI", "BON.D16 CIMENCAM", "BON.D17MINKWELLE",
            "BON.D19CAMWATER", "BON.D111CIMAF", "BON.D115 ECO GREEN",
            "BON.D116 OK PLAST", "BON.A12MBOPPI - UIC", "BON.D18IYOCK",
            "BON.D110 HARJAAP / ACERO METAL", "BON.D15NANGAH",
            # DEIDO
            "DEI.D11MTN", "DEI.D12MTN", "DEI.D13CDB", "DEI.D14MBOPPI",
            "DEI.D18NOUVEL AKWA", "DEI.D15POLANO", "DEI.D16SOCOPAO",
            "DEI.D19QUAI", "DEI.D110ANCIEN AKWA", "DEI.D112NDOI MAETUR",
            "DEI.A12MAKEPE ( D17 BONEWONDA)",
            # NGODI BAKOKO
            "NGO.D18 STADE JAPOMA", "NGO.D19 LOGEMENT SOCIAUX",
            "NGO.D11FERME AVICOLE", "NGO.D12RECASEMENT BILLE",
            "NGO.D13TRADEX", "NGO.D14LEPROSERIE", "NGO.D15MBOKO",
            "NGO.D16LIVRAISON MAGZI", "NGO.D17 NKOLBONG",
            # MAKEPE
            "MAK.D11BONAMOUSSADI 1", "MAK.D13DA2", "MAK.D15CRAYON D'OR",
            "MAK.D16MALANGUE", "MAK.D17BUREAUX MAETUR", "MAK.D18DM2",
            "MAK.D110DISSAKE", "MAK.D12BONAMOUSSADI 2", "MAK.D14CIMB",
            "MAK.D114ORANGE DATA CENTER", "MAK.D111KOTTO NGONGANG",
            "MAK.D112MAIRIE 1", "MAK.D113MAIRIE 2",
            # LOGBABA
            "LBB.D16SNEC", "LBB.D11G N  PK17", "LBB.D17ACIERIE",
            "LBB.D18METAFRIQUE", "LBB.D19PROMAL 3", "LBB.D111LBBBABA", "LBB.D114 LBBBABA",
            # DJAMBOUTOU
            "DJA.D11 CICAM", "DJA.D13 HUILERIE", "DJA.D15 RADIO",
            "DJA.D17 DEM", "DJA D19 SODECOTON", "DJA.D20 AEROPORT",
            "DJA.D21 STADE ROUMDE-ADJIA", "DJA.D12 VILLE",
            "DJA.D14 CICAM CABLE", "DJA.D18 SOCAPROD",
            "DJA.D31 BOKLE", "DJA.D32 GASHIGA",
            # GUIDER
            "GUI.D32 FIGUIL", "GUI.D33 MAYO OULO", "GUI.D35 GUIDER", "GUI.D36 CIMENCAM",
            # LAGDO
            "LAG.D12 CITE", "LAG.D31 TCH", "LAG.D32 LAM",
            # MAROUA
            "MRA.D11 VILLE", "MRA.D12 VILLE", "MRA.D13 VILLE",
            "MRA.D31 MOKOLO", "MRA.D34 BOGOMAGA", "MRA.D36 MINDIF",
            "MRA.D32 MERI", "MRA.D35 YAGOUA",
            # NGAOUNDERE
            "NGA.D11 VILLE", "NGA.D12 VINA", "NGA.D13 AEROPORT",
            "NGA.D14 ACERO METAL", "NGA.D31 MEIGANGA", "NGA.D33 TCHABAL",
            # DJOB
            "DJO.D32 EBOLOWA VILLE", "DJO.D34 AMBAM", "DJO.D35 AMBAM I",
            # EKOMBITIE
            "EKO.D31 LOLODORF (Ex Ebolowa)", "EKO.D32 SNEC",
            "EKO.D33 MBALMAYO", "EKO.D34 SANGMELIMA",
            # BAMENDA
            "BDA.D11 VILLE", "BDA.D12 VILLE", "BDA.D13 VILLE",
            "BDA.D31 MBENGWI", "BDA.D32 WUM", "BDA.D33 MAMFE",
            "BDA.D35 KUMBO", "BDA.D36 MBOUDA",
            # BAFOUSSAM
            "BFS.D11 VILLE", "BFS.D11 VILLE-BAFOUSSAM", "BFS.D12 VILLE",
            "BFS.D13 VILLE", "BFS.D31 MBOUDA", "BFS.D32 FOUMBOT", "BFS.D33 BANGANGTE",
            # BERTOUA
            "BENGBIS.D VILLE", "BER.D11 VILLE", "BER.D12VILLE",
            "BER.D31 BATOURI", "BER.D32 BELABO", "BER.D33 ABG", "BETARE.D CENTRALE",
            # MILE 2 LIMBE
            "LBE.D31BUEA", "LBE.D32LIMBE", "LBE.D33TIKO", "LBE.D34SONARA",
            # NJOMBE
            "NJBE.D32 LOUM", "NJBE.D33 MBANGA", "NJBE.D34 PHP",
            # NKONGSAMBA
            "NKS.D11VILLE", "NKS.D12VILLE", "NKS.D13VILLE",
            "NKS.D31MANJO", "NKS.D32BAFANG",
            # NDJOCK NKONG
            "NDJ.D31 POUMA", "NDJ.D32BAFIA", "NDJ.D33 MATOMB",
            # MPOLONGWE
            "MPOL.D31 EDEA", "MPOL.D32 KRIBI", "MPOL.D33 PAK",
            "MPOL.D35 SNH", "MPOL.D36 KRIBI",
            # EDEA / SLL / CAMPO
            "ED15KV.D14 VILLE N°1", "ED15KV.D14 VILLE N°2",
            "SLL.D11 MASSOCK", "CAMPO.D VILLE",
            # DISTRIBUTION MAINTENANCE POSTES
            "RAME 15kV N°1", "RAME 15kV N°2", "RAME 30kV N°1",
            "RAME 30kV N°2", "RAME 15kV", "RAME 30kV",
            "RAME 15kV N°3","RAME 30kV N°3",
            # TRANSPORT
            "AT N°1  90/15kV", "AT N°2  90/15kV", "AT N°3  90/15kV",
            "AT N°1  90/30kV", "AT N°2  90/30kV", "AT  90/15kV", "AT  90/30kV",
            "AT N°1  225/90kV", "AT N°2  225/90kV", "AT N°1  225/15kV",
            "AT N°3  90/15kV", "AT  110/15kV", "AT   90/15kV",
            "Jeu de barres 90kV", "Jeu de barres 90kV ", "Jeu de barres 225 kV",
            "Jeu de barres 225kV", "Jeu de barres 110kV",
            "Appareillages Protection 90kV et Auxiliaires",
            "Appareillages Protection 225kV et Auxiliaires",
            "Appareillages Protection 110kV et Auxiliaires",
            "D.Ligne 90kV OYOMABANG_BRGM", "D.Ligne 90kV OYOMABANG_NGOUSSO",
            "D.Ligne 90kV NGOUSSO_KONDENGUI", "D.Ligne 90kV OYOMABANG_AHALA",
            "D.Ligne 90kV AHALA_NSIMALEN", "D.Ligne 90kV OYOMABANG-NOMAYOS",
            "D.Ligne 225kV MANGOMBE-OYOMABANG", "D.Ligne 225 kV  NATCHIGAL-NYOM II",
            "D.Ligne 225 kV  NYOM II-OYOMABANG", "D.Ligne 90kV LOGBABA-KOUMASSI",
            "D.Ligne 90kV BONABERI-BEKOKO", "D.Ligne 90kV DEIDO-BONABERI",
            "D.Ligne 90kV BASSA-DEIDO", "D.Ligne 90kV BASSA-MAKEPE",
            "D.Ligne 90kV LOGBABA-NGODI BAKOKO", "D.Ligne 225kV MANGOMBE-LOGBABA",
            "D.Ligne 225kV SOGLOULOU-LOGBABA", "D.Ligne 90kV LOGBABA-BASSA",
            "D.Ligne 110kV GUIDER-MAROUA", "D.Ligne 110kV LAGDO-DJAMBOUTOU",
            "D.Ligne 110kV DJAMBOUTOU-GUIDER", "D.Ligne 110kV LAGDO-NGAOUNDERE",
            "D.Ligne 90kV MEMVELE-DJOB", "D.Ligne 90kV AHALA-EKOMBITIE",
            "D.Ligne 90kV C_EDEA-NDJOCK NKONG", "D.Ligne 90kV NDJOCK NKONG-OYOMABANG",
            "D.Ligne 90kV BEKOKO-NJOMBE", "D.Ligne 90kV NJOMBE-NKONGSAMBA",
            "D.Ligne 90kV BEKOKO-MILE2 LIMBE", "D.Ligne 90kV NKONGSAMBA-BAFOUSSAM",
            "D.Ligne 90kV BAFOUSSAM-BAMENDA", "D.Ligne 90kV LOM PANGAR-BERTOUA",
            "D.Ligne 225 kV  SONGLOULOU- MANGOMBE 1",
            "D.Ligne 225 kV  SONGLOULOU- MANGOMBE 2",
            "D.Ligne 90 kV DIBAMBA – NGODI BAKOKO",
            "TRAVEE 225 kV TFO", "TRAVEE 90 kV TFO", "TFO 225/90 kV 105 MVA",
            # PRODUCTION
            "Groupe 01 - TR01", "Groupe 02 - TR02", "Groupe 03 - TR03",
            "Groupe 04 - ALUCAM", "Groupe 05 - ALUCAM", "Groupe 06 - ALUCAM",
            "EDEA_Groupe 07 - ALUCAM", "Groupe 08 - ALUCAM", "Groupe 09 - ALUCAM",
            "Groupe 10 - TR10", "Groupe 11 - TR11", "Groupe 12 -TR12",
            "Groupe 13 - TR13", "Groupe 14 - TR14",
            "Groupe 1-  TR01", "Groupe 2 - TR02", "Groupe 3 - TR03", "Groupe 4 - TR04",
            "Groupe 1 - TR01", "Groupe 2 - TR01", "Groupe 3 - TR02",
            "Groupe 4 - TR02", "Groupe 5 - TR03", "Groupe 6 - TR03",
            "Groupe 7 - TR04", "Groupe 8 - TR04",
            "Groupe 1 - TR01", "Groupe 2 - TR02", "Groupe 3 - TR03",
            "Groupe 4 - TR04", "Groupe 5 - TR05", "Groupe 6 - TR06", "Groupe 7 - TR07",
            "Groupe 01", "Groupe 02", "Groupe 03", "Groupe 04", "Groupe 05",
            "Groupe 06", "Groupe 07", "Groupe 08", "Groupe 09", "Groupe 10",
            "Groupe 11", "Groupe 12", "Groupe 13",
            "Groupe 1 ", "Groupe 2", "Groupe 3", "Groupe 4",
            "Groupe 5", "Groupe 6", "Groupe 7", "Groupe 8",
        ]
        for nom in departs_data:
            Depart.objects.get_or_create(nom=nom.strip(), defaults={"actif": True})
        self.stdout.write(" Départs créés")

        #   TYPES DE TRAVAUX 
        types_travaux_data = [
            # PRODUCTION
            "CONTROLES GENERAUX",
            "Révision ciblé",
            "Entretien",
            # TRANSPORT
            "Entretien appareillages de protection HTB",
            "Entretien Jeu de barres",
            "Entretien transformateurs HTB",
            "Entretien lignes de transport",
            "Mise en service travée",
            "Entretien Auxiliaire de commande",
            # DISTRIBUTION
            "CONFECTION",
            "CONSTRUCTION",
            "Création",
            "DEPLACEMENT",
            "Dépose",
            "Elagage et Abattage",
            "Entretien Diagnostic poste HTB/HTA",
            "Eradication des zones rouges",
            "INSPECTION",
            "MAINTENANCE",
            "Maintenance de réseau",
            "Maintenance des poteaux bois",
            "Maintenance des transformateurs",
            "MONTAGE",
            "NORMALISATION",
            "Normalisations BT",
            "Normalisations MT",
            "PROTECTION",
            "RACCORDEMENT",
            "REHABILITATION",
            "Rehabilitation des lignes d'ossature HTA",
            "REMPLACEMENT",
            "RENFORCEMENT",
            "REPARATION",
        ]
        for libelle in types_travaux_data:
            TypeActivite.objects.get_or_create(libelle=libelle)
        self.stdout.write(" Types de travaux créés")

        #   CENTRALES THERMIQUES 
        centrales_data = [
            "CENTRALE THERMIQUE LOGBABA GAZ",
            "CENTRALE THERMIQUE LOGBABA 2",
            "CENTRALE THERMIQUE OYOMABANG 1",
            "CENTRALE THERMIQUE OYOMABANG 2",
            "CENTRALE THERMIQUE BAFOUSSAM",
            "CENTRALE THERMIQUE BERTOUA",
            "CENTRALE THERMIQUE BAMENDA",
            "CENTRALE THERMIQUE MBALMAYO",
            "CENTRALE THERMIQUE EBOLOWA",
            "KPDC",
            "DPDC",
            "CENTRALE THERMIQUE LIMBE",
        ]
        for nom in centrales_data:
            Centrale.objects.get_or_create(nom=nom, defaults={"actif": True})
        self.stdout.write(" Centrales thermiques créées")

        #   UNITES DEMANDERESSES 
        entites_data = [
            # PRODUCTION
            {"name": "DCP Songloulou", "type": "PROD"},
            {"name": "DCP Edéa", "type": "PROD"},
            {"name": "DCP Lagdo", "type": "PROD"},
            {"name": "IPP NHPC", "type": "PROD"},
            {"name": "IPP DPDC", "type": "PROD"},
            {"name": "IPP KPDC", "type": "PROD"},
            # TRANSPORT
            {"name": "Transport Centre-Sud-Est", "type": "TRANS"},
            {"name": "Transport Littoral-Sud Ouest", "type": "TRANS"},
            {"name": "Transport Ouest Nord Ouest", "type": "TRANS"},
            {"name": "Transport Nord-Extrême Nord-Adamaoua", "type": "TRANS"},
            # DISTRIBUTION
            {"name": "Distribution Poste source", "type": "DIST"},
            {"name": "Exploitation Douala Nord", "type": "DIST"},
            {"name": "Exploitation Douala Sud", "type": "DIST"},
            {"name": "Exploitation Douala Ouest", "type": "DIST"},
            {"name": "Exploitation Douala Est", "type": "DIST"},
            {"name": "Exploitation Douala Centre", "type": "DIST"},
            {"name": "Exploitation Yaoundé Nord", "type": "DIST"},
            {"name": "Exploitation Yaoundé Sud", "type": "DIST"},
            {"name": "Exploitation Yaoundé Ouest", "type": "DIST"},
            {"name": "Exploitation Yaoundé Est", "type": "DIST"},
            {"name": "Exploitation Yaoundé Centre", "type": "DIST"},
            {"name": "Exploitation technique Centre", "type": "DIST"},
            {"name": "Exploitation technique Sud Mbalmayo", "type": "DIST"},
            {"name": "Exploitation technique Est", "type": "DIST"},
            {"name": "Exploitation technique Ouest Nord Ouest", "type": "DIST"},
            {"name": "Exploitation technique Sanaga Océan", "type": "DIST"},
            {"name": "Exploitation technique Nord", "type": "DIST"},
            {"name": "Exploitation technique Extrême-Nord", "type": "DIST"},
            {"name": "Exploitation technique Adamaoua", "type": "DIST"},
            {"name": "Exploitation technique Sud Ouest Moungo", "type": "DIST"},
        ]

        for e in entites_data:
            EntiteMetier.objects.get_or_create(name=e['name'],defaults={"type": e['type']})
            self.stdout.write("✅ Unités demanderesses créées")
            
            
            
                #   REFERENCE RESEAU 
        references_data = [
            # DISTRIBUTION - MAINTENANCE POSTES
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_BRGM_POSTE SOURCE_HTA_TRANSFO 90/15kV N°1_RAME 15kV N°1", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "BRGM", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 15kV N°1"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_BRGM_POSTE SOURCE_HTA_TRANSFO 90/15kV N°2_RAME 15kV N°2", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "BRGM", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 15kV N°2"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_NGOUSSO_POSTE SOURCE_HTA_TRANSFO 90/30kV N°1_RAME 30kV N°1", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "NGOUSSO", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 30kV N°1"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_NGOUSSO_POSTE SOURCE_HTA_TRANSFO 90/15kVN°2_RAME 15kV N°2", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "NGOUSSO", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 15kV N°2"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_NGOUSSO_POSTE SOURCE_HTA_TRANSFO 90/15kV N°3_RAME 15kV N°3", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "NGOUSSO", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 15kV N°3"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_KONDENGUI_POSTE SOURCE_HTA_TRANSFO 90/15kV_RAME 15kV", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "KONDENGUI", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 15kV"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_AHALA_POSTE SOURCE_HTA_TRANSFO 90/15kV_RAME 15kV", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "AHALA", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 15kV"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_NSIMALEN_POSTE SOURCE_HTA_TRANSFO 90/15kV_RAME 15kV", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "NSIMALEN", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 15kV"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_NOMAYOS_POSTE SOURCE_HTA_TRANSFO 90/30kV_RAME 30kV", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "NOMAYOS", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 30kV"},
            {"code": "DISTRIBUTION-MAINTENANCE POSTES_OYOMABANG_POSTE SOURCE_HTA_TRANSFO 90/15kV _RAME 15kV", "troncon": "DISTRIBUTION-MAINTENANCE POSTES", "poste": "OYOMABANG", "ouvrage": "POSTE SOURCE_HTA", "depart": "RAME 15kV"},
            # TRANSPORT
            {"code": "TRANSPORT-CSE_BRGM_POSTE SOURCE_HTB_AT N°1  90/15kV", "troncon": "TRANSPORT-CSE", "poste": "BRGM", "ouvrage": "POSTE SOURCE_HTB", "depart": "AT N°1  90/15kV"},
            {"code": "TRANSPORT-CSE_BRGM_POSTE SOURCE_HTB_AT N°2  90/15kV", "troncon": "TRANSPORT-CSE", "poste": "BRGM", "ouvrage": "POSTE SOURCE_HTB", "depart": "AT N°2  90/15kV"},
            {"code": "TRANSPORT-CSE_BRGM_POSTE SOURCE_HTB_Jeu de barres 90kV", "troncon": "TRANSPORT-CSE", "poste": "BRGM", "ouvrage": "POSTE SOURCE_HTB", "depart": "Jeu de barres 90kV"},
            {"code": "TRANSPORT-CSE_BRGM_LIGNE_HTB_D.Ligne 90kV OYOMABANG_BRGM", "troncon": "TRANSPORT-CSE", "poste": "BRGM", "ouvrage": "LIGNE_HTB", "depart": "D.Ligne 90kV OYOMABANG_BRGM"},
            # PRODUCTION
            {"code": "PRODUCTION - EDEA_DCP_Groupe 01 - TR01", "troncon": "PRODUCTION - EDEA", "poste": None, "ouvrage": "DCP", "depart": "Groupe 01 - TR01"},
            {"code": "PRODUCTION - EDEA_DCP_Groupe 02 - TR02", "troncon": "PRODUCTION - EDEA", "poste": None, "ouvrage": "DCP", "depart": "Groupe 02 - TR02"},
            {"code": "PRODUCTION - LAGDO_DCP_Groupe 1-  TR01", "troncon": "PRODUCTION - LAGDO", "poste": None, "ouvrage": "DCP", "depart": "Groupe 1-  TR01"},
            {"code": "PRODUCTION - NHPC_IPP_Groupe 1 - TR01", "troncon": "PRODUCTION - NHPC", "poste": None, "ouvrage": "IPP", "depart": "Groupe 1 - TR01"},
        ]

        for r in references_data:
            try:
                troncon = Troncon.objects.get(nom=r['troncon'])
                ouvrage = Ouvrage.objects.get(nom=r['ouvrage'])
                poste = Poste.objects.get(nom=r['poste']) if r['poste'] else None
                depart = Depart.objects.get(nom=r['depart'].strip()) if r['depart'] else None

                ReferenceReseau.objects.get_or_create(
                    code_reference=r['code'],
                    defaults={
                        "libelle": r['code'],
                        "ouvrage": ouvrage,
                        "poste": poste,
                        "troncon": troncon,
                        "depart": depart,
                        "actif": True
                    }
                )
            except Exception as e:
                self.stdout.write(f"⚠️ Erreur pour {r['code']} : {e}")

        self.stdout.write("  Références réseau créées")
                    
        self.stdout.write(self.style.SUCCESS(" Seed référentiel terminé avec succès !"))