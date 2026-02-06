"""
PDF generation service for workout and diet plans.

Generates a rich PDF document for a PlanCycle including:
- Client data (with latest measurements)
- Plan metadata (dates, duration, goal)
- Diet plan (meals, descriptions, foods)
- Workout plan (exercises, sets/reps/rest/notes)
"""

from io import BytesIO
from datetime import datetime
from html import escape as html_escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from django.utils import timezone


def generate_plan_pdf(plan_cycle):
    """
    Generate a PDF document for a PlanCycle including diet and workout plans.
    
    Args:
        plan_cycle: PlanCycle instance
        
    Returns:
        BytesIO buffer containing the PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5 * inch, bottomMargin=0.5 * inch)
    story = []
    styles = getSampleStyleSheet()

    # Helper: safe Paragraph creator for tables and long text
    def p(text, style_name="Normal"):
        """
        Safe Paragraph:
        - None -> ""
        - Escape HTML (&, <, >)
        - \n -> <br/>
        """
        if text is None:
            text = ""
        else:
            text = str(text)
        text = html_escape(text).replace("\n", "<br/>")
        # Fallback gracefully if custom style is not registered
        try:
            style = styles[style_name]
        except KeyError:
            style = styles["Normal"]
        return Paragraph(text, style)

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=12,
        alignment=TA_CENTER,
    )

    heading_style = ParagraphStyle(
        "CustomHeading",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#1e40af"),
        spaceAfter=8,
        spaceBefore=12,
    )

    subheading_style = ParagraphStyle(
        "CustomSubHeading",
        parent=styles["Heading3"],
        fontSize=12,
        textColor=colors.HexColor("#4b5563"),
        spaceAfter=6,
        spaceBefore=8,
    )
    styles.add(subheading_style)

    # Title
    story.append(Paragraph("Plan de Entrenamiento y Nutrición", title_style))
    story.append(Spacer(1, 0.2 * inch))

    # ------------------------------------------------------------------
    # Client & Plan data section
    # ------------------------------------------------------------------
    client = plan_cycle.client
    coach = plan_cycle.coach

    client_name = client.full_name
    client_age = getattr(client, "age", None)
    height_m = client.height_m

    # Latest measurement (if any)
    latest_measurement = client.measurements.order_by("-date").first()
    if latest_measurement:
        current_weight = latest_measurement.weight_kg
        weight_date_str = latest_measurement.date.strftime("%d/%m/%Y")
        weight_text = f"{current_weight} kg (medición {weight_date_str})"
        measurements_parts = []
        if latest_measurement.waist_cm:
            measurements_parts.append(f"Cintura: {latest_measurement.waist_cm} cm")
        if latest_measurement.chest_cm:
            measurements_parts.append(f"Pecho: {latest_measurement.chest_cm} cm")
        if latest_measurement.hips_cm:
            measurements_parts.append(f"Cadera: {latest_measurement.hips_cm} cm")
        if latest_measurement.bicep_cm:
            measurements_parts.append(f"Bíceps: {latest_measurement.bicep_cm} cm")
        if latest_measurement.thigh_cm:
            measurements_parts.append(f"Muslo: {latest_measurement.thigh_cm} cm")
        if latest_measurement.calf_cm:
            measurements_parts.append(f"Pantorrilla: {latest_measurement.calf_cm} cm")
        if latest_measurement.body_fat_pct:
            measurements_parts.append(f"Grasa corporal: {latest_measurement.body_fat_pct}%")

        if measurements_parts:
            measurements_text = "<br/>".join(f"• {part}" for part in measurements_parts)
        else:
            measurements_text = "Sin medidas detalladas registradas."
    else:
        current_weight = client.initial_weight_kg
        weight_text = f"{current_weight} kg (peso inicial)"
        measurements_text = "Sin mediciones registradas."

    coach_name = coach.get_full_name() or coach.username
    start_date_str = plan_cycle.start_date.strftime("%d/%m/%Y")
    end_date_str = plan_cycle.end_date.strftime("%d/%m/%Y")
    duration_days = plan_cycle.duration_days
    today_str = timezone.localdate().strftime("%d/%m/%Y")

    story.append(Paragraph("Datos del Cliente y del Plan", heading_style))

    client_plan_data = [
        [p("Cliente:", "CustomSubHeading"), p(client_name)],
    ]
    if client_age is not None:
        client_plan_data.append([p("Edad:", "CustomSubHeading"), p(f"{client_age} años")])

    client_plan_data.extend(
        [
            [p("Altura:", "CustomSubHeading"), p(f"{height_m} m")],
            [p("Peso actual:", "CustomSubHeading"), p(weight_text)],
            [p("Medidas:", "CustomSubHeading"), p(measurements_text)],
            [p("Coach:", "CustomSubHeading"), p(coach_name)],
            [p("Fecha actual:", "CustomSubHeading"), p(today_str)],
            [p("Periodo del plan:", "CustomSubHeading"), p(f"{start_date_str} - {end_date_str}")],
            [p("Duración:", "CustomSubHeading"), p(f"{duration_days} días")],
        ]
    )

    if plan_cycle.goal:
        goal_display = getattr(plan_cycle, "get_goal_display", lambda: plan_cycle.goal)()
        client_plan_data.append([p("Objetivo:", "CustomSubHeading"), p(goal_display)])

    client_plan_table = Table(client_plan_data, colWidths=[2.2 * inch, 3.8 * inch])
    client_plan_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )

    story.append(client_plan_table)
    story.append(Spacer(1, 0.3 * inch))
    
    # Diet Plan Section
    if hasattr(plan_cycle, 'diet_plan') and plan_cycle.diet_plan:
        diet_plan = plan_cycle.diet_plan
        story.append(Paragraph("Plan de Nutrición", heading_style))
        
        # Diet plan summary if available
        if diet_plan.daily_calories:
            summary_data = []
            if diet_plan.daily_calories:
                summary_data.append([p('Calorías diarias:', 'CustomSubHeading'), p(f'{diet_plan.daily_calories} kcal')])
            if diet_plan.protein_pct:
                summary_data.append([p('Proteína:', 'CustomSubHeading'), p(f'{diet_plan.protein_pct}%')])
            if diet_plan.carbs_pct:
                summary_data.append([p('Carbohidratos:', 'CustomSubHeading'), p(f'{diet_plan.carbs_pct}%')])
            if diet_plan.fat_pct:
                summary_data.append([p('Grasas:', 'CustomSubHeading'), p(f'{diet_plan.fat_pct}%')])
            
            if summary_data:
                summary_table = Table(summary_data, colWidths=[2.5 * inch, 3.5 * inch])
                summary_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#fef3c7')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 0.2*inch))
        
        # Meals
        meals = diet_plan.meals.all().order_by('order', 'meal_type')
        if meals.exists():
            for meal in meals:
                meal_type_display = meal.get_meal_type_display()
                story.append(Paragraph(meal_type_display, subheading_style))
                
                meal_data = []
                if meal.name:
                    meal_data.append([p('Nombre:', 'CustomSubHeading'), p(meal.name)])
                if meal.description:
                    meal_data.append([p('Descripción:', 'CustomSubHeading'), p(meal.description)])
                
                # Meal items if available
                if hasattr(meal, 'items') and meal.items.exists():
                    items_list = []
                    for item in meal.items.all().order_by('order'):
                        food_name = item.food.name
                        quantity = item.quantity
                        items_list.append(f"• {food_name}: {quantity}g")
                    if items_list:
                        # Use <br/> for line breaks in Paragraph
                        items_text = "<br/>".join(items_list)
                        meal_data.append([p('Alimentos:', 'CustomSubHeading'), p(items_text)])
                
                if meal_data:
                    meal_table = Table(meal_data, colWidths=[1.5 * inch, 5.5 * inch])
                    meal_table.setStyle(TableStyle([
                        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('LEFTPADDING', (0, 0), (-1, -1), 4),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ]))
                    story.append(meal_table)
                    story.append(Spacer(1, 0.15*inch))
        else:
            story.append(Paragraph("No hay comidas definidas en este plan.", styles['Normal']))
        
        story.append(Spacer(1, 0.2*inch))
        story.append(PageBreak())
    
    # Workout Plan Section
    if hasattr(plan_cycle, 'workout_plan') and plan_cycle.workout_plan:
        workout_plan = plan_cycle.workout_plan
        story.append(Paragraph("Plan de Entrenamiento", heading_style))
        
        if workout_plan.description:
            story.append(p(workout_plan.description))
            story.append(Spacer(1, 0.15 * inch))
        
        # Training entries grouped by date
        from apps.plans.models import TrainingEntry
        entries = TrainingEntry.objects.filter(workout_plan=workout_plan).order_by('date', 'id')
        
        if entries.exists():
            current_date = None
            for entry in entries:
                entry_date = entry.date
                date_str = entry_date.strftime('%d/%m/%Y')
                
                # New date header
                if current_date != entry_date:
                    if current_date is not None:
                        story.append(Spacer(1, 0.2 * inch))
                    story.append(Paragraph(f"<b>{html_escape(date_str)}</b>", subheading_style))
                    current_date = entry_date
                
                # Exercise entry
                exercise_name = entry.exercise.name
                entry_data = [
                    [p('Ejercicio:', 'CustomSubHeading'), p(exercise_name)],
                ]
                
                if entry.series:
                    entry_data.append([p('Series:', 'CustomSubHeading'), p(str(entry.series))])
                if entry.repetitions:
                    entry_data.append([p('Repeticiones:', 'CustomSubHeading'), p(entry.repetitions)])
                if entry.weight_kg:
                    entry_data.append([p('Peso:', 'CustomSubHeading'), p(f'{entry.weight_kg} kg')])
                if entry.rest_seconds:
                    entry_data.append([p('Descanso:', 'CustomSubHeading'), p(f'{entry.rest_seconds} seg')])
                if entry.notes:
                    entry_data.append([p('Notas:', 'CustomSubHeading'), p(entry.notes)])
                
                entry_table = Table(entry_data, colWidths=[1.5 * inch, 5.5 * inch])
                entry_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#dbeafe')),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ]))
                story.append(entry_table)
                story.append(Spacer(1, 0.1*inch))
        else:
            story.append(Paragraph("No hay ejercicios definidos en este plan.", styles['Normal']))
    
    # Footer
    story.append(Spacer(1, 0.3 * inch))
    generated_at = timezone.now().strftime("%d/%m/%Y %H:%M")
    footer_text = f"Generado el {generated_at}"
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    story.append(Paragraph(html_escape(footer_text), footer_style))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)

    # Safety check: avoid saving an unexpectedly small/empty PDF
    pdf_size = buffer.getbuffer().nbytes
    if pdf_size < 800:
        raise ValueError(
            f"Generated PDF is unexpectedly small ({pdf_size} bytes). "
            "Ensure the plan has sufficient data before generating the PDF."
        )

    return buffer
