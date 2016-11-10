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
                                          help="Cost price for Collective Purchases. "
                                               "Expressed in the default unit of measure of the product.",
                                          string="Cost Price"),
        'cp_ok': fields.boolean("Can be purchased in Collective Purchases")
    }
