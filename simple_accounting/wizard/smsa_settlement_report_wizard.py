from odoo import models, fields, api
from datetime import datetime, time

class SmsaSettlementReportWizard(models.TransientModel):
    _name = 'smsa.settlement.report.wizard'
    _description = 'SMSA Settlement Report Wizard'

    start_date = fields.Date(string='Start Date', required=True, default=fields.Date.context_today)
    end_date = fields.Date(string='End Date', required=True, default=fields.Date.context_today)

    def action_print_report(self):
        self.ensure_one()
        end_datetime = datetime.combine(self.end_date, time.max)
        
        # Only fetch SMSA related transactions. Assuming all cargo transactions with tracking or service=SMSA.
        # But wait, earlier the user said "4 inv has delivery partner as smsa...". 
        # Actually, in simple accounting, we can just fetch all incomes that have a cargo invoice attached, or simply all transactions in the date range that have company_cost > 0.
        # For simplicity, we'll fetch all transactions.
        domain = [
            ('date', '>=', self.start_date),
            ('date', '<=', end_datetime),
            ('type', '=', 'income'),
            ('cargo_invoice_id.delivery_partner', '=', 'smsa')
        ]
        transactions = self.env['simple.accounting.transaction'].search(domain, order='date asc')
        
        # Calculate totals
        cash_bank_txs = transactions.filtered(lambda t: t.payment_method in ['cash', 'bank'])
        cod_txs = transactions.filtered(lambda t: t.payment_method == 'cod')
        
        # 1. Total service charges owed to SMSA (for Cash and Bank packages)
        total_cash_bank_fees = sum(cash_bank_txs.mapped('company_cost'))
        
        # 2. Total COD profits held by SMSA (which reduces the bill)
        total_cod_profits = sum(cod_txs.mapped('net_impact'))
        
        # 3. COD Total Costs (just for reporting display)
        total_cod_fees = sum(cod_txs.mapped('company_cost'))
        
        # 4. Total Collected by SMSA (The full Bill Amount)
        total_cod_collected = sum(cod_txs.mapped('amount'))
        
        # New simplified math: 
        # Bill = (Total Fees for ALL packages) - (Total Money SMSA physically collected from COD)
        total_service_charges = total_cash_bank_fees + total_cod_fees
        net_owed = total_service_charges - total_cod_collected
        
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_name': self.env.company.name,
            'currency': self.env.company.currency_id.symbol,
            'print_time': fields.Datetime.now(),
            
            'cash_bank_txs': cash_bank_txs.read(['date', 'name', 'cargo_invoice_id', 'shipper_name', 'tracking_no', 'payment_method', 'amount', 'company_cost', 'net_impact']),
            'cod_txs': cod_txs.read(['date', 'name', 'cargo_invoice_id', 'shipper_name', 'tracking_no', 'payment_method', 'amount', 'company_cost', 'net_impact']),
            
            'total_cash_bank_fees': total_cash_bank_fees,
            'total_cod_profits': total_cod_profits,
            'total_cod_fees': total_cod_fees,
            'total_cod_collected': total_cod_collected,
            'net_owed': net_owed,
            
            'total_service_charges': total_cash_bank_fees + total_cod_fees,
        }
        
        return self.env.ref('simple_accounting.action_report_smsa_settlement').report_action(self, data=data)
