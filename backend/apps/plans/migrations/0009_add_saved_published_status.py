# Generated manually for plan state management (DRAFT | SAVED | PUBLISHED)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0008_revert_meal_unique_constraint'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plancycle',
            name='status',
            field=models.CharField(
                choices=[
                    ('draft', 'Draft'),
                    ('saved', 'Saved'),
                    ('published', 'Published'),
                    ('active', 'Active'),
                    ('completed', 'Completed'),
                    ('cancelled', 'Cancelled'),
                ],
                default='draft',
                max_length=12,
            ),
        ),
    ]
