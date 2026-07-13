from odoo import models, fields, api
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

class SimpleAccountingReportWizard(models.TransientModel):
    _name = 'simple.accounting.report.wizard'
    _description = 'Generate Accounting Ledger'

    report_type = fields.Selection([
        ('this_week', 'This Week'),
        ('this_month', 'This Month'),
        ('this_year', 'This Year'),
        ('custom', 'Custom Range')
    ], string='Report Type', default='this_month', required=True)

    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)

    @api.onchange('report_type')
    def _onchange_report_type(self):
        today = date.today()
        if self.report_type == 'this_week':
            self.start_date = today - relativedelta(days=today.weekday())
            self.end_date = self.start_date + relativedelta(days=6)
        elif self.report_type == 'this_month':
            self.start_date = today.replace(day=1)
            self.end_date = self.start_date + relativedelta(months=1, days=-1)
        elif self.report_type == 'this_year':
            self.start_date = today.replace(month=1, day=1)
            self.end_date = today.replace(month=12, day=31)

    def action_print_report(self):
        self.ensure_one()
        # Find all transactions in range up to the end of the day
        end_datetime = datetime.combine(self.end_date, time.max)
        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', end_datetime)
        ]
        transactions = self.env['simple.accounting.transaction'].search(domain, order='date asc')
        
        income_txs = transactions.filtered(lambda t: t.type == 'income')
        expense_txs = transactions.filtered(lambda t: t.type == 'expense')
        
        total_income = sum(income_txs.mapped('amount'))
        total_expense = sum(expense_txs.mapped('amount')) + sum(income_txs.mapped('company_cost'))
        net_profit = sum(transactions.mapped('net_impact'))
        
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'transactions': transactions.read(['date', 'name', 'user_id', 'category_id', 'type', 'amount', 'company_cost', 'net_impact']),
            'total_income': total_income,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'company_name': self.env.company.name,
            'currency': self.env.company.currency_id.symbol,
            'print_time': fields.Datetime.now(),
        }
        
        # Prepare the report action
        return self.env.ref('simple_accounting.action_report_simple_accounting_ledger').report_action(self, data=data)
