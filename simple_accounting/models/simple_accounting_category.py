from odoo import models, fields

class SimpleAccountingCategory(models.Model):
    _name = 'simple.accounting.category'
    _description = 'Accounting Category'
    _order = 'name asc'

    name = fields.Char(string='Category Name', required=True)
    type = fields.Selection([
        ('income', 'Income'),
        ('expense', 'Expense')
    ], string='Default Type', required=True, default='expense')
    
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The category name must be unique!')
    ]
