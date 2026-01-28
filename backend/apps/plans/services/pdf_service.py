"""
PDF generation service for workout and diet plans.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=8,
        spaceBefore=12
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=6,
        spaceBefore=8
    )
    
    # Title
    story.append(Paragraph("Plan de Entrenamiento y Nutrición", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Client and Coach Info
    client_name = plan_cycle.client.full_name
    coach_name = plan_cycle.coach.get_full_name() or plan_cycle.coach.username
    start_date = plan_cycle.start_date.strftime('%d/%m/%Y')
    end_date = plan_cycle.end_date.strftime('%d/%m/%Y')
    duration_days = plan_cycle.duration_days
    
    info_data = [
        ['Cliente:', client_name],
        ['Entrenador:', coach_name],
        ['Fecha de inicio:', start_date],
        ['Fecha de fin:', end_date],
        ['Duración:', f'{duration_days} días'],
    ]
    
    if plan_cycle.goal:
        info_data.append(['Objetivo:', plan_cycle.get_goal_display()])
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Diet Plan Section
    if hasattr(plan_cycle, 'diet_plan') and plan_cycle.diet_plan:
        diet_plan = plan_cycle.diet_plan
        story.append(Paragraph("Plan de Nutrición", heading_style))
        
        # Diet plan summary if available
        if diet_plan.daily_calories:
            summary_data = []
            if diet_plan.daily_calories:
                summary_data.append(['Calorías diarias:', f'{diet_plan.daily_calories} kcal'])
            if diet_plan.protein_pct:
                summary_data.append(['Proteína:', f'{diet_plan.protein_pct}%'])
            if diet_plan.carbs_pct:
                summary_data.append(['Carbohidratos:', f'{diet_plan.carbs_pct}%'])
            if diet_plan.fat_pct:
                summary_data.append(['Grasas:', f'{diet_plan.fat_pct}%'])
            
            if summary_data:
                summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
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
                    meal_data.append(['Nombre:', meal.name])
                if meal.description:
                    meal_data.append(['Descripción:', meal.description])
                
                # Meal items if available
                if hasattr(meal, 'items') and meal.items.exists():
                    items_list = []
                    for item in meal.items.all().order_by('order'):
                        food_name = item.food.name
                        quantity = item.quantity
                        items_list.append(f"• {food_name}: {quantity}g")
                    if items_list:
                        meal_data.append(['Alimentos:', '\n'.join(items_list)])
                
                if meal_data:
                    meal_table = Table(meal_data, colWidths=[1.5*inch, 5.5*inch])
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
            story.append(Paragraph(workout_plan.description, styles['Normal']))
            story.append(Spacer(1, 0.15*inch))
        
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
                        story.append(Spacer(1, 0.2*inch))
                    story.append(Paragraph(f"<b>{date_str}</b>", subheading_style))
                    current_date = entry_date
                
                # Exercise entry
                exercise_name = entry.exercise.name
                entry_data = [
                    ['Ejercicio:', exercise_name],
                ]
                
                if entry.series:
                    entry_data.append(['Series:', str(entry.series)])
                if entry.repetitions:
                    entry_data.append(['Repeticiones:', entry.repetitions])
                if entry.weight_kg:
                    entry_data.append(['Peso:', f'{entry.weight_kg} kg'])
                if entry.rest_seconds:
                    entry_data.append(['Descanso:', f'{entry.rest_seconds} seg'])
                if entry.notes:
                    entry_data.append(['Notas:', entry.notes])
                
                entry_table = Table(entry_data, colWidths=[1.5*inch, 5.5*inch])
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
    story.append(Spacer(1, 0.3*inch))
    generated_at = timezone.now().strftime('%d/%m/%Y %H:%M')
    footer_text = f"Generado el {generated_at}"
    story.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
