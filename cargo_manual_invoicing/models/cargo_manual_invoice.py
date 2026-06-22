from odoo import models, fields, api
# pyrefly: ignore [missing-import]
from odoo.exceptions import ValidationError
import re


class CargoManualInvoice(models.Model):
    _name = 'cargo.manual.invoice'
    _description = 'Cargo Manual Invoice'
    _order = 'id desc'
    _rec_name = 'invoice_number'

    # ── System & Metadata ──────────────────────────────────────────────
    invoice_number = fields.Char(
        string='Invoice Number',
        readonly=True,
        copy=False,
        default='New',
    )
    shipping_date = fields.Datetime(
        string='Shipping Date',
        default=fields.Datetime.now,
        required=True,
    )
    shipment_type = fields.Selection(
        [('domestic', 'Domestic'), ('international', 'International')],
        string='Shipment Type',
        default='international',
        required=True,
    )
    agent_name = fields.Char(
        string='User',
        default=lambda self: self.env.user.name,
        readonly=True,
    )

    # ── Shipper Info ───────────────────────────────────────────────────
    origin = fields.Char(string='Origin', default='Saudi Arabia Riyadh', required=True)
    shipper_name = fields.Char(string='Shipper Name', required=True)
    shipper_mobile = fields.Char(string='Mobile', required=True)
    shipper_tel = fields.Char(string='Tel')
    shipper_id_no = fields.Char(string='ID No')
    shipper_company = fields.Char(string='Company')
    shipper_email = fields.Char(string='Email ID')
    shipper_address = fields.Char(string='Address', required=True)

    # ── Receiver Info ──────────────────────────────────────────────────
    destination = fields.Char(string='Destination', required=True)
    receiver_name = fields.Char(string='Receiver Name', required=True)
    receiver_mobile = fields.Char(string='Mobile', required=True)
    receiver_tel = fields.Char(string='Tel')
    receiver_company = fields.Char(string='Company')
    receiver_email = fields.Char(string='Email ID')
    receiver_address = fields.Char(string='Address', required=True)

    # ── Cargo Details ──────────────────────────────────────────────────
    weight = fields.Float(string='Weight', required=True)
    pieces = fields.Integer(string='Pieces', required=True, default=1)
    carrier = fields.Char(string='Carrier', required=True)
    airway_bill = fields.Char(string='Airway Bill')
    product_info = fields.Text(string='Product Info', required=True)
    special_info = fields.Text(string='Special Info')
    paymode = fields.Selection(
        [('cash', 'Cash'), ('card', 'Card'), ('company', 'Company')],
        string='Paymode',
        default='cash',
        required=True,
    )
    status = fields.Char(string='Status', default='ORDER PLACED', required=True)

    # ── Financials ─────────────────────────────────────────────────────
    net_amount = fields.Float(string='Net Amount', required=True)
    vat_amount = fields.Float(string='VAT 15%')
    extra_charge = fields.Float(string='Extra Charge')
    gross_total = fields.Float(
        string='Gross Total',
        compute='_compute_gross_total',
        store=True,
    )

    @api.depends('net_amount', 'vat_amount', 'extra_charge')
    def _compute_gross_total(self):
        for rec in self:
            rec.gross_total = rec.net_amount + rec.vat_amount + rec.extra_charge

    @api.onchange('shipment_type', 'net_amount')
    def _onchange_compute_vat(self):
        if self.shipment_type == 'domestic':
            self.vat_amount = round(self.net_amount * 0.15, 2)
        else:
            self.vat_amount = 0.0

    @api.constrains('shipper_mobile')
    def _check_shipper_mobile(self):
        for rec in self:
            if rec.shipper_mobile and not re.match(r'^[\d\s\+\-()]{7,20}$', rec.shipper_mobile):
                raise ValidationError('Shipper Mobile: Enter a valid phone number (7-20 digits).')

    @api.constrains('receiver_mobile')
    def _check_receiver_mobile(self):
        for rec in self:
            if rec.receiver_mobile and not re.match(r'^[\d\s\+\-()]{7,20}$', rec.receiver_mobile):
                raise ValidationError('Receiver Mobile: Enter a valid phone number (7-20 digits).')

    @api.constrains('shipper_email')
    def _check_shipper_email(self):
        for rec in self:
            if rec.shipper_email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', rec.shipper_email):
                raise ValidationError('Shipper Email: Enter a valid email address.')

    @api.constrains('receiver_email')
    def _check_receiver_email(self):
        for rec in self:
            if rec.receiver_email and not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', rec.receiver_email):
                raise ValidationError('Receiver Email: Enter a valid email address.')

    @api.constrains('net_amount')
    def _check_net_amount(self):
        for rec in self:
            if rec.net_amount < 0:
                raise ValidationError('Net Amount cannot be negative.')

    @api.constrains('weight')
    def _check_weight(self):
        for rec in self:
            if rec.weight <= 0:
                raise ValidationError('Weight must be greater than zero.')

    @api.constrains('pieces')
    def _check_pieces(self):
        for rec in self:
            if rec.pieces <= 0:
                raise ValidationError('Pieces must be at least 1.')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('invoice_number', 'New') == 'New':
                vals['invoice_number'] = self.env['ir.sequence'].next_by_code(
                    'cargo.manual.invoice'
                ) or 'New'
        return super().create(vals_list)

    def action_print_invoice(self):
        return self.env.ref(
            'cargo_manual_invoicing.action_report_cargo_invoice'
        ).report_action(self)