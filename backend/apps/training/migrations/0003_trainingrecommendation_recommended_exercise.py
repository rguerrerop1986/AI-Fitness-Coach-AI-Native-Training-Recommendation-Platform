# Generated manually for refactor: use catalogs.Exercise as recommendation source

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0004_add_exercise_intensity_tags'),
        ('training', '0002_alter_dailycheckin_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingrecommendation',
            name='recommended_exercise',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='training_recommendations',
                to='catalogs.exercise',
            ),
        ),
    ]
