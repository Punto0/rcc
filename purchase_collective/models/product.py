# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

class product_template(osv.Model):
    _inherit = ["product.template"]
    _name = 'product.template'

    _columns = {
        #'cp_price': fields.property(type = 'float', digits_compute=dp.get_precision('Product Price'), 
        #                                  help="Expressed in the default unit of measure of the product.",
        #                                  string="Price for Collective Purchases"),
        #'cp_ok': fields.boolean("The product can be sold in Collective Purchases" )
        'sale_ok': fields.boolean("Allow Single Orders",
                                 help="It can be sold individually through the normal shop"),
        'purchase_ok': fields.boolean("Allow Collective Purchase Orders",
                                 help="This usually implies a big number of stock and logistical operations. Please, ask to the FairMarket Team or the Collective Purchases Network if you want offer you products this way before applying"),
        'cp_order_id': fields.many2one('purchase_collective.order', 'Collective Purchase Allowed',
                                 help="This fields restricts the Collective Purchase wich can offered this product. Leave empty to allow in all Collective Purchases opened for the supllier"),
    }

    _defaults = {
        'sale_ok': True,    
        'purchase_ok': False,
    } 
