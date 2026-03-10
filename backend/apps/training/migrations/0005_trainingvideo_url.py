# Add optional URL to TrainingVideo for client dashboard playback

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0004_recommendation_engine_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='trainingvideo',
            name='url',
            field=models.URLField(blank=True, help_text='Optional video URL for client playback'),
        ),
    ]
