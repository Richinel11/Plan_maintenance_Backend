from ..models import Role
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Initialise les rôles du système'

    def handle(self, *args, **kwargs):
        roles = [
        {
            'nom': 'Opérateur de saisie',
            'code_role': 'OPERATEUR_SAISIE',
            'description': 'Crée et met à jour les travaux de maintenance dans le système'
        },
        {
            'nom': 'Gestionnaire de planification',
            'code_role': 'GESTIONNAIRE_PLANNING',
            'description': 'Analyse et aligne les plannings de maintenance entre les entités'
        },
        {
            'nom': "Responsable d'exploitation",
            'code_role': 'RESPONSABLE_EXPLOITATION',
            'description': 'Affilie les équipes et valide les plannings transmis'
        },
        {
            'nom': 'CCR',
            'code_role': 'CCR',
            'description': 'Reçoit les DDR, autorise ou refuse les arrêts et génère les NAPT'
        },
        {
            'nom': 'Équipe communication',
            'code_role': 'EQUIPE_COMMUNICATION',
            'description': 'Diffuse les Notes d\'Arrêt Programmées de Travaux (NAPT)'
        },
        {
            'nom': 'Régulateur / Auditeur',
            'code_role': 'REGULATEUR',
            'description': 'Consulte en lecture seule les KPI, rapports et historiques'
        },
        {
            'nom': 'Administrateur',
            'code_role': 'ADMIN',
            'description': 'a tous les droits permissions dans l\'aplication'
        },
    ] 

        for role in roles:
            obj, created = Role.objects.get_or_create(
                code_role=role['code_role'],
                defaults={
                    'nom': role['nom'],
                    'description': role['description'],
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f" Créé : {obj.nom}"))
            else:
                self.stdout.write(f" Existe déjà : {obj.nom}")
