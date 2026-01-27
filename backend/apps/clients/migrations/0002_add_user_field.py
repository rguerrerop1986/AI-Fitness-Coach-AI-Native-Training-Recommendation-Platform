# Generated manually for adding user field to Client model

from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='user',
            field=models.OneToOneField(
                blank=True,
                help_text='Linked User account for client portal access',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='client_profile',
                to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
