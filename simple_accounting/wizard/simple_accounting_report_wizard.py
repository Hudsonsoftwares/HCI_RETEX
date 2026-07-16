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
        
        # Group by day
        from collections import defaultdict
        
        daily_groups = defaultdict(list)
        for tx in transactions:
            daily_groups[tx.date.date()].append(tx)
            
        sorted_days = sorted(daily_groups.keys())
        days_data = []
        
        for day in sorted_days:
            day_txs = self.env['simple.accounting.transaction'].browse([t.id for t in daily_groups[day]])
            
            day_start_datetime = datetime.combine(day, time.min)
            
            # Opening Cash Balance
            past_cash_txs = self.env['simple.accounting.transaction'].search([
                ('date', '<', day_start_datetime),
                ('payment_method', '=', 'cash')
            ])
            cash_opening_balance = sum(past_cash_txs.mapped('net_impact'))
            
            # Bank Opening Balance
            past_bank_txs = self.env['simple.accounting.transaction'].search([
                ('date', '<', day_start_datetime),
                ('payment_method', '=', 'bank')
            ])
            bank_opening_balance = sum(past_bank_txs.mapped('net_impact'))
            
            # Remin Sale (Monthly)
            month_start_datetime = datetime.combine(day.replace(day=1), time.min)
            past_month_sales = self.env['simple.accounting.transaction'].search([
                ('date', '>=', month_start_datetime),
                ('date', '<', day_start_datetime),
                ('type', '=', 'income')
            ])
            remin_sale = sum(past_month_sales.mapped('amount'))
            
            # Today's Breakdown
            income_txs = day_txs.filtered(lambda t: t.type == 'income')
            expense_txs = day_txs.filtered(lambda t: t.type == 'expense')
            
            today_sale = sum(income_txs.mapped('amount'))
            today_expense = sum(expense_txs.mapped('amount')) + sum(income_txs.mapped('company_cost'))
            
            today_bank_income = sum(income_txs.filtered(lambda t: t.payment_method == 'bank').mapped('amount'))
            today_cash_income = sum(income_txs.filtered(lambda t: t.payment_method == 'cash').mapped('amount'))
            today_cod_income = sum(income_txs.filtered(lambda t: t.payment_method == 'cod').mapped('amount'))
            
            today_bank_expense = sum(expense_txs.filtered(lambda t: t.payment_method == 'bank').mapped('amount')) + sum(income_txs.filtered(lambda t: t.payment_method == 'bank').mapped('company_cost'))
            today_cash_expense = sum(expense_txs.filtered(lambda t: t.payment_method == 'cash').mapped('amount')) + sum(income_txs.filtered(lambda t: t.payment_method == 'cash').mapped('company_cost'))
            
            # COD Expense: Explicitly log the entire Amount of COD incomes as an expense, because SMSA keeps the whole amount
            today_cod_expense = sum(expense_txs.filtered(lambda t: t.payment_method == 'cod').mapped('amount')) + sum(income_txs.filtered(lambda t: t.payment_method == 'cod').mapped('amount'))
            
            # Ensure the total expense includes the COD expense (profit)
            today_expense = today_bank_expense + today_cash_expense + today_cod_expense
            
            expense_lines = []
            for tx in expense_txs:
                expense_lines.append({'name': tx.category_id.name if tx.category_id else tx.name, 'amount': tx.amount})
            for tx in income_txs:
                if tx.company_cost > 0:
                    expense_lines.append({'name': f"Cost: {tx.category_id.name if tx.category_id else tx.name}", 'amount': tx.company_cost})
                    
            condensed_expenses = defaultdict(float)
            for ex in expense_lines:
                condensed_expenses[ex['name']] += ex['amount']
            expense_breakdown = [{'name': k, 'amount': v} for k, v in condensed_expenses.items() if v > 0]
            
            today_cash_balance = today_cash_income - today_cash_expense
            cash_closing_balance = cash_opening_balance + today_cash_balance
            
            today_bank = today_bank_income - today_bank_expense
            bank_closing_balance = bank_opening_balance + today_bank
            
            # Ensure transactions are serialized correctly for qweb
            tx_data = []
            for t in day_txs:
                tx_data.append({
                    'date': t.date.strftime('%d/%m/%Y') if t.date else '',
                    'name': t.name,
                    'cargo_invoice_id': t.cargo_invoice_id.display_name if t.cargo_invoice_id else '',
                    'shipper_name': t.shipper_name or '',
                    'mobile': t.mobile or '',
                    'weight': t.weight or '',
                    'destination': t.destination or '',
                    'service': t.service or '',
                    'tracking_no': t.tracking_no or '',
                    'amount': t.amount,
                    'company_cost': t.company_cost,
                    'type': t.type,
                    'payment_method': t.payment_method,
                    'net_impact': t.net_impact,
                })
            
            days_data.append({
                'date_str': day.strftime('%d-%b-%y').upper(),
                'transactions': tx_data,
                'bank_opening_balance': bank_opening_balance,
                'today_bank': today_bank,
                'bank_closing_balance': bank_closing_balance,
                'remin_sale': remin_sale,
                'today_sale': today_sale,
                'total_sale': remin_sale + today_sale,
                'cash_opening_balance': cash_opening_balance,
                'today_cash_balance': today_cash_balance,
                'cash_closing_balance': cash_closing_balance,
                'today_expense_total': today_expense,
                'today_cash_income': today_cash_income,
                'today_bank_income': today_bank_income,
                'today_cod_income': today_cod_income,
                'today_bank_expense': today_bank_expense,
                'today_cash_expense': today_cash_expense,
                'today_cod_expense': today_cod_expense,
                'expense_breakdown': expense_breakdown,
            })
            
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'days_data': days_data,
            'company_name': self.env.company.name,
            'currency': self.env.company.currency_id.symbol,
            'print_time': fields.Datetime.now(),
            'current_user': self.env.user.name,
        }
        
        # Prepare the report action
        return self.env.ref('simple_accounting.action_report_simple_accounting_ledger').report_action(self, data=data)
