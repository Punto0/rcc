# -*- coding: utf-8 -*-

import logging

from openerp import models, fields, api, osv, _, SUPERUSER_ID

_logger = logging.getLogger(__name__)

class PurchaseCollectiveOrderLine(models.Model):
    _name = 'purchase_collective.order_line'
    _inherit = 'purchase.order.line'  
    _description = 'Collective Purchase Order Line'

    order_id = fields.Many2one('purchase_collective.order','Collective Order Reference',select=True,required=True,ondelete='cascade')
    payed = fields.Boolean('Payment done')
    delivered = fields.Boolean('Delivered')

    @api.multi
    def button_save_data(self):
        cr, uid, context = self.env.cr, self.env.user, self.env.context
        self.order_id.subscribe(uid.partner_id)
        self.order_id.onchange_order_line()
        return True

    # Set the price_unit so the user can see it in the form but not change it
    def check_price(self, cr, uid, desconocido, product_id, unit_price):
       _logger.info("check_price : uid : %s -- desconocido : %s -- product_id : %s -- unit_price: %s" %(uid,desconocido,product_id,unit_price))
       res = {'value': {'price_unit' : '0'} }
       warning = {}
       purchase_price = None
       if product_id:
           purchase_price = self.pool.get('product.product').browse(cr, uid, product_id).standard_price
           #warning = {  
           #    'title': _("Warning"),  
           #    'message': _('Unit price given, is different than the purchase price of the selected product setup by the supplier.'),  
           #}
           res = {'value': {'price_unit' : purchase_price}}
       return {'value': res.get('value'), 'warning':warning}

    def create(self, cr, uid, vals, context = None):
        _logger.info("Create order line uid : %s -- vals : %s -- context : %s " %(uid,vals, context))
        if not vals.get('price_unit'):
            product_id = vals.get('product_id')
            price = self.check_price(cr, uid, 'a', product_id, '1.0')
            vals['price_unit'] = price['value']['price_unit']
        logging.info("price_unit : %s " %vals.get('price_unit'))

        context = dict(context or {}, mail_create_nolog=True)
        order_line_id =  super(PurchaseCollectiveOrderLine, self).create(cr, uid, vals, context=context)
        self.browse(cr, uid, order_line_id).button_save_data()
        return order_line_id

##############################################

