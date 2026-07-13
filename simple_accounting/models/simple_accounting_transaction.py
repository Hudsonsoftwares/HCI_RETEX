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

    @api.model
    def _migrate_income_amounts(self):
        incomes = self.search([('type', '=', 'income'), ('selling_price', '=', 0.0)])
        for inc in incomes:
            inc.selling_price = inc.amount
            inc.company_cost = 0.0
