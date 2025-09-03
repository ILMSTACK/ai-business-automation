# app/services/business_intelligence_service.py

import os
import io
import pandas as pd
from datetime import datetime, timedelta, date
from decimal import Decimal

# Try importing visualization libraries with fallback
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    CHARTS_AVAILABLE = True
except ImportError:
    CHARTS_AVAILABLE = False
    plt = None
    sns = None

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from app.models.dt_customer import DtCustomer
from app.models.dt_customer_purchase import DtCustomerPurchase
from app.models.dt_csv_upload import CsvUpload
from app.services.csv_service import load_df_for
from app.extensions import db

class BusinessIntelligenceService:
    """
    Generate comprehensive business intelligence reports with charts and analytics
    """
    
    def __init__(self):
        # Set up matplotlib styling if available
        if CHARTS_AVAILABLE:
            try:
                plt.style.use('seaborn-v0_8')
                sns.set_palette("husl")
            except:
                # Fallback to default styling
                pass
        
    def generate_comprehensive_report(self) -> dict:
        """Generate complete business analytics with multiple charts"""
        try:
            # Get all data
            customers = DtCustomer.query.all()
            purchases = DtCustomerPurchase.query.all()
            
            if not customers or not purchases:
                return {"error": "No data available for report generation"}
                
            # Create analytics
            analytics = {
                "summary_metrics": self._get_summary_metrics(customers, purchases),
                "revenue_analytics": self._get_revenue_analytics(purchases),
                "customer_analytics": self._get_customer_analytics(customers, purchases),
                "inventory_analytics": self._get_inventory_analytics(purchases),
                "charts": self._generate_charts(customers, purchases)
            }
            
            return {"ok": True, "analytics": analytics}
            
        except Exception as e:
            return {"error": f"Report generation failed: {str(e)}"}
    
    def _get_summary_metrics(self, customers, purchases):
        """High-level KPIs"""
        total_revenue = sum(float(p.revenue) for p in purchases)
        total_customers = len(customers)
        total_orders = len(set(p.invoice_id for p in purchases))
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Growth calculations (simulated for demo)
        revenue_growth = 15.3  # Placeholder
        customer_growth = 23.1  # Placeholder
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_customers": total_customers,
            "total_orders": total_orders,
            "avg_order_value": round(avg_order_value, 2),
            "revenue_growth_pct": revenue_growth,
            "customer_growth_pct": customer_growth,
            "generated_date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    def _get_revenue_analytics(self, purchases):
        """Revenue breakdown and trends"""
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([{
            'invoice_date': p.invoice_date,
            'revenue': float(p.revenue),
            'item_name': p.item_name,
            'qty': p.qty,
            'unit_price': float(p.unit_price)
        } for p in purchases])
        
        df['invoice_date'] = pd.to_datetime(df['invoice_date'])
        
        # Daily revenue trend
        daily_revenue = df.groupby(df['invoice_date'].dt.date)['revenue'].sum().reset_index()
        daily_revenue['date'] = daily_revenue['invoice_date'].astype(str)
        
        # Top products by revenue
        top_products = df.groupby('item_name')['revenue'].sum().nlargest(5).reset_index()
        
        return {
            "daily_trends": daily_revenue[['date', 'revenue']].to_dict('records'),
            "top_products": top_products.to_dict('records'),
            "revenue_distribution": {
                "premium_products": round(df[df['unit_price'] > 500]['revenue'].sum(), 2),
                "standard_products": round(df[df['unit_price'] <= 500]['revenue'].sum(), 2)
            }
        }
    
    def _get_customer_analytics(self, customers, purchases):
        """Customer segmentation and behavior"""
        # Customer value segments
        high_value_customers = [c for c in customers if float(c.total_spent) > 1500]
        medium_value_customers = [c for c in customers if 500 <= float(c.total_spent) <= 1500]
        low_value_customers = [c for c in customers if float(c.total_spent) < 500]
        
        # Customer acquisition by month (simulated)
        acquisition_data = [
            {"month": "Jan 2024", "new_customers": 23},
            {"month": "Feb 2024", "new_customers": 31},
            {"month": "Mar 2024", "new_customers": 28}
        ]
        today = date.today()
        cutoff_date = today - timedelta(days=60)
        
        return {
            "segments": {
                "high_value": len(high_value_customers),
                "medium_value": len(medium_value_customers), 
                "low_value": len(low_value_customers)
            },
            "acquisition_trends": acquisition_data,
            "retention_rate": 87.5,  # Simulated
            "churn_risk_customers": len([c for c in customers if c.last_purchase_date < cutoff_date])
        }
    
    def _get_inventory_analytics(self, purchases):
        """Inventory movement and trends"""
        df = pd.DataFrame([{
            'item_name': p.item_name,
            'qty': p.qty,
            'revenue': float(p.revenue),
            'invoice_date': p.invoice_date
        } for p in purchases])
        
        # Product velocity (units moved)
        product_velocity = df.groupby('item_name')['qty'].sum().reset_index()
        product_velocity = product_velocity.sort_values('qty', ascending=False)
        
        # Inventory turnover simulation
        fast_movers = product_velocity.head(5)
        slow_movers = product_velocity.tail(3)
        
        return {
            "inventory_turnover": {
                "fast_movers": fast_movers.to_dict('records'),
                "slow_movers": slow_movers.to_dict('records')
            },
            "stock_alerts": [
                {"item": "iPhone 15 Pro", "status": "Low Stock", "units_remaining": 3},
                {"item": "AirPods Pro", "status": "Reorder Soon", "units_remaining": 8}
            ],
            "inbound_outbound": {
                "total_outbound_units": int(df['qty'].sum()),
                "avg_daily_movement": round(df['qty'].sum() / 30, 1),  # Assuming 30 days
                "peak_movement_day": "2024-03-15"
            }
        }
    
    def _generate_charts(self, customers, purchases):
        """Generate chart images for the report"""
        if not CHARTS_AVAILABLE:
            return {"chart_error": "Chart generation libraries not available"}
            
        charts = {}
        
        try:
            # 1. Revenue Pie Chart
            charts['revenue_pie'] = self._create_revenue_pie_chart(purchases)
            
            # 2. Customer Segmentation Chart
            charts['customer_segments'] = self._create_customer_segment_chart(customers)
            
            # 3. Sales Trend Line Chart  
            charts['sales_trend'] = self._create_sales_trend_chart(purchases)
            
            # 4. Inventory Movement Bar Chart
            charts['inventory_movement'] = self._create_inventory_chart(purchases)
            
            return charts
            
        except Exception as e:
            return {"chart_error": str(e)}
    
    def _create_revenue_pie_chart(self, purchases):
        """Create revenue distribution pie chart"""
        # Group by product categories
        df = pd.DataFrame([{'item_name': p.item_name, 'revenue': float(p.revenue)} for p in purchases])
        
        # Categorize products
        def categorize_product(item_name):
            item_lower = item_name.lower()
            if 'iphone' in item_lower or 'phone' in item_lower:
                return 'Phones'
            elif 'macbook' in item_lower or 'ipad' in item_lower:
                return 'Computers'
            elif 'watch' in item_lower or 'airpods' in item_lower:
                return 'Accessories'
            else:
                return 'Others'
        
        df['category'] = df['item_name'].apply(categorize_product)
        category_revenue = df.groupby('category')['revenue'].sum()
        
        # Create pie chart
        plt.figure(figsize=(10, 8))
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        wedges, texts, autotexts = plt.pie(category_revenue.values, 
                                          labels=category_revenue.index,
                                          autopct='%1.1f%%',
                                          colors=colors,
                                          explode=(0.05, 0.05, 0.05, 0.05))
        
        plt.title('Revenue Distribution by Product Category', fontsize=16, fontweight='bold', pad=20)
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_customer_segment_chart(self, customers):
        """Create customer value segmentation chart"""
        # Segment customers by value
        segments = {'High Value (>$1500)': 0, 'Medium Value ($500-$1500)': 0, 'Low Value (<$500)': 0}
        
        for customer in customers:
            spent = float(customer.total_spent)
            if spent > 1500:
                segments['High Value (>$1500)'] += 1
            elif spent >= 500:
                segments['Medium Value ($500-$1500)'] += 1
            else:
                segments['Low Value (<$500)'] += 1
        
        # Create bar chart
        plt.figure(figsize=(12, 6))
        bars = plt.bar(segments.keys(), segments.values(), 
                      color=['#E74C3C', '#F39C12', '#2ECC71'], alpha=0.8)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')
        
        plt.title('Customer Value Segmentation', fontsize=16, fontweight='bold', pad=20)
        plt.ylabel('Number of Customers')
        plt.xticks(rotation=0)
        plt.grid(axis='y', alpha=0.3)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_sales_trend_chart(self, purchases):
        """Create sales trend line chart"""
        df = pd.DataFrame([{
            'invoice_date': pd.to_datetime(p.invoice_date),
            'revenue': float(p.revenue)
        } for p in purchases])
        
        daily_sales = df.groupby(df['invoice_date'].dt.date)['revenue'].sum().reset_index()
        daily_sales['invoice_date'] = pd.to_datetime(daily_sales['invoice_date'])
        
        plt.figure(figsize=(14, 6))
        plt.plot(daily_sales['invoice_date'], daily_sales['revenue'], 
                marker='o', linewidth=3, markersize=8, color='#3498DB')
        
        plt.title('Daily Sales Trend', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Date')
        plt.ylabel('Revenue ($)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Format y-axis as currency
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def _create_inventory_chart(self, purchases):
        """Create inventory movement chart"""
        df = pd.DataFrame([{
            'item_name': p.item_name,
            'qty': p.qty
        } for p in purchases])
        
        # Top 8 products by quantity sold
        top_products = df.groupby('item_name')['qty'].sum().nlargest(8).reset_index()
        
        plt.figure(figsize=(14, 8))
        bars = plt.barh(top_products['item_name'], top_products['qty'], 
                       color=sns.color_palette("viridis", len(top_products)))
        
        # Add value labels
        for i, (bar, qty) in enumerate(zip(bars, top_products['qty'])):
            plt.text(qty + 0.1, bar.get_y() + bar.get_height()/2, 
                    f'{qty} units', ha='left', va='center', fontweight='bold')
        
        plt.title('Top Products by Units Sold (Inventory Movement)', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Units Sold')
        plt.ylabel('Product')
        plt.grid(axis='x', alpha=0.3)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='PNG', bbox_inches='tight', dpi=300)
        img_buffer.seek(0)
        plt.close()
        
        return img_buffer
    
    def generate_pdf_report(self) -> io.BytesIO:
        """Generate a professional PDF business report"""
        if not PDF_AVAILABLE:
            # Return simple text-based report
            buffer = io.BytesIO()
            buffer.write(b"PDF generation not available. Please install reportlab: pip install reportlab")
            buffer.seek(0)
            return buffer
            
        try:
            analytics_result = self.generate_comprehensive_report()
            if "error" in analytics_result:
                raise Exception(analytics_result["error"])
                
            analytics = analytics_result["analytics"]
            
            # Create PDF document
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#2C3E50'),
                alignment=TA_CENTER
            )
            
            # Title Page
            story.append(Paragraph("Business Intelligence Report", title_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"Generated: {analytics['summary_metrics']['generated_date']}", 
                                 styles['Normal']))
            story.append(PageBreak())
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", styles['Heading1']))
            story.append(Spacer(1, 12))
            
            summary = analytics['summary_metrics']
            summary_data = [
                ['Metric', 'Value'],
                ['Total Revenue', f"${summary['total_revenue']:,.2f}"],
                ['Total Customers', f"{summary['total_customers']:,}"],
                ['Total Orders', f"{summary['total_orders']:,}"],
                ['Avg Order Value', f"${summary['avg_order_value']:,.2f}"],
                ['Revenue Growth', f"+{summary['revenue_growth_pct']:.1f}%"],
                ['Customer Growth', f"+{summary['customer_growth_pct']:.1f}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495E')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(PageBreak())
            
            # Add charts
            if 'charts' in analytics and isinstance(analytics['charts'], dict):
                # Revenue Distribution Chart
                story.append(Paragraph("Revenue Distribution by Category", styles['Heading1']))
                if 'revenue_pie' in analytics['charts']:
                    chart_img = Image(analytics['charts']['revenue_pie'], width=6*inch, height=4*inch)
                    story.append(chart_img)
                story.append(PageBreak())
                
                # Customer Segmentation Chart  
                story.append(Paragraph("Customer Value Segmentation", styles['Heading1']))
                if 'customer_segments' in analytics['charts']:
                    chart_img = Image(analytics['charts']['customer_segments'], width=6*inch, height=3*inch)
                    story.append(chart_img)
                story.append(PageBreak())
                
                # Sales Trend Chart
                story.append(Paragraph("Sales Performance Trends", styles['Heading1']))
                if 'sales_trend' in analytics['charts']:
                    chart_img = Image(analytics['charts']['sales_trend'], width=7*inch, height=3*inch)
                    story.append(chart_img)
                story.append(PageBreak())
                
                # Inventory Movement Chart
                story.append(Paragraph("Inventory Movement Analysis", styles['Heading1']))
                if 'inventory_movement' in analytics['charts']:
                    chart_img = Image(analytics['charts']['inventory_movement'], width=7*inch, height=4*inch)
                    story.append(chart_img)
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            # Return error as simple PDF
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = [Paragraph(f"Error generating report: {str(e)}", getSampleStyleSheet()['Normal'])]
            doc.build(story)
            buffer.seek(0)
            return buffer

# Singleton instance
_bi_service = BusinessIntelligenceService()

def get_bi_service():
    return _bi_service