class PurchaseCollectiveOrder(models.Model):
    _name = 'purchase_collective.order'
    _inherit = ['purchase.order',]  
    _description = 'Collective Purchases'

    
    order_line = fields.One2many('purchase_collective.order_line','order_id','Collective Order Lines',states={'approved':[('readonly',True)],'done':[('readonly',True)]},copy=True )

    deadline_date = fields.Date(string='Order Deadline', required=True, help="This is the end date of the order. Place your orders before this date")
    
    amount_untaxed = fields.Float('Amount untaxed',compute="onchange_order_line")
    amount_tax = fields.Float('Taxes',compute="onchange_order_line")
    amount_total = fields.Float('Amount Total',compute="onchange_order_line")

    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip', size=24)
    city = fields.Char('City')
    state_id = fields.Many2one("res.country.state", 'State', ondelete='restrict')
    country_id = fields.Many2one('res.country', 'Country', ondelete='restrict')
    email = fields.Char('Email')
    phone = fields.Char('Phone')
    #fax = fields.Char('Fax')
    mobile = fields.Char('Mobile')

    @api.onchange('order_line') 
    def onchange_order_line(self, cr, uid, ids, args=None):
        #_logger.info("cr: %s -- uid : %s -- ids : %s -- args: %s" %(cr,uid,ids,args))

        #cr, uid, context = self.env.cr, self.env.user, self.env.context
        #res = {}
        #cur_obj=self.pool.get('res.currency')
        #line_obj = self.pool['purchase.collective.order.line']

        res = {
                'amount_untaxed': 0.0,
                'amount_tax': 0.0,
                'amount_total': 0.0,
        }

        val = val1 = 0.0

        order = self.browse(cr, SUPERUSER_ID, ids)
        #_logger.info("order %s " %order.id)

        if order:
            cur = order.pricelist_id.currency_id
            for line in order.order_line:
                val1 += line.price_subtotal
                #line_price = line._calc_line_base_price(cr, uid, context=context)
                #line_qty = line._calc_line_quantity(cr, uid, context=context)
                for c in self.pool['account.tax'].compute_all(cr, uid, line.taxes_id, line.price_unit, line.product_qty, line.product_id, order.partner_id)['taxes']:
                    val += c.get('amount', 0.0)

            #_logger.info("Vals : %s -- %s " %(val, val1))

            res['amount_tax']=cur.round(val)
            res['amount_untaxed']=cur.round(val1)
            res['amount_total']=res['amount_untaxed'] + res['amount_tax']

            #_logger.info("Res : %s " %res)

            order.write({'amount_untaxed': res['amount_untaxed']})
            order.write({'amount_tax': res['amount_tax']})
            order.write({'amount_total': res['amount_total']})

        return res
    
    @api.multi 
    def subscribe(self, partner):
        self.message_subscribe(partner_ids=[(partner.id)])
        self.message_post(body=("Order line created by %s" %(partner.name)))
  
    @api.multi
    def button_details(self):
       context = self.env.context.copy()
       view_id = self.env.ref(
            'purchase_collective.'
            'purchase_order_line_button_form_view2').id

       context['default_partner_id'] = self.partner_id.id
       context['default_order_id'] = self.id 
       context['default_pricelist_id'] = self.pricelist_id.id
       context['default_order_date'] = self.date_order
       context['default_date_planned'] = self.deadline_date
       context['view_buttons'] = True
       #context['fiscal_position'] = self.fiscal_position
       #context['state'] = self.state
       #context['parent'] = self.id

       #partial_id = self.pool.get("purchase.collective.order.line").create(context=context)

       view = {
            'name': _('Details'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase_collective.order_line',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'readonly': False,
            #'res_id': partial_id,
            'context': context
       }
       return view

    def _get_order(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('purchase_collective.order_line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()
    
    def create(self, cr, uid, vals, context=None):
        logging.info("Creating order %s" %vals)  
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase_collective.order', context=context) or '/'
        if not vals.get('location_id'):
            for user_obj in self.pool.get('res.users').browse(cr, uid, [uid], context =context):
                vals['location_id'] = user_obj.partner_id.property_stock_supplier.id
                logging.info('adding location info %s' %vals.get('location_id'))
        if not vals.get('pricelist_id'):        
            for user_obj in self.pool.get('res.users').browse(cr, uid, [uid], context =context):
                vals['pricelist_id'] = user_obj.partner_id.property_product_pricelist_purchase.id
                logging.info('adding pricelist %s' %vals.get('pricelist_id'))


        context = dict(context or {}, mail_create_nolog=True)
        order =  super(PurchaseCollectiveOrder, self).create(cr, uid, vals, context=context)
        #self.message_post(cr, uid, [order], body=("RFQ created"), context=context)
        return order

    def unlink(self, cr, uid, ids, context=None):
        purchase_orders = self.read(cr, uid, ids, ['state'], context=context)
        unlink_ids = []
        for s in purchase_orders:
            if s['state'] in ['draft','cancel']:
                unlink_ids.append(s['id'])
            else:
                raise osv.except_osv(_('Invalid Action!'), _('In order to delete a purchase order, you must cancel it first.'))

        # automatically sending subflow.delete upon deletion
        self.signal_workflow(cr, uid, unlink_ids, 'purchase_cancel')

        return super(PurchaseCollectiveOrder, self).unlink(cr, uid, unlink_ids, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        # FORWARDPORT UP TO SAAS-6
        new_id = super(PurchaseCollectiveOrder, self).copy(cr, uid, id, default=default, context=context)
        for po in self.browse(cr, uid, [new_id], context=context):
            for line in po.order_line:
                vals = self.pool.get('purchase_collective.order_line').onchange_product_id(
                    cr, uid, line.id, po.pricelist_id.id, line.product_id.id, line.product_qty,
                    line.product_uom.id, po.partner_id.id, date_order=po.date_order, context=context
                )
                if vals.get('value', {}).get('date_planned'):
                    line.write({'date_planned': vals['value']['date_planned']})
        return new_id

    def set_order_line_status(self, cr, uid, ids, status, context=None):
        line = self.pool.get('purchase_collective.order_line')
        order_line_ids = []
        proc_obj = self.pool.get('procurement.order')
        for order in self.browse(cr, uid, ids, context=context):
            if status in ('draft', 'cancel'):
                order_line_ids += [po_line.id for po_line in order.order_line]
            else: # Do not change the status of already cancelled lines
                order_line_ids += [po_line.id for po_line in order.order_line if po_line.state != 'cancel']
        if order_line_ids:
            line.write(cr, uid, order_line_ids, {'state': status}, context=context)
        if order_line_ids and status == 'cancel':
            procs = proc_obj.search(cr, uid, [('purchase_line_id', 'in', order_line_ids)], context=context)
            if procs:
                proc_obj.write(cr, uid, procs, {'state': 'exception'}, context=context)
        return True

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not any(line.state != 'cancel' for line in po.order_line):
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            if po.invoice_method == 'picking' and not any([l.product_id and l.product_id.type in ('product', 'consu') and l.state != 'cancel' for l in po.order_line]):
                raise osv.except_osv(
                    _('Error!'),
                    _("You cannot confirm a purchase order with Invoice Control Method 'Based on incoming shipments' that doesn't contain any stockable item."))
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)        
        self.pool.get('purchase_collective.order_line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid}, context=context)
        return True

    def _set_po_lines_invoiced(self, cr, uid, ids, context=None):
        for po in self.browse(cr, uid, ids, context=context):
            is_invoiced = []
            if po.invoice_method == 'picking':
                # We determine the invoiced state of the PO line based on the invoiced state
                # of the associated moves. This should cover all possible cases:
                # - all moves are done and invoiced
                # - a PO line is split into multiple moves (e.g. if multiple pickings): some
                #   pickings are done, some are in progress, some are cancelled
                for po_line in po.order_line:
                    if (po_line.move_ids and
                            all(move.state in ('done', 'cancel') for move in po_line.move_ids) and
                            not all(move.state == 'cancel' for move in po_line.move_ids) and
                            all(move.invoice_state == 'invoiced' for move in po_line.move_ids if move.state == 'done')
                            and po_line.invoice_lines and all(line.invoice_id.state not in ['draft', 'cancel'] for line in po_line.invoice_lines)):
                        is_invoiced.append(po_line.id)
                    elif po_line.product_id.type == 'service':
                        is_invoiced.append(po_line.id)
            else:
                for po_line in po.order_line:
                    if (po_line.invoice_lines and 
                            all(line.invoice_id.state not in ['draft', 'cancel'] for line in po_line.invoice_lines)):
                        is_invoiced.append(po_line.id)
            if is_invoiced:
                self.pool['purchase_collective.order_line'].write(cr, uid, is_invoiced, {'invoiced': True})
            workflow.trg_write(uid, 'purchase_colective.order', po.id, cr)

    def wkf_confirm_order(self, cr, uid, ids, context=None):
        todo = []
        for po in self.browse(cr, uid, ids, context=context):
            if not any(line.state != 'cancel' for line in po.order_line):
                raise osv.except_osv(_('Error!'),_('You cannot confirm a purchase order without any purchase order line.'))
            if po.invoice_method == 'picking' and not any([l.product_id and l.product_id.type in ('product', 'consu') and l.state != 'cancel' for l in po.order_line]):
                raise osv.except_osv(
                    _('Error!'),
                    _("You cannot confirm a purchase order with Invoice Control Method 'Based on incoming shipments' that doesn't contain any stockable item."))
            for line in po.order_line:
                if line.state=='draft':
                    todo.append(line.id)        
        self.pool.get('purchase_collective.order_line').action_confirm(cr, uid, todo, context)
        for id in ids:
            self.write(cr, uid, [id], {'state' : 'confirmed', 'validator' : uid}, context=context)
        return True

    def action_picking_create(self, cr, uid, ids, context=None):
        for order in self.browse(cr, uid, ids):
            picking_vals = {
                'picking_type_id': order.picking_type_id.id,
                'partner_id': order.partner_id.id,
                'date': order.date_order,
                'origin': order.name
            }
            picking_id = self.pool.get('stock.picking').create(cr, uid, picking_vals, context=context)
            # esta llamada da fallo
            #self._create_stock_moves(cr, uid, order, order.order_line, picking_id, context=context)
        return picking_id


###################################################



