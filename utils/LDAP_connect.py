# ldap_auth.py
import os
from ldap3 import Server, Connection, ALL, SUBTREE
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPSocketOpenError, LDAPInvalidFilterError
import logging
from dotenv import load_dotenv
 
# Charger les variables d'environnement
load_dotenv()
 
# Configuration du logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
 
def ldap_login(user_id, password):
    """
    Fonction d'authentification Active Directory (adaptée du code JavaScript)
    """
    # Configuration basée sur votre code JavaScript
    LDAP_SERVER = os.getenv("LDAP_SERVER")
    LDAP_DOMAIN = os.getenv("LDAP_DOMAIN")
    LDAP_URL = f"ldap://{LDAP_SERVER}:{os.getenv('LDAP_PORT')}"
    print(f"Tentative de connexion AD pour: {user_id}")
    try:
        # --- CONNEXION ET AUTHENTIFICATION ---
        # Format UPN comme dans votre code JavaScript
        user_dn = f"{user_id}@{LDAP_DOMAIN}"
        print(f"Tentative de bind avec: {user_dn}")
        # Création du serveur
        server = Server(LDAP_URL, get_info=ALL)
        # Connexion et authentification
        conn = Connection(server, user=user_dn, password=password, auto_bind=True)
        print(f"Authentification AD réussie pour: {user_id}")
        # --- RECHERCHE DES INFORMATIONS UTILISATEUR ---
        # Recherche dans OU=Guests,OU=Cameroon (premier essai)
        search_base = "OU=Guests,OU=Cameroon,DC=camlight,DC=cm"
        search_filter = f"(&(objectCategory=person)(objectclass=user)(sAMAccountName={user_id}))"
        attributes = ['mail', 'givenName', 'sn', 'displayName', 'memberOf', 'distinguishedName']
        print(f"Recherche dans: {search_base}")
        conn.search(
            search_base=search_base,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=attributes
        )
        # Si non trouvé dans Guests, recherche dans Eneo People
        if not conn.entries:
            search_base = "OU=Eneo People,OU=People,OU=Cameroon,DC=camlight,DC=cm"
            print(f"Non trouvé, recherche dans: {search_base}")
            conn.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes
            )
            if not conn.entries:
                print("Utilisateur non trouvé dans l'annuaire AD")
                raise Exception("Votre compte n'est pas valide dans l'annuaire de l'entreprise ENEO")
        # --- EXTRACTION DES DONNÉES UTILISATEUR ---
        user_data = conn.entries[0]
        print("userData:", user_data)
        # Formatage des données
        user_info = {
            'username': user_id,
            'dn': str(user_data.distinguishedName) if hasattr(user_data, 'distinguishedName') else str(user_data.entry_dn),
            'email': str(user_data.mail) if hasattr(user_data, 'mail') else "",
            'givenName': str(user_data.givenName) if hasattr(user_data, 'givenName') else "",
            'sn': str(user_data.sn) if hasattr(user_data, 'sn') else "",
            'displayName': str(user_data.displayName) if hasattr(user_data, 'displayName') else 
                          f"{str(user_data.givenName) if hasattr(user_data, 'givenName') else ''} {str(user_data.sn) if hasattr(user_data, 'sn') else ''}".strip(),
            'groups': [str(group) for group in user_data.memberOf] if hasattr(user_data, 'memberOf') else [],
            'distinguishedName': str(user_data.distinguishedName) if hasattr(user_data, 'distinguishedName') else str(user_data.entry_dn)
        }
        print(f"Utilisateur trouvé: {user_info['displayName']}")
        return user_info
    except LDAPBindError as e:
        # --- GESTION DES ERREURS D'AUTHENTIFICATION ---
        error_msg = str(e)
        print(f"Erreur AD pour {user_id}: {error_msg}")
        logger.error(f"Erreur LDAP pour {user_id}: {error_msg}")
        if 'invalidCredentials' in error_msg or '49' in error_msg or '52e' in error_msg:
            raise Exception("Tentative de connexion échouée : Nom utilisateur ou mot de passe incorrect")
        elif 'account disabled' in error_msg.lower() or '52b' in error_msg or '533' in error_msg:
            raise Exception("Compte désactivé")
        elif 'account locked' in error_msg.lower() or '775' in error_msg or '530' in error_msg:
            raise Exception("Compte verrouillé")
        elif 'password expired' in error_msg.lower() or '532' in error_msg:
            raise Exception("Mot de passe expiré")
        else:
            raise Exception("Erreur d'authentification AD")
    except LDAPSocketOpenError as e:
        print(f"Erreur de connexion AD pour {user_id}: {str(e)}")
        raise Exception("Erreur de connexion au serveur AD")
    except Exception as e:
        # --- GESTION DES AUTRES ERREURS ---
        error_msg = str(e)
        print(f"Erreur générale pour {user_id}: {error_msg}")
        logger.error(f"Erreur LDAP pour {user_id}: {error_msg}")
        if 'no such object' in error_msg.lower() or '525' in error_msg:
            raise Exception("Votre compte n'est pas valide dans l'annuaire de l'entreprise ENEO")
        else:
            raise Exception("Erreur technique lors de l'authentification AD")
    finally:
        # --- DÉCONNEXION SÉCURISÉE ---
        try:
            if 'conn' in locals() and conn.bound:
                conn.unbind()
                print("Connexion AD fermée")
        except Exception as unbind_error:
            print(f"Erreur lors de la déconnexion AD: {unbind_error}")
 
def ldap_login_with_fallback(user_id, password):
    """
    Version avec fallback superadmin (optionnel)
    """
    try:
        return ldap_login(user_id, password)
    except Exception as error:
        # Fallback pour superadmin local si nécessaire
        SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD")
        if user_id == 'admin' and password and password == SUPERADMIN_PASSWORD:
            print('Authentification Superadmin locale réussie !')
            return {
                'username': 'admin',
                'dn': 'local/superadmin',
                'displayName': 'Super Administrateur',
                'email': 'admin@eneo.cm'
            }
        # Propager l'erreur originale si ce n'est pas le superadmin
        raise error
 
# Exemple d'utilisation
if __name__ == "__main__":
    # Test de la fonction
    try:
        # Remplacez par vos identifiants de test
        user_info = ldap_login_with_fallback("votre_utilisateur", "votre_mot_de_passe")
        print("Authentification réussie:")
        print(user_info)
    except Exception as e:
        print(f"Erreur: {e}")