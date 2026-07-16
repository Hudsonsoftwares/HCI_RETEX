from odoo import models, fields, api
from datetime import date, datetime, time
from dateutil.relativedelta import relativedelta

class SimpleAccountingPnlWizard(models.TransientModel):
    _name = 'simple.accounting.pnl.wizard'
    _description = 'Profit and Loss Report Wizard'

    report_type = fields.Selection([
        ('today', 'Today'),
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
        if self.report_type == 'today':
            self.start_date = today
            self.end_date = today
        elif self.report_type == 'this_week':
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
        
        end_datetime = datetime.combine(self.end_date, time.max)
        start_datetime = datetime.combine(self.start_date, time.min)
        
        domain = [
            ('date', '>=', start_datetime),
            ('date', '<=', end_datetime)
        ]
        
        transactions = self.env['simple.accounting.transaction'].search(domain, order='date asc')
        
        incomes = transactions.filtered(lambda t: t.type == 'income')
        expenses = transactions.filtered(lambda t: t.type == 'expense')
        
        total_sales = sum(incomes.mapped('amount'))
        
        # Expenses + Cargo cost portions
        bank_exp = sum(expenses.filtered(lambda t: t.payment_method == 'bank').mapped('amount')) + sum(incomes.filtered(lambda t: t.payment_method == 'bank').mapped('company_cost'))
        cash_exp = sum(expenses.filtered(lambda t: t.payment_method == 'cash').mapped('amount')) + sum(incomes.filtered(lambda t: t.payment_method == 'cash').mapped('company_cost'))
        cod_exp = sum(expenses.filtered(lambda t: t.payment_method == 'cod').mapped('amount')) + sum(incomes.filtered(lambda t: t.payment_method == 'cod').mapped('amount'))
        
        total_expenses = bank_exp + cash_exp + cod_exp
        net_profit = total_sales - total_expenses
        
        data = {
            'form': {
                'start_date': self.start_date,
                'end_date': self.end_date,
                'report_type': dict(self._fields['report_type'].selection).get(self.report_type),
            },
            'summary': {
                'total_sales': total_sales,
                'total_expenses': total_expenses,
                'net_profit': net_profit,
            },
            'transactions': transactions.read(['date', 'name', 'payment_method', 'type', 'amount', 'company_cost']),
            'current_user': self.env.user.name,
            'print_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        
        return self.env.ref('simple_accounting.action_report_simple_accounting_pnl').report_action(self, data=data)


