# ESTRUCTURAL CheckIn: pliegues, diámetros, perímetros, RC, estatura

from django.db import migrations, models


def _decimal52():
    return models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)


def _decimal62():
    return models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)


class Migration(migrations.Migration):

    dependencies = [
        ('tracking', '0004_traininglog_recommendation_fields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='checkin',
            name='weight_kg',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='checkin',
            name='height_m',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='Estatura en metros (ESTRUCTURAL)', max_digits=4, null=True),
        ),
        migrations.AddField(
            model_name='checkin',
            name='rc_termino',
            field=models.IntegerField(blank=True, help_text='Frecuencia cardíaca al término', null=True),
        ),
        migrations.AddField(
            model_name='checkin',
            name='rc_1min_bpm',
            field=models.IntegerField(blank=True, help_text='Frecuencia cardíaca 1 minuto después (API: rc_1min)', null=True),
        ),
        migrations.AddField(
            model_name='checkin',
            name='is_structural',
            field=models.BooleanField(default=True, help_text='Check-in tipo ESTRUCTURAL con pliegues/diámetros/perímetros'),
        ),
        migrations.AddField(model_name='checkin', name='skinfold_triceps_1', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_triceps_2', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_triceps_3', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_triceps_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_subscapular_1', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_subscapular_2', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_subscapular_3', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_subscapular_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_suprailiac_1', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_suprailiac_2', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_suprailiac_3', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_suprailiac_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_abdominal_1', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_abdominal_2', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_abdominal_3', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_abdominal_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_ant_thigh_1', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_ant_thigh_2', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_ant_thigh_3', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_ant_thigh_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_calf_1', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_calf_2', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_calf_3', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='skinfold_calf_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_femoral_l', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_femoral_r', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_femoral_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_humeral_l', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_humeral_r', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_humeral_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_styloid_l', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_styloid_r', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='diameter_styloid_avg', field=_decimal52()),
        migrations.AddField(model_name='checkin', name='perimeter_waist', field=_decimal62()),
        migrations.AddField(model_name='checkin', name='perimeter_abdomen', field=_decimal62()),
        migrations.AddField(model_name='checkin', name='perimeter_calf', field=_decimal62()),
        migrations.AddField(model_name='checkin', name='perimeter_hip', field=_decimal62()),
        migrations.AddField(model_name='checkin', name='perimeter_chest', field=_decimal62()),
        migrations.AddField(model_name='checkin', name='perimeter_arm_relaxed', field=_decimal62()),
        migrations.AddField(model_name='checkin', name='perimeter_arm_flexed', field=_decimal62()),
        migrations.AddField(model_name='checkin', name='perimeter_thigh_relaxed', field=_decimal62()),
        migrations.AddField(model_name='checkin', name='perimeter_thigh_flexed', field=_decimal62()),
    ]
