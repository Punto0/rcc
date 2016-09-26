url = 'http://vps311858.ovh.net:8069'
db = 'rcc2'
username = 'admin'
password = 'testpass'

import xmlrpclib

#conexión básica sin autenticar
common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
common.version() # devuelve versión si ok

#autenticar usuario, devuelve el uid a usar después
uid = common.authenticate(db, username, password, {})

models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

# ejecutar un método del modelo
models.execute_kw(db, uid, password,'res.partner', 'check_access_rights', ['read'], {'raise_exception': False})

#listar registros
models.execute_kw(db, uid, password, 'res.partner', 'search', [[['is_company', '=', True], ['customer', '=', True]]])

#paginación de resultados
models.execute_kw(db, uid, password, 'res.partner', 'search', [[['is_company', '=', True], ['customer', '=', True]]], {'offset': 10, 'limit': 5})

#contar resultados
models.execute_kw(db, uid, password, 'res.partner', 'search_count', [[['is_company', '=', True], ['customer', '=', True]]])

#Leer resultados, todos los campos 
ids = models.execute_kw(db, uid, password, 'res.partner', 'search', [[['is_company', '=', True], ['customer', '=', True]]], {'limit': 1})
[record] = models.execute_kw(db, uid, password,'res.partner', 'read', [ids])
# count the number of fields fetched by default
len(record)

# Conversedly, picking only three fields deemed interesting.
models.execute_kw(db, uid, password,'res.partner', 'read',[ids],{'fields': ['name', 'country_id', 'comment']}) 

#Listar campos del modelo
models.execute_kw(db, uid, password, 'res.partner', 'fields_get', [], {'attributes': ['string', 'help', 'type']})

#Atajo búsqueda y lectura
models.execute_kw(db, uid, password,'res.partner', 'search_read',[[['is_company', '=', True], ['customer', '=', True]]], {'fields': ['name', 'country_id', 'comment'], 'limit': 5})

#Crear objeto
id = models.execute_kw(db, uid, password, 'res.partner', 'create', [{'name': "New Partner", }])

#Actualizar objeto
models.execute_kw(db, uid, password, 'res.partner', 'write', [[id], {'name': "Newer partner" }])
# get record name after having changed it
models.execute_kw(db, uid, password, 'res.partner', 'name_get', [[id]])

#Borrar
models.execute_kw(db, uid, password, 'res.partner', 'unlink', [[id]])
# check if the deleted record is still in the database
models.execute_kw(db, uid, password,'res.partner', 'search', [[['id', '=', id]]])

# Señales en workflows
client = models.execute_kw(db, uid, password,'res.partner', 'search_read', [[('customer', '=', True)]], {'limit': 1, 'fields': ['property_account_receivable','property_payment_term','property_account_position']})[0]
invoice_id = models.execute_kw(db, uid, password,'account.invoice', 'create', [{'partner_id': client['id'],'account_id': client['property_account_receivable'][0],'invoice_line': [(0, False, {'name': "AAA"})]}])

models.exec_workflow(db, uid, password, 'account.invoice', 'invoice_open', invoice_id)

