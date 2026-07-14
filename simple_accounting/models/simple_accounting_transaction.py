from odoo import models, fields, api

class SimpleAccountingTransaction(models.Model):
    _name = 'simple.accounting.transaction'
    _description = 'Accounting Transaction'
    _order = 'date desc, id desc'

    name = fields.Char(string='Description', required=True)
    date = fields.Datetime(string='Date & Time', required=True, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Created By', default=lambda self: self.env.user, readonly=True)
    category_id = fields.Many2one('simple.accounting.category', string='Category', required=True)
    
    type = fields.Selection([
        ('income', 'Income (Credit)'),
        ('expense', 'Expense (Debit)')
    ], string='Type', required=True, default='expense')
    
    # ── Cargo Integration ──────────────────────────────────────────────
    cargo_invoice_id = fields.Many2one('cargo.manual.invoice', string='Cargo Invoice')
    shipper_name = fields.Char(string='Shipper Name')
    mobile = fields.Char(string='Mobile')
    weight = fields.Float(string='Weight')
    destination = fields.Char(string='Destination')
    service = fields.Char(string='Service (Carrier)')
    tracking_no = fields.Char(string='Tracking No')
    cargo_gross_total = fields.Monetary(string='Gross Total (SAR)', currency_field='currency_id')
    # ───────────────────────────────────────────────────────────────────
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id)
    
    company_cost = fields.Monetary(string='Company Cost', currency_field='currency_id')
    selling_price = fields.Monetary(string='Selling Price', currency_field='currency_id')
    amount = fields.Monetary(string='Total Amount', required=True, currency_field='currency_id')
    
    net_impact = fields.Monetary(string='Net Profit / Loss', compute='_compute_net_impact', 
                                 store=True, currency_field='currency_id')

    @api.depends('amount', 'type', 'selling_price', 'company_cost')
    def _compute_net_impact(self):
        for record in self:
            if record.type == 'income':
                record.net_impact = record.selling_price - record.company_cost
            else:
                record.net_impact = -record.amount

    @api.onchange('company_cost', 'selling_price', 'type')
    def _onchange_cost_price(self):
        if self.type == 'income':
            self.amount = self.selling_price

    @api.onchange('category_id')
    def _onchange_category_id(self):
        if self.category_id:
            self.type = self.category_id.type

    @api.onchange('cargo_invoice_id')
    def _onchange_cargo_invoice_id(self):
        if self.cargo_invoice_id:
            # Auto-fill fields from the selected invoice
            self.shipper_name = self.cargo_invoice_id.shipper_name
            self.mobile = self.cargo_invoice_id.shipper_mobile
            self.weight = self.cargo_invoice_id.weight
            
            # Use destination country name if available, else fallback
            if self.cargo_invoice_id.destination_country_id:
                self.destination = self.cargo_invoice_id.destination_country_id.name
            else:
                self.destination = self.cargo_invoice_id.destination
                
            self.service = self.cargo_invoice_id.carrier
            self.tracking_no = self.cargo_invoice_id.airway_bill
            self.cargo_gross_total = self.cargo_invoice_id.gross_total

    @api.model
    def _migrate_income_amounts(self):
        incomes = self.search([('type', '=', 'income'), ('selling_price', '=', 0.0)])
        for inc in incomes:
            inc.selling_price = inc.amount
            inc.company_cost = 0.0
