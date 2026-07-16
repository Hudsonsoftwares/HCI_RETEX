from odoo import models, fields, api

class CargoDashboard(models.Model):
    _name = 'cargo.dashboard'
    _description = 'Cargo Invoicing Dashboard'

    name = fields.Char(default='Live Operations Overview', readonly=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id, readonly=True)
                                  
    total_revenue = fields.Monetary(string='Total Revenue (All Time)', compute='_compute_metrics', currency_field='currency_id')
    total_invoice_count = fields.Integer(string='Total Invoices (All Time)', compute='_compute_metrics')
    
    today_revenue = fields.Monetary(string='Today Revenue', compute='_compute_metrics', currency_field='currency_id')
    today_invoice_count = fields.Integer(string='Today Invoices', compute='_compute_metrics')
    
    month_revenue = fields.Monetary(string='Month Revenue', compute='_compute_metrics', currency_field='currency_id')
    month_invoice_count = fields.Integer(string='Month Invoices', compute='_compute_metrics')
    
    year_revenue = fields.Monetary(string='Year Revenue', compute='_compute_metrics', currency_field='currency_id')
    year_invoice_count = fields.Integer(string='Year Invoices', compute='_compute_metrics')
    
    def _compute_metrics(self):
        for rec in self:
            all_invoices = self.env['cargo.manual.invoice'].search([])
            
            # All-time
            rec.total_revenue = sum(all_invoices.mapped('gross_total'))
            rec.total_invoice_count = len(all_invoices)
            
            # Context Date
            today_date = fields.Date.context_today(self)
            current_month = today_date.month
            current_year = today_date.year
            
            # --- TODAY ---
            today_invoices = all_invoices.filtered(lambda i: i.shipping_date and i.shipping_date.date() == today_date)
            rec.today_revenue = sum(today_invoices.mapped('gross_total'))
            rec.today_invoice_count = len(today_invoices)
            
            # --- THIS MONTH ---
            month_invoices = all_invoices.filtered(lambda i: i.shipping_date and i.shipping_date.date().month == current_month and i.shipping_date.date().year == current_year)
            rec.month_revenue = sum(month_invoices.mapped('gross_total'))
            rec.month_invoice_count = len(month_invoices)
            
            # --- THIS YEAR ---
            year_invoices = all_invoices.filtered(lambda i: i.shipping_date and i.shipping_date.date().year == current_year)
            rec.year_revenue = sum(year_invoices.mapped('gross_total'))
            rec.year_invoice_count = len(year_invoices)
