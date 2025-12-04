import os
import json
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
import logging

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Генератор отчетов о рисках тендеров"""
    
    def __init__(self):
        self.reports_dir = "/app/reports"
        os.makedirs(self.reports_dir, exist_ok=True)

        # === подключаем DejaVu Sans ===
        base_dir = "/app/fonts"
        self.font_regular_path = os.path.join(base_dir, "DejaVuSans.ttf")
        self.font_bold_path = os.path.join(base_dir, "DejaVuSans-Bold.ttf")
        self.font_italic_path = os.path.join(base_dir, "DejaVuSans-Oblique.ttf")
        self.font_bold_italic_path = os.path.join(base_dir, "DejaVuSans-BoldOblique.ttf")

        # Имена шрифтов в ReportLab
        self.font_name = "DejaVuSans"
        self.font_name_bold = "DejaVuSans-Bold"
        self.font_name_italic = "DejaVuSans-Oblique"
        self.font_name_bold_italic = "DejaVuSans-BoldOblique"

        self._setup_fonts()
    
    def _setup_fonts(self):
        """Настройка шрифтов DejaVu Sans для поддержки кириллицы"""
        try:
            # Регистрируем все варианты
            pdfmetrics.registerFont(TTFont(self.font_name, self.font_regular_path))
            pdfmetrics.registerFont(TTFont(self.font_name_bold, self.font_bold_path))
            pdfmetrics.registerFont(TTFont(self.font_name_italic, self.font_italic_path))
            pdfmetrics.registerFont(
                TTFont(self.font_name_bold_italic, self.font_bold_italic_path)
            )

            # Связка для <b>/<i> в Paragraph (base family = DejaVuSans)
            addMapping(self.font_name, 0, 0, self.font_name)               # normal
            addMapping(self.font_name, 1, 0, self.font_name_bold)          # bold
            addMapping(self.font_name, 0, 1, self.font_name_italic)        # italic
            addMapping(self.font_name, 1, 1, self.font_name_bold_italic)   # bold+italic

            logger.info("✔ DejaVu Sans fonts loaded successfully")

        except Exception as e:
            logger.error(f"❌ Failed to load DejaVu Sans fonts: {e}")
            # fallback на стандартные шрифты ReportLab
            self.font_name = "Helvetica"
            self.font_name_bold = "Helvetica-Bold"
            self.font_name_italic = "Helvetica-Oblique"
            self.font_name_bold_italic = "Helvetica-BoldOblique"
    
    async def generate_pdf_report(self, results: List[Dict[str, Any]]) -> str:
        """Генерация PDF отчета"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tender_risk_report_{timestamp}.pdf"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Создание PDF документа
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            # Контент документа
            story = []
            
            # Добавление титульной страницы
            self._add_title_page(story, len(results))
            
            # Добавление содержания (на той же странице)
            story.append(Spacer(1, 1.5*cm))
            self._add_table_of_contents(story, results)
            story.append(PageBreak())
            
            # Анализ каждого тендера
            for i, result in enumerate(results, 1):
                self._add_tender_analysis_to_pdf(story, i, result)
                if i < len(results):
                    story.append(PageBreak())
            
            # Сборка PDF
            doc.build(story)
            
            logger.info(f"PDF отчет создан: {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка создания PDF отчета: {e}")
            raise
    
    def _add_title_page(self, story: List, total_tenders: int):
        """Добавление титульной страницы"""
        # Заголовок
        title_style = ParagraphStyle(
            'Title',
            fontName=self.font_name_bold,
            fontSize=22,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=15,
            alignment=TA_CENTER,
            leading=26
        )
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            fontName=self.font_name,
            fontSize=13,
            textColor=colors.HexColor('#555555'),
            spaceAfter=20,
            alignment=TA_CENTER
        )
        
        # Заголовок
        story.append(Spacer(1, 2*cm))
        story.append(Paragraph("АНАЛИТИЧЕСКИЙ ОТЧЕТ", title_style))
        story.append(Paragraph("Комплексная оценка рисков тендерных закупок", subtitle_style))
        
        # Линия-разделитель
        line_table = Table([['']], colWidths=[17*cm])
        line_table.setStyle(TableStyle([
            ('LINEABOVE', (0, 0), (-1, 0), 2, colors.HexColor('#2c5aa0')),
        ]))
        story.append(line_table)
        story.append(Spacer(1, 0.8*cm))
        
        # Информация о документе в виде таблицы
        current_date = datetime.now()
        
        info_data = [
            ['Дата формирования:', current_date.strftime('%d.%m.%Y')],
            ['Время формирования:', current_date.strftime('%H:%M:%S')],
            ['Количество объектов:', str(total_tenders)],
            ['Тип анализа:', 'Автоматизированная оценка с применением AI'],
        ]
        
        info_table = Table(info_data, colWidths=[8*cm, 9*cm])
        info_table.setStyle(TableStyle([
            ('FONT', (0, 0), (0, -1), self.font_name_bold, 10),
            ('FONT', (1, 0), (1, -1), self.font_name, 10),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        
        story.append(info_table)
        
        # Футер титульной страницы
        story.append(Spacer(1, 3*cm))
        
        footer_style = ParagraphStyle(
            'Footer',
            fontName=self.font_name_italic,
            fontSize=9,
            textColor=colors.HexColor('#888888'),
            alignment=TA_CENTER
        )
        
        story.append(Paragraph("Документ содержит конфиденциальную информацию", footer_style))
        story.append(Paragraph("Предназначен для внутреннего использования", footer_style))
    
    def _add_table_of_contents(self, story: List, results: List[Dict]):
        """Добавление содержания"""
        toc_title_style = ParagraphStyle(
            'TOCTitle',
            fontName=self.font_name_bold,
            fontSize=16,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=15,
            spaceBefore=10
        )
        
        story.append(Paragraph("СОДЕРЖАНИЕ", toc_title_style))
        
        # Таблица содержания с правильными размерами колонок
        toc_data = [['№', 'Наименование тендера', 'ID тендера', 'Риск']]
        
        for i, result in enumerate(results, 1):
            analysis = result.get('analysis', {})
            risk_level = analysis.get('overall_risk_level', 'неизвестно')
            
            # Обрезаем название если слишком длинное
            name = result['tender_name']
            if len(name) > 55:
                name = name[:52] + '...'
            
            toc_data.append([
                str(i),
                name,
                result['tender_id'],
                risk_level.upper()
            ])
        
        # Правильные размеры колонок с учетом полей
        toc_table = Table(toc_data, colWidths=[1.2*cm, 10.3*cm, 3*cm, 2.5*cm])
        toc_table.setStyle(TableStyle([
            # Заголовок
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONT', (0, 0), (-1, 0), self.font_name_bold, 9),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Тело таблицы
            ('FONT', (0, 1), (-1, -1), self.font_name, 8),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('ALIGN', (3, 1), (3, -1), 'CENTER'),
            
            # Границы
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c5aa0')),
            
            # Отступы
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            
            # Чередующиеся строки
            *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f5f5')) 
              for i in range(2, len(toc_data), 2)]
        ]))
        
        story.append(toc_table)
    
    def _add_tender_analysis_to_pdf(self, story: List, index: int, result: Dict):
        """Добавление детального анализа тендера"""
        analysis = result.get('analysis', {})
        
        # Заголовок тендера с номером
        header_style = ParagraphStyle(
            'TenderHeader',
            fontName=self.font_name_bold,
            fontSize=14,
            textColor=colors.white,
            spaceAfter=15,
            alignment=TA_LEFT,
            leftIndent=10,
            leading=18
        )
        
        header_table = Table(
            [[Paragraph(f"ТЕНДЕР #{index}", header_style)]],
            colWidths=[17*cm]
        )
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#2c5aa0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(header_table)
        story.append(Spacer(1, 0.4*cm))
        
        # Основная информация о тендере
        self._add_tender_info_section(story, result, analysis)
        story.append(Spacer(1, 0.4*cm))
        
        # Оценка рисков
        self._add_risk_assessment_section(story, analysis)
        story.append(Spacer(1, 0.4*cm))
        
        # Резюме
        self._add_executive_summary_section(story, analysis)
        story.append(Spacer(1, 0.4*cm))
        
        # Ключевые риски
        self._add_key_risks_section(story, analysis)
        story.append(Spacer(1, 0.4*cm))
        
        # Тревожные сигналы и положительные факторы
        self._add_flags_and_factors_section(story, analysis)
        story.append(Spacer(1, 0.4*cm))
        
        # Рекомендации
        self._add_recommendations_section(story, analysis)
        story.append(Spacer(1, 0.4*cm))
        
        # Детальный анализ
        self._add_detailed_analysis_section(story, analysis)
    
    def _add_tender_info_section(self, story: List, result: Dict, analysis: Dict):
        """Секция с основной информацией о тендере"""
        section_title_style = ParagraphStyle(
            'SectionTitle',
            fontName=self.font_name_bold,
            fontSize=11,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=8,
            spaceBefore=5
        )
        
        story.append(Paragraph("1. ОСНОВНАЯ ИНФОРМАЦИЯ", section_title_style))
        
        # Используем Paragraph для переноса длинного текста
        info_style = ParagraphStyle(
            'InfoText',
            fontName=self.font_name,
            fontSize=9,
            leading=12
        )
        
        info_data = [
            [Paragraph('<b>Наименование:</b>', info_style), 
             Paragraph(result['tender_name'], info_style)],
            [Paragraph('<b>ID тендера:</b>', info_style), 
             Paragraph(result['tender_id'], info_style)],
        ]
        
        info_table = Table(info_data, colWidths=[3.5*cm, 13.5*cm])
        info_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, -1), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        
        story.append(info_table)
    
    def _add_risk_assessment_section(self, story: List, analysis: Dict):
        """Секция с оценкой рисков"""
        section_title_style = ParagraphStyle(
            'SectionTitle',
            fontName=self.font_name_bold,
            fontSize=11,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=8,
            spaceBefore=5
        )
        
        story.append(Paragraph("2. ОЦЕНКА РИСКОВ", section_title_style))
        
        risk_level = analysis.get('overall_risk_level', 'неизвестно')
        risk_score = analysis.get('risk_score_estimate', 0)
        
        # Определение цвета риска
        risk_color = self._get_risk_color(risk_level)
        risk_bg_color = self._get_risk_bg_color(risk_level)
        
        risk_style = ParagraphStyle(
            'RiskText',
            fontName=self.font_name,
            fontSize=9
        )
        
        risk_value_style = ParagraphStyle(
            'RiskValue',
            fontName=self.font_name_bold,
            fontSize=10
        )
        
        risk_data = [
            [Paragraph('<b>Уровень риска:</b>', risk_style), 
             Paragraph(risk_level.upper(), risk_value_style)],
            [Paragraph('<b>Числовая оценка:</b>', risk_style), 
             Paragraph(f"{risk_score}/10", risk_style)]
        ]
        
        risk_table = Table(risk_data, colWidths=[3.5*cm, 13.5*cm])
        risk_table.setStyle(TableStyle([
            ('TEXTCOLOR', (1, 0), (1, 0), risk_color),
            ('BACKGROUND', (1, 0), (1, 0), risk_bg_color),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]))
        
        story.append(risk_table)
    
    def _add_executive_summary_section(self, story: List, analysis: Dict):
        """Секция с резюме"""
        section_title_style = ParagraphStyle(
            'SectionTitle',
            fontName=self.font_name_bold,
            fontSize=11,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=8,
            spaceBefore=5
        )
        
        text_style = ParagraphStyle(
            'BodyText',
            fontName=self.font_name,
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY,
            leading=12,
            spaceBefore=5,
            spaceAfter=5
        )
        
        story.append(Paragraph("3. РЕЗЮМЕ", section_title_style))
        
        summary = analysis.get('executive_summary', 'Резюме отсутствует')
        summary = str(summary) if not isinstance(summary, str) else summary
        
        summary_table = Table([[Paragraph(summary, text_style)]], colWidths=[17*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#2c5aa0')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(summary_table)
    
    def _add_key_risks_section(self, story: List, analysis: Dict):
        """Секция с ключевыми рисками"""
        section_title_style = ParagraphStyle(
            'SectionTitle',
            fontName=self.font_name_bold,
            fontSize=11,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=8,
            spaceBefore=5
        )
        
        story.append(Paragraph("4. КЛЮЧЕВЫЕ РИСКИ", section_title_style))
        
        if 'key_risks' in analysis and analysis['key_risks']:
            cell_style = ParagraphStyle(
                'CellText',
                fontName=self.font_name,
                fontSize=8,
                leading=10
            )
            
            header_style = ParagraphStyle(
                'HeaderText',
                fontName=self.font_name_bold,
                fontSize=8,
                leading=10
            )
            
            risks_data = [[
                Paragraph('Категория', header_style),
                Paragraph('Уровень', header_style),
                Paragraph('Описание', header_style)
            ]]
            
            for risk in analysis['key_risks']:
                category = risk.get('category', 'Не указано')
                severity = risk.get('severity', 'неизвестно')
                description = risk.get('description', '')
                
                # Добавляем доказательства если есть
                if 'evidence' in risk and risk['evidence']:
                    description += f"\n\n<i>Доказательства:</i> {risk['evidence']}"
                
                risks_data.append([
                    Paragraph(category, cell_style),
                    Paragraph(severity.upper(), cell_style),
                    Paragraph(description, cell_style)
                ])
            
            # Правильные размеры колонок
            risks_table = Table(risks_data, colWidths=[3.5*cm, 2*cm, 11.5*cm])
            risks_table.setStyle(TableStyle([
                # Заголовок
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                
                # Границы
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c5aa0')),
                
                # Отступы
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                
                # Выравнивание
                ('ALIGN', (1, 1), (1, -1), 'CENTER'),
                
                # Чередующиеся строки
                *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f5f5')) 
                  for i in range(2, len(risks_data), 2)]
            ]))
            
            story.append(risks_table)
        else:
            story.append(Paragraph("Ключевые риски не выявлены", self._get_body_style()))
    
    def _add_flags_and_factors_section(self, story: List, analysis: Dict):
        """Секция с тревожными сигналами и положительными факторами"""
        section_title_style = ParagraphStyle(
            'SectionTitle',
            fontName=self.font_name_bold,
            fontSize=11,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=8,
            spaceBefore=5
        )
        
        story.append(Paragraph("5. АНАЛИЗ ФАКТОРОВ", section_title_style))
        
        list_style = ParagraphStyle(
            'ListStyle',
            fontName=self.font_name,
            fontSize=8,
            leading=11,
            leftIndent=0
        )
        
        subsection_style = ParagraphStyle(
            'SubsectionStyle',
            fontName=self.font_name_bold,
            fontSize=9,
            leading=11
        )
        
        # Тревожные сигналы
        red_flags_title = Paragraph('ТРЕВОЖНЫЕ СИГНАЛЫ', subsection_style)
        red_flags_items = []
        
        if 'red_flags' in analysis and analysis['red_flags']:
            for flag in analysis['red_flags']:
                flag_text = str(flag) if not isinstance(flag, str) else flag
                red_flags_items.append(Paragraph(f"• {flag_text}", list_style))
        else:
            red_flags_items.append(Paragraph("Не выявлено", list_style))
        
        # Положительные факторы
        positive_title = Paragraph('ПОЛОЖИТЕЛЬНЫЕ ФАКТОРЫ', subsection_style)
        positive_items = []
        
        if 'positive_factors' in analysis and analysis['positive_factors']:
            for factor in analysis['positive_factors']:
                factor_text = str(factor) if not isinstance(factor, str) else factor
                positive_items.append(Paragraph(f"• {factor_text}", list_style))
        else:
            positive_items.append(Paragraph("Не выявлено", list_style))
        
        # Таблица
        factors_data = [
            [red_flags_title, positive_title],
            [[item for item in red_flags_items], [item for item in positive_items]]
        ]
        
        factors_table = Table(factors_data, colWidths=[8.5*cm, 8.5*cm])
        factors_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#ffebee')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#e8f5e9')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(factors_table)
    
    def _add_recommendations_section(self, story: List, analysis: Dict):
        """Секция с рекомендациями"""
        section_title_style = ParagraphStyle(
            'SectionTitle',
            fontName=self.font_name_bold,
            fontSize=11,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=8,
            spaceBefore=5
        )
        
        story.append(Paragraph("6. РЕКОМЕНДАЦИИ", section_title_style))
        
        if 'recommendations' in analysis and analysis['recommendations']:
            cell_style = ParagraphStyle(
                'CellText',
                fontName=self.font_name,
                fontSize=8,
                leading=11
            )
            
            header_style = ParagraphStyle(
                'HeaderText',
                fontName=self.font_name_bold,
                fontSize=8,
                leading=10
            )
            
            rec_data = [[
                Paragraph('№', header_style),
                Paragraph('Рекомендация', header_style)
            ]]
            
            for i, rec in enumerate(analysis['recommendations'], 1):
                rec_text = str(rec) if not isinstance(rec, str) else rec
                rec_data.append([
                    Paragraph(str(i), cell_style),
                    Paragraph(rec_text, cell_style)
                ])
            
            rec_table = Table(rec_data, colWidths=[1.2*cm, 15.8*cm])
            rec_table.setStyle(TableStyle([
                # Заголовок
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Тело
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                
                # Границы
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
                ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#2c5aa0')),
                
                # Отступы
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                
                # Чередующиеся строки
                *[('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f5f5f5')) 
                  for i in range(2, len(rec_data), 2)]
            ]))
            
            story.append(rec_table)
        else:
            story.append(Paragraph("Рекомендации отсутствуют", self._get_body_style()))
    
    def _add_detailed_analysis_section(self, story: List, analysis: Dict):
        """Секция с детальным анализом"""
        section_title_style = ParagraphStyle(
            'SectionTitle',
            fontName=self.font_name_bold,
            fontSize=11,
            textColor=colors.HexColor('#2c5aa0'),
            spaceAfter=8,
            spaceBefore=5
        )
        
        story.append(Paragraph("7. ДЕТАЛЬНЫЙ АНАЛИЗ", section_title_style))
        
        body_style = ParagraphStyle(
            'DetailedText',
            fontName=self.font_name,
            fontSize=8,
            textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY,
            leading=11,
            spaceBefore=3,
            spaceAfter=3
        )
        
        subsection_style = ParagraphStyle(
            'DetailedSubsection',
            fontName=self.font_name_bold,
            fontSize=9,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=4,
            spaceBefore=8
        )
        
        if 'detailed_analysis' in analysis:
            detailed = analysis['detailed_analysis']
            
            # Конвертация в строку если это dict или другой тип
            if isinstance(detailed, dict):
                for key, value in detailed.items():
                    story.append(Paragraph(key.upper(), subsection_style))
                    story.append(Paragraph(str(value), body_style))
            elif isinstance(detailed, list):
                for item in detailed:
                    story.append(Paragraph(str(item), body_style))
                    story.append(Spacer(1, 0.15*cm))
            else:
                # Разбиваем текст на параграфы
                text = str(detailed)
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    if para.strip():
                        # Проверяем, является ли это заголовком
                        if para.strip().endswith(':') and len(para) < 100:
                            story.append(Paragraph(para.strip(), subsection_style))
                        else:
                            story.append(Paragraph(para.strip(), body_style))
                            story.append(Spacer(1, 0.15*cm))
    
    def _get_body_style(self):
        """Стиль для обычного текста"""
        return ParagraphStyle(
            'BodyText',
            fontName=self.font_name,
            fontSize=9,
            textColor=colors.HexColor('#333333'),
            alignment=TA_JUSTIFY,
            leading=12
        )
    
    def _get_risk_color(self, risk_level: str) -> colors.Color:
        """Получение цвета текста в зависимости от уровня риска"""
        risk_level = risk_level.lower()
        if 'высок' in risk_level:
            return colors.HexColor('#c62828')
        elif 'средн' in risk_level:
            return colors.HexColor('#f57c00')
        elif 'низк' in risk_level:
            return colors.HexColor('#2e7d32')
        return colors.black
    
    def _get_risk_bg_color(self, risk_level: str) -> colors.Color:
        """Получение цвета фона в зависимости от уровня риска"""
        risk_level = risk_level.lower()
        if 'высок' in risk_level:
            return colors.HexColor('#ffebee')
        elif 'средн' in risk_level:
            return colors.HexColor('#fff3e0')
        elif 'низк' in risk_level:
            return colors.HexColor('#e8f5e9')
        return colors.white
    
    async def generate_txt_report(self, results: List[Dict[str, Any]]) -> str:
        """Генерация TXT отчета"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tender_risk_report_{timestamp}.txt"
            filepath = os.path.join(self.reports_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # Титульная страница
                f.write("╔" + "═" * 78 + "╗\n")
                f.write("║" + " " * 15 + "АНАЛИТИЧЕСКИЙ ОТЧЕТ" + " " * 44 + "║\n")
                f.write("║" + " " * 8 + "Комплексная оценка рисков тендерных закупок" + " " * 27 + "║\n")
                f.write("╚" + "═" * 78 + "╝\n\n")
                
                # Информация о документе
                f.write(f"Дата формирования: {datetime.now().strftime('%d.%m.%Y')}\n")
                f.write(f"Время формирования: {datetime.now().strftime('%H:%M:%S')}\n")
                f.write(f"Количество проанализированных объектов: {len(results)}\n")
                f.write(f"Тип анализа: Автоматизированная оценка рисков с применением AI\n\n")
                
                f.write("─" * 80 + "\n\n")
                
                # Содержание
                f.write("СОДЕРЖАНИЕ\n")
                f.write("=" * 80 + "\n\n")
                
                for i, result in enumerate(results, 1):
                    analysis = result.get('analysis', {})
                    risk_level = analysis.get('overall_risk_level', 'неизвестно')
                    name = result['tender_name'][:60] + ('...' if len(result['tender_name']) > 60 else '')
                    f.write(f"{i}. {name}\n")
                    f.write(f"   ID: {result['tender_id']} | Риск: {risk_level.upper()}\n\n")
                
                f.write("=" * 80 + "\n\n")
                
                # Анализ каждого тендера
                for i, result in enumerate(results, 1):
                    self._add_tender_analysis_to_txt(f, i, result)
                    if i < len(results):
                        f.write("\n" + "═" * 80 + "\n\n")
                
                # Футер
                f.write("\n" + "─" * 80 + "\n")
                f.write("Документ содержит конфиденциальную информацию\n")
                f.write("Предназначен для внутреннего использования\n")
                f.write("─" * 80 + "\n")
            
            logger.info(f"TXT отчет создан: {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка создания TXT отчета: {e}")
            raise
    
    def _add_tender_analysis_to_txt(self, f, index: int, result: Dict):
        """Добавление анализа одного тендера в TXT"""
        analysis = result.get('analysis', {})
        
        # Заголовок тендера
        f.write("╔" + "═" * 78 + "╗\n")
        f.write(f"║  ТЕНДЕР #{index}" + " " * (70 - len(str(index))) + "║\n")
        f.write("╚" + "═" * 78 + "╝\n\n")
        
        # 1. Основная информация
        f.write("1. ОСНОВНАЯ ИНФОРМАЦИЯ\n")
        f.write("─" * 80 + "\n")
        f.write(f"Наименование: {result['tender_name']}\n")
        f.write(f"ID тендера:   {result['tender_id']}\n\n")
        
        # 2. Оценка рисков
        risk_level = analysis.get('overall_risk_level', 'неизвестно')
        risk_score = analysis.get('risk_score_estimate', 0)
        
        f.write("2. ОЦЕНКА РИСКОВ\n")
        f.write("─" * 80 + "\n")
        f.write(f"┌{'─' * 40}┐\n")
        f.write(f"│ Уровень риска: {risk_level.upper():^25} │\n")
        f.write(f"│ Числовая оценка: {risk_score}/10{' ' * 21} │\n")
        f.write(f"└{'─' * 40}┘\n\n")
        
        # 3. Резюме
        f.write("3. РЕЗЮМЕ\n")
        f.write("─" * 80 + "\n")
        if 'executive_summary' in analysis:
            summary = str(analysis['executive_summary']) if not isinstance(analysis['executive_summary'], str) else analysis['executive_summary']
            f.write(f"{summary}\n\n")
        
        # 4. Ключевые риски
        f.write("4. КЛЮЧЕВЫЕ РИСКИ\n")
        f.write("─" * 80 + "\n")
        if 'key_risks' in analysis and analysis['key_risks']:
            for i, risk in enumerate(analysis['key_risks'], 1):
                category = risk.get('category', 'Риск')
                severity = risk.get('severity', 'неизвестно')
                description = risk.get('description', '')
                
                f.write(f"{i}. {category} [{severity.upper()}]\n")
                f.write(f"   {description}\n")
                if 'evidence' in risk:
                    f.write(f"   Доказательства: {risk['evidence']}\n")
                f.write("\n")
        else:
            f.write("Ключевые риски не выявлены\n\n")
        
        # 5. Анализ факторов
        f.write("5. АНАЛИЗ ФАКТОРОВ\n")
        f.write("─" * 80 + "\n")
        
        # Тревожные сигналы
        f.write("ТРЕВОЖНЫЕ СИГНАЛЫ:\n")
        if 'red_flags' in analysis and analysis['red_flags']:
            for flag in analysis['red_flags']:
                flag_text = str(flag) if not isinstance(flag, str) else flag
                f.write(f"  ⚠ {flag_text}\n")
        else:
            f.write("  Не выявлено\n")
        f.write("\n")
        
        # Положительные факторы
        f.write("ПОЛОЖИТЕЛЬНЫЕ ФАКТОРЫ:\n")
        if 'positive_factors' in analysis and analysis['positive_factors']:
            for factor in analysis['positive_factors']:
                factor_text = str(factor) if not isinstance(factor, str) else factor
                f.write(f"  ✓ {factor_text}\n")
        else:
            f.write("  Не выявлено\n")
        f.write("\n")
        
        # 6. Рекомендации
        f.write("6. РЕКОМЕНДАЦИИ\n")
        f.write("─" * 80 + "\n")
        if 'recommendations' in analysis and analysis['recommendations']:
            for i, rec in enumerate(analysis['recommendations'], 1):
                rec_text = str(rec) if not isinstance(rec, str) else rec
                f.write(f"{i}. {rec_text}\n")
        else:
            f.write("Рекомендации отсутствуют\n")
        f.write("\n")
        
        # 7. Детальный анализ
        f.write("7. ДЕТАЛЬНЫЙ АНАЛИЗ\n")
        f.write("─" * 80 + "\n")
        if 'detailed_analysis' in analysis:
            detailed = analysis['detailed_analysis']
            
            if isinstance(detailed, dict):
                for key, value in detailed.items():
                    f.write(f"\n{key.upper()}:\n")
                    f.write(f"{value}\n")
            elif isinstance(detailed, list):
                for item in detailed:
                    f.write(f"{str(item)}\n")
            else:
                f.write(f"{str(detailed)}\n")
        f.write("\n")
    
    async def generate_json_report(self, results: List[Dict[str, Any]]) -> str:
        """Генерация JSON отчета"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tender_risk_report_{timestamp}.json"
            filepath = os.path.join(self.reports_dir, filename)
            
            # Подготовка данных для JSON
            report_data = {
                "report_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "generated_date": datetime.now().strftime('%d.%m.%Y'),
                    "generated_time": datetime.now().strftime('%H:%M:%S'),
                    "total_tenders": len(results),
                    "report_version": "1.0",
                    "report_type": "Автоматизированная оценка рисков с применением AI"
                },
                "tenders": results
            }
            
            # Сохранение в JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"JSON отчет создан: {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка создания JSON отчета: {e}")
            raise
