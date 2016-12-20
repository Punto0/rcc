# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class product_template(osv.Model):
    _inherit = ["product.template"]
    _name = 'product.template'

    _columns = {
        'cp_price': fields.property(type = 'float', digits_compute=dp.get_precision('Product Price'), 
                                          help="Price for Collective Purchases. "
                                               "Expressed in the default unit of measure of the product.",
                                          string="Collective Purchase Price"),
        'cp_ok': fields.boolean("The product can be sold in Collective Purchases"),
        'sale_ok': fields.boolean(help="It can be sold individually through the normal shop", string="Allow Single Orders"),
        'purchase_ok': fields.boolean(help="It can sold in batchs through collective purchases", string="Allow Collective Orders"),
    }

    _defaults = {
        'purchase_ok': False,
    } 
