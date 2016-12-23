# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import time
import random
import logging
import pprint
from openerp import SUPERUSER_ID
import openerp.addons.decimal_precision as dp
from openerp.osv import osv, orm, fields
from openerp.addons.web.http import request
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class sale_order(osv.Model):
    _inherit = "sale.order"

    def _website_cp_product_id_change(self, cr, uid, ids, order_id, product_id, qty, line_id=None, context=None):
        so = self.pool.get('sale.order').browse(cr, uid, order_id, context=context)
        #logging.info("init website_cp_product_id_change -- Company : %s -- Sale Order : %s -- product_id : %s --" %(so.company_id.name, so.name, product_id))
        if not context:
            context = {}
        context = dict(context, company_id=so.company_id.id)
        #logging.info("Context : %s" %context)

        product = self.pool.get('product.product').browse(cr, SUPERUSER_ID, product_id, context)

        if not product.taxes_id: 
              product.write( { 'taxes_id' : [(4, 7)] } )
        #logging.info("taxes %s" %product.taxes_id)

        if not product:
            return {'value': {'th_weight': 0,'product_uos_qty': qty}, 'domain': {'product_uom': [],'product_uos': []}}
        #if not date_order:
        #	    date_order = time.strftime(DEFAULT_SERVER_DATE_FORMAT)

        result = {}
        result['tax_id'] = 7
        result['name'] = product.name
        if product.description_sale:
            result['name'] += '\n'+product.description_sale
        result['th_weight'] = qty * product.weight
        result['product_uos_qty'] = qty
        # override listas de precios, si se quieren usar hay que quitar esto
        result['price_unit'] = product.list_price
        result['product_id'] = product.id
        result['order_id'] = order_id
        logging.info("return : %s" %result)
        return result

        domain = {'product_uom': [],'product_uos': []}

        values = self.pool.get('sale.order.line').product_id_change(cr, SUPERUSER_ID, [], 
            pricelist=so.pricelist_id.id, 
            product=product.id, 
            partner_id=so.partner_id.id, 
            qty=qty,
            #fiscal_position=fp,
            context=context)['value']

        #logging.info("Values : %s" %values) 

        if line_id:
            line = self.pool.get('sale.order.line').browse(cr, SUPERUSER_ID, line_id, context=context)
            values['name'] = line.name
        else:
            values['name'] = product.description_sale and "%s\n%s" % (product.display_name, product.description_sale) or product.display_name
            values['price'] = product.list_price
            values['company_id'] = so.company_id
            #if values.get('tax_id') != None:
              #values['tax_id'] = [(6, 0, values['tax_id'])]
        #logging.info("Returning values : %s " %values)  
        return values
    
    def _cp_cart_update(self, cr, uid, ids, product_id=None, line_id=None, add_qty=0, set_qty=0, context=None, **kwargs):
        # Add or set product quantity, add_qty can be negative
        #logging.info("init cp_cart_update ids: %s -- product_id : %s " %(ids,product_id))
        #logging.info("context : %s " %(context))
        #logging.info("kwargs : %s " %kwargs)
        sol = self.pool.get('sale.order.line')
        for so in self.browse(cr, uid, ids, context=context):
            if so.state != 'draft':
                #request.session['purchase_order_id'] = None
                #raise osv.except_osv(_('Error!'), _('It is forbidden to modify a purchase order which is not in draft status'))
                request.website.purchase_reset() 
            if line_id != False:
                line_ids = so._cart_find_product_line(product_id, line_id, context=context, **kwargs)
                if line_ids:
                    line_id = line_ids[0]

            order_min = so.cp_order_id.qty_min 

            #logging.info("context cp Order : %s " %context.get('cp_order_id'))
            #logging.info("sale Order : %s ", pprint.pformat(so))
            #logging.info("Order parent : %s ", pprint.pformat(so.cp_order_id.id))
            #logging.info("order_min : %s -- add_qty : %s -- set_qty : %s " %(order_min, add_qty, set_qty))
            #order_min = order.qty_min
            # Create line if no line with product_id can be located
            if not line_id:
                values = self._website_product_id_change(cr, uid, ids, so.id, product_id, qty=1, context=context)
                logging.info("Creating sale.order.line with values : %s" %values)
                line_id = sol.create(cr, SUPERUSER_ID, values, context=context)
                if add_qty:
                  add_qty -= 1

            # compute new quantity
          
            if set_qty:
                quantity = set_qty

            elif add_qty != None:
                quantity = sol.browse(cr, SUPERUSER_ID, line_id, context=context).product_uom_qty + (add_qty or 0)

            if quantity < order_min:
                quantity = order_min 

            values = self._website_product_id_change(cr, uid, ids, so.id, product_id, qty=quantity, line_id=line_id, context=context)
            values['product_uom_qty'] = quantity
            sol.write(cr, SUPERUSER_ID, [line_id], values, context=context)

        #logging.info("cart update returning : %s -- %s" %(line_id, quantity))
        return {'line_id': line_id, 'quantity': quantity}

        # Actualizamos el total de la orden colectiva y subscribimos el usuario al muro
        def action_button_confirm(self, cr, uid, ids, context=None):
            if self.is_cp:
                cp_order = self.pool.get('purchase_collective.order').browse(cr, SUPERUSER_ID, self.cp_order_id, context=context)
                cp_order.onchange_order_line(cr, uid, self.cp_order_id)
                cp_order.subscribe(cr, uid, [])
            return super(sale_order, self).action_button_confirm(cr, uid, ids, context=context)

