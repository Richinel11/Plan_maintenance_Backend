from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('planning', '0007_add_missing_priorite_column'),
    ]

    operations = [
        migrations.AddField(
            model_name='travail',
            name='alignement_verrouille',
            field=models.BooleanField(default=False),
        ),
    ]
