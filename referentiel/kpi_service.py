from planning.models import Travail

def _get_poste_from_travail(travail: Travail) -> str: 
        """Récupère le nom du poste depuis les items de la référence."""
        if not travail.reference:
            return "Inconnu"
        item = travail.reference.items.filter( #type: ignore[attr-defined]
            type__nom='POSTE'
        ).first()
        return item.valeur if item else travail.reference.valeur 