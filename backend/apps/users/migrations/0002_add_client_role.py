# Generated manually for adding CLIENT role

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('coach', 'Coach'), ('assistant', 'Assistant'), ('client', 'Client')],
                default='coach',
                max_length=10
            ),
        ),
    ]
