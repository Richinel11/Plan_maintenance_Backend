# Fusion des deux têtes de migration issues du merge de bugfix-/-alerte
# dans kryss : 0008 (alignement_verrouille) et 0005_planning_transmission
# divergent toutes les deux depuis 0004_alter_travail_niveau_coupure.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('planning', '0005_planning_transmission'),
        ('planning', '0008_travail_alignement_verrouille'),
    ]

    operations = [
    ]
