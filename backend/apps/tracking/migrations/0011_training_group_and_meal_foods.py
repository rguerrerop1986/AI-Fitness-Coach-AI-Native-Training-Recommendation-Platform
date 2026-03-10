# Add training_group to DailyTrainingRecommendation and create DailyDietRecommendationMealFood

from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('catalogs', '0004_add_exercise_intensity_tags'),
        ('tracking', '0010_daily_training_and_diet_recommendations'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailytrainingrecommendation',
            name='training_group',
            field=models.CharField(
                blank=True,
                choices=[
                    ('upper_body', 'Tren superior'),
                    ('lower_body', 'Tren inferior'),
                    ('core', 'Core'),
                    ('insanity', 'Insanity'),
                    ('full_body', 'Full Body'),
                    ('active_recovery', 'Reposo activo'),
                ],
                help_text='Focus group for display: upper_body, lower_body, core, etc.',
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name='DailyDietRecommendationMealFood',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(
                    decimal_places=1,
                    default=1,
                    help_text='Quantity in the given unit (e.g. grams or pieces)',
                    max_digits=8,
                    validators=[django.core.validators.MinValueValidator(0.1)],
                )),
                ('unit', models.CharField(default='g', help_text='Unit: g, ml, pieza, etc.', max_length=20)),
                ('order', models.PositiveSmallIntegerField(default=0)),
                ('food', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='daily_recommendation_meal_foods',
                    to='catalogs.food',
                )),
                ('meal', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='meal_foods',
                    to='tracking.dailydietrecommendationmeal',
                )),
            ],
            options={
                'db_table': 'daily_diet_recommendation_meal_foods',
                'ordering': ['meal', 'order'],
            },
        ),
    ]
