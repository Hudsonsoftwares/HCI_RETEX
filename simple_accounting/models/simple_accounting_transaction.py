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
    selling_price = fields.Monetary(string='Bill Amount', currency_field='currency_id')
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

    @api.model
    def _cron_send_monthly_report(self):
        import base64
        import csv
        import io
        from datetime import datetime
        from dateutil.relativedelta import relativedelta
        
        # 1. Get dates for current month
        today = datetime.now()
        first_day_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_this_month = first_day_this_month + relativedelta(months=1, seconds=-1)
        
        # 2. Search transactions
        transactions = self.sudo().search([
            ('date', '>=', first_day_this_month),
            ('date', '<=', last_day_this_month)
        ], order='date asc')
        
        # Calculate totals
        total_income = sum(transactions.filtered(lambda t: t.type == 'income').mapped('amount'))
        total_expense = sum(transactions.filtered(lambda t: t.type == 'expense').mapped('amount'))
        net_profit = sum(transactions.mapped('net_impact'))
        
        # 3. Generate CSV (Excel-compatible)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Description', 'Category', 'Type', 'Amount', 'Company Cost', 'Net Profit / Loss', 'Cargo Invoice', 'Shipper', 'Mobile', 'Created By'])
        
        for tx in transactions:
            writer.writerow([
                tx.date.strftime('%Y-%m-%d %H:%M:%S') if tx.date else '',
                tx.name or '',
                tx.category_id.name if tx.category_id else '',
                dict(self._fields['type'].selection).get(tx.type, ''),
                tx.amount,
                tx.company_cost,
                tx.net_impact,
                tx.cargo_invoice_id.display_name if tx.cargo_invoice_id else '',
                tx.shipper_name or '',
                tx.mobile or '',
                tx.user_id.name if tx.user_id else ''
            ])
            
        writer.writerow([])
        writer.writerow(['SUMMARY', '', '', '', '', '', ''])
        writer.writerow(['Total Income', total_income])
        writer.writerow(['Total Expenses', total_expense])
        writer.writerow(['Net Profit / Loss', net_profit])
        
        csv_content = output.getvalue()
        csv_base64 = base64.b64encode(csv_content.encode('utf-8')).decode('utf-8')
        
        # 4. Generate PDF Report via Wizard logic
        wizard = self.env['simple.accounting.report.wizard'].sudo().create({
            'report_type': 'custom',
            'start_date': first_day_this_month.date(),
            'end_date': last_day_this_month.date()
        })
        
        from odoo import fields
        data = {
            'start_date': wizard.start_date,
            'end_date': wizard.end_date,
            'transactions': transactions.read(['date', 'name', 'cargo_invoice_id', 'user_id', 'category_id', 'type', 'amount', 'company_cost', 'net_impact']),
            'total_income': total_income,
            'total_expense': total_expense,
            'net_profit': net_profit,
            'company_name': self.env.company.name,
            'currency': self.env.company.currency_id.symbol,
            'print_time': fields.Datetime.now(),
        }
        
        pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'simple_accounting.action_report_simple_accounting_ledger',
            res_ids=wizard.ids,
            data=data
        )
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        # 5. Create Attachments
        csv_report_name = f"Monthly_Accounting_Report_{first_day_this_month.strftime('%B_%Y')}.csv"
        csv_attachment = self.env['ir.attachment'].sudo().create({
            'name': csv_report_name,
            'type': 'binary',
            'datas': csv_base64,
            'res_model': 'simple.accounting.transaction',
            'res_id': 0,
            'mimetype': 'text/csv'
        })
        
        pdf_report_name = f"Monthly_Ledger_{first_day_this_month.strftime('%B_%Y')}.pdf"
        pdf_attachment = self.env['ir.attachment'].sudo().create({
            'name': pdf_report_name,
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'simple.accounting.transaction',
            'res_id': 0,
            'mimetype': 'application/pdf'
        })
        
        # 6. Send Email
        recipient_email = 'retexexpresscargo@gmail.com'
            
        if not recipient_email:
            return  # Nowhere to send
            
        month_str = first_day_this_month.strftime('%B %Y')
        subject = f"Monthly Accounting Report: {month_str}"
        body = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Monthly Accounting Report</h2>
                <p>Hello,</p>
                <p>Please find attached the accounting ledger and spreadsheet for <strong>{month_str}</strong>.</p>
                <table style="border-collapse: collapse; width: 50%; margin-top: 20px; margin-bottom: 20px;">
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total Income</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_income:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Total Expenses</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: right;">{total_expense:,.2f}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px; font-weight: bold; font-size: 1.1em;">Net Profit / Loss</td>
                        <td style="border: 1px solid #ddd; padding: 8px; text-align: right; font-weight: bold; font-size: 1.1em; color: {'#16a34a' if net_profit >= 0 else '#dc2626'};">{net_profit:,.2f}</td>
                    </tr>
                </table>
                <p>Best regards,<br/>Hudson Accounting System</p>
            </div>
        """
        
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': recipient_email,
            'attachment_ids': [(6, 0, [csv_attachment.id, pdf_attachment.id])],
            'auto_delete': True,
        }
        self.env['mail.mail'].sudo().create(mail_values).send()