class website(orm.Model):
    _inherit = 'website'

    def purchase_product_domain(self, cr, uid, ids, context=None):
        return [("purchase_ok", "=", True)]

    def purchase_get_order(self, cr, uid, ids, force_create=False, code=None, update_pricelist=None, cp_order_id=None, context=None):
        #logging.info("init purchase_get_order - ids %s" %ids)
        purchase_order_obj = self.pool['sale.order']
        purchase_order_id = request.session.get('purchase_order_id')
        purchase_order = None

        # Test validity of the purchase_order_id
        if purchase_order_id and purchase_order_obj.exists(cr, SUPERUSER_ID, purchase_order_id, context=context):
            purchase_order = purchase_order_obj.browse(cr, SUPERUSER_ID, purchase_order_id, context=context)
        else:
            purchase_order_id = None
        if cp_order_id:
            parent = cp_order_id
        else:
            parent = context.get('cp_order_id')
        # create so if needed
        if not purchase_order_id and (force_create or code):
            logging.info("Creating sale order with cp parent : %s -- %s" %(cp_order_id,parent))
            # TODO cache partner_id session
            partner = self.pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context).partner_id

            for w in self.browse(cr, uid, ids):
                values = {
                    'is_cp' : True,
                    'cp_order_id' : parent,
                    'user_id': w.user_id.id,
                    'partner_id': partner.id,
                    'pricelist_id': partner.property_product_pricelist.id,
                    'fiscal_position':2  
                    #'section_id': self.pool.get('ir.model.data').get_object_reference(cr, uid, 'website', 'salesteam_website_sales')[1],
                }
                purchase_order_id = purchase_order_obj.create(cr, SUPERUSER_ID, values, context=context)
                values = purchase_order_obj.onchange_partner_id(cr, SUPERUSER_ID, [], partner.id, context=context)['value']
                purchase_order_obj.write(cr, SUPERUSER_ID, [purchase_order_id], values, context=context)
                request.session['purchase_order_id'] = purchase_order_id
                request.session['cp_order_id'] = parent
                purchase_order = purchase_order_obj.browse(cr, SUPERUSER_ID, purchase_order_id, context=context)

        if purchase_order_id:
            # TODO cache partner_id session
            partner = self.pool['res.users'].browse(cr, SUPERUSER_ID, uid, context=context).partner_id
            # check for change of pricelist with a coupon
            if code and code != purchase_order.pricelist_id.code:
                pricelist_ids = self.pool['product.pricelist'].search(cr, SUPERUSER_ID, [('code', '=', code)], context=context)
                if pricelist_ids:
                    pricelist_id = pricelist_ids[0]
                    request.session['purchase_order_code_pricelist_id'] = pricelist_id
                    update_pricelist = True

            pricelist_id = request.session.get('purchase_order_code_pricelist_id') or partner.property_product_pricelist.id

            # check for change of partner_id ie after signup
            if purchase_order.partner_id.id != partner.id and request.website.partner_id.id != partner.id:
                flag_pricelist = False
                if pricelist_id != purchase_order.pricelist_id.id:
                    flag_pricelist = True
                fiscal_position = purchase_order.fiscal_position and purchase_order.fiscal_position.id or False

                values = purchase_order_obj.onchange_partner_id(cr, SUPERUSER_ID, [purchase_order_id], partner.id, context=context)['value']
                if values.get('fiscal_position'):
                    order_lines = map(int,sale.order.line)
                    values.update(purchase_order_obj.onchange_fiscal_position(cr, SUPERUSER_ID, [],
                        values['fiscal_position'], [[6, 0, order_lines]], context=context)['value'])

                values['partner_id'] = partner.id

                if flag_pricelist or values.get('fiscal_position', False) != fiscal_position:
                    update_pricelist = True

            # update the pricelist
            if update_pricelist:
                values = {'pricelist_id': pricelist_id}
                values.update(purchase_order.onchange_pricelist_id(pricelist_id, None)['value'])
                purchase_order.update(values)
                for line in purchase_order.order_line:
                    if line.exists():
                        purchase_order._cart_update(product_id=line.product_id.id, line_id=line.id, add_qty=0)

            # update browse record
            if (code and code != purchase_order.pricelist_id.code) or purchase_order.partner_id.id !=  partner.id:
                purchase_order = purchase_order_obj.browse(cr, SUPERUSER_ID, purchase_order.id, context=context)

        else:
            request.session['purchase_order_id'] = None
            return None
        #logging.info("end get_purchase_order - return : %s -- %s" %(purchase_order.id, purchase_order.name))
        return purchase_order

    def purchase_get_transaction(self, cr, uid, ids, context=None):
        transaction_obj = self.pool.get('payment.transaction')
        tx_id = request.session.get('purchase_transaction_id')
        if tx_id:
            tx_ids = transaction_obj.search(cr, SUPERUSER_ID, [('id', '=', tx_id), ('state', 'not in', ['cancel'])], context=context)
            if tx_ids:
                return transaction_obj.browse(cr, SUPERUSER_ID, tx_ids[0], context=context)
            else:
                request.session['purchase_transaction_id'] = False
        return False

    def purchase_reset(self, cr, uid, ids, context=None):
        #order = request.website.sale_get_order()
        #if order:
        #    for line in order.website_order_line:
        #        line.unlink()
        #order = request.website.purchase_get_order()
        #if order:
        #    for line in order.website_order_line:
        #        line.unlink()
        request.session.update({
            'purchase_order_id': False,
            #'purchase_transaction_id': False,
            #'purchase_order_code_pricelist_id': False,
            'cp_order_id': False,
            #'sale_order_id': False,   
        })
        
