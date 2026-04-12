from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
from django.conf import settings

from .initial_assessment_upload import initial_assessment_document_upload_to

User = get_user_model()


class Client(models.Model):
    """Client model for storing client information."""

    class Sex(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    class Level(models.TextChoices):
        BEGINNER = 'beginner', 'Principiante'
        INTERMEDIATE = 'intermediate', 'Intermedio'
        ADVANCED = 'advanced', 'Avanzado'

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    sex = models.CharField(max_length=1, choices=Sex.choices)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    height_m = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0.50), MaxValueValidator(2.50)],
        help_text='Height in meters (e.g. 1.85)',
    )
    level = models.CharField(
        max_length=12,
        choices=Level.choices,
        default=Level.BEGINNER,
        help_text='Client level for AI routine suggestions',
    )
    initial_weight_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(300)]
    )
    notes = models.TextField(blank=True)
    consent_checkbox = models.BooleanField(default=False)
    emergency_contact = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(null=True, blank=True)
    deactivated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deactivated_clients',
    )
    deactivation_reason = models.TextField(blank=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='client_profile',
        help_text="Linked User account for client portal access"
    )
    coach = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='clients',
        help_text="Coach responsible for this client (must have role=coach)",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'clients'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class Measurement(models.Model):
    """Client body measurements model."""
    
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE, 
        related_name='measurements'
    )
    date = models.DateField()
    weight_kg = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        validators=[MinValueValidator(30), MaxValueValidator(300)]
    )
    body_fat_pct = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(50)]
    )
    chest_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(200)]
    )
    waist_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(200)]
    )
    hips_cm = models.DecimalField(
        max_digits=5, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(50), MaxValueValidator(200)]
    )
    bicep_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(100)]
    )
    thigh_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(30), MaxValueValidator(150)]
    )
    calf_cm = models.DecimalField(
        max_digits=4, 
        decimal_places=1,
        null=True, 
        blank=True,
        validators=[MinValueValidator(20), MaxValueValidator(100)]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'measurements'
        ordering = ['-date']
        unique_together = ['client', 'date']
    
    def __str__(self):
        return f"{self.client.full_name} - {self.date} ({self.weight_kg}kg)"


class InitialAssessment(models.Model):
    """
    Entrevista inicial de entrenamiento y nutrición (historial por cliente).
    Solo una fila activa por cliente (ver restricción en Meta).
    """

    class EstadoSalud(models.TextChoices):
        EXCELENTE = 'excelente', 'Excelente'
        BUENO = 'bueno', 'Bueno'
        REGULAR = 'regular', 'Regular'
        MALO = 'malo', 'Malo'

    class ObjetivoPeso(models.TextChoices):
        BAJAR = 'bajar', 'Bajar'
        MANTENER = 'mantener', 'Mantener'
        AUMENTAR = 'aumentar', 'Aumentar'

    _scale_1_10 = [MinValueValidator(1), MaxValueValidator(10)]

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='initial_assessments',
    )
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Solo una evaluación activa por cliente; las nuevas desactivan la anterior.',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='initial_assessments_created',
    )

    # 1. Datos personales
    nombre_completo = models.CharField(max_length=255)
    edad = models.PositiveIntegerField()
    fecha_nacimiento = models.DateField()
    telefono = models.CharField(max_length=40, blank=True)
    contacto_emergencia = models.TextField(blank=True)
    peso_actual = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Peso actual en kg',
    )
    estatura = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(0.50), MaxValueValidator(2.50)],
        help_text='Estatura en metros (p. ej. 1.75)',
    )
    correo_electronico = models.EmailField()

    # 2. Historial de salud
    estado_salud = models.CharField(max_length=20, choices=EstadoSalud.choices)
    ultima_revision_medica = models.DateField(null=True, blank=True)
    tiene_lesion_o_impedimento = models.BooleanField(default=False)
    lesion_o_impedimento_detalle = models.TextField(blank=True)
    tiene_condicion_medica = models.BooleanField(default=False)
    condicion_medica_detalle = models.TextField(blank=True)
    alergias = models.TextField(blank=True)
    medicamentos_actuales = models.TextField(blank=True)
    suplementos_actuales = models.TextField(blank=True)

    # 3. Estilo de vida
    fuma = models.BooleanField(default=False)
    frecuencia_fuma = models.CharField(max_length=255, blank=True)
    consume_alcohol = models.BooleanField(default=False)
    frecuencia_alcohol = models.CharField(max_length=255, blank=True)
    ocupacion = models.CharField(max_length=255, blank=True)
    horas_sueno_promedio = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(24)],
    )

    # 4. Actividad física
    actualmente_realiza_ejercicio = models.BooleanField(default=False)
    tipo_ejercicio_actual = models.TextField(blank=True)
    dias_entrena_por_semana = models.PositiveSmallIntegerField(null=True, blank=True)
    minutos_cardio_por_sesion = models.PositiveIntegerField(null=True, blank=True)
    minutos_fuerza_por_sesion = models.PositiveIntegerField(null=True, blank=True)
    actividades_fisicas_favoritas = models.TextField(blank=True)

    # 5. Nutrición
    sigue_dieta_actualmente = models.BooleanField(default=False)
    dieta_actual_detalle = models.TextField(blank=True)
    ha_seguido_plan_alimentacion = models.BooleanField(default=False)
    plan_alimentacion_detalle = models.TextField(blank=True)
    quien_compra_y_prepara_comida = models.TextField(blank=True)
    comidas_por_dia = models.PositiveSmallIntegerField(null=True, blank=True)

    # 6. Historial de peso
    peso_mas_bajo_ultimos_5_anios = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
    )
    peso_mas_alto_ultimos_5_anios = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0.01)],
    )
    objetivo_peso = models.CharField(max_length=20, choices=ObjetivoPeso.choices)

    # 7. Metas y motivación
    metas_salud_fitness = models.TextField()
    obstaculos_principales = models.TextField()
    fortalezas_personales = models.TextField()
    importancia_meta_1_10 = models.PositiveSmallIntegerField(validators=_scale_1_10)
    confianza_meta_1_10 = models.PositiveSmallIntegerField(validators=_scale_1_10)

    # 8. Consentimiento
    declaracion_aceptada = models.BooleanField(default=False)
    nombre_cliente_consentimiento = models.CharField(max_length=255)
    firma_texto = models.TextField()
    fecha_consentimiento = models.DateField()

    # 9. Documento adjunto (path vía storage; no binario en PostgreSQL)
    documento_adjunto = models.FileField(
        upload_to=initial_assessment_document_upload_to,
        max_length=512,
        blank=True,
        null=True,
        help_text='Archivo en el backend de almacenamiento configurado (local hoy, Azure mañana).',
    )
    documento_nombre_original = models.CharField(max_length=512, blank=True)
    documento_tamano_bytes = models.PositiveIntegerField(null=True, blank=True)
    documento_content_type = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'initial_assessments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', '-created_at']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['client'],
                condition=models.Q(is_active=True),
                name='uniq_active_initial_assessment_per_client',
            ),
        ]

    def __str__(self):
        return f'InitialAssessment v{self.version} client={self.client_id} active={self.is_active}'
