# -*- coding: utf-8 -*-
from openerp import http

# class CollectivePurchase(http.Controller):
#     @http.route('/collective_purchase/collective_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/collective_purchase/collective_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('collective_purchase.listing', {
#             'root': '/collective_purchase/collective_purchase',
#             'objects': http.request.env['collective_purchase.collective_purchase'].search([]),
#         })

#     @http.route('/collective_purchase/collective_purchase/objects/<model("collective_purchase.collective_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('collective_purchase.object', {
#             'object': obj
#         })