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
    
    payment_method = fields.Selection([
        ('cash', 'Cash (Counter)'),
        ('bank', 'Bank'),
        ('cod', 'COD (Cash on Delivery)')
    ], string='Payment Method', required=True, default='cash')
    
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """ Force descending order when grouping by date so newest days appear first """
        if not orderby and groupby:
            # Check if any grouping involves the 'date' field
            if any(g.split(':')[0] == 'date' for g in (groupby if isinstance(groupby, list) else [groupby])):
                orderby = 'date desc'
        return super(SimpleAccountingTransaction, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
    
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
    
    company_cost = fields.Monetary(string='Actual Cost', currency_field='currency_id')
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
        

        # 4. Generate Ledger PDF Report
        wizard = self.env['simple.accounting.report.wizard'].sudo().create({
            'report_type': 'custom',
            'start_date': first_day_this_month.date(),
            'end_date': last_day_this_month.date()
        })
        ledger_data = wizard.action_print_report().get('data')
        ledger_pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'simple_accounting.action_report_simple_accounting_ledger',
            res_ids=wizard.ids,
            data=ledger_data
        )
        ledger_pdf_base64 = base64.b64encode(ledger_pdf_content).decode('utf-8')
        
        # 4b. Generate PnL Report
        pnl_wizard = self.env['simple.accounting.pnl.wizard'].sudo().create({
            'report_type': 'custom',
            'start_date': first_day_this_month.date(),
            'end_date': last_day_this_month.date()
        })
        pnl_data = pnl_wizard.action_print_report().get('data')
        pnl_pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'simple_accounting.action_report_simple_accounting_pnl',
            res_ids=pnl_wizard.ids,
            data=pnl_data
        )
        pnl_pdf_base64 = base64.b64encode(pnl_pdf_content).decode('utf-8')

        # 4c. Generate SMSA Settlement Report
        smsa_wizard = self.env['smsa.settlement.report.wizard'].sudo().create({
            'start_date': first_day_this_month.date(),
            'end_date': last_day_this_month.date()
        })
        smsa_data = smsa_wizard.action_print_report().get('data')
        smsa_pdf_content, _ = self.env['ir.actions.report'].sudo()._render_qweb_pdf(
            'simple_accounting.action_report_smsa_settlement',
            res_ids=smsa_wizard.ids,
            data=smsa_data
        )
        smsa_pdf_base64 = base64.b64encode(smsa_pdf_content).decode('utf-8')
        
        # 5. Create Attachments
        ledger_attachment = self.env['ir.attachment'].sudo().create({
            'name': f"Monthly_Ledger_{first_day_this_month.strftime('%B_%Y')}.pdf",
            'type': 'binary',
            'datas': ledger_pdf_base64,
            'res_model': 'simple.accounting.transaction',
            'res_id': 0,
            'mimetype': 'application/pdf'
        })
        
        pnl_attachment = self.env['ir.attachment'].sudo().create({
            'name': f"Monthly_Profit_Loss_{first_day_this_month.strftime('%B_%Y')}.pdf",
            'type': 'binary',
            'datas': pnl_pdf_base64,
            'res_model': 'simple.accounting.transaction',
            'res_id': 0,
            'mimetype': 'application/pdf'
        })
        
        smsa_attachment = self.env['ir.attachment'].sudo().create({
            'name': f"Monthly_SMSA_Settlement_{first_day_this_month.strftime('%B_%Y')}.pdf",
            'type': 'binary',
            'datas': smsa_pdf_base64,
            'res_model': 'simple.accounting.transaction',
            'res_id': 0,
            'mimetype': 'application/pdf'
        })
        
        # 6. Send Email
        recipient_email = 'retexexpresscargo@gmail.com'
            
        if not recipient_email:
            return  # Nowhere to send
            
        month_str = first_day_this_month.strftime('%B %Y')
        subject = f"Monthly Accounting Reports: {month_str}"
        body = f"""
            <div style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>Monthly Accounting Reports</h2>
                <p>Hello,</p>
                <p>Please find attached your monthly accounting reports for <strong>{month_str}</strong>.</p>
                <ul>
                    <li><strong>Monthly Ledger:</strong> Full detailed accounting ledger.</li>
                    <li><strong>Profit and Loss:</strong> Comprehensive monthly summary.</li>
                    <li><strong>SMSA Settlement:</strong> Courier collection calculations.</li>
                </ul>
                <p>Best regards,<br/>Hudson Accounting System</p>
            </div>
        """
        
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': recipient_email,
            'attachment_ids': [(6, 0, [ledger_attachment.id, pnl_attachment.id, smsa_attachment.id])],
            'auto_delete': True,
        }
        self.env['mail.mail'].sudo().create(mail_values).send()
