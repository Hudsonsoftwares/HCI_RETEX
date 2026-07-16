from odoo import models, fields, api

class SimpleAccountingDashboard(models.Model):
    _name = 'simple.accounting.dashboard'
    _description = 'Simple Accounting Dashboard'

    name = fields.Char(default='Live Financial Overview', readonly=True)
    
    currency_id = fields.Many2one('res.currency', string='Currency', 
                                  default=lambda self: self.env.company.currency_id, readonly=True)
                                  
    cash_balance = fields.Monetary(string='Counter Cash Balance', compute='_compute_balances', currency_field='currency_id')
    bank_balance = fields.Monetary(string='Bank Balance', compute='_compute_balances', currency_field='currency_id')
    total_profit = fields.Monetary(string='Total Profit (All Time)', compute='_compute_balances', currency_field='currency_id')
    
    today_sale = fields.Monetary(string='Today Sale', compute='_compute_balances', currency_field='currency_id')
    today_expense = fields.Monetary(string='Today Expense', compute='_compute_balances', currency_field='currency_id')
    today_profit = fields.Monetary(string='Today Profit', compute='_compute_balances', currency_field='currency_id')
    today_transaction_count = fields.Integer(string='Today Transactions', compute='_compute_balances')
    
    month_sale = fields.Monetary(string='Month Sale', compute='_compute_balances', currency_field='currency_id')
    month_expense = fields.Monetary(string='Month Expense', compute='_compute_balances', currency_field='currency_id')
    month_profit = fields.Monetary(string='Month Profit', compute='_compute_balances', currency_field='currency_id')
    month_transaction_count = fields.Integer(string='Month Transactions', compute='_compute_balances')
    
    year_sale = fields.Monetary(string='Year Sale', compute='_compute_balances', currency_field='currency_id')
    year_expense = fields.Monetary(string='Year Expense', compute='_compute_balances', currency_field='currency_id')
    year_profit = fields.Monetary(string='Year Profit', compute='_compute_balances', currency_field='currency_id')
    year_transaction_count = fields.Integer(string='Year Transactions', compute='_compute_balances')
    
    def _compute_balances(self):
        for rec in self:
            # All-time cash transactions
            cash_txs = self.env['simple.accounting.transaction'].search([('payment_method', '=', 'cash')])
            rec.cash_balance = sum(cash_txs.mapped('net_impact'))
            
            # All-time bank transactions
            bank_txs = self.env['simple.accounting.transaction'].search([('payment_method', '=', 'bank')])
            rec.bank_balance = sum(bank_txs.mapped('net_impact'))
            
            rec.total_profit = rec.cash_balance + rec.bank_balance
            
            # Context Date
            today_date = fields.Date.context_today(self)
            current_month = today_date.month
            current_year = today_date.year
            
            all_txs = self.env['simple.accounting.transaction'].search([])
            
            # --- TODAY ---
            today_txs = all_txs.filtered(lambda t: fields.Date.context_today(self, t.date) == today_date)
            
            incomes_today = today_txs.filtered(lambda t: t.type == 'income')
            expenses_today = today_txs.filtered(lambda t: t.type == 'expense')
            
            rec.today_transaction_count = len(today_txs)
            rec.today_sale = sum(incomes_today.mapped('amount'))
            
            today_bank_exp = sum(expenses_today.filtered(lambda t: t.payment_method == 'bank').mapped('amount')) + sum(incomes_today.filtered(lambda t: t.payment_method == 'bank').mapped('company_cost'))
            today_cash_exp = sum(expenses_today.filtered(lambda t: t.payment_method == 'cash').mapped('amount')) + sum(incomes_today.filtered(lambda t: t.payment_method == 'cash').mapped('company_cost'))
            today_cod_exp = sum(expenses_today.filtered(lambda t: t.payment_method == 'cod').mapped('amount')) + sum(incomes_today.filtered(lambda t: t.payment_method == 'cod').mapped('amount'))
            rec.today_expense = today_bank_exp + today_cash_exp + today_cod_exp
            rec.today_profit = rec.today_sale - rec.today_expense
            
            # --- THIS MONTH ---
            month_txs = all_txs.filtered(lambda t: fields.Date.context_today(self, t.date).month == current_month and fields.Date.context_today(self, t.date).year == current_year)
            
            incomes_month = month_txs.filtered(lambda t: t.type == 'income')
            expenses_month = month_txs.filtered(lambda t: t.type == 'expense')
            
            rec.month_transaction_count = len(month_txs)
            rec.month_sale = sum(incomes_month.mapped('amount'))
            
            month_bank_exp = sum(expenses_month.filtered(lambda t: t.payment_method == 'bank').mapped('amount')) + sum(incomes_month.filtered(lambda t: t.payment_method == 'bank').mapped('company_cost'))
            month_cash_exp = sum(expenses_month.filtered(lambda t: t.payment_method == 'cash').mapped('amount')) + sum(incomes_month.filtered(lambda t: t.payment_method == 'cash').mapped('company_cost'))
            month_cod_exp = sum(expenses_month.filtered(lambda t: t.payment_method == 'cod').mapped('amount')) + sum(incomes_month.filtered(lambda t: t.payment_method == 'cod').mapped('amount'))
            rec.month_expense = month_bank_exp + month_cash_exp + month_cod_exp
            rec.month_profit = rec.month_sale - rec.month_expense
            
            # --- THIS YEAR ---
            year_txs = all_txs.filtered(lambda t: fields.Date.context_today(self, t.date).year == current_year)
            
            incomes_year = year_txs.filtered(lambda t: t.type == 'income')
            expenses_year = year_txs.filtered(lambda t: t.type == 'expense')
            
            rec.year_transaction_count = len(year_txs)
            rec.year_sale = sum(incomes_year.mapped('amount'))
            
            year_bank_exp = sum(expenses_year.filtered(lambda t: t.payment_method == 'bank').mapped('amount')) + sum(incomes_year.filtered(lambda t: t.payment_method == 'bank').mapped('company_cost'))
            year_cash_exp = sum(expenses_year.filtered(lambda t: t.payment_method == 'cash').mapped('amount')) + sum(incomes_year.filtered(lambda t: t.payment_method == 'cash').mapped('company_cost'))
            year_cod_exp = sum(expenses_year.filtered(lambda t: t.payment_method == 'cod').mapped('amount')) + sum(incomes_year.filtered(lambda t: t.payment_method == 'cod').mapped('amount'))
            rec.year_expense = year_bank_exp + year_cash_exp + year_cod_exp
            rec.year_profit = rec.year_sale - rec.year_expense

    @api.model
    def action_open_dashboard(self):
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({})
            
        return {
            'name': 'Live Dashboard',
            'type': 'ir.actions.act_window',
            'res_model': 'simple.accounting.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'current',
        }
