from decimal import Decimal
from rest_framework import serializers
from .models import CheckIn, TrainingLog, DietLog

# ---- Structural check-in: soft ranges (Spanish messages) ----
STRUCTURAL_RANGES = {
    'weight_kg': (20, 300, 'Peso debe estar entre 20 y 300 kg'),
    'height_m': (Decimal('0.50'), Decimal('2.50'), 'Estatura debe estar entre 0.50 y 2.50 m'),
    'rc': (30, 220, 'Frecuencia cardíaca debe estar entre 30 y 220'),
    'skinfold_mm': (1, 80, 'Pliegues deben estar entre 1 y 80 mm'),
    'perimeter_cm': (10, 250, 'Perímetros deben estar entre 10 y 250 cm'),
}


# ---- Exercise summary for nested read (TrainingLog) ----
def _exercise_summary(exercise):
    if not exercise:
        return None
    return {'id': exercise.id, 'name': exercise.name, 'image_url': exercise.image_url or ''}


class TrainingLogSerializer(serializers.ModelSerializer):
    suggested_exercise_summary = serializers.SerializerMethodField()
    executed_exercise_summary = serializers.SerializerMethodField()

    def get_suggested_exercise_summary(self, obj):
        return _exercise_summary(obj.suggested_exercise)

    def get_executed_exercise_summary(self, obj):
        return _exercise_summary(obj.executed_exercise)

    class Meta:
        model = TrainingLog
        fields = [
            'id', 'client', 'plan_cycle', 'coach', 'date',
            'suggested_exercise', 'executed_exercise',
            'suggested_exercise_summary', 'executed_exercise_summary',
            'execution_status', 'duration_minutes', 'rpe', 'energy_level',
            'pain_level', 'notes',
            'recommendation_version', 'recommendation_meta', 'recommendation_confidence',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_rpe(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Debe estar entre 1 y 10.')
        return value

    def validate_energy_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Debe estar entre 1 y 10.')
        return value

    def validate_pain_level(self, value):
        if value is not None and (value < 0 or value > 10):
            raise serializers.ValidationError('Debe estar entre 0 y 10.')
        return value


class DietLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DietLog
        fields = [
            'id', 'client', 'plan_cycle', 'coach', 'date',
            'adherence_percent', 'calories_estimate_kcal', 'protein_estimate_g',
            'carbs_estimate_g', 'fats_estimate_g',
            'hunger_level', 'cravings_level', 'digestion_quality', 'notes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_adherence_percent(self, value):
        if value is not None and (value < 0 or value > 100):
            raise serializers.ValidationError('Adherence must be between 0 and 100.')
        return value

    def validate_hunger_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Debe estar entre 1 y 10.')
        return value

    def validate_cravings_level(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Debe estar entre 1 y 10.')
        return value

    def validate_digestion_quality(self, value):
        if value is not None and (value < 1 or value > 10):
            raise serializers.ValidationError('Debe estar entre 1 y 10.')
        return value


def _round2(value):
    if value is None:
        return None
    return round(Decimal(str(float(value))), 2)


class CheckInSerializer(serializers.ModelSerializer):
    """Read: expone rc_1min (alias de rc_1min_bpm) y todos los campos ESTRUCTURAL."""
    rc_1min = serializers.IntegerField(source='rc_1min_bpm', read_only=True)

    class Meta:
        model = CheckIn
        fields = [
            'id', 'client', 'date', 'weight_kg', 'height_m', 'bmi', 'body_fat_pct',
            'rc_termino', 'rc_1min', 'is_structural',
            'chest_cm', 'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm',
            'skinfold_triceps_1', 'skinfold_triceps_2', 'skinfold_triceps_3', 'skinfold_triceps_avg',
            'skinfold_subscapular_1', 'skinfold_subscapular_2', 'skinfold_subscapular_3', 'skinfold_subscapular_avg',
            'skinfold_suprailiac_1', 'skinfold_suprailiac_2', 'skinfold_suprailiac_3', 'skinfold_suprailiac_avg',
            'skinfold_abdominal_1', 'skinfold_abdominal_2', 'skinfold_abdominal_3', 'skinfold_abdominal_avg',
            'skinfold_ant_thigh_1', 'skinfold_ant_thigh_2', 'skinfold_ant_thigh_3', 'skinfold_ant_thigh_avg',
            'skinfold_calf_1', 'skinfold_calf_2', 'skinfold_calf_3', 'skinfold_calf_avg',
            'diameter_femoral_l', 'diameter_femoral_r', 'diameter_femoral_avg',
            'diameter_humeral_l', 'diameter_humeral_r', 'diameter_humeral_avg',
            'diameter_styloid_l', 'diameter_styloid_r', 'diameter_styloid_avg',
            'perimeter_waist', 'perimeter_abdomen', 'perimeter_calf', 'perimeter_hip', 'perimeter_chest',
            'perimeter_arm_relaxed', 'perimeter_arm_flexed',
            'perimeter_thigh_relaxed', 'perimeter_thigh_flexed',
            'rpe', 'fatigue', 'diet_adherence', 'workout_adherence', 'notes',
            'created_at', 'updated_at', 'plan_cycle',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CheckInCreateSerializer(serializers.ModelSerializer):
    """
    Crea/actualiza check-in ESTRUCTURAL.
    Acepta payload anidado (skinfolds, diameters, perimeters, feedback) y lo mapea a campos planos.
    Validación fuerte: todos los campos ESTRUCTURAL requeridos para nuevo check-in.
    """
    rc_1min = serializers.IntegerField(write_only=True, required=False)
    client_id = serializers.IntegerField(write_only=True, required=False)
    skinfolds = serializers.JSONField(required=False, write_only=True)
    diameters = serializers.JSONField(required=False, write_only=True)
    perimeters = serializers.JSONField(required=False, write_only=True)
    feedback = serializers.JSONField(required=False, write_only=True)

    class Meta:
        model = CheckIn
        fields = [
            'date', 'client_id',
            'weight_kg', 'height_m', 'rc_termino', 'rc_1min', 'rc_1min_bpm',
            'skinfolds', 'diameters', 'perimeters', 'feedback',
            'body_fat_pct', 'chest_cm', 'waist_cm', 'hips_cm', 'bicep_cm', 'thigh_cm', 'calf_cm',
            'rpe', 'fatigue', 'diet_adherence', 'workout_adherence', 'notes',
            'skinfold_triceps_1', 'skinfold_triceps_2', 'skinfold_triceps_3', 'skinfold_triceps_avg',
            'skinfold_subscapular_1', 'skinfold_subscapular_2', 'skinfold_subscapular_3', 'skinfold_subscapular_avg',
            'skinfold_suprailiac_1', 'skinfold_suprailiac_2', 'skinfold_suprailiac_3', 'skinfold_suprailiac_avg',
            'skinfold_abdominal_1', 'skinfold_abdominal_2', 'skinfold_abdominal_3', 'skinfold_abdominal_avg',
            'skinfold_ant_thigh_1', 'skinfold_ant_thigh_2', 'skinfold_ant_thigh_3', 'skinfold_ant_thigh_avg',
            'skinfold_calf_1', 'skinfold_calf_2', 'skinfold_calf_3', 'skinfold_calf_avg',
            'diameter_femoral_l', 'diameter_femoral_r', 'diameter_femoral_avg',
            'diameter_humeral_l', 'diameter_humeral_r', 'diameter_humeral_avg',
            'diameter_styloid_l', 'diameter_styloid_r', 'diameter_styloid_avg',
            'perimeter_waist', 'perimeter_abdomen', 'perimeter_calf', 'perimeter_hip', 'perimeter_chest',
            'perimeter_arm_relaxed', 'perimeter_arm_flexed',
            'perimeter_thigh_relaxed', 'perimeter_thigh_flexed',
        ]

    def _flatten_nested(self, data):
        """Convierte payload anidado a campos planos. Modifica data in-place."""
        # rc_1min -> rc_1min_bpm (se asigna en create/update)
        if 'rc_1min' in data:
            data['rc_1min_bpm'] = data.pop('rc_1min', None)
        # BMI: never trust client; we compute server-side
        data.pop('bmi', None)
        # Feedback
        feedback = data.pop('feedback', None)
        if feedback:
            data.setdefault('rpe', feedback.get('rpe'))
            data.setdefault('fatigue', feedback.get('fatigue'))
            data.setdefault('diet_adherence', feedback.get('diet_adherence_pct'))
            data.setdefault('workout_adherence', feedback.get('training_adherence_pct'))
            data.setdefault('notes', feedback.get('notes'))
        # Skinfolds: triceps, subscapular, suprailiac, abdominal, ant_thigh, calf
        skinfold_map = {
            'triceps': 'skinfold_triceps',
            'subscapular': 'skinfold_subscapular',
            'suprailiac': 'skinfold_suprailiac',
            'abdominal': 'skinfold_abdominal',
            'ant_thigh': 'skinfold_ant_thigh',
            'calf': 'skinfold_calf',
        }
        skinfolds = data.pop('skinfolds', None)
        if skinfolds:
            for key, prefix in skinfold_map.items():
                block = skinfolds.get(key) or {}
                data[f'{prefix}_1'] = block.get('m1')
                data[f'{prefix}_2'] = block.get('m2')
                data[f'{prefix}_3'] = block.get('m3')
                data[f'{prefix}_avg'] = block.get('avg')
        # Diameters: femoral, humeral, styloid
        diameter_map = {'femoral': 'diameter_femoral', 'humeral': 'diameter_humeral', 'styloid': 'diameter_styloid'}
        diameters = data.pop('diameters', None)
        if diameters:
            for key, prefix in diameter_map.items():
                block = diameters.get(key) or {}
                data[f'{prefix}_l'] = block.get('l')
                data[f'{prefix}_r'] = block.get('r')
                data[f'{prefix}_avg'] = block.get('avg')
        # Perimeters
        perimeters = data.pop('perimeters', None)
        if perimeters:
            data['perimeter_waist'] = perimeters.get('waist')
            data['perimeter_abdomen'] = perimeters.get('abdomen')
            data['perimeter_calf'] = perimeters.get('calf')
            data['perimeter_hip'] = perimeters.get('hip')
            data['perimeter_chest'] = perimeters.get('chest')
            arm = perimeters.get('arm') or {}
            data['perimeter_arm_relaxed'] = arm.get('relaxed')
            data['perimeter_arm_flexed'] = arm.get('flexed')
            thigh = perimeters.get('thigh') or {}
            data['perimeter_thigh_relaxed'] = thigh.get('relaxed')
            data['perimeter_thigh_flexed'] = thigh.get('flexed')
        return data

    def to_internal_value(self, data):
        if isinstance(data, dict):
            data = dict(data)
            self._flatten_nested(data)
        return super().to_internal_value(data)

    def _soft_validate_range(self, value, low, high, msg):
        if value is None:
            return
        try:
            v = float(value)
            if v < low or v > high:
                raise serializers.ValidationError(msg)
        except (TypeError, ValueError):
            pass

    def validate(self, attrs):
        is_structural = attrs.get('is_structural', True)
        errors = {}

        # Rangos soft
        weight = attrs.get('weight_kg')
        if weight is not None:
            self._soft_validate_range(weight, 20, 300, STRUCTURAL_RANGES['weight_kg'][2])
        height = attrs.get('height_m')
        if height is not None:
            try:
                h = float(height)
                if h <= 0:
                    errors['height_m'] = ['La estatura debe ser mayor que 0.']
                else:
                    self._soft_validate_range(h, 0.5, 2.5, STRUCTURAL_RANGES['height_m'][2])
            except (TypeError, ValueError):
                errors['height_m'] = ['Estatura inválida.']
        for field in ('rc_termino', 'rc_1min_bpm'):
            v = attrs.get(field)
            if v is not None:
                self._soft_validate_range(v, 30, 220, STRUCTURAL_RANGES['rc'][2])

        if is_structural:
            # Requeridos principales
            if attrs.get('weight_kg') is None:
                errors['weight_kg'] = ['Peso (kg) es obligatorio.']
            if attrs.get('height_m') is None:
                errors['height_m'] = ['Estatura (m) es obligatoria.']
            if attrs.get('rc_termino') is None:
                errors['rc_termino'] = ['RC término es obligatorio.']
            if attrs.get('rc_1min_bpm') is None:
                errors['rc_1min'] = ['RC 1 min es obligatorio.']
            # Pliegues: _1, _2, _3 obligatorios
            pliegues = [
                'skinfold_triceps', 'skinfold_subscapular', 'skinfold_suprailiac',
                'skinfold_abdominal', 'skinfold_ant_thigh', 'skinfold_calf',
            ]
            for p in pliegues:
                for suf in ('_1', '_2', '_3'):
                    f = p + suf
                    if attrs.get(f) is None:
                        errors[f] = [f'Medición {suf} es obligatoria.']
            # Diámetros: L y R
            for d in ('diameter_femoral', 'diameter_humeral', 'diameter_styloid'):
                for suf in ('_l', '_r'):
                    f = d + suf
                    if attrs.get(f) is None:
                        errors[f] = ['Valor obligatorio.']
            # Perímetros
            perims = [
                'perimeter_waist', 'perimeter_abdomen', 'perimeter_calf', 'perimeter_hip', 'perimeter_chest',
                'perimeter_arm_relaxed', 'perimeter_arm_flexed', 'perimeter_thigh_relaxed', 'perimeter_thigh_flexed',
            ]
            for f in perims:
                if attrs.get(f) is None:
                    errors[f] = ['Perímetro es obligatorio.']

        if errors:
            raise serializers.ValidationError(errors)
        return attrs

    def _compute_skinfold_avg(self, v1, v2, v3):
        if v1 is None or v2 is None or v3 is None:
            return None
        return _round2((float(v1) + float(v2) + float(v3)) / 3)

    def _compute_diameter_avg(self, l, r):
        if l is None or r is None:
            return None
        return _round2((float(l) + float(r)) / 2)

    def _compute_bmi(self, weight_kg, height_m):
        """BMI = weight_kg / (height_m ** 2), rounded to 2 decimals. Returns None if invalid."""
        if weight_kg is None or height_m is None:
            return None
        try:
            h = float(height_m)
            if h <= 0:
                return None
            w = float(weight_kg)
            return _round2(Decimal(str(w)) / (Decimal(str(h)) * Decimal(str(h))))
        except (TypeError, ValueError, ZeroDivisionError):
            return None

    def _set_bmi(self, attrs):
        bmi = self._compute_bmi(attrs.get('weight_kg'), attrs.get('height_m'))
        if bmi is not None:
            attrs['bmi'] = bmi
        elif 'bmi' in attrs:
            del attrs['bmi']

    def _set_averages(self, attrs):
        pliegues = [
            'skinfold_triceps', 'skinfold_subscapular', 'skinfold_suprailiac',
            'skinfold_abdominal', 'skinfold_ant_thigh', 'skinfold_calf',
        ]
        for p in pliegues:
            avg = self._compute_skinfold_avg(attrs.get(p + '_1'), attrs.get(p + '_2'), attrs.get(p + '_3'))
            if avg is not None:
                attrs[p + '_avg'] = avg
        for d in ('diameter_femoral', 'diameter_humeral', 'diameter_styloid'):
            avg = self._compute_diameter_avg(attrs.get(d + '_l'), attrs.get(d + '_r'))
            if avg is not None:
                attrs[d + '_avg'] = avg

    def create(self, validated_data):
        validated_data.pop('client_id', None)
        self._set_averages(validated_data)
        self._set_bmi(validated_data)
        validated_data.setdefault('is_structural', True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('client_id', None)
        self._set_averages(validated_data)
        self._set_bmi(validated_data)
        return super().update(instance, validated_data)
