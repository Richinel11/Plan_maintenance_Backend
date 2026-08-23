from django.db import migrations, models
import planning.models


class Migration(migrations.Migration):

    dependencies = [
        ('planning', '0006_alter_propositionalignement_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='travail',
            name='priorite',
            field=models.CharField(
                max_length=5,
                choices=planning.models.Travail.Priorite.choices,
                default=planning.models.Travail.Priorite.P3,
                null=True,
                blank=True,
            ),
        ),
    ]