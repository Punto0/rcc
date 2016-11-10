"""
class PurchaseCollectiveOrderLine(models.Model):
    _name = 'purchase_collective.order_line'
    _inherit = 'purchase.order.line'  
    _description = 'Collective Purchase Order Line'

    order_id = fields.Many2one('purchase_collective.order','Collective Order Reference',select=True,required=True,ondelete='cascade')
    payed = fields.Boolean('Payment done')
    delivered = fields.Boolean('Delivered')

    button_invisible = fields.Boolean('button inv', compute='button_inv')

    @api.multi
    def button_save_data(self):
        cr, uid, context = self.env.cr, self.env.user, self.env.context
        self.order_id.subscribe(uid.partner_id)
        self.order_id.onchange_order_line()
        return True

    # Set the price_unit so the user can see it in the form but not change it
    def check_price(self, cr, uid, desconocido, product_id):
       _logger.info("check_price : uid : %s -- desconocido : %s -- product_id : %s" %(uid,desconocido,product_id))
       res = {'value': {'price_unit' : '0'} }
       warning = {}
       #purchase_price = None
       if product_id:
           purchase_price = self.pool.get('product.product').browse(cr, SUPERUSER_ID, product_id).standard_price
           _logger.info("purchase_price : %s" %purchase_price)
           res = {'value': {'price_unit' : purchase_price}}
           #warning = {  
           #    'title': _("Warning"),  
           #    'message': _('You can not change the price.'),  
           #}
       return {'value': res.get('value'), 'warning':warning}

    def create(self, cr, uid, vals, context = None):
        #_logger.info("Create order line uid : %s -- vals : %s -- context : %s " %(uid,vals, context))
        if not vals.get('price_unit'):
            product_id = vals.get('product_id')
            price = self.check_price(cr, uid, 'a', product_id)
            vals['price_unit'] = price['value']['price_unit']
        #logging.info("price_unit : %s " %vals.get('price_unit'))

        context = dict(context or {}, mail_create_nolog=True)
        order_line_id =  super(PurchaseCollectiveOrderLine, self).create(cr, uid, vals, context=context)
        self.browse(cr, uid, order_line_id).button_save_data()
        return order_line_id

    @api.one
    def button_manual_payment(self):
        cr, uid, context = self.env.cr, self.env.user, self.env.context
        _logger.info("Manual payment  context : %s" %context)
        _logger.info("uid : %s -- created by : %s" %(uid, self.create_uid))
        if uid.id == self.create_uid.id:
            self.payed = True
            self.action_confirm()
        else:
            raise Warning(_('You can not pay a order line that not belongs to you'))
        return True 
    @api.one
    def button_faircoin_payment(self):
        cr, uid, context = self.env.cr, self.env.user, self.env.context
        _logger.info("faircoin payment  context : %s" %context)
        _logger.info("uid : %s -- created by : %s" %(uid, self.create_uid))
        if uid.id == self.create_uid.id:
            self.payed = True
            self.action_confirm()
        else:
            raise Warning(_('You can not pay a order line that not belongs to you'))
        return True

    @api.one
    def button_getfaircoin_payment(self):
        cr, uid, context = self.env.cr, self.env.user, self.env.context
        _logger.info("getaircoin payment  context : %s" %context)
        _logger.info("uid : %s -- created by : %s" %(uid, self.create_uid))
        if uid.id == self.create_uid.id:
            self.payed = True
            self.action_confirm()
        else:
            raise Warning(_('You can not pay a order line that not belongs to you'))
        return True

    @api.one
    def button_inv(self):
        cr, uid, context = self.env.cr, self.env.user, self.env.context
        _logger.info("uid : %s -- create_uid : %s" %(uid.id,self.create_uid.id))
        if uid.id == self.create_uid.id:
            _logger.info("return true")
            self.button_invisible = True   
            return True 
        else:
            _logger.info("return false")
            self.button_invisible = False 
            return False

    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        """
        # onchange handler of product_id.
        """
        if context is None:
            context = {}

        res = {'value': {'price_unit': price_unit or 9.9, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            if not uom_id:
                uom_id = self.default_get(cr, uid, ['product_uom'], context=context).get('product_uom', False)
                res['value']['product_uom'] = uom_id
            return res

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')

        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, SUPERUSER_ID, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name or not uom_id:
            # The 'or not uom_id' part of the above condition can be removed in master. See commit message of the rev. introducing this line.
            dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
            if product.description_purchase:
                name += '\n' + product.description_purchase
            res['value'].update({'name': name})

        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id

        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.datetime.now()

      
        supplierinfo = False
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        #dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or 1.0
        #res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})

        price = price_unit
        _logger.info("price %s " %price)

        if price_unit is False or price_unit is None:
            # - determine price_unit and taxes_id
            if pricelist_id:
                date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product.id, qty or 1.0, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
            else:
                price = product.standard_price

        if uid == SUPERUSER_ID:
            company_id = self.pool['res.users'].browse(cr, uid, [uid]).company_id.id
            taxes = product.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id)
        else:
            taxes = product.supplier_taxes_id
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes, context=context)
        #price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, product.supplier_taxes_id, taxes_ids)
        # added, falla por algún lado y no actualiza el precio correctamente para usuarios distintos del creador de la orden
        price = product.standard_price
        _logger.info("price %s " %price)
        res['value'].update({'price_unit': price, 'taxes_id': taxes_ids})
        return res

    product_id_change = onchange_product_id

##############################################
"""
